import json
import os
import sys

# 添加上级目录到路径，以便导入llm_connector
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from llm_connector import create_client, chat_with_llm

def read_qa_json_file():
    """直接读取QA JSON文件"""
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

def create_similarity_prompt(user_question, qa_pairs):
    """创建相似度匹配的prompt"""
    prompt = f"""你是一个前端高级工程师，拥有丰富的技术经验和专业知识。

现在需要你进行问题相似度匹配：

用户问题：{user_question}

请从以下问答库中找出与用户问题最相似的问题。如果找到相似度超过80%的问题，请回答"SIMILAR"并给出对应的答案；如果没有找到相似度超过80%的问题，请回答"NOT_SIMILAR"。

问答库：
"""
    
    # 添加前20个问答对作为示例（避免token过多）
    for i, qa in enumerate(qa_pairs[:20], 1):
        prompt += f"{i}. 问题：{qa.get('question', '')}\n   答案：{qa.get('answer', '')}\n\n"
    
    prompt += """请严格按照以下格式回答：
- 如果找到相似问题：SIMILAR|答案内容
- 如果没有找到相似问题：NOT_SIMILAR

注意：只回答SIMILAR或NOT_SIMILAR，不要添加其他内容。"""
    
    return prompt

def ask_llm_for_similarity(client, user_question, qa_data):
    """使用大模型进行相似度匹配"""
    if not qa_data or 'qa_pairs' not in qa_data:
        return None, None
    
    qa_pairs = qa_data['qa_pairs']
    prompt = create_similarity_prompt(user_question, qa_pairs)
    
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
    print("=== 智能问答系统（相似度匹配版）===")
    print("正在初始化...")
    
    # 读取问答库
    qa_data = read_qa_json_file()
    if not qa_data:
        print("❌ 无法读取问答库，程序退出")
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
            
            # 使用大模型进行相似度匹配
            print("🤖 正在分析问题相似度...")
            similarity_result, answer = ask_llm_for_similarity(client, user_input, qa_data)
            
            if similarity_result == "SIMILAR" and answer:
                print(f"✅ 找到相似问题")
                print(f"📝 答案：{answer}")
            elif similarity_result == "NOT_SIMILAR":
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
