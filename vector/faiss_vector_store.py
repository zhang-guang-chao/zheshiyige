import json
import os
import numpy as np
import pickle
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba

def read_qa_json_file():
    """读取QA JSON文件"""
    # 获取当前文件所在目录的上级目录中的split_pdf文件夹
    current_dir = os.path.dirname(__file__)
    split_pdf_dir = os.path.join(current_dir, '..', 'split_pdf')
    json_file_path = os.path.join(split_pdf_dir, 'qa_output_2_web_engineer.json')
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"成功读取QA文件: {os.path.basename(json_file_path)}")
        print(f"总共有 {data.get('total_qa_pairs', 0)} 个问答对")
        return data
    
    except FileNotFoundError:
        print(f"文件未找到: {json_file_path}")
        return None
    except Exception as e:
        print(f"读取JSON文件时出错: {e}")
        return None

def preprocess_text(text):
    """预处理文本"""
    # 简单的文本预处理
    text = text.lower()
    # 移除标点符号
    import re
    text = re.sub(r'[^\w\s]', '', text)
    return text

def create_tfidf_vectors(qa_data):
    """使用TF-IDF创建文本向量"""
    if not qa_data or 'qa_pairs' not in qa_data:
        print("没有找到QA数据")
        return None, None, None
    
    qa_pairs = qa_data['qa_pairs']
    
    # 准备文本数据
    questions = []
    answers = []
    combined_texts = []
    
    for qa in qa_pairs:
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        
        questions.append(question)
        answers.append(answer)
        # 将问题和答案组合
        combined_text = f"{question} {answer}"
        combined_texts.append(preprocess_text(combined_text))
    
    print(f"准备处理 {len(combined_texts)} 个文本...")
    
    # 创建TF-IDF向量
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words=None,
        ngram_range=(1, 2)
    )
    
    tfidf_matrix = vectorizer.fit_transform(combined_texts)
    print(f"TF-IDF矩阵形状: {tfidf_matrix.shape}")
    
    return tfidf_matrix, vectorizer, {
        'questions': questions,
        'answers': answers,
        'combined_texts': combined_texts
    }

def create_faiss_index(tfidf_matrix):
    """创建FAISS索引"""
    # 转换为numpy数组
    vectors = tfidf_matrix.toarray().astype('float32')
    dimension = vectors.shape[1]
    
    print(f"创建FAISS索引，维度: {dimension}")
    
    # 创建L2距离的索引
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)
    
    print(f"FAISS索引创建完成，包含 {index.ntotal} 个向量")
    return index

def save_faiss_store(index, vectorizer, metadata, output_dir='faiss_data'):
    """保存FAISS向量存储到文件"""
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存FAISS索引
    faiss_path = os.path.join(output_dir, 'qa_index.faiss')
    faiss.write_index(index, faiss_path)
    print(f"FAISS索引已保存到: {faiss_path}")
    
    # 保存向量器
    vectorizer_path = os.path.join(output_dir, 'tfidf_vectorizer.pkl')
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    print(f"TF-IDF向量器已保存到: {vectorizer_path}")
    
    # 保存元数据
    metadata_path = os.path.join(output_dir, 'qa_metadata.pkl')
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"元数据已保存到: {metadata_path}")
    
    return faiss_path, vectorizer_path, metadata_path

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

def main():
    """主函数"""
    print("=== FAISS本地向量存储系统 ===")
    print("正在初始化...")
    
    # 读取QA数据
    qa_data = read_qa_json_file()
    if not qa_data:
        print("❌ 无法读取问答库，程序退出")
        return
    
    # 创建TF-IDF向量
    print("\n正在创建TF-IDF向量...")
    tfidf_matrix, vectorizer, metadata = create_tfidf_vectors(qa_data)
    if tfidf_matrix is None:
        print("❌ TF-IDF向量创建失败")
        return
    
    # 创建FAISS索引
    print("\n正在创建FAISS索引...")
    index = create_faiss_index(tfidf_matrix)
    if index is None:
        print("❌ FAISS索引创建失败")
        return
    
    # 保存FAISS向量存储
    print("\n正在保存FAISS向量存储...")
    faiss_path, vectorizer_path, metadata_path = save_faiss_store(index, vectorizer, metadata)
    
    print("\n✅ FAISS向量存储创建完成！")
    print(f"FAISS索引文件: {faiss_path}")
    print(f"向量器文件: {vectorizer_path}")
    print(f"元数据文件: {metadata_path}")
    
    # 测试搜索功能
    print("\n=== 测试FAISS搜索功能 ===")
    test_queries = [
        "JavaScript有哪些数据类型？",
        "什么是Symbol？",
        "React Hooks是什么？"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = search_similar_questions_faiss(index, vectorizer, metadata, query, top_k=3)
        
        for result in results:
            print(f"  {result['rank']}. 相似度: {result['similarity']:.4f} (距离: {result['distance']:.4f})")
            print(f"     问题: {result['question']}")
            print(f"     答案: {result['answer'][:100]}...")
    
    # 测试加载功能
    print("\n=== 测试加载功能 ===")
    loaded_index, loaded_vectorizer, loaded_metadata = load_faiss_store()
    if loaded_index:
        print("✅ 加载测试成功！")
        results = search_similar_questions_faiss(loaded_index, loaded_vectorizer, loaded_metadata, "JavaScript数据类型", top_k=1)
        if results:
            print(f"加载后搜索测试: {results[0]['question']}")

if __name__ == "__main__":
    main() 