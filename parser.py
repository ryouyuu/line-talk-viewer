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
        # 形式1: [2025/01/15 12:34] ゆいな: おはよう！
        self.message_pattern1 = re.compile(
            r'\[(\d{4}/\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})\]\s+([^:]+):\s*(.+)'
        )
        
        # 形式2: 21:47 ゆうき だいすき（タブ区切り）
        self.message_pattern2 = re.compile(
            r'^(\d{1,2}:\d{2})\s+([^\t]+)\s+(.+)$'
        )
        
        # システムメッセージのパターン
        # 例: [2025/01/15 12:34] ゆいながグループに参加しました。
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
            解析されたメッセージのDataFrame
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
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 日付行の検出（例: 2023/07/13(木)）
            date_match = re.match(r'^(\d{4}/\d{1,2}/\d{1,2})\([月火水木金土日]\)$', line)
            if date_match:
                current_date = date_match.group(1)
                continue
                
            # 形式1: [2025/01/15 12:34] ゆいな: おはよう！
            match1 = self.message_pattern1.match(line)
            if match1:
                date_str, time_str, sender, message = match1.groups()
                try:
                    datetime_obj = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
                    messages.append({
                        'datetime': datetime_obj,
                        'date': date_str,
                        'time': time_str,
                        'sender': sender.strip(),
                        'message': message.strip(),
                        'type': 'message'
                    })
                except ValueError as e:
                    logger.warning(f"日時解析エラー: {line} - {e}")
                    continue
            
            # 形式2: 21:47 ゆうき だいすき（タブ区切り）
            elif current_date:
                match2 = self.message_pattern2.match(line)
                if match2:
                    time_str, sender, message = match2.groups()
                    try:
                        datetime_obj = datetime.strptime(f"{current_date} {time_str}", "%Y/%m/%d %H:%M")
                        messages.append({
                            'datetime': datetime_obj,
                            'date': current_date,
                            'time': time_str,
                            'sender': sender.strip(),
                            'message': message.strip(),
                            'type': 'message'
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
                            'datetime': datetime_obj,
                            'date': date_str,
                            'time': time_str,
                            'sender': 'システム',
                            'message': system_message.strip(),
                            'type': 'system'
                        })
                    except ValueError as e:
                        logger.warning(f"システムメッセージ日時解析エラー: {line} - {e}")
                        continue
        
        if not messages:
            raise ValueError("有効なメッセージが見つかりませんでした")
        
        # DataFrameに変換して日時順にソート
        df = pd.DataFrame(messages)
        df = df.sort_values('datetime').reset_index(drop=True)
        
        logger.info(f"解析完了: {len(df)}件のメッセージを処理しました")
        return df
    
    def get_speakers(self, df: pd.DataFrame) -> List[str]:
        """会話参加者を取得"""
        return df[df['type'] == 'message']['sender'].unique().tolist()
    
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
    sample_content = """[2025/01/15 12:34] ゆいな: おはよう〜！
[2025/01/15 12:35] ゆうき: おはよう！今日は晴れてるね
[2025/01/15 12:36] ゆいな: うん！散歩に行こうよ
[2025/01/15 12:37] ゆうき: いいね！どこ行く？
[2025/01/15 12:38] ゆいな: 公園でお弁当食べよう
[2025/01/15 12:39] ゆうき: 楽しみだな〜
[2025/01/16 09:15] ゆいな: おはようございます！
[2025/01/16 09:16] ゆうき: おはよう！今日も一日頑張ろう
[2025/01/16 09:17] ゆいな: うん！頑張る！
[2025/01/16 20:30] ゆいな: お疲れ様〜
[2025/01/16 20:31] ゆうき: お疲れ様！今日はどうだった？
[2025/01/16 20:32] ゆいな: 楽しかった！また明日も頑張ろうね
[2025/01/16 20:33] ゆうき: うん！おやすみ
[2025/01/16 20:34] ゆいな: おやすみ〜"""
    
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