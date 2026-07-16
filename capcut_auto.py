import pyautogui
import time
import sys
import threading
import subprocess
from pynput import keyboard

# ==================== 配置区域 ====================
# 1. 轨道 Y 坐标 (需要你根据自己屏幕稍微调整一下)
Y_SUBTITLE = 689  # 字幕轨道所在的垂直高度 (Y坐标)
Y_AUDIO = 800     # 音频轨道所在的垂直高度 (Y坐标)
X_CLICK_START = 500 # 尝试点击轨道的起始水平位置 (X坐标)

# 2. 截图路径
SEARCH_BOX_IMG = 'search_box.png' # 你需要提前截一张搜索框的小图放在同目录下

# 3. 参数调节
WAIT_AFTER_SEARCH = 1.0 # 搜索回车后，等待剪映跳转的时间(秒)
CONFIDENCE_LEVEL = 0.8  # 图像识别的宽容度 (0.8表示80%相似即可)

# ==================================================

# 全局中止标志
abort_flag = False

def on_press(key):
    global abort_flag
    # 只有按下 Esc 键才中断，防止拦截到脚本自己模拟的按键（比如打字、回车）
    if key == keyboard.Key.esc:
        print(f"\n[!] 检测到 ESC 按键，正在紧急中断脚本...")
        abort_flag = True
        return False # 停止监听器

def start_keyboard_listener():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def scan_for_color(start_x, y, color_type, max_scan=500):
    """
    沿着水平方向向右扫描特定的颜色特征
    color_type: 'red' (字幕) 或 'blue' (音频)
    返回找到颜色的 X 坐标，找不到返回 None
    """
    try:
        s = pyautogui.screenshot()
        is_retina = s.width > pyautogui.size().width
        
        for dx in range(0, max_scan, 5):
            check_x = start_x + dx
            px, py = check_x, y
            if is_retina:
                px *= 2
                py *= 2
                
            r, g, b = s.getpixel((px, py))[:3]
            
            if color_type == 'red':
                # 字幕是偏红色/橙色，R值明显大于G和B
                if r > 100 and r > g * 1.5 and r > b * 1.5:
                    return check_x
            elif color_type == 'blue':
                # 音频是偏蓝色，B值明显大于R
                if b > 100 and b > r * 1.5 and g > r * 0.8:
                    return check_x
    except Exception as e:
        pass
        
    return None

def find_and_focus_search_box():
    """尝试点击字幕轨道，直到搜索框出现"""
    global abort_flag
    current_x = X_CLICK_START
    max_tries = 15
    
    for _ in range(max_tries):
        if abort_flag: return None
        
        # 1. 扫描红色字幕轨道并点击 (防误点空白处)
        actual_x = scan_for_color(current_x, Y_SUBTITLE, 'red', max_scan=300)
        if actual_x:
            pyautogui.click(actual_x, Y_SUBTITLE)
            time.sleep(0.5) # 等待UI响应
        else:
            print("-> 当前附近未检测到红色字幕块，往右挪一点再找...")
            current_x += 30
            continue
        
        # 2. 在屏幕上寻找搜索框
        try:
            search_box_location = pyautogui.locateCenterOnScreen(SEARCH_BOX_IMG, confidence=CONFIDENCE_LEVEL)
            if search_box_location:
                # 【核心修复】Mac 视网膜屏幕下，图片识别返回的是“物理像素”，但 click 需要“逻辑坐标”
                # 必须将坐标除以缩放比例 (通常是 2)，否则鼠标会点到十万八千里外！
                scale = pyautogui.screenshot().width / pyautogui.size().width
                actual_x = search_box_location.x / scale
                actual_y = search_box_location.y / scale
                
                print(f"-> 成功找到搜索框！实际点击坐标应为 ({actual_x}, {actual_y})")
                
                # 返回一个带有 x 和 y 属性的对象（兼容原来的代码）
                class Pos:
                    def __init__(self, x, y):
                        self.x = x
                        self.y = y
                return Pos(actual_x, actual_y)
        except pyautogui.ImageNotFoundException:
            pass # 没找到，继续下一次循环
            
        print("-> 未找到搜索框，尝试点旁边一点...")
        current_x += 30 # 往右挪 30 个像素再试
        
    print("-> 尝试多次仍未找到搜索框，可能界面有变或截图不匹配。")
    return None

def wait_for_capcut():
    print("\n等待剪映变为当前活动窗口 (请切换到剪映并全屏)...", flush=True)
    last_app = ""
    while True:
        cmd = 'osascript -e \'tell application "System Events" to get name of first application process whose frontmost is true\''
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        app_name = result.stdout.strip()
        
        if app_name != last_app and app_name != "":
            print(f"当前置顶窗口是: [{app_name}]，继续等待剪映...", flush=True)
            last_app = app_name

        if app_name in ["剪映专业版", "CapCut", "JianYingPro", "JianyingPro", "剪映", "VideoFusion-macOS"]:
            print(f"-> 检测到 {app_name} 已激活！", flush=True)
            break
        time.sleep(1)

def main():
    global abort_flag
    
    # 1. 先等待剪映成为当前窗口
    wait_for_capcut()
    
    # 2. 剪映激活后，弹窗让用户输入数字 (使用 Mac 原生弹窗避免 Tkinter 报错)
    prompt_cmd = '''osascript -e 'text returned of (display dialog "请输入要循环的最大数字 (例如 7):" default answer "" with title "剪映自动化脚本")' '''
    result = subprocess.run(prompt_cmd, shell=True, capture_output=True, text=True)
    max_num_str = result.stdout.strip()
    
    if not max_num_str:
        print("用户取消了输入，退出脚本。")
        return
        
    try:
        max_num = int(max_num_str)
    except ValueError:
        print("请输入有效的整数！")
        return

    print("\n准备就绪！将在 1 秒后开始执行...")
    time.sleep(1)
    
    # 启动后台键盘监听防呆机制
    start_keyboard_listener()
    
    search_box_pos_cache = None
    
    for i in range(1, max_num + 1):
        if abort_flag:
            break
            
        print(f"\n========== 正在处理数字: {i} ==========")
        
        # 1. 选中字幕并找到搜索框
        if search_box_pos_cache is None:
            # 第一次循环，需要边点边找图片
            search_box_pos = find_and_focus_search_box()
            if not search_box_pos or abort_flag:
                print("-> 找不到搜索框，任务终止。")
                break
            search_box_pos_cache = search_box_pos
        else:
            # 后续循环，搜索框里已经有了数字，找原图会失败。所以直接用上次缓存的坐标即可。
            print("-> 扫描红色字幕轨道并点击...")
            actual_x = scan_for_color(X_CLICK_START, Y_SUBTITLE, 'red', max_scan=300)
            if actual_x:
                pyautogui.click(actual_x, Y_SUBTITLE)
            else:
                pyautogui.click(X_CLICK_START, Y_SUBTITLE)
            time.sleep(0.5)
            search_box_pos = search_box_pos_cache
            
        # 2. 精准点击搜索框的正中心
        click_x = search_box_pos.x
        click_y = search_box_pos.y
        
        # 强行抢夺焦点：先单击，等一下，再双击
        pyautogui.click(click_x, click_y)
        time.sleep(0.2)
        pyautogui.doubleClick(click_x, click_y)
        time.sleep(0.3) # 必须给剪映留出反应时间，确保光标在闪烁
        
        # 只有在搜索第二个数字（i > 1）时，才需要清空前一个数字
        if i > 1:
            # 双击已经全选了数字，只需要退格 1 次即可清空
            pyautogui.press('backspace', presses=1)
            time.sleep(0.1)
            
        pyautogui.write(str(i))
        time.sleep(0.2)
        pyautogui.press('enter')
        
        print(f"-> 搜索数字 {i} 完成，等待画面跳转...")
        time.sleep(WAIT_AFTER_SEARCH) # 等待剪映时间线滚动到对应位置
        
        if abort_flag: break
        
        # 3. 扫描蓝色音频轨道并选中 (防误点)
        print("-> 扫描并点击蓝色音频轨道...")
        audio_x = scan_for_color(X_CLICK_START, Y_AUDIO, 'blue', max_scan=500)
        if audio_x:
            pyautogui.click(audio_x, Y_AUDIO)
        else:
            print("-> 警告：未检测到蓝色音频块，强行在默认位置点击。")
            pyautogui.click(X_CLICK_START, Y_AUDIO)
        time.sleep(0.3)
        
        # 4. 按 M 打点
        print("-> 按下 M 键打点...")
        pyautogui.press('m')
        time.sleep(0.5) # 给一点缓冲时间再进入下一次循环

    if abort_flag:
        print("\n=== 任务被手动中断 ===")
    else:
        print("\n=== 全部任务完成！ ===")

if __name__ == "__main__":
    main()
