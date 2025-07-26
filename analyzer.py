import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from janome.tokenizer import Tokenizer
from janome.analyzer import Analyzer
from janome.charfilter import UnicodeNormalizeCharFilter
from janome.tokenfilter import POSKeepFilter, LowerCaseFilter
import re

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionAnalyzer:
    """感情分析を行うクラス"""
    
    def __init__(self):
        """感情分析器を初期化"""
        self.model_loaded = False
        self.sentiment_analyzer = None
        logger.info("感情分析モデルは必要時に読み込みます")
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        テキストの感情分析を実行
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            感情分析結果（positive, negative, neutralの確率）
        """
        if not self.model_loaded or not text.strip():
            return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
        
        try:
            # 長いテキストは分割
            if len(text) > 500:
                text = text[:500]
            
            result = self.sentiment_analyzer(text)
            
            # 結果を正規化
            if result[0]['label'] == 'positive':
                return {'positive': 0.8, 'negative': 0.1, 'neutral': 0.1}
            elif result[0]['label'] == 'negative':
                return {'positive': 0.1, 'negative': 0.8, 'neutral': 0.1}
            else:
                return {'positive': 0.1, 'negative': 0.1, 'neutral': 0.8}
                
        except Exception as e:
            logger.error(f"感情分析エラー: {e}")
            return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
    
    def analyze_messages(self, df: pd.DataFrame, batch_size: int = 32) -> pd.DataFrame:
        """
        メッセージDataFrameの感情分析を実行（バッチ処理対応）
        
        Args:
            df: メッセージDataFrame
            batch_size: バッチサイズ
            
        Returns:
            感情分析結果を含むDataFrame
        """
        if df.empty:
            return df
        
        # 感情分析モデルを必要時に読み込み
        if not self.model_loaded:
            try:
                from transformers import pipeline
                self.sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="nlptown/bert-base-multilingual-uncased-sentiment",
                    device=-1  # CPU使用
                )
                self.model_loaded = True
                logger.info("感情分析モデルを読み込みました")
            except Exception as e:
                logger.warning(f"感情分析モデルの読み込みに失敗: {e}")
                self.model_loaded = False
        
        # システムメッセージを除外
        message_df = df[df['type'] != 'system'].copy()
        system_df = df[df['type'] == 'system'].copy()
        
        if message_df.empty:
            return df
        
        results = []
        
        # バッチ処理
        for i in range(0, len(message_df), batch_size):
            batch = message_df.iloc[i:i+batch_size]
            messages = batch['message'].tolist()
            
            try:
                # バッチで感情分析実行
                if self.model_loaded:
                    batch_results = self.sentiment_analyzer(messages)
                    
                    for result in batch_results:
                        if result['label'] == 'positive':
                            results.append({'positive': 0.8, 'negative': 0.1, 'neutral': 0.1})
                        elif result['label'] == 'negative':
                            results.append({'positive': 0.1, 'negative': 0.8, 'neutral': 0.1})
                        else:
                            results.append({'positive': 0.1, 'negative': 0.1, 'neutral': 0.8})
                else:
                    # モデルが読み込めない場合はデフォルト値
                    for _ in range(len(messages)):
                        results.append({'positive': 0.33, 'negative': 0.33, 'neutral': 0.34})
                        
            except Exception as e:
                logger.error(f"バッチ感情分析エラー: {e}")
                # エラー時はデフォルト値
                for _ in range(len(messages)):
                    results.append({'positive': 0.33, 'negative': 0.33, 'neutral': 0.34})
            
            # 進捗表示
            logger.info(f"感情分析進捗: {min(i + batch_size, len(message_df))}/{len(message_df)}")
        
        # システムメッセージ用の結果を追加
        for _ in range(len(system_df)):
            results.append({'positive': 0, 'negative': 0, 'neutral': 1})
        
        # 結果をDataFrameに追加
        emotion_df = pd.DataFrame(results)
        df_with_emotion = pd.concat([df, emotion_df], axis=1)
        
        return df_with_emotion
    
    def get_daily_emotion_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        日別感情分析サマリーを取得
        
        Args:
            df: 感情分析済みDataFrame
            
        Returns:
            日別感情集計DataFrame
        """
        if df.empty or 'positive' not in df.columns:
            return pd.DataFrame()
        
        daily_emotion = df.groupby('date').agg({
            'positive': 'sum',
            'negative': 'sum', 
            'neutral': 'sum'
        }).reset_index()
        
        return daily_emotion

class WordAnalyzer:
    """頻出ワード分析を行うクラス"""
    
    def __init__(self):
        """ワード分析器を初期化"""
        self.tokenizer = Tokenizer()
        
        # 分析対象外の品詞
        self.exclude_pos = ['助詞', '助動詞', '記号', '接続助詞', '副助詞']
        
        # 除外ワード（一般的すぎる単語）
        self.stop_words = {
            'の', 'に', 'は', 'を', 'が', 'で', 'と', 'から', 'まで', 'より',
            'や', 'か', 'も', 'など', 'って', 'です', 'ます', 'だ', 'です',
            'お', 'ご', 'さん', 'ちゃん', 'くん', 'ね', 'よ', 'な', 'わ',
            'あ', 'い', 'う', 'え', 'お', 'ん', 'っ', 'ー', '！', '？', '。',
            '、', '「', '」', '（', '）', '【', '】', '『', '』', '・'
        }
    
    def extract_words(self, text: str) -> List[str]:
        """
        テキストから名詞を抽出
        
        Args:
            text: 分析対象テキスト
            
        Returns:
            抽出された名詞リスト
        """
        if not text.strip():
            return []
        
        try:
            # 形態素解析
            tokens = self.tokenizer.tokenize(text)
            
            words = []
            for token in tokens:
                # 品詞情報を取得
                pos = token.part_of_speech.split(',')[0]
                
                # 名詞のみを抽出（除外品詞はスキップ）
                if pos == '名詞' and token.surface not in self.stop_words:
                    # 1文字の単語は除外
                    if len(token.surface) > 1:
                        words.append(token.surface)
            
            return words
            
        except Exception as e:
            logger.error(f"ワード抽出エラー: {e}")
            return []
    
    def analyze_messages(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        メッセージDataFrameから頻出ワードを抽出
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            ワード頻度辞書
        """
        if df.empty:
            return {}
        
        word_freq = {}
        
        for idx, row in df.iterrows():
            if row['type'] == 'system':
                continue
            
            words = self.extract_words(row['message'])
            
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 進捗表示
            if (idx + 1) % 50 == 0:
                logger.info(f"ワード分析進捗: {idx + 1}/{len(df)}")
        
        # 頻度順にソート
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return dict(sorted_words)
    
    def get_speaker_word_freq(self, df: pd.DataFrame, speaker: str) -> Dict[str, int]:
        """
        特定発言者の頻出ワードを取得
        
        Args:
            df: メッセージDataFrame
            speaker: 発言者名
            
        Returns:
            ワード頻度辞書
        """
        speaker_df = df[df['sender'] == speaker].copy()
        return self.analyze_messages(speaker_df)
    
    def get_daily_word_freq(self, df: pd.DataFrame, target_date: str) -> Dict[str, int]:
        """
        特定日付の頻出ワードを取得
        
        Args:
            df: メッセージDataFrame
            target_date: 対象日付
            
        Returns:
            ワード頻度辞書
        """
        daily_df = df[df['date'] == target_date].copy()
        return self.analyze_messages(daily_df)

class TopicAnalyzer:
    """トピック分析を行うクラス（GPT API使用）"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        トピック分析器を初期化
        
        Args:
            api_key: OpenAI APIキー（オプション）
        """
        self.api_key = api_key
        self.client = None
        
        if api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI APIクライアントを初期化しました")
            except Exception as e:
                logger.warning(f"OpenAI API初期化エラー: {e}")
    
    def summarize_daily_conversation(self, df: pd.DataFrame, target_date: str) -> str:
        """
        特定日付の会話を要約
        
        Args:
            df: メッセージDataFrame
            target_date: 対象日付
            
        Returns:
            要約テキスト
        """
        if not self.client:
            return "GPT APIが設定されていません"
        
        daily_df = df[df['date'] == target_date].copy()
        
        if daily_df.empty:
            return "その日の会話がありません"
        
        # 会話テキストを作成
        conversation = []
        for _, row in daily_df.iterrows():
            if row['type'] == 'message':
                conversation.append(f"{row['sender']}: {row['message']}")
        
        if not conversation:
            return "有効な会話がありません"
        
        conversation_text = "\n".join(conversation)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは会話分析の専門家です。与えられた会話を1-2文で簡潔に要約してください。"
                    },
                    {
                        "role": "user", 
                        "content": f"以下の会話を要約してください：\n\n{conversation_text}"
                    }
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"GPT API要約エラー: {e}")
            return "要約に失敗しました"

class ConversationAnalyzer:
    """会話分析・統計を行うクラス"""
    
    def __init__(self):
        """会話分析器を初期化"""
        # 絵文字パターン
        self.emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F270]'
        )
        
        # スタンプパターン
        self.stamp_pattern = re.compile(r'\[スタンプ\]')
        
        # 時間帯の定義
        self.time_periods = {
            '早朝': (5, 8),
            '午前': (8, 12),
            '昼': (12, 14),
            '午後': (14, 18),
            '夕方': (18, 20),
            '夜': (20, 23),
            '深夜': (23, 5)
        }
    
    def analyze_time_distribution(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        時間帯別メッセージ分布を分析
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            時間帯別メッセージ数
        """
        if df.empty:
            return {}
        
        # 時間を抽出
        df['hour'] = pd.to_datetime(df['time'], format='%H:%M').dt.hour
        
        time_dist = {}
        
        for period, (start, end) in self.time_periods.items():
            if start < end:
                # 通常の時間帯（例：8-12時）
                count = len(df[(df['hour'] >= start) & (df['hour'] < end)])
            else:
                # 深夜（23-5時）
                count = len(df[(df['hour'] >= start) | (df['hour'] < end)])
            
            time_dist[period] = count
        
        return time_dist
    
    def analyze_message_length(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        メッセージ長分析
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            メッセージ長統計
        """
        if df.empty:
            return {}
        
        # メッセージ長を計算
        df['length'] = df['message'].str.len()
        
        # 全体統計
        overall_stats = {
            '平均文字数': df['length'].mean(),
            '最大文字数': df['length'].max(),
            '最小文字数': df['length'].min(),
            '中央値': df['length'].median()
        }
        
        # 長さ別分類
        length_categories = {
            '短い（1-10文字）': len(df[df['length'] <= 10]),
            '中程度（11-50文字）': len(df[(df['length'] > 10) & (df['length'] <= 50)]),
            '長い（51-100文字）': len(df[(df['length'] > 50) & (df['length'] <= 100)]),
            'とても長い（100文字以上）': len(df[df['length'] > 100])
        }
        
        # 発言者別統計
        speaker_stats = {}
        for speaker in df['sender'].unique():
            speaker_df = df[df['sender'] == speaker]
            speaker_stats[speaker] = {
                '平均文字数': speaker_df['length'].mean(),
                'メッセージ数': len(speaker_df),
                '総文字数': speaker_df['length'].sum()
            }
        
        return {
            '全体統計': overall_stats,
            '長さ別分類': length_categories,
            '発言者別統計': speaker_stats
        }
    
    def analyze_emoji_usage(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        絵文字・スタンプ使用分析
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            絵文字・スタンプ使用統計
        """
        if df.empty:
            return {}
        
        emoji_stats = {
            '絵文字使用メッセージ数': 0,
            'スタンプ使用メッセージ数': 0,
            '絵文字総数': 0,
            'スタンプ総数': 0,
            'よく使う絵文字': {},
            '発言者別絵文字使用': {}
        }
        
        for idx, row in df.iterrows():
            if row['type'] == 'system':
                continue
            
            message = row['message']
            sender = row['sender']
            
            # 絵文字検出
            emojis = self.emoji_pattern.findall(message)
            if emojis:
                emoji_stats['絵文字使用メッセージ数'] += 1
                emoji_stats['絵文字総数'] += len(emojis)
                
                # 発言者別統計
                if sender not in emoji_stats['発言者別絵文字使用']:
                    emoji_stats['発言者別絵文字使用'][sender] = 0
                emoji_stats['発言者別絵文字使用'][sender] += len(emojis)
                
                # 個別絵文字統計
                for emoji in emojis:
                    emoji_stats['よく使う絵文字'][emoji] = emoji_stats['よく使う絵文字'].get(emoji, 0) + 1
            
            # スタンプ検出
            if self.stamp_pattern.search(message):
                emoji_stats['スタンプ使用メッセージ数'] += 1
                emoji_stats['スタンプ総数'] += 1
        
        # よく使う絵文字を上位10個に制限
        emoji_stats['よく使う絵文字'] = dict(
            sorted(emoji_stats['よく使う絵文字'].items(), 
                   key=lambda x: x[1], reverse=True)[:10]
        )
        
        return emoji_stats
    
    def analyze_response_time(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        返信速度分析
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            返信速度統計
        """
        if df.empty:
            return {}
        
        # 日時を結合してdatetimeオブジェクトを作成
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.sort_values('datetime')
        
        response_times = []
        speaker_response_times = {}
        
        for i in range(1, len(df)):
            current_msg = df.iloc[i]
            prev_msg = df.iloc[i-1]
            
            # 同じ日で、異なる発言者の場合
            if (current_msg['date'] == prev_msg['date'] and 
                current_msg['sender'] != prev_msg['sender']):
                
                time_diff = (current_msg['datetime'] - prev_msg['datetime']).total_seconds() / 60  # 分単位
                
                if time_diff <= 60:  # 1時間以内の返信のみ
                    response_times.append(time_diff)
                    
                    # 発言者別統計
                    responder = current_msg['sender']
                    if responder not in speaker_response_times:
                        speaker_response_times[responder] = []
                    speaker_response_times[responder].append(time_diff)
        
        # 統計計算
        if response_times:
            overall_stats = {
                '平均返信時間（分）': np.mean(response_times),
                '中央値返信時間（分）': np.median(response_times),
                '最短返信時間（分）': np.min(response_times),
                '最長返信時間（分）': np.max(response_times),
                '返信回数': len(response_times)
            }
        else:
            overall_stats = {
                '平均返信時間（分）': 0,
                '中央値返信時間（分）': 0,
                '最短返信時間（分）': 0,
                '最長返信時間（分）': 0,
                '返信回数': 0
            }
        
        # 発言者別統計
        speaker_stats = {}
        for speaker, times in speaker_response_times.items():
            speaker_stats[speaker] = {
                '平均返信時間（分）': np.mean(times),
                '返信回数': len(times)
            }
        
        return {
            '全体統計': overall_stats,
            '発言者別統計': speaker_stats
        }
    
    def analyze_message_speed(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        返信速度分析（メッセージ送信速度分析）
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            返信速度統計
        """
        if df.empty:
            return {}
        
        # 日時を結合してdatetimeオブジェクトを作成
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.sort_values('datetime')
        
        # 発言者別のメッセージ送信間隔を分析
        speaker_speeds = {}
        conversation_speeds = []
        
        for speaker in df['sender'].unique():
            speaker_df = df[df['sender'] == speaker].copy()
            speaker_df = speaker_df.sort_values('datetime')
            
            if len(speaker_df) < 2:
                continue
            
            # 同一発言者の連続メッセージ間隔を計算
            intervals = []
            for i in range(1, len(speaker_df)):
                time_diff = (speaker_df.iloc[i]['datetime'] - speaker_df.iloc[i-1]['datetime']).total_seconds() / 60
                if time_diff <= 30:  # 30分以内の連続メッセージのみ
                    intervals.append(time_diff)
            
            if intervals:
                speaker_speeds[speaker] = {
                    '平均送信間隔（分）': np.mean(intervals),
                    '最短送信間隔（分）': np.min(intervals),
                    '最長送信間隔（分）': np.max(intervals),
                    '連続メッセージ数': len(intervals) + 1,
                    '送信速度レベル': self._get_speed_level(np.mean(intervals))
                }
        
        # 会話全体のテンポ分析
        all_intervals = []
        for i in range(1, len(df)):
            time_diff = (df.iloc[i]['datetime'] - df.iloc[i-1]['datetime']).total_seconds() / 60
            if time_diff <= 60:  # 1時間以内のメッセージ間隔
                all_intervals.append(time_diff)
        
        if all_intervals:
            overall_speed_stats = {
                '平均メッセージ間隔（分）': np.mean(all_intervals),
                '中央値メッセージ間隔（分）': np.median(all_intervals),
                '最短メッセージ間隔（分）': np.min(all_intervals),
                '最長メッセージ間隔（分）': np.max(all_intervals),
                '総メッセージ数': len(df),
                '会話テンポレベル': self._get_conversation_tempo_level(np.mean(all_intervals))
            }
        else:
            overall_speed_stats = {
                '平均メッセージ間隔（分）': 0,
                '中央値メッセージ間隔（分）': 0,
                '最短メッセージ間隔（分）': 0,
                '最長メッセージ間隔（分）': 0,
                '総メッセージ数': len(df),
                '会話テンポレベル': '不明'
            }
        
        # 時間帯別の送信速度分析
        try:
            df['hour'] = pd.to_datetime(df['time'], format='%H:%M').dt.hour
        except Exception as e:
            logger.warning(f"時間形式の解析エラー: {e}")
            # フォールバック: 文字列から時間を抽出
            df['hour'] = df['time'].str.extract(r'(\d{1,2}):').astype(int)
        
        hourly_speeds = {}
        
        for hour in range(24):
            hourly_df = df[df['hour'] == hour]
            if len(hourly_df) > 1:
                hourly_intervals = []
                hourly_df = hourly_df.sort_values('datetime')
                for i in range(1, len(hourly_df)):
                    time_diff = (hourly_df.iloc[i]['datetime'] - hourly_df.iloc[i-1]['datetime']).total_seconds() / 60
                    if time_diff <= 30:
                        hourly_intervals.append(time_diff)
                
                if hourly_intervals:
                    hourly_speeds[hour] = {
                        '平均間隔（分）': np.mean(hourly_intervals),
                        'メッセージ数': len(hourly_df),
                        '速度レベル': self._get_speed_level(np.mean(hourly_intervals))
                    }
        
        return {
            '全体統計': overall_speed_stats,
            '発言者別速度': speaker_speeds,
            '時間帯別速度': hourly_speeds
        }
    
    def _get_speed_level(self, avg_interval: float) -> str:
        """送信速度レベルを判定"""
        if avg_interval <= 1:
            return "超高速 🚀"
        elif avg_interval <= 3:
            return "高速 ⚡"
        elif avg_interval <= 10:
            return "中速 🏃"
        elif avg_interval <= 30:
            return "低速 🚶"
        else:
            return "超低速 🐌"
    
    def _get_conversation_tempo_level(self, avg_interval: float) -> str:
        """会話テンポレベルを判定"""
        if avg_interval <= 2:
            return "超活発 🔥"
        elif avg_interval <= 5:
            return "活発 💬"
        elif avg_interval <= 15:
            return "普通 📱"
        elif avg_interval <= 60:
            return "ゆったり 😌"
        else:
            return "静か 🤫"
    
    def analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        季節性分析（月別・曜日別）
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            季節性統計
        """
        if df.empty:
            return {}
        
        try:
            # 日付をdatetimeに変換
            df['datetime'] = pd.to_datetime(df['date'])
            df['month'] = df['datetime'].dt.month
            df['weekday'] = df['datetime'].dt.dayofweek
        except Exception as e:
            logger.error(f"季節性分析での日付変換エラー: {e}")
            return {}
        
        # 月別統計
        monthly_stats = df.groupby('month').agg({
            'message': 'count',
            'sender': 'nunique'
        }).rename(columns={'message': 'メッセージ数', 'sender': '参加者数'})
        
        # 曜日別統計
        weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        weekday_stats = df.groupby('weekday').agg({
            'message': 'count',
            'sender': 'nunique'
        }).rename(columns={'message': 'メッセージ数', 'sender': '参加者数'})
        weekday_stats.index = [weekday_names[i] for i in weekday_stats.index]
        
        return {
            '月別統計': monthly_stats.to_dict('index'),
            '曜日別統計': weekday_stats.to_dict('index')
        }
    
    def get_conversation_summary(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        会話全体のサマリーを取得
        
        Args:
            df: メッセージDataFrame
            
        Returns:
            会話サマリー
        """
        if df.empty:
            return {}
        
        # 基本統計
        basic_stats = {
            '総メッセージ数': len(df),
            '会話日数': df['date'].nunique(),
            '参加者数': df['sender'].nunique(),
            '期間': f"{df['date'].min()} 〜 {df['date'].max()}"
        }
        
        # 各分析を実行
        time_dist = self.analyze_time_distribution(df)
        length_stats = self.analyze_message_length(df)
        emoji_stats = self.analyze_emoji_usage(df)
        response_stats = self.analyze_response_time(df)
        speed_stats = self.analyze_message_speed(df)
        seasonal_stats = self.analyze_seasonal_patterns(df)
        
        return {
            '基本統計': basic_stats,
            '時間帯分布': time_dist,
            'メッセージ長統計': length_stats,
            '絵文字・スタンプ統計': emoji_stats,
            '返信速度統計': response_stats,
            '送信速度統計': speed_stats,
            '季節性統計': seasonal_stats
        }

class SearchFilter:
    """検索・フィルタ機能を提供するクラス"""
    
    def __init__(self):
        """検索フィルタを初期化"""
        pass
    
    def filter_by_date_range(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """
        日付範囲でフィルタ
        
        Args:
            df: メッセージDataFrame
            start_date: 開始日（YYYY/MM/DD）
            end_date: 終了日（YYYY/MM/DD）
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty:
            return df
        
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            df['date_dt'] = pd.to_datetime(df['date'])
            filtered_df = df[(df['date_dt'] >= start_dt) & (df['date_dt'] <= end_dt)].copy()
            filtered_df = filtered_df.drop('date_dt', axis=1)
            
            return filtered_df
        except Exception as e:
            logger.error(f"日付範囲フィルタエラー: {e}")
            return df
    
    def filter_by_speaker(self, df: pd.DataFrame, speakers: List[str]) -> pd.DataFrame:
        """
        送信者でフィルタ
        
        Args:
            df: メッセージDataFrame
            speakers: 送信者リスト
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty or not speakers:
            return df
        
        return df[df['sender'].isin(speakers)].copy()
    
    def filter_by_message_type(self, df: pd.DataFrame, message_types: List[str]) -> pd.DataFrame:
        """
        メッセージタイプでフィルタ
        
        Args:
            df: メッセージDataFrame
            message_types: メッセージタイプリスト（'text', 'stamp', 'image', 'system'）
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty or not message_types:
            return df
        
        filtered_df = df.copy()
        
        # メッセージタイプを判定
        def get_message_type(row):
            message = row['message']
            if row['type'] == 'system':
                return 'system'
            elif '[スタンプ]' in message:
                return 'stamp'
            elif any(keyword in message.lower() for keyword in ['画像', 'image', '写真']):
                return 'image'
            else:
                return 'text'
        
        filtered_df['message_type'] = filtered_df.apply(get_message_type, axis=1)
        filtered_df = filtered_df[filtered_df['message_type'].isin(message_types)]
        filtered_df = filtered_df.drop('message_type', axis=1)
        
        return filtered_df
    
    def filter_by_emotion(self, df: pd.DataFrame, emotion_type: str, threshold: float = 0.5) -> pd.DataFrame:
        """
        感情でフィルタ
        
        Args:
            df: メッセージDataFrame
            emotion_type: 感情タイプ（'positive', 'negative', 'neutral'）
            threshold: 閾値
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty or emotion_type not in ['positive', 'negative', 'neutral']:
            return df
        
        if emotion_type not in df.columns:
            return df
        
        return df[df[emotion_type] >= threshold].copy()
    
    def filter_by_length(self, df: pd.DataFrame, min_length: int = 0, max_length: int = None) -> pd.DataFrame:
        """
        メッセージ長でフィルタ
        
        Args:
            df: メッセージDataFrame
            min_length: 最小文字数
            max_length: 最大文字数（Noneの場合は制限なし）
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty:
            return df
        
        df['length'] = df['message'].str.len()
        
        if max_length is None:
            filtered_df = df[df['length'] >= min_length].copy()
        else:
            filtered_df = df[(df['length'] >= min_length) & (df['length'] <= max_length)].copy()
        
        filtered_df = filtered_df.drop('length', axis=1)
        return filtered_df
    
    def filter_by_keyword(self, df: pd.DataFrame, keywords: List[str], case_sensitive: bool = False) -> pd.DataFrame:
        """
        キーワードでフィルタ
        
        Args:
            df: メッセージDataFrame
            keywords: キーワードリスト
            case_sensitive: 大文字小文字を区別するか
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty or not keywords:
            return df
        
        def contains_keyword(message):
            if case_sensitive:
                return any(keyword in message for keyword in keywords)
            else:
                return any(keyword.lower() in message.lower() for keyword in keywords)
        
        return df[df['message'].apply(contains_keyword)].copy()
    
    def filter_by_time_range(self, df: pd.DataFrame, start_time: str, end_time: str) -> pd.DataFrame:
        """
        時間範囲でフィルタ
        
        Args:
            df: メッセージDataFrame
            start_time: 開始時間（HH:MM）
            end_time: 終了時間（HH:MM）
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty:
            return df
        
        try:
            df['time_dt'] = pd.to_datetime(df['time'], format='%H:%M')
            start_dt = pd.to_datetime(start_time, format='%H:%M')
            end_dt = pd.to_datetime(end_time, format='%H:%M')
            
            if start_dt <= end_dt:
                # 通常の時間範囲（例：09:00-18:00）
                filtered_df = df[(df['time_dt'] >= start_dt) & (df['time_dt'] <= end_dt)].copy()
            else:
                # 深夜をまたぐ時間範囲（例：23:00-05:00）
                filtered_df = df[(df['time_dt'] >= start_dt) | (df['time_dt'] <= end_dt)].copy()
            
            filtered_df = filtered_df.drop('time_dt', axis=1)
            return filtered_df
        except Exception as e:
            logger.error(f"時間範囲フィルタエラー: {e}")
            return df
    
    def filter_by_emoji(self, df: pd.DataFrame, has_emoji: bool = True) -> pd.DataFrame:
        """
        絵文字の有無でフィルタ
        
        Args:
            df: メッセージDataFrame
            has_emoji: 絵文字を含むメッセージを取得するか
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty:
            return df
        
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U00027BF\U0001F900-\U0001F9FF\U0001F018-\U0001F270]'
        )
        
        def contains_emoji(message):
            return bool(emoji_pattern.search(message))
        
        if has_emoji:
            return df[df['message'].apply(contains_emoji)].copy()
        else:
            return df[~df['message'].apply(contains_emoji)].copy()
    
    def apply_multiple_filters(self, df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
        """
        複数のフィルタを適用
        
        Args:
            df: メッセージDataFrame
            filters: フィルタ設定辞書
            
        Returns:
            フィルタ済みDataFrame
        """
        if df.empty:
            return df
        
        filtered_df = df.copy()
        
        # 日付範囲フィルタ
        if 'date_range' in filters:
            start_date, end_date = filters['date_range']
            filtered_df = self.filter_by_date_range(filtered_df, start_date, end_date)
        
        # 送信者フィルタ
        if 'speakers' in filters:
            filtered_df = self.filter_by_speaker(filtered_df, filters['speakers'])
        
        # メッセージタイプフィルタ
        if 'message_types' in filters:
            filtered_df = self.filter_by_message_type(filtered_df, filters['message_types'])
        
        # 感情フィルタ
        if 'emotion' in filters:
            emotion_type, threshold = filters['emotion']
            filtered_df = self.filter_by_emotion(filtered_df, emotion_type, threshold)
        
        # 長さフィルタ
        if 'length' in filters:
            min_len, max_len = filters['length']
            filtered_df = self.filter_by_length(filtered_df, min_len, max_len)
        
        # キーワードフィルタ
        if 'keywords' in filters:
            keywords, case_sensitive = filters['keywords']
            filtered_df = self.filter_by_keyword(filtered_df, keywords, case_sensitive)
        
        # 時間範囲フィルタ
        if 'time_range' in filters:
            start_time, end_time = filters['time_range']
            filtered_df = self.filter_by_time_range(filtered_df, start_time, end_time)
        
        # 絵文字フィルタ
        if 'has_emoji' in filters:
            filtered_df = self.filter_by_emoji(filtered_df, filters['has_emoji'])
        
        return filtered_df

def create_sample_emotion_data() -> pd.DataFrame:
    """テスト用の感情分析サンプルデータを作成"""
    sample_data = {
        'date': ['2025/01/15', '2025/01/15', '2025/01/16', '2025/01/16'],
        'positive': [3, 2, 1, 2],
        'negative': [0, 1, 0, 1], 
        'neutral': [1, 0, 2, 1]
    }
    return pd.DataFrame(sample_data)

if __name__ == "__main__":
    # テスト実行
    print("感情分析器テスト...")
    emotion_analyzer = EmotionAnalyzer()
    
    test_texts = [
        "おはよう！今日は晴れてるね",
        "うん！散歩に行こうよ", 
        "楽しかった！また明日も頑張ろうね"
    ]
    
    for text in test_texts:
        result = emotion_analyzer.analyze_text(text)
        print(f"'{text}' -> {result}")
    
    print("\nワード分析器テスト...")
    word_analyzer = WordAnalyzer()
    
    test_text = "おはよう！今日は公園で散歩に行こうよ"
    words = word_analyzer.extract_words(test_text)
    print(f"'{test_text}' -> {words}") 