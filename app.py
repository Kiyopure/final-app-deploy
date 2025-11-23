import streamlit as st
import os
from datetime import datetime
import json
from pathlib import Path
import hashlib

# PDFとDOCX処理用
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

# OpenAI API
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ベクトルデータベース (ChromaDB)
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

# 埋め込み用
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class CompanyKnowledgeBase:
    """社内情報ナレッジベース管理クラス"""
    
    def __init__(self, persist_directory="./company_db"):
        self.persist_directory = persist_directory
        self.documents = []
        
        # ChromaDBクライアントの初期化
        if chromadb:
            self.chroma_client = chromadb.Client(Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            ))
            try:
                self.collection = self.chroma_client.get_collection("company_docs")
            except:
                self.collection = self.chroma_client.create_collection("company_docs")
        else:
            self.chroma_client = None
            self.collection = None
            
        # 埋め込みモデルの初期化
        if SentenceTransformer:
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        else:
            self.embedding_model = None
    
    def extract_text_from_pdf(self, file_path):
        """PDFからテキストを抽出"""
        if not PdfReader:
            return "PDFライブラリがインストールされていません"
        
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"PDF読み込みエラー: {str(e)}"
    
    def extract_text_from_docx(self, file_path):
        """DOCXからテキストを抽出"""
        if not Document:
            return "DOCXライブラリがインストールされていません"
        
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            return f"DOCX読み込みエラー: {str(e)}"
    
    def extract_text_from_txt(self, file_path):
        """TXTファイルからテキストを抽出"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='shift-jis') as f:
                    return f.read()
            except Exception as e:
                return f"TXT読み込みエラー: {str(e)}"
        except Exception as e:
            return f"ファイル読み込みエラー: {str(e)}"
    
    def add_document(self, file_path, file_name):
        """文書をデータベースに追加"""
        # ファイルタイプに応じてテキストを抽出
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif ext == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif ext == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            return False, "サポートされていないファイル形式です"
        
        if not text or text.startswith("エラー") or text.startswith("ライブラリ"):
            return False, text
        
        # 文書をチャンクに分割 (約500文字ごと)
        chunks = self._split_text(text, chunk_size=500)
        
        # ChromaDBに保存
        if self.collection and self.embedding_model:
            doc_id = hashlib.md5(file_name.encode()).hexdigest()
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{i}"
                embedding = self.embedding_model.encode(chunk).tolist()
                
                self.collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "file_name": file_name,
                        "chunk_id": i,
                        "timestamp": datetime.now().isoformat()
                    }],
                    ids=[chunk_id]
                )
        
        # メタデータを保存
        self.documents.append({
            "file_name": file_name,
            "chunks": len(chunks),
            "timestamp": datetime.now().isoformat(),
            "text_preview": text[:200]
        })
        
        return True, f"文書を追加しました: {len(chunks)}個のチャンクに分割"
    
    def _split_text(self, text, chunk_size=500):
        """テキストをチャンクに分割"""
        chunks = []
        sentences = text.split('。')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def search(self, query, top_k=3):
        """クエリに関連する文書を検索"""
        if not self.collection or not self.embedding_model:
            return []
        
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            return results
        except Exception as e:
            st.error(f"検索エラー: {str(e)}")
            return []
    
    def get_document_list(self):
        """登録されている文書のリストを取得"""
        return self.documents


class CompanyAIAssistant:
    """社内情報特化型AIアシスタント"""
    
    def __init__(self, knowledge_base, api_key=None):
        self.knowledge_base = knowledge_base
        self.api_key = api_key
        
        if OpenAI and api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def generate_answer(self, question, context_docs):
        """質問に対する回答を生成"""
        if not self.client:
            return "OpenAI APIキーが設定されていません"
        
        # コンテキストを構築
        context = "\n\n".join([
            f"【参考資料{i+1}】\n{doc}"
            for i, doc in enumerate(context_docs)
        ])
        
        # プロンプトを構築
        system_prompt = """あなたは社内情報に特化したAIアシスタントです。
提供された社内文書を参照して、質問に正確に答えてください。
文書に記載されていない情報については、「提供された情報では不明です」と回答してください。"""
        
        user_prompt = f"""以下の社内文書を参照して質問に答えてください。

【社内文書】
{context}

【質問】
{question}

【回答】"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"回答生成エラー: {str(e)}"


def main():
    st.set_page_config(
        page_title="社内情報特化型AI検索",
        page_icon="🏢",
        layout="wide"
    )
    
    st.title("🏢 社内情報特化型AI検索システム")
    st.markdown("---")
    
    # セッション状態の初期化
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = CompanyKnowledgeBase()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # サイドバー: 設定とドキュメント管理
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # OpenAI APIキー入力
        api_key = st.text_input(
            "OpenAI APIキー",
            type="password",
            help="GPT-4を使用するためのAPIキーを入力してください"
        )
        
        if api_key:
            st.session_state.api_key = api_key
        
        st.markdown("---")
        st.header("📚 文書管理")
        
        # ファイルアップロード
        uploaded_files = st.file_uploader(
            "社内文書をアップロード",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="PDF, DOCX, TXTファイルに対応しています"
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if st.button(f"📄 {uploaded_file.name} を追加", key=uploaded_file.name):
                    # 一時ファイルとして保存
                    temp_path = f"./temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # データベースに追加
                    success, message = st.session_state.knowledge_base.add_document(
                        temp_path,
                        uploaded_file.name
                    )
                    
                    # 一時ファイルを削除
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        st.markdown("---")
        
        # 登録文書一覧
        st.subheader("📋 登録済み文書")
        docs = st.session_state.knowledge_base.get_document_list()
        
        if docs:
            for doc in docs:
                with st.expander(f"📄 {doc['file_name']}"):
                    st.write(f"**チャンク数:** {doc['chunks']}")
                    st.write(f"**登録日時:** {doc['timestamp']}")
                    st.write(f"**プレビュー:**")
                    st.text(doc['text_preview'])
        else:
            st.info("まだ文書が登録されていません")
    
    # メインエリア: チャットインターフェース
    st.header("💬 AI検索チャット")
    
    # チャット履歴表示
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**👤 あなた:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI:** {message['content']}")
                if 'sources' in message:
                    with st.expander("📚 参考にした文書"):
                        for source in message['sources']:
                            st.text(source)
            st.markdown("---")
    
    # 質問入力
    question = st.text_input(
        "質問を入力してください",
        placeholder="例: 経費申請の手順を教えてください",
        key="question_input"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        search_button = st.button("🔍 検索", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ 履歴をクリア", use_container_width=True)
    
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    if search_button and question:
        if not st.session_state.get('api_key'):
            st.error("⚠️ OpenAI APIキーを設定してください")
        else:
            with st.spinner("検索中..."):
                # 関連文書を検索
                results = st.session_state.knowledge_base.search(question, top_k=3)
                
                if results and results.get('documents') and results['documents'][0]:
                    # AIアシスタントを初期化
                    assistant = CompanyAIAssistant(
                        st.session_state.knowledge_base,
                        st.session_state.api_key
                    )
                    
                    # 回答を生成
                    context_docs = results['documents'][0]
                    answer = assistant.generate_answer(question, context_docs)
                    
                    # チャット履歴に追加
                    st.session_state.chat_history.append({
                        'role': 'user',
                        'content': question
                    })
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': answer,
                        'sources': context_docs
                    })
                    
                    st.rerun()
                else:
                    st.warning("関連する社内文書が見つかりませんでした。文書を追加してください。")
    
    # フッター
    st.markdown("---")
    st.markdown("""
    ### 📖 使い方
    1. **サイドバー**からOpenAI APIキーを設定
    2. 社内文書（PDF/DOCX/TXT）をアップロードして追加
    3. チャット欄で質問を入力して検索
    4. AIが社内文書を参照して回答を生成
    
    ### 💡 注意事項
    - OpenAI APIキーが必要です（GPT-4を使用）
    - 初回実行時に必要なライブラリのインストールが必要な場合があります
    - 文書は自動的にベクトル化され、セマンティック検索が可能になります
    """)


if __name__ == "__main__":
    # 必要なディレクトリを作成
    os.makedirs("./company_db", exist_ok=True)
    main()
