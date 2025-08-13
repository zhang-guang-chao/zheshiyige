import json
import os
import sys
import numpy as np
import pickle
import faiss

# 添加上级目录到路径，以便导入llm_connector
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from llm_connector import create_client, chat_with_llm

def load_faiss_store(output_dir='faiss_data'):
    """加载FAISS向量存储"""
    try:
        # 加载FAISS索引
        faiss_path = os.path.join(output_dir, 'qa_index.faiss')
        index = faiss.read_index(faiss_path)
        print(f"FAISS索引加载成功，包含 {index.ntotal} 个向量")
        
        # 加载向量器
        vectorizer_path = os.path.join(output_dir, 'tfidf_vectorizer.pkl')
        with open(vectorizer_path, 'rb') as f:
            vectorizer = pickle.load(f)
        
        # 加载元数据
        metadata_path = os.path.join(output_dir, 'qa_metadata.pkl')
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        print("✅ FAISS向量存储加载成功！")
        return index, vectorizer, metadata
        
    except Exception as e:
        print(f"❌ 加载FAISS向量存储失败: {e}")
        return None, None, None

def preprocess_text(text):
    """预处理文本"""
    # 简单的文本预处理
    text = text.lower()
    # 移除标点符号
    import re
    text = re.sub(r'[^\w\s]', '', text)
    return text

def search_similar_questions_faiss(index, vectorizer, metadata, query, top_k=5):
    """使用FAISS搜索相似问题"""
    # 预处理查询
    processed_query = preprocess_text(query)
    
    # 将查询转换为TF-IDF向量
    query_vector = vectorizer.transform([processed_query]).toarray().astype('float32')
    
    # 使用FAISS搜索
    distances, indices = index.search(query_vector, top_k)
    
    results = []
    for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
        if idx < len(metadata['questions']):
            # 将L2距离转换为相似度分数 (1 / (1 + distance))
            similarity = 1 / (1 + distance)
            results.append({
                'rank': i + 1,
                'similarity': float(similarity),
                'distance': float(distance),
                'question': metadata['questions'][idx],
                'answer': metadata['answers'][idx]
            })
    
    return results

def create_similarity_prompt(user_question, search_results):
    """创建相似度匹配的prompt"""
    prompt = f"""你是一个前端高级工程师，拥有丰富的技术经验和专业知识。

现在需要你进行问题相似度匹配：

用户问题：{user_question}

请从以下搜索结果中找出与用户问题最相似的问题。如果找到相似度超过80%的问题，请回答"SIMILAR"并给出对应的答案；如果没有找到相似度超过80%的问题，请回答"NOT_SIMILAR"。

搜索结果：
"""
    
    # 添加搜索结果
    for i, result in enumerate(search_results[:5], 1):
        prompt += f"{i}. 问题：{result['question']}\n   答案：{result['answer']}\n   相似度：{result['similarity']:.4f}\n\n"
    
    prompt += """请严格按照以下格式回答：
- 如果找到相似问题：SIMILAR|答案内容
- 如果没有找到相似问题：NOT_SIMILAR

注意：只回答SIMILAR或NOT_SIMILAR，不要添加其他内容。"""
    
    return prompt

def ask_llm_for_similarity(client, user_question, search_results):
    """使用大模型进行相似度匹配"""
    if not search_results:
        return "NOT_SIMILAR", None
    
    prompt = create_similarity_prompt(user_question, search_results)
    
    messages = [
        {"role": "system", "content": "你是一个前端高级工程师，专门负责技术问题的相似度匹配。请严格按照指定格式回答。"},
        {"role": "user", "content": prompt}
    ]
    
    response = chat_with_llm(client, messages, stream=False)
    
    if response:
        if "SIMILAR|" in response:
            # 提取答案部分
            answer_part = response.split("SIMILAR|", 1)[1] if "SIMILAR|" in response else response
            return "SIMILAR", answer_part.strip()
        elif "NOT_SIMILAR" in response:
            return "NOT_SIMILAR", None
        else:
            # 如果格式不正确，尝试解析
            if "SIMILAR" in response:
                return "SIMILAR", response
            else:
                return "NOT_SIMILAR", None
    
    return None, None

def main():
    """主函数"""
    print("=== 智能问答系统（FAISS向量版）===")
    print("正在初始化...")
    
    # 加载FAISS向量存储
    index, vectorizer, metadata = load_faiss_store()
    if not index:
        print("❌ 无法加载FAISS向量存储，程序退出")
        return
    
    # 创建LLM客户端
    client = create_client()
    if not client:
        print("❌ 无法创建LLM客户端，程序退出")
        return
    
    print("✅ 系统初始化完成！")
    print("输入 'quit' 或 'exit' 退出对话")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            # 使用FAISS搜索相似问题
            print("🔍 正在搜索相似问题...")
            search_results = search_similar_questions_faiss(index, vectorizer, metadata, user_input, top_k=5)
            
            if search_results:
                print(f"找到 {len(search_results)} 个相似问题")
                # 显示前3个结果
                for i, result in enumerate(search_results[:3], 1):
                    print(f"  {i}. 相似度: {result['similarity']:.4f} - {result['question']}")
                
                # 使用大模型进行相似度匹配
                print("🤖 正在分析问题相似度...")
                similarity_result, answer = ask_llm_for_similarity(client, user_input, search_results)
                
                if similarity_result == "SIMILAR" and answer:
                    print(f"✅ 找到相似问题")
                    print(f"📝 答案：{answer}")
                elif similarity_result == "NOT_SIMILAR":
                    print("AI: 不好意思，我不知道")
                else:
                    print("AI: 不好意思，我不知道")
            else:
                print("AI: 不好意思，我不知道")
                    
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()
