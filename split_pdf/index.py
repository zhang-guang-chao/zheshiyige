import tkinter as tk
from tkinter import filedialog
import PyPDF2
import json
import os

def select_pdf_and_print_name():
    """创建一个窗口选择PDF文件并打印文件名"""
    # 初始化Tkinter
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 设置文件选择对话框
    file_path = filedialog.askopenfilename(
        title="选择PDF文件",
        filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
    )
    
    if file_path:  # 如果用户选择了文件
        # 获取文件名（不含路径）
        pdf_name = file_path.split("/")[-1]  # Linux/macOS
        pdf_name = pdf_name.split("\\")[-1]  # Windows
        
        print(f"您选择的PDF文件是: {pdf_name}")
        
        # 提取PDF文字
        extract_pdf_text(file_path, pdf_name)
    else:
        print("未选择任何文件")

def extract_pdf_text(pdf_path, pdf_name):
    """提取PDF中的文字并保存为JSON文件"""
    try:
        # 打开PDF文件
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # 提取所有页面的文字
            text_content = []
            full_text = ""  # 用于存储合并后的完整文本
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                text_content.append({
                    "page": page_num + 1,
                    "text": text
                })
                # 将每页文字添加到完整文本中，并在页面之间添加分隔符
                # full_text += f"\n--- 第 {page_num + 1} 页 ---\n"
                full_text += text
                # full_text += "\n"
            
            # 创建JSON数据结构
            pdf_data = {
                "filename": pdf_name,
                "total_pages": len(pdf_reader.pages),
                "pages": text_content
            }
            
            # 生成输出文件名
            output_filename = pdf_name.replace('.pdf', '_extracted.json')
            output_path = os.path.join(os.path.dirname(pdf_path), output_filename)
            
            # 保存为JSON文件
            with open(output_path, 'w', encoding='utf-8') as json_file:
                json.dump(pdf_data, json_file, ensure_ascii=False, indent=2)
            
            # 创建包含完整文本的新JSON文件
            full_text_data = {
                "filename": pdf_name,
                "total_pages": len(pdf_reader.pages),
                "full_text": full_text.strip()  # 移除首尾空白字符
            }
            
            # 生成完整文本的JSON文件名
            full_text_filename = pdf_name.replace('.pdf', '_full_text.json')
            full_text_path = os.path.join(os.path.dirname(pdf_path), full_text_filename)
            
            # 保存完整文本的JSON文件
            with open(full_text_path, 'w', encoding='utf-8') as json_file:
                json.dump(full_text_data, json_file, ensure_ascii=False, indent=2)
            
            print(f"PDF文字提取完成！")
            print(f"总页数: {len(pdf_reader.pages)}")
            print(f"分页JSON文件已保存到: {output_path}")
            print(f"完整文本JSON文件已保存到: {full_text_path}")
            
    except Exception as e:
        print(f"提取PDF文字时出错: {str(e)}")

# 运行函数
if __name__ == "__main__":
    select_pdf_and_print_name()