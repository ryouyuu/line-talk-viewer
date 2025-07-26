import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def create_line_style_css() -> str:
    """LINE風のスタイルCSSを生成（モバイル対応）"""
    return """
    <style>
    /* モバイル対応のベーススタイル */
    * {
        box-sizing: border-box;
    }
    
    body {
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        -webkit-text-size-adjust: 100%;
        -webkit-tap-highlight-color: transparent;
    }
    
    .chat-container {
        max-width: 100%;
        width: 100%;
        margin: 0 auto;
        padding: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        border-radius: 0;
        overflow-x: hidden;
    }
    
    /* デスクトップ用の最大幅設定 */
    @media (min-width: 768px) {
        .chat-container {
            max-width: 400px;
            padding: 10px;
        }
    }
    
    .message-group {
        margin: 6px 0;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        width: 100%;
    }
    
    .message-group .message-sent {
        align-self: flex-end;
    }
    
    .message-bubble {
        margin: 2px 0;
        padding: 8px 12px;
        border-radius: 18px;
        max-width: 85%;
        word-wrap: break-word;
        word-break: break-word;
        position: relative;
        animation: fadeIn 0.3s ease-in;
        font-size: 14px;
        line-height: 1.4;
        overflow-wrap: break-word;
    }
    
    /* モバイル用のメッセージバブル調整 */
    @media (max-width: 767px) {
        .message-bubble {
            max-width: 90%;
            font-size: 15px;
            padding: 10px 14px;
        }
    }
    
    .message-sent {
        background: linear-gradient(135deg, #00C73C 0%, #00A33C 100%);
        color: white;
        margin-left: auto;
        margin-right: 4px;
        border-bottom-right-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .message-received {
        background: white;
        color: #333;
        margin-right: auto;
        margin-left: 4px;
        border-bottom-left-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .message-system {
        background-color: rgba(255,255,255,0.9);
        color: #666;
        text-align: center;
        margin: 10px auto;
        border-radius: 15px;
        font-size: 11px;
        font-style: italic;
        padding: 6px 12px;
        max-width: 80%;
        width: fit-content;
    }
    
    .message-info {
        font-size: 10px;
        margin-bottom: 2px;
        opacity: 0.7;
        font-weight: 500;
    }
    
    .message-time {
        font-size: 9px;
        opacity: 0.6;
        margin-top: 2px;
        text-align: right;
    }
    
    .date-separator {
        text-align: center;
        margin: 12px 0;
        color: rgba(255,255,255,0.8);
        font-weight: 600;
        font-size: 11px;
        background: rgba(255,255,255,0.1);
        padding: 6px 12px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        max-width: 90%;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* モバイル用の日付セパレーター調整 */
    @media (max-width: 767px) {
        .date-separator {
            font-size: 12px;
            padding: 8px 16px;
        }
    }
    
    .search-highlight {
        background-color: #FFD700;
        padding: 1px 3px;
        border-radius: 3px;
        font-weight: bold;
        color: #333;
    }
    
    .profile-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 12px;
        margin: 0 6px;
        flex-shrink: 0;
    }
    
    /* モバイル用のアバター調整 */
    @media (max-width: 767px) {
        .profile-avatar {
            width: 32px;
            height: 32px;
            font-size: 14px;
            margin: 0 8px;
        }
    }
    
    .message-with-avatar {
        display: flex;
        align-items: flex-end;
        margin: 4px 0;
        width: 100%;
    }
    
    .message-content {
        display: flex;
        flex-direction: column;
        flex: 1;
        min-width: 0;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stats-card {
        background: rgba(255,255,255,0.95);
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 8px 0;
        backdrop-filter: blur(10px);
    }
    
    /* モバイル用の統計カード調整 */
    @media (max-width: 767px) {
        .stats-card {
            padding: 15px;
            border-radius: 15px;
            margin: 10px 0;
        }
    }
    
    .emotion-positive { color: #28a745; }
    .emotion-negative { color: #dc3545; }
    .emotion-neutral { color: #6c757d; }
    
    /* 絵文字のスタイル */
    .emoji {
        font-size: 16px;
        vertical-align: middle;
    }
    
    /* リンクのスタイル */
    .message-bubble a {
        color: inherit;
        text-decoration: underline;
        word-break: break-all;
    }
    
    /* スタンプのスタイル */
    .stamp-message {
        font-size: 20px;
        text-align: center;
        padding: 8px;
    }
    
    /* モバイル用のスタンプ調整 */
    @media (max-width: 767px) {
        .stamp-message {
            font-size: 24px;
            padding: 10px;
        }
    }
    
    /* タッチデバイス用の最適化 */
    @media (hover: none) and (pointer: coarse) {
        .message-bubble {
            -webkit-tap-highlight-color: transparent;
        }
        
        .message-bubble:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }
    }
    
    /* スクロールバーのカスタマイズ */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.1);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.3);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.5);
    }
    
    /* 長いテキストの処理 */
    .message-bubble {
        overflow-wrap: break-word;
        word-break: break-word;
        hyphens: auto;
    }
    
    /* 画像のレスポンシブ対応 */
    .message-bubble img {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
    }
    
    /* モバイル用の余白調整 */
    @media (max-width: 767px) {
        .chat-container {
            padding: 4px;
        }
        
        .message-bubble {
            margin: 1px 0;
        }
    }
    </style>
    """

def render_message_bubble(message: Dict, is_own_message: bool, search_keyword: str = "") -> str:
    """
    メッセージをLINE風の吹き出しHTMLで表示
    
    Args:
        message: メッセージ辞書
        is_own_message: 自分のメッセージかどうか
        search_keyword: 検索キーワード（ハイライト用）
    
    Returns:
        HTML文字列
    """
    sender = message['sender']
    time_str = message['time']
    content = message['message']
    
    # 検索キーワードをハイライト
    if search_keyword and search_keyword.lower() in content.lower():
        content = content.replace(
            search_keyword, 
            f'<span class="search-highlight">{search_keyword}</span>'
        )
    
    # スタンプメッセージの処理
    if content == "[スタンプ]":
        content = '<div class="stamp-message">🎵</div>'
    
    # 絵文字のスタイル適用
    content = content.replace('😊', '<span class="emoji">😊</span>')
    content = content.replace('☀️', '<span class="emoji">☀️</span>')
    content = content.replace('🐶', '<span class="emoji">🐶</span>')
    
    if message['type'] == 'system':
        return f"""
        <div class="message-bubble message-system">
            {content}
        </div>
        """
    
    # アバターの初期文字を取得
    avatar_text = sender[0] if sender else "?"
    
    if is_own_message:
        # 自分のメッセージ（右寄せ）
        return f"""
        <div class="message-bubble message-sent">
            <div class="message-content">
                {content}
                <div class="message-time">{time_str}</div>
            </div>
        </div>
        """
    else:
        # 相手のメッセージ（左寄せ、アバター付き）
        return f"""
        <div class="message-with-avatar">
            <div class="profile-avatar">{avatar_text}</div>
            <div class="message-bubble message-received">
                <div class="message-content">
                    <div class="message-info">{sender}</div>
                    {content}
                    <div class="message-time">{time_str}</div>
                </div>
            </div>
        </div>
        """

def render_chat_messages(df: pd.DataFrame, own_name: str, search_keyword: str = "") -> str:
    """
    会話履歴をLINE風UIで表示
    
    Args:
        df: メッセージDataFrame
        own_name: 自分の名前
        search_keyword: 検索キーワード
    
    Returns:
        HTML文字列
    """
    if df.empty:
        return "<p>メッセージがありません。</p>"
    
    html_parts = []
    current_date = None
    current_sender = None
    
    for _, message in df.iterrows():
        # 日付セパレーター
        if message['date'] != current_date:
            current_date = message['date']
            date_obj = datetime.strptime(current_date, "%Y/%m/%d")
            
            # 日本語の曜日表示
            weekday_names = {
                0: '月曜日',
                1: '火曜日', 
                2: '水曜日',
                3: '木曜日',
                4: '金曜日',
                5: '土曜日',
                6: '日曜日'
            }
            weekday = weekday_names[date_obj.weekday()]
            formatted_date = date_obj.strftime(f"%Y年%m月%d日 ({weekday})")
            html_parts.append(f'<div class="date-separator">{formatted_date}</div>')
            current_sender = None
        
        # メッセージ吹き出し
        is_own = message['sender'] == own_name
        bubble_html = render_message_bubble(message, is_own, search_keyword)
        
        # 同じ発言者の連続メッセージをグループ化
        if current_sender == message['sender']:
            # 前のメッセージグループに追加
            html_parts.append(bubble_html)
        else:
            # 新しいメッセージグループを開始
            if current_sender is not None:
                html_parts.append('</div>')
            html_parts.append(f'<div class="message-group">{bubble_html}')
            current_sender = message['sender']
    
    # 最後のグループを閉じる
    if current_sender is not None:
        html_parts.append('</div>')
    
    return '\n'.join(html_parts)

def create_emotion_chart(emotion_data: pd.DataFrame) -> go.Figure:
    """感情分析結果の棒グラフを作成"""
    if emotion_data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="感情分析データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.bar(
        emotion_data, 
        x='date', 
        y=['positive', 'negative', 'neutral'],
        title="日別感情分析結果",
        labels={'value': 'メッセージ数', 'variable': '感情', 'date': '日付'},
        color_discrete_map={
            'positive': '#28a745',
            'negative': '#dc3545', 
            'neutral': '#6c757d'
        }
    )
    
    fig.update_layout(
        xaxis_title="日付",
        yaxis_title="メッセージ数",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_wordcloud_figure(word_freq: Dict[str, int], title: str = "頻出ワード") -> go.Figure:
    """WordCloud風の可視化を作成（Plotly使用）"""
    if not word_freq:
        fig = go.Figure()
        fig.add_annotation(
            text="頻出ワードデータがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # 上位20語を取得
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
    words, frequencies = zip(*sorted_words)
    
    fig = go.Figure(data=[
        go.Bar(
            x=frequencies,
            y=words,
            orientation='h',
            marker_color='#00C73C',
            text=frequencies,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="出現回数",
        yaxis_title="ワード",
        height=400,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def display_stats_cards(df: pd.DataFrame, own_name: str) -> None:
    """統計情報をカード形式で表示"""
    if df.empty:
        st.warning("データがありません")
        return
    
    # 基本統計
    total_messages = len(df)
    total_days = df['date'].nunique()
    speakers = df[df['type'] == 'message']['sender'].unique()
    
    # 発言比率
    own_messages = len(df[df['sender'] == own_name])
    other_messages = total_messages - own_messages
    own_ratio = (own_messages / total_messages * 100) if total_messages > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総メッセージ数", f"{total_messages:,}件")
    
    with col2:
        st.metric("会話日数", f"{total_days}日")
    
    with col3:
        st.metric("参加者数", f"{len(speakers)}人")
    
    with col4:
        st.metric(f"{own_name}の発言率", f"{own_ratio:.1f}%")
    
    # 日別メッセージ数
    daily_counts = df.groupby('date').size().reset_index(name='count')
    fig = px.line(
        daily_counts, 
        x='date', 
        y='count',
        title="日別メッセージ数推移",
        labels={'count': 'メッセージ数', 'date': '日付'}
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def highlight_search_results(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """検索結果をハイライト表示"""
    if not keyword:
        return df
    
    # 検索結果をハイライト
    def highlight_text(text):
        if keyword.lower() in text.lower():
            return f"**{text}**"
        return text
    
    df_highlighted = df.copy()
    df_highlighted['message'] = df_highlighted['message'].apply(highlight_text)
    
    return df_highlighted

def create_sample_data_file() -> str:
    """サンプルデータファイルを作成"""
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

def create_time_distribution_chart(time_dist: Dict[str, int]) -> go.Figure:
    """時間帯別メッセージ分布のグラフを作成"""
    if not time_dist:
        fig = go.Figure()
        fig.add_annotation(
            text="時間帯データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    periods = list(time_dist.keys())
    counts = list(time_dist.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=periods,
            y=counts,
            marker_color='#00C73C',
            text=counts,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="時間帯別メッセージ分布",
        xaxis_title="時間帯",
        yaxis_title="メッセージ数",
        height=400
    )
    
    return fig

def create_message_length_chart(length_stats: Dict[str, Dict]) -> go.Figure:
    """メッセージ長分析のグラフを作成"""
    if not length_stats or '長さ別分類' not in length_stats:
        fig = go.Figure()
        fig.add_annotation(
            text="メッセージ長データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    categories = list(length_stats['長さ別分類'].keys())
    counts = list(length_stats['長さ別分類'].values())
    
    fig = go.Figure(data=[
        go.Pie(
            labels=categories,
            values=counts,
            hole=0.4,
            marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        )
    ])
    
    fig.update_layout(
        title="メッセージ長別分布",
        height=400
    )
    
    return fig

def create_emoji_usage_chart(emoji_stats: Dict[str, Dict]) -> go.Figure:
    """絵文字使用分析のグラフを作成"""
    if not emoji_stats or 'よく使う絵文字' not in emoji_stats:
        fig = go.Figure()
        fig.add_annotation(
            text="絵文字データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    emojis = list(emoji_stats['よく使う絵文字'].keys())
    counts = list(emoji_stats['よく使う絵文字'].values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=emojis,
            y=counts,
            marker_color='#FFD93D',
            text=counts,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="よく使う絵文字 TOP10",
        xaxis_title="絵文字",
        yaxis_title="使用回数",
        height=400
    )
    
    return fig

def create_response_time_chart(response_stats: Dict[str, Dict]) -> go.Figure:
    """返信速度分析のグラフを作成"""
    if not response_stats or '発言者別統計' not in response_stats:
        fig = go.Figure()
        fig.add_annotation(
            text="返信速度データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    speakers = list(response_stats['発言者別統計'].keys())
    avg_times = [stats['平均返信時間（分）'] for stats in response_stats['発言者別統計'].values()]
    response_counts = [stats['返信回数'] for stats in response_stats['発言者別統計'].values()]
    
    fig = go.Figure()
    
    # 平均返信時間の棒グラフ
    fig.add_trace(go.Bar(
        name='平均返信時間（分）',
        x=speakers,
        y=avg_times,
        yaxis='y',
        marker_color='#00C73C'
    ))
    
    # 返信回数の折れ線グラフ（第2軸）
    fig.add_trace(go.Scatter(
        name='返信回数',
        x=speakers,
        y=response_counts,
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="発言者別返信速度分析",
        xaxis_title="発言者",
        yaxis=dict(title="平均返信時間（分）", side="left"),
        yaxis2=dict(title="返信回数", side="right", overlaying="y"),
        height=400,
        legend=dict(x=0.02, y=0.98)
    )
    
    return fig

def create_message_speed_chart(speed_stats: Dict[str, Dict]) -> go.Figure:
    """返信速度分析のグラフを作成"""
    if not speed_stats or '発言者別速度' not in speed_stats:
        fig = go.Figure()
        fig.add_annotation(
            text="返信速度データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    speakers = list(speed_stats['発言者別速度'].keys())
    avg_intervals = [stats['平均送信間隔（分）'] for stats in speed_stats['発言者別速度'].values()]
    message_counts = [stats['連続メッセージ数'] for stats in speed_stats['発言者別速度'].values()]
    speed_levels = [stats['送信速度レベル'] for stats in speed_stats['発言者別速度'].values()]
    
    # 速度レベルに応じて色を設定
    colors = []
    for level in speed_levels:
        if '🚀' in level:
            colors.append('#FF6B6B')  # 赤（超高速）
        elif '⚡' in level:
            colors.append('#FFA500')  # オレンジ（高速）
        elif '🏃' in level:
            colors.append('#FFD93D')  # 黄色（中速）
        elif '🚶' in level:
            colors.append('#4ECDC4')  # 水色（低速）
        else:
            colors.append('#6C757D')  # グレー（超低速）
    
    fig = go.Figure()
    
    # 平均送信間隔の棒グラフ
    fig.add_trace(go.Bar(
        name='平均送信間隔（分）',
        x=speakers,
        y=avg_intervals,
        yaxis='y',
        marker_color=colors,
        text=[f"{level}<br>{interval:.1f}分" for level, interval in zip(speed_levels, avg_intervals)],
        textposition='auto',
        textfont=dict(size=10)
    ))
    
    # 連続メッセージ数の折れ線グラフ（第2軸）
    fig.add_trace(go.Scatter(
        name='連続メッセージ数',
        x=speakers,
        y=message_counts,
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#00C73C', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="🚀 返信速度分析（メッセージ送信速度）",
        xaxis_title="発言者",
        yaxis=dict(title="平均送信間隔（分）", side="left"),
        yaxis2=dict(title="連続メッセージ数", side="right", overlaying="y"),
        height=400,
        legend=dict(x=0.02, y=0.98)
    )
    
    return fig

def create_hourly_speed_chart(speed_stats: Dict[str, Dict]) -> go.Figure:
    """時間帯別返信速度のグラフを作成"""
    if not speed_stats or '時間帯別速度' not in speed_stats:
        fig = go.Figure()
        fig.add_annotation(
            text="時間帯別速度データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    hours = list(range(24))
    avg_intervals = []
    message_counts = []
    speed_levels = []
    
    for hour in hours:
        if hour in speed_stats['時間帯別速度']:
            stats = speed_stats['時間帯別速度'][hour]
            avg_intervals.append(stats['平均間隔（分）'])
            message_counts.append(stats['メッセージ数'])
            speed_levels.append(stats['速度レベル'])
        else:
            avg_intervals.append(0)
            message_counts.append(0)
            speed_levels.append("データなし")
    
    fig = go.Figure()
    
    # 平均間隔の棒グラフ
    fig.add_trace(go.Bar(
        name='平均送信間隔（分）',
        x=hours,
        y=avg_intervals,
        marker_color='#FF6B6B',
        text=[f"{level}<br>{interval:.1f}分" if interval > 0 else "データなし" 
              for level, interval in zip(speed_levels, avg_intervals)],
        textposition='auto',
        textfont=dict(size=8)
    ))
    
    # メッセージ数の折れ線グラフ（第2軸）
    fig.add_trace(go.Scatter(
        name='メッセージ数',
        x=hours,
        y=message_counts,
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#00C73C', width=3),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="⏰ 時間帯別返信速度",
        xaxis_title="時間",
        yaxis=dict(title="平均送信間隔（分）", side="left"),
        yaxis2=dict(title="メッセージ数", side="right", overlaying="y"),
        height=400,
        legend=dict(x=0.02, y=0.98),
        xaxis=dict(tickmode='linear', tick0=0, dtick=2)
    )
    
    return fig

def create_seasonal_chart(seasonal_stats: Dict[str, Dict]) -> go.Figure:
    """季節性分析のグラフを作成"""
    if not seasonal_stats:
        fig = go.Figure()
        fig.add_annotation(
            text="季節性データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = go.Figure()
    
    # 月別統計
    if '月別統計' in seasonal_stats:
        months = list(range(1, 13))
        monthly_counts = []
        for month in months:
            if month in seasonal_stats['月別統計']:
                monthly_counts.append(seasonal_stats['月別統計'][month]['メッセージ数'])
            else:
                monthly_counts.append(0)
        
        fig.add_trace(go.Scatter(
            name='月別メッセージ数',
            x=months,
            y=monthly_counts,
            mode='lines+markers',
            line=dict(color='#00C73C', width=3),
            marker=dict(size=8)
        ))
    
    # 曜日別統計
    if '曜日別統計' in seasonal_stats:
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        weekday_counts = []
        for day in weekdays:
            if day in seasonal_stats['曜日別統計']:
                weekday_counts.append(seasonal_stats['曜日別統計'][day]['メッセージ数'])
            else:
                weekday_counts.append(0)
        
        fig.add_trace(go.Bar(
            name='曜日別メッセージ数',
            x=weekdays,
            y=weekday_counts,
            marker_color='#4ECDC4',
            opacity=0.7
        ))
    
    fig.update_layout(
        title="季節性分析（月別・曜日別）",
        xaxis_title="月/曜日",
        yaxis_title="メッセージ数",
        height=400,
        barmode='group'
    )
    
    return fig

def create_speaker_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """発言者比較のグラフを作成"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="発言者データがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # 発言者別統計
    speaker_stats = df.groupby('sender').agg({
        'message': 'count',
        'sender': 'count'
    }).rename(columns={'message': 'メッセージ数'})
    
    speakers = list(speaker_stats.index)
    message_counts = list(speaker_stats['メッセージ数'])
    
    fig = go.Figure(data=[
        go.Bar(
            x=speakers,
            y=message_counts,
            marker_color=['#00C73C', '#FF6B6B', '#4ECDC4', '#45B7D1'],
            text=message_counts,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="発言者別メッセージ数",
        xaxis_title="発言者",
        yaxis_title="メッセージ数",
        height=400
    )
    
    return fig

def create_daily_activity_heatmap(df: pd.DataFrame) -> go.Figure:
    """日別・時間別アクティビティヒートマップを作成"""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="アクティビティデータがありません",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # 時間を抽出
    df['hour'] = pd.to_datetime(df['time'], format='%H:%M').dt.hour
    df['weekday'] = pd.to_datetime(df['date']).dt.dayofweek
    
    # 曜日名
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    
    # ヒートマップデータを作成
    heatmap_data = []
    for hour in range(24):
        row = []
        for weekday in range(7):
            count = len(df[(df['hour'] == hour) & (df['weekday'] == weekday)])
            row.append(count)
        heatmap_data.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=weekday_names,
        y=list(range(24)),
        colorscale='Viridis',
        text=heatmap_data,
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="日別・時間別アクティビティヒートマップ",
        xaxis_title="曜日",
        yaxis_title="時間",
        height=500
    )
    
    return fig

def display_advanced_stats(df: pd.DataFrame, own_name: str) -> None:
    """高度な統計情報を表示"""
    if df.empty:
        st.warning("データがありません")
        return
    
    # 会話分析器を初期化
    from analyzer import ConversationAnalyzer
    analyzer = ConversationAnalyzer()
    
    # 分析実行
    with st.spinner("高度な分析を実行中..."):
        summary = analyzer.get_conversation_summary(df)
    
    if not summary:
        st.error("分析に失敗しました")
        return
    
    # タブで分析結果を表示
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "⏰ 時間帯分析", 
        "📏 メッセージ長", 
        "😊 絵文字分析", 
        "⚡ 返信時間", 
        "🚀 送信速度",
        "📅 季節性"
    ])
    
    with tab1:
        st.subheader("⏰ 時間帯別メッセージ分布")
        time_chart = create_time_distribution_chart(summary['時間帯分布'])
        st.plotly_chart(time_chart, use_container_width=True)
        
        # 統計情報
        col1, col2 = st.columns(2)
        with col1:
            st.metric("最も活発な時間帯", 
                     max(summary['時間帯分布'].items(), key=lambda x: x[1])[0])
        with col2:
            st.metric("最も静かな時間帯", 
                     min(summary['時間帯分布'].items(), key=lambda x: x[1])[0])
    
    with tab2:
        st.subheader("📏 メッセージ長分析")
        length_chart = create_message_length_chart(summary['メッセージ長統計'])
        st.plotly_chart(length_chart, use_container_width=True)
        
        # 統計情報
        stats = summary['メッセージ長統計']['全体統計']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均文字数", f"{stats['平均文字数']:.1f}文字")
        with col2:
            st.metric("最大文字数", f"{stats['最大文字数']}文字")
        with col3:
            st.metric("中央値", f"{stats['中央値']:.1f}文字")
    
    with tab3:
        st.subheader("😊 絵文字・スタンプ分析")
        emoji_chart = create_emoji_usage_chart(summary['絵文字・スタンプ統計'])
        st.plotly_chart(emoji_chart, use_container_width=True)
        
        # 統計情報
        emoji_stats = summary['絵文字・スタンプ統計']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("絵文字使用メッセージ", f"{emoji_stats['絵文字使用メッセージ数']}件")
        with col2:
            st.metric("スタンプ使用メッセージ", f"{emoji_stats['スタンプ使用メッセージ数']}件")
        with col3:
            st.metric("絵文字総数", f"{emoji_stats['絵文字総数']}個")
    
    with tab4:
        st.subheader("⚡ 返信時間分析")
        st.info("**返信時間**: 相手のメッセージに対する返信にかかった時間を分析します")
        
        response_chart = create_response_time_chart(summary['返信速度統計'])
        st.plotly_chart(response_chart, use_container_width=True)
        
        # 統計情報
        response_stats = summary['返信速度統計']['全体統計']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均返信時間", f"{response_stats['平均返信時間（分）']:.1f}分")
        with col2:
            st.metric("最短返信時間", f"{response_stats['最短返信時間（分）']:.1f}分")
        with col3:
            st.metric("返信回数", f"{response_stats['返信回数']}回")
    
    with tab5:
        st.subheader("🚀 送信速度分析")
        st.info("**送信速度**: メッセージの送信間隔と会話のテンポを分析します")
        
        # 全体統計
        speed_stats = summary['送信速度統計']['全体統計']
        st.info(f"**会話テンポレベル: {speed_stats['会話テンポレベル']}**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均メッセージ間隔", f"{speed_stats['平均メッセージ間隔（分）']:.1f}分")
        with col2:
            st.metric("最短メッセージ間隔", f"{speed_stats['最短メッセージ間隔（分）']:.1f}分")
        with col3:
            st.metric("最長メッセージ間隔", f"{speed_stats['最長メッセージ間隔（分）']:.1f}分")
        with col4:
            st.metric("総メッセージ数", f"{speed_stats['総メッセージ数']}件")
        
        # 発言者別送信速度
        st.subheader("👥 発言者別送信速度")
        speed_chart = create_message_speed_chart(summary['送信速度統計'])
        st.plotly_chart(speed_chart, use_container_width=True)
        
        # 時間帯別送信速度
        st.subheader("⏰ 時間帯別送信速度")
        hourly_speed_chart = create_hourly_speed_chart(summary['送信速度統計'])
        st.plotly_chart(hourly_speed_chart, use_container_width=True)
        
        # 発言者別詳細統計
        st.subheader("📊 発言者別詳細統計")
        speaker_speeds = summary['送信速度統計']['発言者別速度']
        for speaker, stats in speaker_speeds.items():
            with st.expander(f"**{speaker}** - {stats['送信速度レベル']}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("平均送信間隔", f"{stats['平均送信間隔（分）']:.1f}分")
                with col2:
                    st.metric("最短送信間隔", f"{stats['最短送信間隔（分）']:.1f}分")
                with col3:
                    st.metric("最長送信間隔", f"{stats['最長送信間隔（分）']:.1f}分")
                with col4:
                    st.metric("連続メッセージ数", f"{stats['連続メッセージ数']}件")
    
    with tab6:
        st.subheader("📅 季節性分析")
        seasonal_chart = create_seasonal_chart(summary['季節性統計'])
        st.plotly_chart(seasonal_chart, use_container_width=True)
        
        # アクティビティヒートマップ
        st.subheader("📊 日別・時間別アクティビティ")
        heatmap = create_daily_activity_heatmap(df)
        st.plotly_chart(heatmap, use_container_width=True) 