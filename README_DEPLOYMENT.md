# Streamlit Cloudデプロイガイド

このアプリケーションをStreamlit Cloudにデプロイする手順です。

## 事前準備

1. **GitHubアカウント**が必要です
2. このリポジトリをGitHubにプッシュしておきます
3. **OpenAI APIキー**を取得しておきます

## デプロイ手順

### 1. Streamlit Cloudにサインアップ

1. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
2. GitHubアカウントでサインイン
3. 無料プランで開始

### 2. アプリのデプロイ

1. Streamlit Cloudダッシュボードで「New app」をクリック
2. リポジトリ情報を入力:
   - **Repository**: `Kiyopure/final-app-deploy`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. 「Advanced settings」をクリック

### 3. シークレット(APIキー)の設定

「Secrets」セクションに以下を追加:

```toml
[openai]
api_key = "sk-your-actual-openai-api-key"
```

### 4. デプロイ実行

「Deploy!」ボタンをクリックして待ちます(初回は5-10分かかることがあります)

## アプリのURL

デプロイが完了すると、以下のようなURLでアクセス可能になります:
```
https://your-app-name.streamlit.app
```

## 重要な注意事項

### データの永続化について

Streamlit Cloudは**エフェメラルストレージ**を使用するため:
- アプリが再起動されるとアップロードされたドキュメントやデータベースは消えます
- 本番環境では外部ストレージ(AWS S3、Google Cloud Storage等)の使用を推奨

### リソース制限

Streamlit Cloud無料プランの制限:
- **1 GBメモリ**
- **1 CPU**
- **月間アクティブ時間制限あり**

重いモデル(sentence-transformersなど)を使用する場合、メモリ不足になる可能性があります。

## トラブルシューティング

### メモリ不足エラー

`app.py`で軽量なモデルを使用するか、埋め込み機能を無効化:

```python
# 軽量モデルに変更
self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
```

### ChromaDBエラー

Streamlit Cloudでは永続化が難しいため、代替案:
- シンプルな辞書ベースの検索に変更
- 外部のベクトルデータベース(Pinecone、Weaviateなど)を使用

### ファイルアップロードが消える

アプリ再起動でファイルが消えるのを防ぐには:
- AWS S3やGoogle Cloud Storageに保存する設定を追加
- または、GitHubリポジトリの`sample_documents/`に事前配置

## ローカルテスト

デプロイ前にローカルで動作確認:

```powershell
cd c:\Users\medic\Desktop\社内特化型\final-app-deploy
.\env\Scripts\activate
streamlit run app.py
```

## 更新方法

コードを更新してGitHubにプッシュすると、Streamlit Cloudが自動的に再デプロイします:

```powershell
git add .
git commit -m "更新内容の説明"
git push origin main
```

## サポート

- [Streamlit公式ドキュメント](https://docs.streamlit.io/)
- [Streamlit Community Forum](https://discuss.streamlit.io/)
