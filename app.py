import streamlit as st
import os
from datetime import datetime
from pathlib import Path
import re

# OpenAI API
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class SimpleKnowledgeBase:
    """シンプル版ナレッジベース（TXTのみ）"""
    
    def __init__(self):
        self.documents = []
    
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
        """文書をデータベースに追加（TXTのみ）"""
        ext = Path(file_path).suffix.lower()
        
        if ext != '.txt':
            return False, "現在TXTファイルのみ対応しています"
        
        text = self.extract_text_from_txt(file_path)
        
        # 文書をチャンクに分割 (約500文字ごと)
        chunks = self._split_text(text, chunk_size=500)
        
        # メモリに保存
        self.documents.append({
            "file_name": file_name,
            "chunks": chunks,
            "full_text": text,
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
        """クエリに関連する文書を検索（キーワードベース）"""
        if not self.documents:
            return []
        
        # キーワード抽出（簡易版）
        keywords = re.findall(r'\w+', query.lower())
        
        results = []
        for doc in self.documents:
            for chunk in doc['chunks']:
                score = sum(1 for keyword in keywords if keyword in chunk.lower())
                if score > 0:
                    results.append({
                        'text': chunk,
                        'score': score,
                        'file_name': doc['file_name']
                    })
        
        # スコアでソート
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 上位K件を返す
        top_results = results[:top_k]
        return [r['text'] for r in top_results] if top_results else []
    
    def get_document_list(self):
        """登録されている文書のリストを取得"""
        return [{
            'file_name': doc['file_name'],
            'chunks': len(doc['chunks']),
            'timestamp': doc['timestamp'],
            'text_preview': doc['text_preview']
        } for doc in self.documents]


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


def load_sample_documents(knowledge_base):
    """sample_documentsフォルダから文書を自動読み込み（TXTのみ）"""
    sample_dir = Path("./sample_documents")
    if not sample_dir.exists():
        return 0
    
    count = 0
    for file_path in sample_dir.glob("*.txt"):
        success, _ = knowledge_base.add_document(str(file_path), file_path.name)
        if success:
            count += 1
    
    return count


@st.cache_resource
def get_knowledge_base():
    """ナレッジベースをキャッシュして再利用"""
    kb = SimpleKnowledgeBase()
    load_sample_documents(kb)
    return kb


def main():
    st.set_page_config(
        page_title="社内情報特化型AI検索",
        page_icon="🏢",
        layout="wide"
    )
    
    st.title("🏢 社内情報特化型AI検索システム (シンプル版)")
    st.markdown("---")
    
    # セッション状態の初期化
    if 'knowledge_base' not in st.session_state:
        # キャッシュされたナレッジベースを使用
        st.session_state.knowledge_base = get_knowledge_base()
        st.session_state.sample_loaded = True
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # サイドバー: 設定とドキュメント管理
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # OpenAI APIキー入力
        api_key_input = st.text_input(
            "OpenAI APIキー",
            type="password",
            help="GPT-4を使用するためのAPIキーを入力してください",
            value=st.session_state.get('api_key', '')
        )
        
        # Streamlit Cloudのsecretsからも取得を試みる
        if not api_key_input:
            try:
                api_key_input = st.secrets["openai"]["api_key"]
                st.success("✅ APIキーを検出しました")
            except:
                pass
        
        if api_key_input:
            st.session_state.api_key = api_key_input
        
        st.markdown("---")
        st.header("📚 文書管理")
        
        # サンプル文書読み込み状態の表示
        if st.session_state.get('sample_loaded'):
            st.info("📂 サンプル文書を自動読み込みしました")
        
        # ファイルアップロード
        uploaded_files = st.file_uploader(
            "社内文書をアップロード (TXTのみ)",
            type=['txt'],
            accept_multiple_files=True,
            help="現在TXTファイルのみ対応しています"
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
                        for i, source in enumerate(message['sources']):
                            st.text(f"--- 参考{i+1} ---\n{source}\n")
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
                context_docs = st.session_state.knowledge_base.search(question, top_k=3)
                
                if context_docs:
                    # AIアシスタントを初期化
                    assistant = CompanyAIAssistant(
                        st.session_state.knowledge_base,
                        st.session_state.api_key
                    )
                    
                    # 回答を生成
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
    2. 社内文書（TXTファイル）をアップロードして追加
    3. チャット欄で質問を入力して検索
    4. AIが社内文書を参照して回答を生成
    
    ### 💡 特徴
    - **超シンプル**: 依存関係を最小化（Streamlit + OpenAIのみ）
    - **確実に動作**: TXTファイル専用
    - **キーワード検索**: 高速で軽量
    - **サンプル文書**: 自動的に`sample_documents`フォルダから読み込み
    
    ### ⚠️ 注意事項
    - OpenAI APIキーが必要です（GPT-4を使用）
    - 現在TXTファイルのみ対応
    - PDF/DOCXを使いたい場合は、テキストに変換してからアップロードしてください
    """)


if __name__ == "__main__":
    main()
