# 🏢 社内情報特化型AI検索システム

社内文書（PDF、DOCX、TXT）をアップロードし、AIを使って質問に答えるシステムです。

## 🌟 主な機能

- **文書アップロード**: PDF、DOCX、TXTファイルに対応
- **自動ベクトル化**: 文書を自動的にベクトル化してセマンティック検索を実現
- **AI回答生成**: OpenAI GPT-4を使用して質問に対する回答を生成
- **チャット履歴**: 質問と回答の履歴を保持
- **参考文書表示**: 回答の根拠となった社内文書を表示

## 📋 必要な環境

- Python 3.8以上
- OpenAI APIキー（GPT-4が使用可能なもの）

## 🚀 セットアップ

### 1. 依存パッケージのインストール

```powershell
pip install -r requirements.txt
```

### 2. アプリケーションの起動

```powershell
streamlit run final.py
```

ブラウザが自動的に開き、アプリケーションが表示されます。

## 💡 使い方

### 初期設定

1. サイドバーの「OpenAI APIキー」欄にAPIキーを入力
2. 社内文書をアップロード（複数ファイル可）
3. 「追加」ボタンをクリックして文書を登録

### 質問の方法

1. メインエリアの入力欄に質問を入力
2. 「🔍 検索」ボタンをクリック
3. AIが社内文書を参照して回答を生成
4. 「📚 参考にした文書」をクリックすると、根拠となった文書を確認可能

### 例

**質問例:**
- 「経費申請の手順を教えてください」
- 「有給休暇の申請方法は？」
- 「出張時の交通費精算について」
- 「社員割引制度について教えて」

## 🔧 技術スタック

- **フロントエンド**: Streamlit
- **AI**: OpenAI GPT-4
- **ベクトルDB**: ChromaDB
- **埋め込みモデル**: Sentence Transformers (多言語対応)
- **文書処理**: PyPDF2, python-docx

## 📁 ファイル構造

```
社内特化型/
├── final.py              # メインアプリケーション
├── requirements.txt      # 依存パッケージ
├── README.md            # このファイル
└── company_db/          # データベース（自動作成）
```

## ⚙️ カスタマイズ

### チャンクサイズの変更

`CompanyKnowledgeBase`クラスの`_split_text`メソッドで調整できます：

```python
chunks = self._split_text(text, chunk_size=500)  # 500文字ごと
```

### 検索結果数の変更

`search`メソッドの`top_k`パラメータで調整できます：

```python
results = self.knowledge_base.search(question, top_k=3)  # 上位3件
```

### AIモデルの変更

`CompanyAIAssistant`クラスの`generate_answer`メソッドで変更できます：

```python
model="gpt-4"  # または "gpt-3.5-turbo" など
```

## 🔒 セキュリティ注意事項

- APIキーは環境変数や設定ファイルで管理することを推奨
- 機密情報を含む文書を扱う場合は、適切なアクセス制御を実装してください
- 本番環境では認証機能の追加を検討してください

## 🐛 トラブルシューティング

### ライブラリのインポートエラー

各ライブラリはオプショナルです。不足している場合は個別にインストールしてください：

```powershell
pip install PyPDF2
pip install python-docx
pip install chromadb
pip install sentence-transformers
```

### ChromaDBのエラー

データベースが破損した場合は、`company_db`フォルダを削除して再起動してください。

### OpenAI APIエラー

- APIキーが正しいか確認
- GPT-4が使用可能なプランか確認
- レート制限に達していないか確認

## 📝 ライセンス

このプロジェクトは社内利用を目的としています。

## 🤝 貢献

バグ報告や機能提案は、社内の開発チームまでお願いします。

---

**開発日**: 2025年11月22日
