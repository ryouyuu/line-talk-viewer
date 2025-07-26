import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# 自作モジュールのインポート
from parser import LineTalkParser
from analyzer import EmotionAnalyzer, WordAnalyzer, ConversationAnalyzer, SearchFilter, create_sample_emotion_data
from utils import (
    create_line_style_css, render_chat_messages, create_emotion_chart,
    create_wordcloud_figure, display_stats_cards, create_sample_data_file,
    display_advanced_stats
)

# ページ設定
st.set_page_config(
    page_title="LINEトーク履歴ビジュアライザー",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# モバイル対応のCSSを追加
st.markdown("""
<style>
    /* ベーススタイル */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* モバイル対応のメインコンテナ */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* モバイル用のパディング調整 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    
    /* サイドバーのモバイル対応 */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    @media (max-width: 768px) {
        .css-1d391kg {
            padding-top: 0.5rem;
        }
    }
    
    /* タブのモバイル対応 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        flex-wrap: wrap;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        background-color: white;
        border: 1px solid #e0e0e0;
        font-size: 14px;
        padding: 8px 12px;
        min-width: auto;
        flex: 1;
        text-align: center;
    }
    
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab"] {
            font-size: 12px;
            padding: 6px 8px;
            min-width: 0;
        }
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #00C73C;
        color: white;
        border-color: #00C73C;
    }
    
    /* ボタンのモバイル対応 */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-size: 14px;
        padding: 8px 16px;
    }
    
    @media (max-width: 768px) {
        .stButton > button {
            font-size: 13px;
            padding: 6px 12px;
        }
    }
    
    /* テキスト入力のモバイル対応 */
    .stTextInput > div > div > input {
        font-size: 14px;
        padding: 8px 12px;
    }
    
    @media (max-width: 768px) {
        .stTextInput > div > div > input {
            font-size: 16px; /* iOSでズームを防ぐ */
            padding: 10px 12px;
        }
    }
    
    /* セレクトボックスのモバイル対応 */
    .stSelectbox > div > div > div {
        font-size: 14px;
    }
    
    @media (max-width: 768px) {
        .stSelectbox > div > div > div {
            font-size: 16px;
        }
    }
    
    /* ファイルアップローダーのモバイル対応 */
    .stFileUploader {
        border-radius: 8px;
    }
    
    /* メトリクスのモバイル対応 */
    .metric-container {
        padding: 8px;
        border-radius: 8px;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 4px 0;
    }
    
    @media (max-width: 768px) {
        .metric-container {
            padding: 6px;
            margin: 2px 0;
        }
    }
    
    /* グラフのモバイル対応 */
    .js-plotly-plot {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* エクスパンダーのモバイル対応 */
    .streamlit-expanderHeader {
        font-size: 14px;
        padding: 8px 12px;
    }
    
    @media (max-width: 768px) {
        .streamlit-expanderHeader {
            font-size: 13px;
            padding: 6px 10px;
        }
    }
    
    /* データフレームのモバイル対応 */
    .stDataFrame {
        font-size: 12px;
    }
    
    @media (max-width: 768px) {
        .stDataFrame {
            font-size: 11px;
        }
    }
    
    /* アラートのモバイル対応 */
    .stAlert {
        border-radius: 8px;
        margin: 8px 0;
    }
    
    @media (max-width: 768px) {
        .stAlert {
            margin: 4px 0;
            padding: 8px 12px;
        }
    }
    
    /* プログレスバーのモバイル対応 */
    .stProgress > div > div > div {
        border-radius: 4px;
    }
    
    /* スピナーのモバイル対応 */
    .stSpinner > div {
        border-radius: 8px;
    }
    
    /* カラムのモバイル対応 */
    @media (max-width: 768px) {
        .row-widget.stHorizontal {
            flex-direction: column;
        }
        
        .row-widget.stHorizontal > div {
            width: 100% !important;
            margin-bottom: 8px;
        }
    }
    
    /* ヘッダーのモバイル対応 */
    h1 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
    }
    
    @media (max-width: 768px) {
        h1 {
            font-size: 1.5rem;
            margin-bottom: 0.8rem;
        }
        
        h2 {
            font-size: 1.3rem;
        }
        
        h3 {
            font-size: 1.1rem;
        }
    }
    
    /* テキストのモバイル対応 */
    @media (max-width: 768px) {
        p, div {
            font-size: 14px;
            line-height: 1.5;
        }
    }
    
    /* スクロールバーのカスタマイズ */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
    }
    
    /* タッチデバイス用の最適化 */
    @media (hover: none) and (pointer: coarse) {
        button, input, select {
            -webkit-tap-highlight-color: transparent;
        }
        
        button:active, input:active, select:active {
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }
    }
    
    /* iframeのモバイル対応 */
    iframe {
        border: none;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        width: 100%;
        max-width: 100%;
    }
    
    @media (max-width: 768px) {
        iframe {
            border-radius: 6px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    """メインアプリケーション"""
    
    # モバイル検出（JavaScriptを使用）
    st.markdown("""
    <script>
    function detectMobile() {
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            window.parent.postMessage({type: 'mobile-detected'}, '*');
        }
    }
    detectMobile();
    window.addEventListener('resize', detectMobile);
    </script>
    """, unsafe_allow_html=True)
    
    # モバイル判定（デフォルトでモバイル対応を有効にする）
    if 'is_mobile' not in st.session_state:
        st.session_state['is_mobile'] = True  # デフォルトでモバイル対応
    
    # アプリケーション説明
    st.markdown("""
    **ChatViz** は、LINEのトーク履歴を分析・可視化するツールです。
    
    📱 **モバイル対応** | 🔍 **高度な検索** | 📊 **詳細分析** | 😊 **感情分析**
    """)
    
    # ヘッダー
    st.title("💬 ChatViz")
    st.markdown("*LINEトーク履歴の分析・可視化ツール*")
    st.markdown("---")
    
    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # 参加者リストを取得（ファイルがアップロードされている場合）
        speakers = []
        if st.session_state.get('file_uploaded', False) and 'parsed_data' in st.session_state:
            df = st.session_state['parsed_data']
            parser = st.session_state['parser']
            speakers = parser.get_speakers(df)
        
        # 自分の名前設定
        own_name = st.text_input(
            "あなたの名前を入力してください",
            value=st.session_state.get('selected_speaker', ""),
            help="自分のメッセージを右寄せで表示するために使用します"
        )
        
        # 参加者リストを表示
        if speakers:
            st.info(f"**参加者一覧:** {', '.join(speakers)}")
            
            # 参加者選択
            selected_speaker = st.selectbox("参加者から選択", [""] + speakers, help="自分の名前を選択すると、名前入力欄に自動入力されます")
            if selected_speaker:
                st.session_state['selected_speaker'] = selected_speaker
                st.rerun()
        
        # GPT API設定を削除
        pass
        
        st.markdown("---")
        
                    # サンプルデータボタン
        if st.button("📝 サンプルデータで試す"):
            sample_content = create_sample_data_file()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(sample_content)
                temp_file_path = f.name
            
            # セッション状態に保存
            st.session_state['uploaded_file_path'] = temp_file_path
            st.session_state['file_uploaded'] = True
            st.session_state['show_speaker_selection'] = True
            # 新しいファイルの場合は解析済みデータをクリア
            if 'last_file_path' not in st.session_state or st.session_state['last_file_path'] != temp_file_path:
                st.session_state.pop('parsed_data', None)
                st.session_state.pop('parser', None)
                st.session_state.pop('speaker_selected', None)
            st.success("サンプルデータを読み込みました！")
            st.rerun()
    
    # メインコンテンツ（モバイル対応）
    # 画面幅に応じてレイアウトを調整
    if st.session_state.get('is_mobile', False):
        # モバイル用の縦並びレイアウト
        st.header("📥 ファイルアップロード")
        
        # ファイルアップロード
        uploaded_file = st.file_uploader(
            "LINEトーク履歴ファイル（.txt）をアップロードしてください",
            type=['txt'],
            help="LINEでバックアップしたテキストファイルを選択してください"
        )
        
        if uploaded_file is not None:
            # ファイルを一時保存
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
                f.write(uploaded_file.getvalue())
                temp_file_path = f.name
            
            st.session_state['uploaded_file_path'] = temp_file_path
            st.session_state['file_uploaded'] = True
            st.session_state['show_speaker_selection'] = True
            # 新しいファイルの場合は解析済みデータをクリア
            if 'last_file_path' not in st.session_state or st.session_state['last_file_path'] != temp_file_path:
                st.session_state.pop('parsed_data', None)
                st.session_state.pop('parser', None)
                st.session_state.pop('speaker_selected', None)
            st.success(f"ファイル '{uploaded_file.name}' をアップロードしました！")
    else:
        # デスクトップ用の横並びレイアウト
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("📥 ファイルアップロード")
            
            # ファイルアップロード
            uploaded_file = st.file_uploader(
                "LINEトーク履歴ファイル（.txt）をアップロードしてください",
                type=['txt'],
                help="LINEでバックアップしたテキストファイルを選択してください"
            )
            
            if uploaded_file is not None:
                # ファイルを一時保存
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
                    f.write(uploaded_file.getvalue())
                    temp_file_path = f.name
                
                st.session_state['uploaded_file_path'] = temp_file_path
                st.session_state['file_uploaded'] = True
                st.session_state['show_speaker_selection'] = True
                # 新しいファイルの場合は解析済みデータをクリア
                if 'last_file_path' not in st.session_state or st.session_state['last_file_path'] != temp_file_path:
                    st.session_state.pop('parsed_data', None)
                    st.session_state.pop('parser', None)
                    st.session_state.pop('speaker_selected', None)
                st.success(f"ファイル '{uploaded_file.name}' をアップロードしました！")
    
    # ファイルがアップロードされている場合の処理
    if st.session_state.get('file_uploaded', False) and 'uploaded_file_path' in st.session_state:
        file_path = st.session_state['uploaded_file_path']
        
        # 既に解析済みの場合はセッション状態から取得
        if ('parsed_data' in st.session_state and 'parser' in st.session_state and 
            'last_file_path' in st.session_state and st.session_state['last_file_path'] == file_path):
            df = st.session_state['parsed_data']
            parser = st.session_state['parser']
            speakers = parser.get_speakers(df)
        else:
            try:
                # ファイル解析
                parser = LineTalkParser()
                df = parser.parse_file(file_path)
                
                # セッション状態に保存
                st.session_state['parsed_data'] = df
                st.session_state['parser'] = parser
                st.session_state['last_file_path'] = file_path
                
                # 参加者リストを取得
                speakers = parser.get_speakers(df)
            
            # 参加者選択ポップアップ表示（選択が完了していない場合のみ）
            if st.session_state.get('show_speaker_selection', False) and not st.session_state.get('speaker_selected', False):
                st.markdown("---")
                st.markdown("### 👤 参加者選択")
                st.info("📋 この会話に参加している方の名前を選択してください。")
                
                # 参加者選択セレクトボックス
                selected_speaker = st.selectbox(
                    "どの参加者にしますか？",
                    [""] + speakers,
                    help="自分の名前を選択すると、会話履歴があなたの視点で表示されます"
                )
                
                if selected_speaker:
                    st.session_state['selected_speaker'] = selected_speaker
                    st.session_state['show_speaker_selection'] = False
                    st.session_state['speaker_selected'] = True
                    st.success(f"✅ 「{selected_speaker}」として設定しました！")
                    st.rerun()
                else:
                    st.warning("⚠️ 参加者を選択してください。")
                    st.stop()
            

            

            
            # ユーザー名の検証（名前が入力されている場合のみ）
            if own_name and own_name not in speakers:
                st.error(f"❌ エラー: 「{own_name}」は会話に参加していません。")
                st.info(f"**参加者一覧:** {', '.join(speakers)}")
                st.info("サイドバーで正しい名前を入力してください。")
                return
            
            # 基本情報表示（モバイル対応）
            # 参加者名が設定されている場合のみ表示
            if own_name:
                if st.session_state.get('is_mobile', False):
                # モバイル用の縦並び表示
                st.header("📊 基本情報")
                
                date_range = parser.get_date_range(df)
                
                # モバイル用のメトリクス表示
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("総メッセージ数", f"{len(df):,}件")
                    st.metric("会話日数", f"{df['date'].nunique()}日")
                with col2:
                    st.metric("参加者数", f"{len(speakers)}人")
                    st.metric("日付範囲", f"{date_range[0]} 〜 {date_range[1]}")
                
                st.markdown("**参加者:**")
                for speaker in speakers:
                    if speaker == own_name:
                        st.write(f"• **{speaker}** (あなた)")
                    else:
                        st.write(f"• {speaker}")
            else:
                # デスクトップ用の横並び表示
                with col2:
                    st.header("📊 基本情報")
                    
                    date_range = parser.get_date_range(df)
                    
                    st.metric("総メッセージ数", f"{len(df):,}件")
                    st.metric("会話日数", f"{df['date'].nunique()}日")
                    st.metric("参加者数", f"{len(speakers)}人")
                    st.metric("日付範囲", f"{date_range[0]} 〜 {date_range[1]}")
                    
                    st.markdown("**参加者:**")
                    for speaker in speakers:
                        if speaker == own_name:
                            st.write(f"• **{speaker}** (あなた)")
                        else:
                            st.write(f"• {speaker}")
            
            # タブで機能を分ける（モバイル対応）
            # 参加者名が設定されている場合のみ表示
            if own_name:
                if st.session_state.get('is_mobile', False):
                # モバイル用のタブ（少ないタブ数）
                tab1, tab2, tab3 = st.tabs(["💬 会話", "🔍 検索", "📈 分析"])
                
                with tab1:
                    display_conversation_tab(df, own_name, parser)
                
                with tab2:
                    display_search_tab(df, own_name, parser)
                
                with tab3:
                    # モバイル用の分析選択
                    analysis_type = st.selectbox(
                        "分析タイプを選択",
                        ["基本統計", "感情分析", "頻出ワード", "返信速度", "高度な分析"]
                    )
                    
                    if analysis_type == "基本統計":
                        display_stats_tab(df, own_name)
                    elif analysis_type == "感情分析":
                        display_emotion_analysis(df)
                    elif analysis_type == "頻出ワード":
                        display_word_analysis(df, own_name)
                    elif analysis_type == "返信速度":
                        display_message_speed_analysis(df, own_name)
                    elif analysis_type == "高度な分析":
                        display_advanced_stats(df, own_name)
                else:
                    # デスクトップ用のタブ
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 会話表示", "🔍 検索", "📈 分析", "📊 統計", "📈 高度な分析"])
                    
                    with tab1:
                        display_conversation_tab(df, own_name, parser)
                    
                    with tab2:
                        display_search_tab(df, own_name, parser)
                    
                    with tab3:
                        display_analysis_tab(df, own_name)
                    
                    with tab4:
                        display_stats_tab(df, own_name)
                    
                    with tab5:
                        display_advanced_stats(df, own_name)
            
            pass
                
        except Exception as e:
            st.error(f"ファイル解析エラー: {e}")
            st.info("ファイル形式を確認してください。LINEのバックアップテキストファイルである必要があります。")
    
    else:
        # 初期表示
        st.info("👆 サイドバーの「サンプルデータで試す」ボタンをクリックするか、LINEトーク履歴ファイルをアップロードしてください。")
        
        # 使用例
        st.markdown("### 📋 使用例")
        st.markdown("""
        1. **LINEでバックアップを取得**
           - LINEアプリ → 設定 → トーク → トーク履歴を送信
           - テキストファイル（.txt）が生成されます
        
        2. **ファイルをアップロード**
           - 上記のファイルアップロード機能を使用
        
        3. **会話を確認・分析**
           - スマホ風UIで会話を表示
           - 検索機能で特定の話題を探す
           - 感情分析や頻出ワードで会話を分析
        """)

def display_conversation_tab(df: pd.DataFrame, own_name: str, parser: LineTalkParser):
    """会話表示タブ"""
    st.header("💬 会話履歴")
    
    # 日付選択
    dates = sorted(df['date'].unique())
    selected_date = st.selectbox(
        "表示する日付を選択",
        dates,
        index=len(dates) - 1 if dates else 0
    )
    
    # 選択された日付のメッセージを取得
    daily_df = parser.filter_by_date(df, selected_date)
    
    if not daily_df.empty:
        # LINE風UIで表示
        chat_html = render_chat_messages(daily_df, own_name)
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
            {create_line_style_css()}
            </style>
        </head>
        <body>
            <div class="chat-container">{chat_html}</div>
        </body>
        </html>
        """
        st.components.v1.html(full_html, height=600, scrolling=True)
    else:
        st.info("選択された日付にメッセージがありません。")

def display_search_tab(df: pd.DataFrame, own_name: str, parser: LineTalkParser):
    """検索タブ"""
    st.header("🔍 メッセージ検索・フィルタ")
    
    # 検索フィルタを初期化
    search_filter = SearchFilter()
    
    # タブで検索機能を分ける
    search_tab1, search_tab2 = st.tabs(["🔍 キーワード検索", "⚙️ 詳細フィルタ"])
    
    with search_tab1:
        # 基本的なキーワード検索
        search_keyword = st.text_input(
            "検索キーワードを入力",
            placeholder="例: おはよう、楽しい、など"
        )
        
        if search_keyword:
            # 検索実行
            search_results = parser.search_messages(df, search_keyword)
            
            if not search_results.empty:
                st.success(f"「{search_keyword}」を含むメッセージを {len(search_results)} 件見つけました")
                
                # 検索結果を表示
                chat_html = render_chat_messages(search_results, own_name, search_keyword)
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                    {create_line_style_css()}
                    </style>
                </head>
                <body>
                    <div class="chat-container">{chat_html}</div>
                </body>
                </html>
                """
                st.components.v1.html(full_html, height=600, scrolling=True)
                
                # 検索結果の詳細
                with st.expander("📋 検索結果詳細"):
                    for _, row in search_results.iterrows():
                        st.write(f"**{row['date']} {row['time']}** - {row['sender']}: {row['message']}")
            else:
                st.warning(f"「{search_keyword}」を含むメッセージが見つかりませんでした。")
        else:
            st.info("検索キーワードを入力してください。")
    
    with search_tab2:
        # 詳細フィルタ機能
        st.subheader("⚙️ 詳細フィルタ設定")
        
        # 日付範囲フィルタ
        st.write("**📅 日付範囲**")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日", value=pd.to_datetime(df['date'].min()))
        with col2:
            end_date = st.date_input("終了日", value=pd.to_datetime(df['date'].max()))
        
        # 送信者フィルタ
        st.write("**👥 送信者**")
        speakers = df['sender'].unique()
        selected_speakers = st.multiselect(
            "送信者を選択",
            options=speakers,
            default=speakers.tolist()
        )
        
        # メッセージタイプフィルタ
        st.write("**📝 メッセージタイプ**")
        message_types = st.multiselect(
            "メッセージタイプを選択",
            options=['text', 'stamp', 'image', 'system'],
            default=['text', 'stamp', 'image', 'system']
        )
        
        # メッセージ長フィルタ
        st.write("**📏 メッセージ長**")
        col1, col2 = st.columns(2)
        with col1:
            min_length = st.number_input("最小文字数", min_value=0, value=0)
        with col2:
            max_length = st.number_input("最大文字数", min_value=0, value=1000)
        
        # 時間範囲フィルタ
        st.write("**⏰ 時間範囲**")
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input("開始時間", value=datetime.strptime("00:00", "%H:%M").time())
        with col2:
            end_time = st.time_input("終了時間", value=datetime.strptime("23:59", "%H:%M").time())
        
        # 絵文字フィルタ
        st.write("**😊 絵文字**")
        emoji_option = st.selectbox(
            "絵文字の有無",
            options=["すべて", "絵文字を含む", "絵文字を含まない"]
        )
        
        # フィルタ適用ボタン
        if st.button("🔍 フィルタを適用", type="primary"):
            # フィルタ設定を構築
            filters = {}
            
            # 日付範囲
            filters['date_range'] = (start_date.strftime("%Y/%m/%d"), end_date.strftime("%Y/%m/%d"))
            
            # 送信者
            if selected_speakers:
                filters['speakers'] = selected_speakers
            
            # メッセージタイプ
            if message_types:
                filters['message_types'] = message_types
            
            # メッセージ長
            if max_length > 0:
                filters['length'] = (min_length, max_length)
            
            # 時間範囲
            filters['time_range'] = (start_time.strftime("%H:%M"), end_time.strftime("%H:%M"))
            
            # 絵文字
            if emoji_option == "絵文字を含む":
                filters['has_emoji'] = True
            elif emoji_option == "絵文字を含まない":
                filters['has_emoji'] = False
            
            # フィルタ適用
            filtered_df = search_filter.apply_multiple_filters(df, filters)
            
            if not filtered_df.empty:
                st.success(f"フィルタ条件に一致するメッセージを {len(filtered_df)} 件見つけました")
                
                # フィルタ結果を表示
                chat_html = render_chat_messages(filtered_df, own_name)
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                    {create_line_style_css()}
                    </style>
                </head>
                <body>
                    <div class="chat-container">{chat_html}</div>
                </body>
                </html>
                """
                st.components.v1.html(full_html, height=600, scrolling=True)
                
                # フィルタ結果の統計
                st.subheader("📊 フィルタ結果の統計")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("メッセージ数", len(filtered_df))
                with col2:
                    st.metric("日数", filtered_df['date'].nunique())
                with col3:
                    st.metric("送信者数", filtered_df['sender'].nunique())
            else:
                st.warning("フィルタ条件に一致するメッセージが見つかりませんでした")

def display_analysis_tab(df: pd.DataFrame, own_name: str):
    """分析タブ"""
    st.header("📈 会話分析")
    
    # 分析オプション
    analysis_type = st.selectbox(
        "分析タイプを選択",
        ["感情分析", "頻出ワード分析", "高度な会話分析", "返信速度分析"]
    )
    
    if analysis_type == "感情分析":
        display_emotion_analysis(df)
    
    elif analysis_type == "頻出ワード分析":
        display_word_analysis(df, own_name)
    
    elif analysis_type == "高度な会話分析":
        display_advanced_stats(df, own_name)
    
    elif analysis_type == "返信速度分析":
        display_message_speed_analysis(df, own_name)

def display_emotion_analysis(df: pd.DataFrame):
    """感情分析表示"""
    st.subheader("😊 感情分析")
    
    # 感情分析の説明
    st.info("""
    **感情分析について**
    - 各メッセージの感情（ポジティブ/ネガティブ/中性）を分析します
    - 大量のメッセージがある場合、処理に時間がかかります
    - 初回実行時は感情分析モデルのダウンロードが必要です
    """)
    
    # 感情分析実行ボタン
    if st.button("🚀 感情分析を実行", type="primary"):
        # 確認ダイアログ
        if st.session_state.get('emotion_analysis_confirmed', False) or st.button("✅ 実行を確認"):
            st.session_state['emotion_analysis_confirmed'] = True
            
            # 感情分析実行
            with st.spinner("感情分析を実行中..."):
                emotion_analyzer = EmotionAnalyzer()
                
                # 進捗バーを表示
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # バッチサイズを設定（大量データの場合は小さく）
                batch_size = 16 if len(df) > 1000 else 32
                
                status_text.text(f"感情分析を開始します... (総メッセージ数: {len(df)}件)")
                
                df_with_emotion = emotion_analyzer.analyze_messages(df, batch_size=batch_size)
                
                progress_bar.progress(100)
                status_text.text("感情分析が完了しました！")
                
                # 結果をセッション状態に保存
                st.session_state['emotion_results'] = df_with_emotion
                st.session_state['emotion_analyzer'] = emotion_analyzer
                
                st.success("感情分析が完了しました！結果を表示します。")
    
    # 感情分析結果の表示
    if 'emotion_results' in st.session_state and 'emotion_analyzer' in st.session_state:
        df_with_emotion = st.session_state['emotion_results']
        emotion_analyzer = st.session_state['emotion_analyzer']
        
        if 'positive' in df_with_emotion.columns:
            # 日別感情サマリー
            daily_emotion = emotion_analyzer.get_daily_emotion_summary(df_with_emotion)
            
            if not daily_emotion.empty:
                # グラフ表示
                fig = create_emotion_chart(daily_emotion)
                st.plotly_chart(fig, use_container_width=True)
                
                # 詳細データ
                with st.expander("📊 感情分析詳細データ"):
                    st.dataframe(daily_emotion)
                    
                # 感情分析のリセットボタン
                if st.button("🔄 感情分析をリセット"):
                    if 'emotion_results' in st.session_state:
                        del st.session_state['emotion_results']
                    if 'emotion_analyzer' in st.session_state:
                        del st.session_state['emotion_analyzer']
                    if 'emotion_analysis_confirmed' in st.session_state:
                        del st.session_state['emotion_analysis_confirmed']
                    st.rerun()
            else:
                st.warning("感情分析データがありません")
        else:
            st.warning("感情分析モデルの読み込みに失敗しました")
    else:
        # 感情分析が実行されていない場合のプレビュー
        st.info("👆 上記の「感情分析を実行」ボタンをクリックして分析を開始してください。")
        
        # サンプルデータでプレビュー表示
        sample_emotion_data = create_sample_emotion_data()
        if not sample_emotion_data.empty:
            st.subheader("📊 感情分析プレビュー（サンプルデータ）")
            fig = create_emotion_chart(sample_emotion_data)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("※ これはサンプルデータです。実際の分析結果ではありません。")

def display_word_analysis(df: pd.DataFrame, own_name: str):
    """頻出ワード分析表示"""
    st.subheader("☁️ 頻出ワード分析")
    
    # 分析対象選択
    analysis_target = st.selectbox(
        "分析対象を選択",
        ["全体", "自分の発言", "相手の発言", "特定の日"]
    )
    
    with st.spinner("頻出ワードを分析中..."):
        word_analyzer = WordAnalyzer()
        
        if analysis_target == "全体":
            word_freq = word_analyzer.analyze_messages(df)
        elif analysis_target == "自分の発言":
            word_freq = word_analyzer.get_speaker_word_freq(df, own_name)
        elif analysis_target == "相手の発言":
            speakers = df[df['type'] == 'message']['sender'].unique()
            other_speakers = [s for s in speakers if s != own_name]
            if other_speakers:
                word_freq = word_analyzer.get_speaker_word_freq(df, other_speakers[0])
            else:
                word_freq = {}
        elif analysis_target == "特定の日":
            dates = sorted(df['date'].unique())
            selected_date = st.selectbox("日付を選択", dates)
            word_freq = word_analyzer.get_daily_word_freq(df, selected_date)
        
        if word_freq:
            # ワードクラウド風グラフ表示
            fig = create_wordcloud_figure(word_freq, f"{analysis_target}の頻出ワード")
            st.plotly_chart(fig, use_container_width=True)
            
            # 詳細リスト
            with st.expander("📋 頻出ワード詳細"):
                word_df = pd.DataFrame(list(word_freq.items()), columns=['ワード', '出現回数'])
                st.dataframe(word_df.head(20))
        else:
            st.warning("頻出ワードが見つかりませんでした")

def display_message_speed_analysis(df: pd.DataFrame, own_name: str):
    """返信速度分析表示"""
    st.subheader("🚀 返信速度分析")
    
    st.info("""
    **返信速度分析について**
    - メッセージの送信間隔を分析して、会話のテンポを測定します
    - 発言者別の送信速度レベルを判定します
    - 時間帯別の送信速度パターンを可視化します
    """)
    
    # 分析実行
    with st.spinner("返信速度を分析中..."):
        from analyzer import ConversationAnalyzer
        analyzer = ConversationAnalyzer()
        speed_stats = analyzer.analyze_message_speed(df)
    
    if speed_stats:
        # 全体統計
        overall_stats = speed_stats['全体統計']
        st.subheader("📊 全体統計")
        
        # 会話テンポレベルを強調表示
        tempo_level = overall_stats['会話テンポレベル']
        if '🔥' in tempo_level:
            st.success(f"**会話テンポレベル: {tempo_level}** - 超活発な会話です！")
        elif '💬' in tempo_level:
            st.info(f"**会話テンポレベル: {tempo_level}** - 活発な会話です")
        elif '📱' in tempo_level:
            st.warning(f"**会話テンポレベル: {tempo_level}** - 普通の会話です")
        elif '😌' in tempo_level:
            st.info(f"**会話テンポレベル: {tempo_level}** - ゆったりとした会話です")
        else:
            st.warning(f"**会話テンポレベル: {tempo_level}** - 静かな会話です")
        
        # 統計メトリクス
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均メッセージ間隔", f"{overall_stats['平均メッセージ間隔（分）']:.1f}分")
        with col2:
            st.metric("最短メッセージ間隔", f"{overall_stats['最短メッセージ間隔（分）']:.1f}分")
        with col3:
            st.metric("最長メッセージ間隔", f"{overall_stats['最長メッセージ間隔（分）']:.1f}分")
        with col4:
            st.metric("総メッセージ数", f"{overall_stats['総メッセージ数']}件")
        
        # 発言者別返信速度
        st.subheader("👥 発言者別返信速度")
        from utils import create_message_speed_chart
        speed_chart = create_message_speed_chart(speed_stats)
        st.plotly_chart(speed_chart, use_container_width=True)
        
        # 発言者別詳細統計
        speaker_speeds = speed_stats['発言者別速度']
        if speaker_speeds:
            st.subheader("📋 発言者別詳細統計")
            for speaker, stats in speaker_speeds.items():
                # 速度レベルに応じて色分け
                speed_level = stats['送信速度レベル']
                if '🚀' in speed_level:
                    st.success(f"**{speaker}** - {speed_level}")
                elif '⚡' in speed_level:
                    st.info(f"**{speaker}** - {speed_level}")
                elif '🏃' in speed_level:
                    st.warning(f"**{speaker}** - {speed_level}")
                else:
                    st.error(f"**{speaker}** - {speed_level}")
                
                with st.expander(f"詳細統計"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("平均送信間隔", f"{stats['平均送信間隔（分）']:.1f}分")
                    with col2:
                        st.metric("最短送信間隔", f"{stats['最短送信間隔（分）']:.1f}分")
                    with col3:
                        st.metric("最長送信間隔", f"{stats['最長送信間隔（分）']:.1f}分")
                    with col4:
                        st.metric("連続メッセージ数", f"{stats['連続メッセージ数']}件")
        
        # 時間帯別返信速度
        st.subheader("⏰ 時間帯別返信速度")
        from utils import create_hourly_speed_chart
        hourly_speed_chart = create_hourly_speed_chart(speed_stats)
        st.plotly_chart(hourly_speed_chart, use_container_width=True)
        
        # 速度レベル説明
        st.subheader("📖 速度レベル説明")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **🚀 超高速** (1分以内)
            - 非常に活発な会話
            - 即座の返信が特徴
            
            **⚡ 高速** (1-3分)
            - 活発な会話
            - 素早い返信が特徴
            
            **🏃 中速** (3-10分)
            - 普通の会話テンポ
            - 適度な間隔
            """)
        with col2:
            st.markdown("""
            **🚶 低速** (10-30分)
            - ゆったりとした会話
            - じっくり考えるタイプ
            
            **🐌 超低速** (30分以上)
            - 非常にゆったりとした会話
            - 時間をかけて返信
            """)
    else:
        st.warning("返信速度分析に失敗しました")

# トピック要約機能を削除

def display_stats_tab(df: pd.DataFrame, own_name: str):
    """統計タブ"""
    st.header("📊 会話統計")
    
    # 統計情報表示
    display_stats_cards(df, own_name)
    
    # 詳細統計
    with st.expander("📈 詳細統計"):
        col1, col2 = st.columns(2)
        
        with col1:
            # 発言者別メッセージ数
            speaker_counts = df[df['type'] == 'message']['sender'].value_counts()
            fig = px.pie(
                values=speaker_counts.values,
                names=speaker_counts.index,
                title="発言者別メッセージ数"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 時間帯別メッセージ数
            df['hour'] = pd.to_datetime(df['time'], format='%H:%M').dt.hour
            hour_counts = df['hour'].value_counts().sort_index()
            fig = px.bar(
                x=hour_counts.index,
                y=hour_counts.values,
                title="時間帯別メッセージ数",
                labels={'x': '時間', 'y': 'メッセージ数'}
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    # セッション状態の初期化
    if 'file_uploaded' not in st.session_state:
        st.session_state['file_uploaded'] = False
    
    # 感情分析関連のセッション状態を初期化
    if 'emotion_analysis_confirmed' not in st.session_state:
        st.session_state['emotion_analysis_confirmed'] = False
    
    main() 