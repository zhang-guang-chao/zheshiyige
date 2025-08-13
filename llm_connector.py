import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量 - 指定langchain文件夹下的.env文件
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

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

def chat_with_llm(client, messages, stream=False):
    """与LLM进行对话"""
    try:
        if stream:
            # 流式响应 - 优化版本
            print("🤖 AI正在思考", end="", flush=True)
            
            stream_response = client.chat.completions.create(
                model="doubao-pro-32k-241215",
                messages=messages,
                stream=True,
            )
            
            response_content = ""
            print("\n💬 AI回答: ", end="", flush=True)
            
            # 添加打字机效果
            for chunk in stream_response:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    response_content += content
                    # 添加小延迟，模拟打字效果
                    time.sleep(0.01)
            
            print("\n✅ 回答完成")
            return response_content
        else:
            # 标准响应
            print("🤖 AI正在思考...")
            completion = client.chat.completions.create(
                model="doubao-pro-32k-241215",
                messages=messages,
            )
            response_content = completion.choices[0].message.content
            print(f"💬 AI回答: {response_content}")
            return response_content
    except Exception as e:
        print(f"❌ 对话失败: {e}")
        return None

def interactive_chat():
    """交互式对话功能"""
    print("🚀 欢迎使用AI对话系统！")
    print("=" * 50)
    print("📝 使用说明:")
    print("  • 输入 'quit' 或 'exit' 退出对话")
    print("  • 输入 'clear' 清空对话历史")
    print("  • 输入 'stream' 切换流式/非流式模式")
    print("  • 输入 'status' 查看当前状态")
    print("=" * 50)
    
    client = create_client()
    if not client:
        print("❌ 无法创建客户端，请检查配置")
        return
    
    messages = [
        {"role": "system", "content": "你是一个友好、专业的AI助手。请用中文回答用户的问题。"}
    ]
    
    stream_mode = False
    total_messages = 0
    
    while True:
        try:
            # 显示当前状态
            mode_icon = "⚡" if stream_mode else "📝"
            print(f"\n{mode_icon} 当前模式: {'流式输出' if stream_mode else '标准输出'}")
            print(f"📊 对话轮数: {total_messages}")
            print("-" * 40)
            
            user_input = input("👤 你: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 再见！感谢使用AI对话系统！")
                break
                
            if user_input.lower() == 'clear':
                messages = [
                    {"role": "system", "content": "你是一个友好、专业的AI助手。请用中文回答用户的问题。"}
                ]
                total_messages = 0
                print("✅ 对话历史已清空")
                continue
                
            if user_input.lower() == 'stream':
                stream_mode = not stream_mode
                mode_text = "流式输出" if stream_mode else "标准输出"
                mode_icon = "⚡" if stream_mode else "📝"
                print(f"✅ 已切换到{mode_icon} {mode_text}模式")
                continue
            
            if user_input.lower() == 'status':
                print(f"\n📊 系统状态:")
                print(f"  • 当前模式: {'流式输出' if stream_mode else '标准输出'}")
                print(f"  • 对话轮数: {total_messages}")
                print(f"  • 内存中的消息数: {len(messages)}")
                print(f"  • API状态: {'正常' if client else '异常'}")
                continue
            
            # 添加用户消息
            messages.append({"role": "user", "content": user_input})
            
            # 获取AI响应
            response = chat_with_llm(client, messages, stream=stream_mode)
            
            if response:
                # 添加AI响应到对话历史
                messages.append({"role": "assistant", "content": response})
                total_messages += 1
            else:
                # 如果响应失败，移除用户消息
                messages.pop()
                
        except KeyboardInterrupt:
            print("\n\n👋 再见！感谢使用AI对话系统！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")

def test_standard_request(client):
    """测试标准请求"""
    try:
        print("🧪 测试标准请求...")
        completion = client.chat.completions.create(
            model="doubao-pro-32k-241215",
            messages=[
                {"role": "system", "content": "你是人工智能助手"},
                {"role": "user", "content": "你好"},
            ],
        )
        print(f"✅ 标准请求成功: {completion.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ 标准请求失败: {e}")
        return False

def test_streaming_request(client):
    """测试流式请求"""
    try:
        print("🧪 测试流式请求...")
        stream = client.chat.completions.create(
            model="doubao-pro-32k-241215",
            messages=[
                {"role": "system", "content": "你是人工智能助手"},
                {"role": "user", "content": "你好"},
            ],
            stream=True,
        )
        
        print("💬 流式响应: ", end="", flush=True)
        for chunk in stream:
            if not chunk.choices:
                continue
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                time.sleep(0.01)  # 添加打字效果
        print("\n✅ 流式请求成功")
        return True
    except Exception as e:
        print(f"❌ 流式请求失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 AI对话系统")
    print("=" * 50)
    print("选择功能:")
    print("1. 🚀 开始对话")
    print("2. 🧪 运行测试")
    print("3. 📖 查看帮助")
    
    choice = input("\n请输入选择 (1, 2 或 3): ").strip()
    
    if choice == "1":
        interactive_chat()
    elif choice == "2":
        print("\n🧪 开始测试 LLM 连接器...")
        print("=" * 50)
        
        # 创建客户端
        client = create_client()
        if not client:
            print("❌ 无法创建客户端，请检查配置")
            return
        
        # 测试标准请求
        success1 = test_standard_request(client)
        print("-" * 30)
        
        # 测试流式请求
        success2 = test_streaming_request(client)
        print("-" * 30)
        
        if success1 and success2:
            print("🎉 所有测试通过！系统运行正常！")
        else:
            print("⚠️ 部分测试失败，请检查配置")
    elif choice == "3":
        print("\n📖 使用帮助:")
        print("=" * 50)
        print("🚀 开始对话: 选择选项1，进入交互式对话模式")
        print("⚡ 流式输出: 在对话中输入 'stream' 切换模式")
        print("📝 标准输出: 默认模式，一次性显示完整回答")
        print("🗑️ 清空历史: 输入 'clear' 清空对话历史")
        print("📊 查看状态: 输入 'status' 查看系统状态")
        print("❌ 退出系统: 输入 'quit' 或 'exit' 退出")
        print("=" * 50)
    else:
        print("❌ 无效选择，默认开始对话...")
        interactive_chat()

if __name__ == "__main__":
    main()