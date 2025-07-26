# 💬 ChatViz

LINEのトーク履歴を分析・可視化するWebアプリケーションです。

🌐 **デプロイ版**: https://line-talk-viewer-qy6nsvlg2nwdgfutymga6j.streamlit.app/

## 🌟 機能

### 📊 基本機能
- **会話表示** - LINE風のUIでメッセージを表示
- **検索・フィルタ** - 日付、発言者、キーワードで検索
- **基本統計** - メッセージ数、参加者数などの統計

### 📈 分析機能
- **感情分析** - メッセージの感情を分析（ポジティブ/ネガティブ/ニュートラル）
- **頻出ワード分析** - よく使われる単語を可視化
- **返信速度分析** - メッセージ送信速度を分析
- **高度な会話分析** - 時間帯、メッセージ長、絵文字使用率など

### 📱 モバイル対応
- **レスポンシブデザイン** - スマートフォン・タブレット対応
- **タッチフレンドリー** - 直感的な操作
- **最適化されたUI** - モバイル画面に最適化

## 🚀 デプロイ方法

### Streamlit Cloud（推奨）

1. **GitHubにアップロード**
   ```bash
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/chatviz.git
   git push -u origin main
   ```

2. **Streamlit Cloudでデプロイ**
   - [Streamlit Cloud](https://share.streamlit.io/) にアクセス
   - GitHubアカウントでログイン
   - リポジトリを選択
   - デプロイ

### その他のプラットフォーム

#### Heroku（無料プラン終了）
- 現在は有料プランのみ

#### Railway
- 月500時間まで無料
- 簡単なデプロイ

#### Render
- 月750時間まで無料
- 自動デプロイ対応

## 📋 必要なファイル

```
chatviz/
├── main.py              # メインアプリケーション
├── parser.py            # LINEファイル解析
├── analyzer.py          # 分析機能
├── utils.py             # UI・ユーティリティ
├── requirements.txt     # 依存関係
├── README.md           # このファイル
└── .gitignore          # Git除外設定
```

## 🔧 ローカル実行

```bash
# 依存関係のインストール
pip install -r requirements.txt

# アプリケーション起動
streamlit run main.py
```

## 📁 対応ファイル形式

### 形式1: `[YYYY/MM/DD HH:MM] Sender: Message`
```
[2024/01/15 14:30] 佐藤: こんにちは！
[2024/01/15 14:31] 田中: こんにちは！
```

### 形式2: `HH:MM\tSender\tMessage` + 日付行
```
2024/01/15(月)
14:30	佐藤	こんにちは！
14:31	田中	こんにちは！
```

## 🎯 使用技術

- **Streamlit** - Webアプリケーションフレームワーク
- **Pandas** - データ処理
- **Plotly** - データ可視化
- **Transformers** - 感情分析
- **Janome** - 日本語形態素解析

## 📱 モバイル対応

- **レスポンシブデザイン** - 画面サイズに応じた自動調整
- **タッチ最適化** - タップしやすいUI
- **軽量設計** - 高速読み込み

## 🔒 プライバシー

- アップロードされたファイルは一時的にのみ保存
- 分析結果はブラウザ内でのみ処理
- 外部へのデータ送信なし

## 📄 ライセンス

MIT License

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

---

**注意**: このアプリケーションは個人利用を目的としています。商用利用の際は適切なライセンス確認をお願いします。

---

**ChatViz** - LINEトーク履歴の分析・可視化ツール 