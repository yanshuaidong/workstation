import requests
import json
import time
from typing import Optional, Dict, Any

def call_ai_api(
    prompt: str,
    model: str = "claude-opus-4-20250514-thinking",
    session_cookie: str = "YWFiMTUxNzEtN2E5OS00MjE5LTliYjQtZjk2OTFjYjU5NjZj",
    acw_tc_cookie: str = "1a0c384c17589563169655053eddbea1d9f5ab0f3d7b03c74289746cfa7048",
    temperature: float = 0.6,
    top_p: float = 1.0,
    presence_penalty: float = 0.0,
    frequency_penalty: float = 0.0,
    timeout: int = 60,
    output_file: str = "data.txt",
    debug: bool = False
) -> Optional[Dict[Any, Any]]:
    """
    调用AI接口获取响应
    
    Args:
        prompt: 用户提示词
        model: 模型名称
        session_cookie: SESSION cookie值
        acw_tc_cookie: acw_tc cookie值
        temperature: 温度参数
        top_p: topP参数
        presence_penalty: 存在惩罚
        frequency_penalty: 频率惩罚
        timeout: 超时时间（秒）
        output_file: 输出文件名
        debug: 是否打印调试信息
    
    Returns:
        完整的响应JSON对象，如果失败则返回None
    """
    
    url = "https://ai.xkw.cn/view/v1/chat/get-response-text"
    
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://ai.xkw.cn",
        "Pragma": "no-cache",
        "Referer": "https://ai.xkw.cn/chat",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "is-ajax-request": "true",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }
    
    cookies = {
        "SESSION": session_cookie,
        "acw_tc": acw_tc_cookie
    }
    
    data = {
        "model": model,
        "temperature": temperature,
        "topP": top_p,
        "presencePenalty": presence_penalty,
        "frequencyPenalty": frequency_penalty,
        "messages": [
            {
                "role": "user",
                "content": "You are a helpful assistant. Respond using markdown"
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "stream": True,
        "network": False
    }
    
    print(f"正在请求API，提示词: {prompt}")
    print(f"使用模型: {model}")
    print(f"超时时间: {timeout}秒")
    print("="*50)
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            cookies=cookies, 
            json=data, 
            stream=True, 
            timeout=timeout
        )
        
        if debug:
            print(f"HTTP状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
        
        response.raise_for_status()
        
        # 收集所有响应数据
        complete_response = ""
        thinking_content = ""
        actual_content = ""
        raw_lines = []
        start_time = time.time()
        has_received_data = False
        line_count = 0
        in_thinking = False
        
        print("开始接收流式响应...")
        print("="*50)
        
        for line in response.iter_lines(decode_unicode=True):
            line_count += 1
            if debug:
                print(f"原始行 {line_count}: {repr(line)}")
            
            if line is not None:  # 包括空行
                has_received_data = True
                raw_lines.append(line)
                
                # 处理thinking标签
                if line.strip() == '<think>':
                    in_thinking = True
                    if debug:
                        print("进入thinking模式")
                    continue
                elif line.strip() == '</think>':
                    in_thinking = False
                    if debug:
                        print("退出thinking模式")
                    continue
                
                # 分别收集thinking内容和实际响应内容
                if in_thinking:
                    thinking_content += line + "\n"
                    if debug:
                        print(f"Thinking: {line}")
                else:
                    # 只有非thinking的内容才显示给用户
                    if line.strip():  # 非空行
                        actual_content += line + "\n"
                        print(line)
                    else:
                        actual_content += "\n"
                        print()  # 保持空行
                
                # 完整内容包括所有行
                complete_response += line + "\n"
                        
            # 检查是否在规定时间内开始接收数据
            if not has_received_data and time.time() - start_time > timeout:
                print(f"\n错误: {timeout}秒内未收到任何响应数据")
                return None
            
            # 限制调试输出，避免过多日志
            if debug and line_count > 50:
                print("调试输出过多，停止打印原始行...")
                debug = False
                
        print("\n" + "="*50)
        print("响应接收完成")
        
        # 构建完整的响应对象
        final_response = {
            "complete_content": complete_response.strip(),
            "actual_content": actual_content.strip(),  # 去除thinking的纯响应内容
            "thinking_content": thinking_content.strip(),  # thinking内容
            "raw_lines": raw_lines,
            "metadata": {
                "model": model,
                "prompt": prompt,
                "total_lines": len(raw_lines),
                "thinking_lines": thinking_content.count('\n') if thinking_content else 0,
                "actual_lines": actual_content.count('\n') if actual_content else 0,
                "response_time": time.time() - start_time,
                "http_status": response.status_code
            }
        }
        
        # 打印响应格式信息
        print(f"响应格式信息:")
        print(f"- HTTP状态码: {response.status_code}")
        print(f"- 完整内容字符数: {len(complete_response)}")
        print(f"- 实际响应字符数: {len(actual_content)}")
        print(f"- Thinking内容字符数: {len(thinking_content)}")
        print(f"- 原始行数: {len(raw_lines)}")
        print(f"- 响应时间: {final_response['metadata']['response_time']:.2f}秒")
        
        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_response, f, ensure_ascii=False, indent=2)
        
        print(f"完整响应已保存到: {output_file}")
        
        return final_response
        
    except requests.exceptions.Timeout:
        print(f"错误: 请求超时（{timeout}秒）")
        return None
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return None
    except Exception as e:
        print(f"未知错误: {e}")
        return None


def test_api():
    # """测试API调用"""
    # prompt = "你好，请介绍一下你自己"
    # result = call_ai_api(prompt, debug=False)
    
    # if result:
    #     print("\n测试成功！")
    #     print(f"实际响应内容预览: {result['actual_content'][:100]}...")
    #     if result['thinking_content']:
    #         print(f"Thinking内容预览: {result['thinking_content'][:100]}...")
    # else:
    #     print("\n测试失败！")
# 基本使用
# result = call_ai_api("你的问题")

# 自定义参数
    result = call_ai_api(
        prompt="你好",
        model="claude-opus-4-20250514-thinking",
        timeout=90,  # 延长超时时间
        output_file="data.txt"
    )

    # 获取不同类型的内容
    if result:
        print("AI回复:", result['actual_content'])
        print("思考过程:", result['thinking_content'])
        print("响应时间:", result['metadata']['response_time'])

if __name__ == "__main__":
    test_api()