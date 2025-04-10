import json

from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_deepseek import ChatDeepSeek  # 假设使用官方SDK
from langchain_huggingface import HuggingFaceEmbeddings  # 使用开源Embeddings

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

api_key = config.get("api_key")
base_url = config.get("base_url")
model = config.get("model")

# 1. 准备专用名词知识库（保持不变）
terms = [
    {"source": "FortiToken", "target": "堡垒机令牌", "type": "技术术语"},
    {"source": "SSL VPN", "target": "安全套接字层虚拟专用网络", "type": "技术术语"},
    {"source": "QR code", "target": "快速响应代码", "type": "技术术语"},
]

term_docs = [Document(
    page_content=f"{term['source']} -> {term['target']} ({term['type']})",
    metadata={"source": term['source'], "target": term['target']}
) for term in terms]

# 2. 创建向量数据库（更换Embedding模型）
# 使用开源Embedding模型（示例使用 paraphrase-multilingual-MiniLM-L12-v2）
embedding_model = HuggingFaceEmbeddings(
    model_name = "sentence-transformers/all-mpnet-base-v2"
    # model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vectorstore = Chroma.from_documents(
    documents=term_docs,
    embedding=embedding_model  # 更换为本地Embedding模型
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. 创建Deepseek客户端（根据实际SDK调整）
llm = ChatDeepSeek(
    model=model,
    temperature=1.3,
    max_tokens=8000,
    api_key=api_key,
    # other params...
)

# 4. 构建处理链（提示模板需适配Deepseek）
template = """[INST] 你是一个专业翻译助手，将用户输入的文本翻译成中文，请严格遵循以下术语表：
{context}

待翻译文本：
{input}

要求：
1. 当遇到术语表中的术语时，必须使用术语表中的对应翻译，否则正常翻译
2. 保持技术文档的专业性
3. 禁止任何自由发挥
严格输出翻译后的文本，不要输出其它内容：[/INST]"""

prompt = ChatPromptTemplate.from_template(template)

def format_context(docs):
    """将检索到的文档格式化为术语表"""
    return "\n".join([f"- {doc.metadata['source']}: {doc.metadata['target']}" for doc in docs])

chain = (
        {"context": retriever | format_context, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)


if __name__ == "__main__":
    # 5. 使用示例（保持不变）
    input_text = "1/ FortiToken for SSL VPN (QR code will be provided by operation team, please refer to FortiToken Registration session for detail steps.)"
    result = chain.invoke(input_text)
    print("输入文本：", input_text)
    print("翻译结果：", result)
