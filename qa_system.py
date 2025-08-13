import os
from openai import OpenAI
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    UnstructuredPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import Document
from typing import List, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class QASystemBuilder:
    def __init__(self):
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=os.environ.get("ARK_API_KEY"),
        )
        
        # 初始化LangChain组件
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.environ.get("ARK_API_KEY"),
            openai_api_base="https://ark.cn-beijing.volces.com/api/v3"
        )
        
    def load_documents(self, file_path: str) -> List[Document]:
        """加载本地文档"""
        if file_path.endswith('.txt'):
            loader = TextLoader(file_path)
        elif file_path.endswith('.csv'):
            loader = CSVLoader(file_path)
        elif file_path.endswith('.pdf'):
            loader = UnstructuredPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith('.xlsx'):
            loader = UnstructuredExcelLoader(file_path)
        else:
            raise ValueError(f"不支持的文档格式: {file_path}")
        
        return loader.load()
    
    def process_documents(self, docs: List[Document], persist_dir: str = "./chroma_db") -> Chroma:
        """处理文档并创建向量数据库"""
        # 文档分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(docs)
        
        # 创建向量存储
        vectordb = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=persist_dir
        )
        vectordb.persist()
        return vectordb
    
    def create_qa_chain(self, vectordb: Chroma, model_name: str = "doubao-pro-32k-241215") -> RetrievalQA:
        """创建问答链"""
        llm = ChatOpenAI(
            model_name=model_name,
            temperature=0,
            openai_api_key=os.environ.get("ARK_API_KEY"),
            openai_api_base="https://ark.cn-beijing.volces.com/api/v3"
        )
        
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True
        )
    
    def query(self, qa_chain: RetrievalQA, question: str, stream: bool = False) -> None:
        """查询问答系统"""
        if stream:
            # 流式响应 - 使用真正的流式输出
            print("🤖 AI回答: ", end="", flush=True)
            
            try:
                # 获取相关文档
                retriever = qa_chain.retriever
                docs = retriever.get_relevant_documents(question)
                
                # 构建上下文
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # 构建提示词
                prompt = f"""基于以下文档内容回答问题：

文档内容：
{context}

问题：{question}

请用中文回答，要求准确、详细。"""
                
                # 使用OpenAI客户端进行流式调用
                response = self.client.chat.completions.create(
                    model="doubao-pro-32k-241215",
                    messages=[
                        {"role": "system", "content": "你是一个专业的技术问答助手，请基于提供的文档内容回答问题。"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                
                # 逐字显示响应
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        full_response += content
                
                print()  # 换行
                print("✅ 流式回答完成")
                
                # 保存结果用于显示来源文档
                result = {"result": full_response, "source_documents": docs}
                
            except Exception as e:
                print(f"\n❌ 流式回答出错: {e}")
                return
                
        else:
            # 标准响应
            print("🤖 AI回答: ", end="", flush=True)
            try:
                result = qa_chain({"query": question})
                print(result["result"])
                print("✅ 标准回答完成")
            except Exception as e:
                print(f"\n❌ 标准回答出错: {e}")
                return
        
        # 显示来源文档
        if 'source_documents' in result:
            print("\n📚 来源文档:")
            for i, doc in enumerate(result["source_documents"], 1):
                print(f"\n【文档 {i}】")
                print(f"内容: {doc.page_content[:200]}...")
                print(f"来源: {doc.metadata.get('source', '未知')}")
        else:
            print("\n📚 未找到来源文档")

def main():
    # 初始化系统构建器
    builder = QASystemBuilder()
    
    # 1. 加载本地话术库
    file_path = input("请输入话术库文件路径: ")
    try:
        docs = builder.load_documents(file_path)
        print(f"成功加载文档: {len(docs)}个段落")
    except Exception as e:
        print(f"加载文档失败: {e}")
        return
    
    # 2. 处理文档并创建向量数据库
    persist_dir = "./chroma_db"
    vectordb = builder.process_documents(docs, persist_dir)
    print(f"向量数据库已创建并保存到: {persist_dir}")
    
    # 3. 创建问答链
    qa_chain = builder.create_qa_chain(vectordb)
    print("问答系统已就绪，开始交互...\n")
    
    # 4. 交互问答
    while True:
        question = input("\n请输入问题(输入'退出'结束): ")
        if question.lower() in ['退出', 'exit', 'quit']:
            break
        
        stream = input("是否使用流式响应?(y/n): ").lower() == 'y'
        builder.query(qa_chain, question, stream)

if __name__ == "__main__":
    main()