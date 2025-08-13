智能问答系统架构
├── 数据层 (本地话术库)
├── 嵌入层 (文本向量化)
├── 存储层 (向量数据库)
├── 检索层 (语义搜索)
└── 应用层 (问答接口)


PDF文档 → 文本提取 → 语义化拆分 → 向量化存储 → 问答接口
                     ↑
               大模型语义分析


split_pdf
    |- index.py 提取pdf为json
    |- semantic_split.py 大模型语义化拆分

llm
    ｜- index.py 模拟智能问答 回答json文件中的qa话术

vector
    | - faiss_vector_store.py 向量拆分
    | - index.py faiss向量相似问题
