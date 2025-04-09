from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.docstore.document import Document
import os

# 0. 设置环境变量（使用自己的API密钥）
os.environ["OPENAI_API_KEY"] = "sk-your-key"

# 1. 准备专用名词知识库（示例数据）
terms = [
    {"source": "Transformer", "target": "变压器", "type": "技术术语"},
    {"source": "LLM", "target": "大语言模型", "type": "缩写"},
    {"source": "New York", "target": "纽约", "type": "地名"},
    {"source": "GPT-4", "target": "GPT-4", "type": "产品名"},  # 保持不变的案例
]

# 转换为 Document 对象
term_docs = [Document(
    page_content=f"{term['source']} -> {term['target']} ({term['type']})",
    metadata={"source": term['source'], "target": term['target']}
) for term in terms]

# 2. 创建向量数据库
vectorstore = Chroma.from_documents(
    documents=term_docs,
    embedding=OpenAIEmbeddings()
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})  # 检索前3个相关结果

# 3. 创建自定义提示模板
template = """你是一个专业翻译助手，请根据以下术语表进行翻译：
{context}

待翻译文本：
{input}

注意事项：
1. 严格使用术语表中的对应翻译
2. 保持专业语气
3. 不要添加额外内容
请输出翻译结果："""
prompt = ChatPromptTemplate.from_template(template)

# 4. 初始化大模型
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 5. 构建处理链
def format_context(docs):
    """将检索到的文档格式化为术语表"""
    return "\n".join([f"- {doc.metadata['source']}: {doc.metadata['target']}" for doc in docs])

chain = (
        {"context": retriever | format_context, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)

# 6. 使用示例
input_text = "The Transformer architecture is fundamental to modern LLMs like GPT-4."
result = chain.invoke(input_text)
print("输入文本：", input_text)
print("翻译结果：", result)