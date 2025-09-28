"""
このファイルは、固定の文字列や数値などのデータを変数として一括管理するファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
# LangChainライブラリの安全なインポート
try:
    from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
    from langchain_community.document_loaders.csv_loader import CSVLoader
    from langchain_core.documents import Document
    import pandas as pd
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # LangChainがない場合のダミー値
    PyMuPDFLoader = None
    Docx2txtLoader = None
    TextLoader = None
    CSVLoader = None
    Document = None
    pd = None


def custom_csv_loader(path):
    """社員名簿CSV専用のカスタムローダー - 部署ごとにグループ化"""
    try:
        import pandas as pd
        
        # LangChain Documentクラスの安全なインポート
        if LANGCHAIN_AVAILABLE:
            from langchain_core.documents import Document
        else:
            # LangChainが利用できない場合のシンプルなDocumentクラス
            class Document:
                def __init__(self, page_content, metadata=None):
                    self.page_content = page_content
                    self.metadata = metadata or {}
        
        # CSVファイルを読み込み
        df = pd.read_csv(path, encoding='utf-8-sig')  # BOM対応
        
        # 部署列の確認
        if '部署' not in df.columns:
            # 部署列がない場合は全体を1つのドキュメントとして処理
            text = df.to_string(index=False)
            doc = Document(
                page_content=text,
                metadata={"source": path, "type": "csv"}
            )
            return [doc]
        
        documents = []
        
        # 部署ごとにグループ化
        grouped = df.groupby('部署')
        
        for dept_name, dept_group in grouped:
            # 部署の基本情報（検索用キーワードを強化）
            dept_text = f"部署: {dept_name}\n"
            dept_text += f"部署名: {dept_name}\n"
            dept_text += f"所属人数: {len(dept_group)}名\n"
            dept_text += f"従業員総数: {len(dept_group)}人\n"
            dept_text += f"スタッフ数: {len(dept_group)}人\n\n"
            
            # 検索用キーワードセクション
            dept_text += f"【検索キーワード】{dept_name} 従業員 社員 スタッフ メンバー 人事 一覧 リスト 名簿\n\n"
            
            # 従業員名簿一覧（簡潔版・4名以上表示保証）
            dept_text += f"【{dept_name}従業員名簿・一覧】\n"
            for i, (_, row) in enumerate(dept_group.iterrows(), 1):
                name = row['氏名（フルネーム）'] if pd.notna(row['氏名（フルネーム）']) else 'N/A'
                position = row['役職'] if pd.notna(row['役職']) else 'N/A'
                emp_id = row['社員ID'] if pd.notna(row['社員ID']) else 'N/A'
                dept_text += f"{i}. 【従業員{i}】{name} - 役職: {position} - ID: {emp_id}\n"
            dept_text += f"\n上記{len(dept_group)}名が{dept_name}の全従業員です。\n\n"
            
            # 詳細従業員情報
            dept_text += f"【{dept_name}の詳細従業員情報一覧（全{len(dept_group)}名）】\n\n"

            # 各従業員の情報を追加
            for i, (_, row) in enumerate(dept_group.iterrows(), 1):
                dept_text += f"■ 従業員{i} - {row['氏名（フルネーム）']}\n"
                for col in df.columns:
                    if pd.notna(row[col]):  # NaNでない値のみ追加
                        dept_text += f"  {col}: {row[col]}\n"
                dept_text += f"  所属部署: {dept_name}\n"
                dept_text += "\n---\n\n"
            
            # 検索用の追加情報
            dept_text += f"この部署（{dept_name}）には合計{len(dept_group)}名の従業員が所属しています。\n"
            
            # 役職情報の追加
            if '役職' in df.columns:
                positions = dept_group['役職'].value_counts()
                dept_text += f"役職構成: "
                position_list = []
                for pos, count in positions.items():
                    if pd.notna(pos):
                        position_list.append(f"{pos}({count}名)")
                dept_text += ", ".join(position_list) + "\n"
            
            # ドキュメントオブジェクトを作成
            doc = Document(
                page_content=dept_text,
                metadata={
                    "source": path,
                    "department": dept_name,
                    "employee_count": len(dept_group),
                    "type": "csv"
                }
            )
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        # エラーの場合は空のリストを返す
        return []


############################################################
# 共通変数の定義
############################################################

# ==========================================
# 画面表示系
# ==========================================
APP_NAME = "社内情報特化型生成AI検索アプリ"
ANSWER_MODE_1 = "社内文書検索"
ANSWER_MODE_2 = "社内問い合わせ"
CHAT_INPUT_HELPER_TEXT = "こちらからメッセージを送信してください。"
DOC_SOURCE_ICON = ":material/description: "
LINK_SOURCE_ICON = ":material/link: "
WARNING_ICON = ":material/warning:"
ERROR_ICON = ":material/error:"
SPINNER_TEXT = "回答生成中..."


# ==========================================
# ログ出力系
# ==========================================
LOG_DIR_PATH = "./logs"
LOGGER_NAME = "ApplicationLog"
LOG_FILE = "application.log"
APP_BOOT_MESSAGE = "アプリが起動されました。"


# ==========================================
# LLM設定系
# ==========================================
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.5


# ==========================================
# RAG参照用のデータソース系
# ==========================================
RAG_TOP_FOLDER_PATH = "./data"
# ベクターストアから取得する関連ドキュメントの数
RAG_TOP_K = 5
# テキスト分割の設定
RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 200
def get_csv_loader(path):
    """
    CSVファイルに応じて適切なローダーを返す
    社員名簿.csvの場合はカスタムローダー、それ以外は通常のCSVLoader
    """
    if "社員名簿.csv" in path:
        return custom_csv_loader(path)
    else:
        if LANGCHAIN_AVAILABLE and CSVLoader:
            return CSVLoader(path, encoding="utf-8").load()
        else:
            # フォールバック処理：pandasで読み込んでシンプルなドキュメントを作成
            try:
                import pandas as pd
                df = pd.read_csv(path, encoding='utf-8-sig')
                content = df.to_string(index=False)
                
                # シンプルなDocumentクラス
                class Document:
                    def __init__(self, page_content, metadata=None):
                        self.page_content = page_content
                        self.metadata = metadata or {}
                
                doc = Document(
                    page_content=content,
                    metadata={"source": path, "type": "csv"}
                )
                return [doc]
            except:
                return []

SUPPORTED_EXTENSIONS = {
    ".pdf": PyMuPDFLoader,
    ".docx": Docx2txtLoader,
    ".csv": get_csv_loader,
    ".txt": lambda path: TextLoader(path, encoding="utf-8")
}
WEB_URL_LOAD_TARGETS = [
    "https://generative-ai.web-camp.io/"
]


# ==========================================
# プロンプトテンプレート
# ==========================================
SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT = """
会話履歴と最新の入力をもとに、会話履歴なしでも理解できる独立した入力テキストを生成してください。

特に以下の点に注意してください：
- 部署名、従業員情報、社員データに関する質問の場合は、具体的な検索用語を含めてください
- 「人事部」「従業員」「社員」「スタッフ」などのキーワードを保持してください
- 検索対象を明確に示すような表現に変換してください

例：
- 入力「人事部の従業員情報を教えて」→ 出力「人事部に所属している従業員の一覧情報と詳細を教えてください」
- 入力「マーケティング部のスタッフは？」→ 出力「マーケティング部の社員・従業員の情報を教えてください」
"""

SYSTEM_PROMPT_DOC_SEARCH = """
    あなたは社内の文書検索アシスタントです。
    以下の条件に基づき、ユーザー入力に対して回答してください。

    【条件】
    1. ユーザー入力内容と以下の文脈との間に関連性がある場合、空文字「""」を返してください。
    2. ユーザー入力内容と以下の文脈との関連性が明らかに低い場合、「該当資料なし」と回答してください。

    【文脈】
    {context}
"""

SYSTEM_PROMPT_INQUIRY = """
    あなたは社内情報特化型のアシスタントです。
    以下の条件に基づき、ユーザー入力に対して回答してください。

    【条件】
    1. ユーザー入力内容と以下の文脈との間に関連性がある場合のみ、以下の文脈に基づいて回答してください。
    2. ユーザー入力内容と以下の文脈との関連性が明らかに低い場合、「回答に必要な情報が見つかりませんでした。」と回答してください。
    3. 憶測で回答せず、あくまで以下の文脈を元に回答してください。
    4. できる限り詳細に、マークダウン記法を使って回答してください。
    5. マークダウン記法で回答する際にhタグの見出しを使う場合、最も大きい見出しをh3としてください。
    6. 複雑な質問の場合、各項目についてそれぞれ詳細に回答してください。
    7. 従業員情報、部署情報、社員データに関する質問の場合は、文脈にある情報を積極的に活用して回答してください。
    8. 部署名、従業員名、役職などの検索では、部分的な一致でも関連性があると判断してください。
    9. 「一覧化して」「リスト化して」「教えて」などの要求で従業員情報が4名以上ある場合は、必ず4名以上を表示してください。
    10. 従業員情報の一覧表示では、名前、役職、社員IDを含む形で整理して表示してください。
    11. 文脈に従業員の詳細情報が複数含まれている場合は、可能な限り多くの従業員情報を含めて回答してください。
    12. 従業員一覧の要求では、番号付きリスト形式で表示し、各従業員の基本情報を含めてください。

    【文脈】
    {context}
"""


# ==========================================
# LLMレスポンスの一致判定用
# ==========================================
INQUIRY_NO_MATCH_ANSWER = "回答に必要な情報が見つかりませんでした。"
NO_DOC_MATCH_ANSWER = "該当資料なし"


# ==========================================
# エラー・警告メッセージ
# ==========================================
COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
NO_DOC_MATCH_MESSAGE = """
    入力内容と関連する社内文書が見つかりませんでした。\n
    入力内容を変更してください。
"""
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"
GET_LLM_RESPONSE_ERROR_MESSAGE = "回答生成に失敗しました。"
DISP_ANSWER_ERROR_MESSAGE = "回答表示に失敗しました。"