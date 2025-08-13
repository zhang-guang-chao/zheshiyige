import re
import json
import tkinter as tk
from tkinter import filedialog
from typing import List, Dict, Optional
import tiktoken
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def check_api_key():
    """检查API密钥是否设置"""
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise ValueError("请设置 ARK_API_KEY 环境变量")
    return api_key


def create_client():
    """创建OpenAI客户端"""
    try:
        api_key = check_api_key()
        client = OpenAI(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
        )
        return client
    except Exception as e:
        print(f"创建客户端失败: {e}")
        return None


def select_json_file():
    """选择JSON文件并读取full_text"""
    # 初始化Tkinter
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 设置文件选择对话框
    file_path = filedialog.askopenfilename(
        title="选择包含full_text的JSON文件",
        filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
    )

    if not file_path:
        print("未选择任何文件")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "full_text" not in data:
            print("错误：JSON文件中没有找到 'full_text' 字段")
            return None

        print(f"成功读取JSON文件: {os.path.basename(file_path)}")
        return data["full_text"]

    except Exception as e:
        print(f"读取JSON文件时出错: {e}")
        return None


def split_text_semantically(text: str, max_tokens: int = 2000) -> List[str]:
    """
    语义化拆分长文本
    :param text: 输入文本
    :param max_tokens: 每个分块的最大token数
    :return: 拆分后的文本块列表
    """
    # 初始化tokenizer
    tokenizer = tiktoken.get_encoding("cl100k_base")

    # 按段落分割文本
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = len(tokenizer.encode(para))

        # 如果当前块加上新段落超过限制，保存当前块并开始新块
        if current_tokens + para_tokens > max_tokens and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_tokens = 0

        current_chunk.append(para)
        current_tokens += para_tokens

    # 添加最后一个块
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def generate_qa_pairs(client: OpenAI, text_chunk: str) -> List[Dict[str, str]]:
    """
    使用大模型生成问答对
    :param client: OpenAI客户端实例
    :param text_chunk: 文本块
    :return: 生成的QA对列表
    """
    try:
        response = client.chat.completions.create(
            model="doubao-pro-32k-241215",
            messages=[
                {
                    "role": "system",
                    # "content": "你是一个专业的内容分析师，请根据提供的文本生成高质量的问答对。",
                    "content": "你是一个高级web前端工程师，请根据提供的文本生成高质量的问答对。",
                },
                {
                    "role": "user",
                    "content": f"""请根据以下文本生成3-5个问答对，要求：
1. 问题类型包括：事实型、概念解释型、操作步骤型
2. 答案必须直接引用或精确概括原文
3. 用JSON格式返回结果，格式为：{{"qa_pairs": [{{"question": "问题", "answer": "答案"}}]}}

文本内容：
{text_chunk}""",
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        result = response.choices[0].message.content
        parsed_result = json.loads(result)
        return parsed_result.get("qa_pairs", [])

    except Exception as e:
        print(f"生成QA对时出错: {e}")
        return []


def process_text_to_qa(text: str) -> List[Dict[str, str]]:
    """
    处理文本生成问答对的主流程
    :param text: 输入文本
    :return: 结构化QA对列表
    """
    client = create_client()
    if not client:
        print("无法创建LLM客户端，请检查API配置")
        return []

    print("开始语义化拆分文本...")
    # 语义化拆分文本
    text_chunks = split_text_semantically(text)
    print(f"文本已拆分为 {len(text_chunks)} 个块")

    qa_pairs = []
    for i, chunk in enumerate(text_chunks, 1):
        print(f"正在处理第 {i}/{len(text_chunks)} 个文本块...")
        chunk_qa = generate_qa_pairs(client, chunk)
        qa_pairs.extend(chunk_qa)

    # 后处理：去重和过滤
    unique_qa = []
    seen_questions = set()

    for qa in qa_pairs:
        question = qa.get("question", "").strip()
        answer = qa.get("answer", "").strip()

        if question and answer and question not in seen_questions:
            seen_questions.add(question)
            unique_qa.append({"question": question, "answer": answer})

    return unique_qa


def save_qa_results(qa_pairs: List[Dict[str, str]], output_path: str = None):
    """保存QA结果到JSON文件"""
    if not output_path:
        # output_path = "qa_output.json"
        output_path = "qa_output_2_web_engineer.json"

    result_data = {"total_qa_pairs": len(qa_pairs), "qa_pairs": qa_pairs}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"QA结果已保存到: {output_path}")


def main():
    """主函数"""
    print("=== PDF文本QA生成器 ===")
    print("请选择包含full_text的JSON文件...")

    # 选择并读取JSON文件
    full_text = select_json_file()
    if not full_text:
        return

    print(f"文本长度: {len(full_text)} 字符")

    # 处理文本生成QA对
    qa_results = process_text_to_qa(full_text)

    if qa_results:
        # 保存结果
        save_qa_results(qa_results)
        print(f"✅ 成功生成 {len(qa_results)} 个QA对")
    else:
        print("❌ 未能生成任何QA对")


if __name__ == "__main__":
    main()
