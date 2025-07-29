import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LineTalkParser:
    """LINEトーク履歴ファイルを解析するクラス"""
    
    def __init__(self):
        # LINEメッセージの正規表現パターン（複数形式対応）
        # 形式1: [2025/01/15 12:34] 田中: おはよう！
        self.message_pattern1 = re.compile(
            r'\[(\d{4}/\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})\]\s+([^:]+):\s*(.+)'
        )
        
        # 形式2: 21:47 佐藤 だいすき（タブ区切り）
        self.message_pattern2 = re.compile(
            r'^(\d{1,2}:\d{2})\s+([^\t]+)\s+(.+)$'
        )
        
        # システムメッセージのパターン
        # 例: [2025/01/15 12:34] 田中がグループに参加しました。
        self.system_pattern = re.compile(
            r'\[(\d{4}/\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})\]\s+(.+)'
        )
    
    def parse_file(self, file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """
        LINEトークファイルを解析してDataFrameに変換
        
        Args:
            file_path: トークファイルのパス
            encoding: ファイルエンコーディング
            
        Returns:
            解析されたメッセージのDataFrame（元の順番を保持）
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8で失敗した場合はShift_JISで試行
            try:
                with open(file_path, 'r', encoding='shift_jis') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"ファイル読み込みエラー: {e}")
                raise
        
        messages = []
        lines = content.split('\n')
        
        current_date = None
        line_number = 0  # 行番号を追加して順番を保持
        
        for line in lines:
            line_number += 1
            line = line.strip()
            if not line:
                continue
            
            # 日付行の検出（例: 2023/07/13(木)）
            date_match = re.match(r'^(\d{4}/\d{1,2}/\d{1,2})\([月火水木金土日]\)$', line)
            if date_match:
                current_date = date_match.group(1)
                continue
                
            # 形式1: [2025/01/15 12:34] 田中: おはよう！
            match1 = self.message_pattern1.match(line)
            if match1:
                date_str, time_str, sender, message = match1.groups()
                try:
                    datetime_obj = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
                    messages.append({
                        'line_number': line_number,  # 行番号を追加
                        'datetime': datetime_obj,
                        'date': date_str,
                        'time': time_str,
                        'sender': sender.strip(),
                        'message': message.strip(),
                        'type': 'message',
                        'original_line': line  # 元の行を保持
                    })
                except ValueError as e:
                    logger.warning(f"日時解析エラー: {line} - {e}")
                    continue
            
            # 形式2: 21:47 佐藤 だいすき（タブ区切り）
            elif current_date:
                match2 = self.message_pattern2.match(line)
                if match2:
                    time_str, sender, message = match2.groups()
                    try:
                        datetime_obj = datetime.strptime(f"{current_date} {time_str}", "%Y/%m/%d %H:%M")
                        messages.append({
                            'line_number': line_number,  # 行番号を追加
                            'datetime': datetime_obj,
                            'date': current_date,
                            'time': time_str,
                            'sender': sender.strip(),
                            'message': message.strip(),
                            'type': 'message',
                            'original_line': line  # 元の行を保持
                        })
                    except ValueError as e:
                        logger.warning(f"日時解析エラー: {line} - {e}")
                        continue
            
            # システムメッセージを解析
            else:
                sys_match = self.system_pattern.match(line)
                if sys_match:
                    date_str, time_str, system_message = sys_match.groups()
                    try:
                        datetime_obj = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
                        messages.append({
                            'line_number': line_number,  # 行番号を追加
                            'datetime': datetime_obj,
                            'date': date_str,
                            'time': time_str,
                            'sender': 'システム',
                            'message': system_message.strip(),
                            'type': 'system',
                            'original_line': line  # 元の行を保持
                        })
                    except ValueError as e:
                        logger.warning(f"システムメッセージ日時解析エラー: {line} - {e}")
                        continue
        
        if not messages:
            raise ValueError("有効なメッセージが見つかりませんでした")
        
        # DataFrameに変換して行番号順にソート（元の順番を保持）
        df = pd.DataFrame(messages)
        df = df.sort_values('line_number').reset_index(drop=True)
        
        # 日時の整合性チェック
        self._validate_datetime_order(df)
        
        logger.info(f"解析完了: {len(df)}件のメッセージを処理しました")
        return df
    
    def _validate_datetime_order(self, df: pd.DataFrame) -> None:
        """
        日時の順番をチェックして、異常があれば警告を出す
        
        Args:
            df: 解析されたメッセージのDataFrame
        """
        if len(df) < 2:
            return
        
        # 日時の順番をチェック
        datetime_issues = []
        for i in range(1, len(df)):
            current_dt = df.iloc[i]['datetime']
            prev_dt = df.iloc[i-1]['datetime']
            
            # 前のメッセージより時間が早い場合
            if current_dt < prev_dt:
                datetime_issues.append({
                    'line': i + 1,
                    'current': current_dt,
                    'previous': prev_dt,
                    'difference': (prev_dt - current_dt).total_seconds() / 60  # 分単位
                })
        
        if datetime_issues:
            logger.warning(f"日時の順番に {len(datetime_issues)} 件の異常を検出しました")
            for issue in datetime_issues[:5]:  # 最初の5件のみ表示
                logger.warning(f"行 {issue['line']}: {issue['current']} が {issue['previous']} より {issue['difference']:.1f}分早い")
            
            if len(datetime_issues) > 5:
                logger.warning(f"... 他 {len(datetime_issues) - 5} 件の異常があります")
        else:
            logger.info("日時の順番は正常です")
    
    def get_original_order_info(self, df: pd.DataFrame) -> Dict:
        """
        元の順番に関する情報を取得
        
        Args:
            df: 解析されたメッセージのDataFrame
            
        Returns:
            順番に関する情報
        """
        if df.empty:
            return {}
        
        # 日時順と行番号順の比較
        datetime_order = df.sort_values('datetime').reset_index(drop=True)
        line_order = df.sort_values('line_number').reset_index(drop=True)
        
        # 順番が異なる箇所を検出
        order_differences = []
        for i in range(len(df)):
            if datetime_order.iloc[i]['line_number'] != line_order.iloc[i]['line_number']:
                order_differences.append({
                    'position': i + 1,
                    'datetime_order_line': datetime_order.iloc[i]['line_number'],
                    'line_order_line': line_order.iloc[i]['line_number']
                })
        
        return {
            'total_messages': len(df),
            'order_differences_count': len(order_differences),
            'order_differences': order_differences[:10],  # 最初の10件のみ
            'uses_original_order': len(order_differences) == 0
        }
    
    def get_speakers(self, df: pd.DataFrame) -> List[str]:
        """会話参加者を取得"""
        return df[df['type'] == 'message']['sender'].unique().tolist()
    
    def detect_main_speaker(self, df: pd.DataFrame) -> str:
        """
        ファイルの1行目から参加者名を自動特定し、メインコンテンツの表示対象を決定
        
        Args:
            df: 解析されたメッセージのDataFrame
            
        Returns:
            メインコンテンツの表示対象となる参加者名（1行目の参加者と同じ）
        """
        if df.empty:
            return ""
        
        # 1行目のメッセージを取得
        first_message = df.iloc[0]
        
        # 1行目の参加者名を取得
        first_speaker = first_message['sender']
        
        # 1行目の参加者をメインコンテンツの表示対象とする
        return first_speaker
    
    def get_date_range(self, df: pd.DataFrame) -> Tuple[str, str]:
        """会話の日付範囲を取得"""
        dates = df['date'].unique()
        return min(dates), max(dates)
    
    def filter_by_date(self, df: pd.DataFrame, target_date: str) -> pd.DataFrame:
        """指定日付のメッセージを抽出"""
        return df[df['date'] == target_date].copy()
    
    def filter_by_speaker(self, df: pd.DataFrame, speaker: str) -> pd.DataFrame:
        """指定発言者のメッセージを抽出"""
        return df[df['sender'] == speaker].copy()
    
    def search_messages(self, df: pd.DataFrame, keyword: str) -> pd.DataFrame:
        """キーワード検索"""
        if not keyword:
            return df
        return df[df['message'].str.contains(keyword, case=False, na=False)].copy()
    
    def get_daily_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """日別統計を取得"""
        daily_stats = df.groupby('date').agg({
            'message': 'count',
            'sender': lambda x: x[x != 'システム'].nunique()
        }).rename(columns={
            'message': 'message_count',
            'sender': 'speaker_count'
        })
        return daily_stats.reset_index()

# テスト用のサンプルデータ作成関数
def create_sample_data() -> str:
    """テスト用のサンプルLINEトークデータを作成"""
    sample_content = """[2025/01/15 12:34] 田中: おはよう〜！
[2025/01/15 12:35] 佐藤: おはよう！今日は晴れてるね
[2025/01/15 12:36] 田中: うん！散歩に行こうよ
[2025/01/15 12:37] 佐藤: いいね！どこ行く？
[2025/01/15 12:38] 田中: 公園でお弁当食べよう
[2025/01/15 12:39] 佐藤: 楽しみだな〜
[2025/01/16 09:15] 田中: おはようございます！
[2025/01/16 09:16] 佐藤: おはよう！今日も一日頑張ろう
[2025/01/16 09:17] 田中: うん！頑張る！
[2025/01/16 20:30] 田中: お疲れ様〜
[2025/01/16 20:31] 佐藤: お疲れ様！今日はどうだった？
[2025/01/16 20:32] 田中: 楽しかった！また明日も頑張ろうね
[2025/01/16 20:33] 佐藤: うん！おやすみ
[2025/01/16 20:34] 田中: おやすみ〜"""
    
    return sample_content

if __name__ == "__main__":
    # テスト実行
    parser = LineTalkParser()
    
    # サンプルデータでテスト
    sample_content = create_sample_data()
    with open('sample_line.txt', 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    try:
        df = parser.parse_file('sample_line.txt')
        print("解析結果:")
        print(df.head())
        print(f"\n発言者: {parser.get_speakers(df)}")
        print(f"日付範囲: {parser.get_date_range(df)}")
    except Exception as e:
        print(f"エラー: {e}") 