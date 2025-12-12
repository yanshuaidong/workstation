"""
通用自动点击器 - 使用 PyAutoGUI 模拟鼠标键盘操作
可以操作任何应用程序（浏览器、桌面应用等）

优化功能：
- 屏幕倒计时提示（使用 osascript）
- ESC 键随时退出
- 鼠标轨迹可视化
"""

import pyautogui
import time
import webbrowser
import subprocess
import sys
from pynput import keyboard

# 安全设置
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# 全局变量：是否继续运行
running = True


# ==================== 屏幕提示相关（使用 osascript） ====================

def show_notification(title, message):
    """使用 macOS 通知中心显示提示"""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def show_screen_message(message, duration=2):
    """
    在屏幕中央显示大字提示（使用独立进程）
    """
    # 创建一个临时的 Python 脚本在独立进程中运行
    script = f'''
import tkinter as tk
import sys

root = tk.Tk()
root.attributes('-topmost', True)
root.attributes('-alpha', 0.9)
root.overrideredirect(True)
root.configure(bg='#222222')

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

label = tk.Label(
    root, 
    text="{message}", 
    font=("Arial", 100, "bold"),
    bg="#222222",
    fg="#00FF00",
    padx=60,
    pady=40
)
label.pack()

root.update_idletasks()
w = root.winfo_width()
h = root.winfo_height()
x = (screen_width - w) // 2
y = (screen_height - h) // 2
root.geometry(f"+{{x}}+{{y}}")

root.after({int(duration * 1000)}, root.destroy)
root.mainloop()
'''
    # 在独立进程中运行，不阻塞主程序
    subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def countdown(seconds=3):
    """屏幕倒计时"""
    for i in range(seconds, 0, -1):
        show_screen_message(f"⏱️  {i}", duration=0.9)
        time.sleep(1)
    
    show_screen_message("🚀 开始!", duration=0.8)
    time.sleep(0.8)


def show_complete():
    """显示完成提示"""
    script = '''
import tkinter as tk

root = tk.Tk()
root.attributes('-topmost', True)
root.attributes('-alpha', 0.9)
root.overrideredirect(True)
root.configure(bg='#006600')

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

label = tk.Label(
    root, 
    text="✅ 完成!", 
    font=("Arial", 100, "bold"),
    bg="#006600",
    fg="white",
    padx=60,
    pady=40
)
label.pack()

root.update_idletasks()
w = root.winfo_width()
h = root.winfo_height()
x = (screen_width - w) // 2
y = (screen_height - h) // 2
root.geometry(f"+{x}+{y}")

root.after(2000, root.destroy)
root.mainloop()
'''
    subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def show_stopped():
    """显示停止提示"""
    script = '''
import tkinter as tk

root = tk.Tk()
root.attributes('-topmost', True)
root.attributes('-alpha', 0.9)
root.overrideredirect(True)
root.configure(bg='#660000')

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

label = tk.Label(
    root, 
    text="⛔ 已停止 (ESC)", 
    font=("Arial", 80, "bold"),
    bg="#660000",
    fg="white",
    padx=60,
    pady=40
)
label.pack()

root.update_idletasks()
w = root.winfo_width()
h = root.winfo_height()
x = (screen_width - w) // 2
y = (screen_height - h) // 2
root.geometry(f"+{x}+{y}")

root.after(2000, root.destroy)
root.mainloop()
'''
    subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# ==================== ESC 键监听 ====================

def start_esc_listener():
    """启动 ESC 键监听器"""
    def on_press(key):
        global running
        if key == keyboard.Key.esc:
            running = False
            print("\n⛔ 检测到 ESC 键，正在停止...")
            return False  # 停止监听
    
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener


def check_running():
    """检查是否继续运行"""
    if not running:
        raise KeyboardInterrupt("用户按下 ESC 键")


# ==================== 鼠标操作（带可视化） ====================

def get_mouse_position():
    """获取当前鼠标位置"""
    pos = pyautogui.position()
    print(f"当前鼠标位置: x={pos.x}, y={pos.y}")
    return pos


def click(x=None, y=None, clicks=1, button='left'):
    """点击指定位置（带视觉反馈）"""
    check_running()
    
    if x is not None and y is not None:
        # 先移动到目标位置（带动画）
        pyautogui.moveTo(x, y, duration=0.3)
        print(f"🖱️ 点击位置 ({x}, {y})")
    else:
        pos = pyautogui.position()
        print(f"🖱️ 点击当前位置 ({pos.x}, {pos.y})")
    
    time.sleep(0.1)
    pyautogui.click(clicks=clicks, button=button)


def move_to(x, y, duration=0.5):
    """移动鼠标到指定位置（带动画轨迹）"""
    check_running()
    print(f"➡️ 移动鼠标到 ({x}, {y})")
    pyautogui.moveTo(x, y, duration=duration)


def scroll(amount, x=None, y=None):
    """滚动页面"""
    check_running()
    direction = "⬆️ 向上" if amount > 0 else "⬇️ 向下"
    print(f"{direction}滚动 {abs(amount)} 单位")
    
    if x is not None and y is not None:
        pyautogui.scroll(amount, x, y)
    else:
        pyautogui.scroll(amount)


def scroll_down(amount=3):
    """向下滚动"""
    scroll(-amount)


def scroll_up(amount=3):
    """向上滚动"""
    scroll(amount)


def type_text(text, interval=0.05):
    """输入文本"""
    check_running()
    print(f"⌨️ 输入文本: {text}")
    pyautogui.typewrite(text, interval=interval)


def press_key(key):
    """按下指定按键"""
    check_running()
    print(f"⌨️ 按下按键: {key}")
    pyautogui.press(key)


def hotkey(*keys):
    """按下组合键"""
    check_running()
    print(f"⌨️ 按下组合键: {'+'.join(keys)}")
    pyautogui.hotkey(*keys)


def get_screen_size():
    """获取屏幕尺寸"""
    size = pyautogui.size()
    print(f"📺 屏幕尺寸: {size.width} x {size.height}")
    return size


def open_url(url):
    """使用默认浏览器打开网址"""
    check_running()
    print(f"🌐 正在打开网址: {url}")
    webbrowser.open(url)


# ==================== 演示功能 ====================

def demo_scroll_page():
    """演示：在当前页面上下滚动"""
    print("\n=== 开始滚动演示 ===")
    
    # 向下滚动 5 次
    for i in range(5):
        check_running()
        print(f"第 {i + 1} 次向下滚动")
        scroll_down(5)
        time.sleep(0.8)
    
    time.sleep(1)
    
    # 向上滚动回去
    print("\n滚动回顶部...")
    for i in range(5):
        check_running()
        scroll_up(5)
        time.sleep(0.5)
    
    print("=== 滚动演示完成 ===\n")


# ==================== 主程序 ====================

def main():
    """主函数"""
    global running
    target_url = "https://www.bloomberg.com/latest"
    
    print("=" * 50)
    print("🖱️  通用自动点击器")
    print("=" * 50)
    print("\n按 ESC 键可随时停止程序\n")
    
    # 启动 ESC 键监听
    esc_listener = start_esc_listener()
    
    try:
        # 获取屏幕信息
        screen = get_screen_size()
        
        # 倒计时
        print("\n准备开始...")
        countdown(3)
        
        if not running:
            raise KeyboardInterrupt()
        
        # 打开目标网址
        print("\n1. 打开 Bloomberg 页面...")
        open_url(target_url)
        
        # 等待页面加载
        print("\n2. 等待页面加载（5秒）...")
        for i in range(5):
            check_running()
            time.sleep(1)
        
        # 点击页面中央确保焦点在浏览器上
        center_x, center_y = screen.width // 2, screen.height // 2
        print(f"\n3. 点击屏幕中央获取焦点...")
        click(center_x, center_y)
        time.sleep(1)
        
        # 执行滚动演示
        print("\n4. 执行页面滚动...")
        demo_scroll_page()
        
        # 显示完成
        show_complete()
        print("\n✅ 演示完成！")
        
    except KeyboardInterrupt:
        show_stopped()
        print("\n⛔ 程序已停止")
    finally:
        running = False
        esc_listener.stop()
    
    print("\n程序结束。")


if __name__ == "__main__":
    main()
