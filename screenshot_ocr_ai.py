import os
import pyscreenshot as ImageGrab
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageFont, ImageDraw
import tkinter as tk
from aip import AipOcr
import openai
import pyperclip
import io
from config import BAIDU_OCR_CONFIG, OPENAI_API_KEY

def get_font():
    """获取可用的中文字体"""
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
        "C:/Windows/Fonts/msyh.ttf",    # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttf",  # 微软雅黑粗体
        "C:/Windows/Fonts/simkai.ttf",  # 楷体
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 14)  # 减小字体大小
                print(f"使用字体: {font_path}")
                return font
            except Exception as e:
                print(f"字体加载失败: {e}")
    
    # 如果没有找到中文字体，返回None
    print("未找到中文字体，使用默认字体")
    return None

def get_baidu_api_config():
    app_id = BAIDU_OCR_CONFIG.get("APP_ID")
    api_key = BAIDU_OCR_CONFIG.get("API_KEY")
    secret_key = BAIDU_OCR_CONFIG.get("SECRET_KEY")
    
    if not all([app_id, api_key, secret_key]):
        print("\n配置文件中未设置百度OCR API信息，请手动输入:")
        app_id = input("App ID: ")
        api_key = input("API Key: ")
        secret_key = input("Secret Key: ")
    else:
        print("\n使用配置文件中的百度OCR API信息")
    
    return app_id, api_key, secret_key

def get_openai_api_key():
    if OPENAI_API_KEY:
        print("使用配置文件中的OpenAI API Key")
        return OPENAI_API_KEY
    else:
        api_key = input("\n请输入 OpenAI API Key (可选): ")
        return api_key

def copy_image_to_clipboard(image_path):
    """复制图片到剪贴板"""
    try:
        # 读取图片
        image = Image.open(image_path)
        # 复制到剪贴板
        output = io.BytesIO()
        image.save(output, format="PNG")
        data = output.getvalue()
        
        # 复制到剪贴板
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data[12:])  # 跳过文件头
        win32clipboard.CloseClipboard()
        
        print("图片已复制到剪贴板")
    except Exception as e:
        print(f"复制图片失败: {e}")

def get_file_content(file_path):
    with open(file_path, 'rb') as fp:
        return fp.read()

def ocr_image(image_path, app_id, api_key, secret_key):
    client = AipOcr(app_id, api_key, secret_key)
    image = get_file_content(image_path)
    options = {}
    options["language_type"] = "CHN_ENG"
    options["detect_direction"] = "true"
    options["detect_language"] = "true"
    options["probability"] = "true"
    
    result = client.basicGeneral(image, options)
    
    if "words_result" in result:
        text = "\n".join([item["words"] for item in result["words_result"]])
        print("OCR 识别结果:")
        print(text)
        pyperclip.copy(text)
        print("识别结果已复制到剪贴板")
        return text
    else:
        print("OCR 识别失败:", result)
        return ""

def get_ai_response(text, api_key):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个智能助手，帮助用户处理文本内容。"},
            {"role": "user", "content": f"请分析以下文本:\n{text}"}
        ]
    )
    ai_text = response.choices[0].message.content
    print("AI 分析结果:")
    print(ai_text)
    return ai_text

def show_image_with_copy_button(image_path, ocr_text):
    """显示截图并添加复制按钮"""
    print(f"显示图片预览窗口: {image_path}")
    
    # 创建主窗口
    root = tk.Tk()
    root.title("截图预览")
    
    # 设置窗口大小和位置
    root.geometry("900x700")
    root.resizable(True, True)
    
    # 加载图片
    try:
        image = Image.open(image_path)
        print(f"图片加载成功: {image.width}x{image.height}")
        
        # 调整图片大小，限制最大宽度和高度
        max_width = 800
        max_height = 500
        if image.width > max_width or image.height > max_height:
            image.thumbnail((max_width, max_height), Image.LANCZOS)
            print(f"图片调整大小: {image.width}x{image.height}")
        
        # 创建PhotoImage
        photo = ImageTk.PhotoImage(image)
        print("PhotoImage创建成功")
        
        # 创建画布
        canvas = tk.Canvas(root, width=photo.width(), height=photo.height(), bg="white")
        canvas.pack(padx=20, pady=20)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        print("画布创建成功")
        
        # 保持引用，防止图片被垃圾回收
        canvas.image = photo
        
        # 创建按钮框架
        button_frame = tk.Frame(root, bg="white")
        button_frame.pack(pady=10, fill=tk.X)
        print("按钮框架创建成功")
        
        def copy_image():
            """复制图片到剪贴板"""
            print("复制图片按钮被点击")
            copy_image_to_clipboard(image_path)
            # 显示复制成功提示
            copy_status.config(text="✓ 图片已复制到剪贴板", fg="green")
        
        # 创建复制按钮
        copy_button = tk.Button(button_frame, text="复制图片到剪贴板", command=copy_image, 
                              width=30, height=2, font=('Arial', 12, 'bold'),
                              bg="#4CAF50", fg="white", activebackground="#45a049")
        copy_button.pack(pady=10)
        print("复制按钮创建成功")
        
        # 复制状态标签
        copy_status = tk.Label(button_frame, text="", font=('Arial', 10))
        copy_status.pack(pady=5)
        
        # 显示OCR结果
        if ocr_text:
            text_frame = tk.Frame(root, bg="white", bd=2, relief=tk.GROOVE)
            text_frame.pack(pady=10, padx=20, fill=tk.X, expand=True)
            
            label = tk.Label(text_frame, text="OCR 识别结果:", font=('Arial', 12, 'bold'), bg="white")
            label.pack(anchor=tk.W, padx=10, pady=5)
            
            text_widget = tk.Text(text_frame, height=8, wrap=tk.WORD, font=('Arial', 10))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            text_widget.insert(tk.END, ocr_text)
            text_widget.config(state=tk.DISABLED)
            print("OCR结果显示成功")
        
        # 运行窗口
        print("窗口运行中...")
        root.mainloop()
        print("窗口已关闭")
        
    except Exception as e:
        print(f"显示图片失败: {e}")
        # 创建错误提示窗口
        error_root = tk.Tk()
        error_root.title("错误")
        error_root.geometry("400x200")
        
        error_label = tk.Label(error_root, text=f"显示图片失败: {str(e)}", font=('Arial', 10))
        error_label.pack(pady=50)
        
        close_button = tk.Button(error_root, text="关闭", command=error_root.destroy, width=20)
        close_button.pack(pady=10)
        
        error_root.mainloop()

def take_screenshot():
    print("请选择截图区域...")
    
    # 确保screenshots文件夹存在
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    # 捕获整个屏幕
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    # 初始化变量
    start_x, start_y = -1, -1
    end_x, end_y = -1, -1
    drawing = False
    screenshot_taken = False
    selected_region = None
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal start_x, start_y, end_x, end_y, drawing, screenshot_taken
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_x, start_y = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                end_x, end_y = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            end_x, end_y = x, y
            screenshot_taken = True
    
    # 创建全屏窗口
    cv2.namedWindow("Screenshot", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Screenshot", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("Screenshot", mouse_callback)
    
    while True:
        # 创建显示图像
        display_img = screenshot_np.copy()
        
        if drawing or (start_x != -1 and end_x != -1):
            # 创建半透明覆盖层
            overlay = screenshot_np.copy()
            overlay = cv2.addWeighted(overlay, 0.3, np.zeros(overlay.shape, dtype=np.uint8), 0.7, 0)
            
            # 调整坐标顺序
            x1 = min(start_x, end_x)
            y1 = min(start_y, end_y)
            x2 = max(start_x, end_x)
            y2 = max(start_y, end_y)
            
            # 确保坐标有效
            if x1 < x2 and y1 < y2:
                # 将选择区域从覆盖层中"挖"出来，使用原始亮度
                overlay[y1:y2, x1:x2] = screenshot_np[y1:y2, x1:x2]
                # 绘制选择框
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # 绘制辅助线
                cv2.line(overlay, (x1, y1), (x2, y1), (0, 255, 0), 1)
                cv2.line(overlay, (x1, y1), (x1, y2), (0, 255, 0), 1)
                cv2.line(overlay, (x2, y1), (x2, y2), (0, 255, 0), 1)
                cv2.line(overlay, (x1, y2), (x2, y2), (0, 255, 0), 1)
                
                display_img = overlay
        
        cv2.imshow("Screenshot", display_img)
        key = cv2.waitKey(1) & 0xFF
        
        # 检查是否完成截图
        if screenshot_taken:
            break
        # 按ESC键取消
        elif key == 27:
            print("截图取消")
            cv2.destroyAllWindows()
            return None
    
    # 确保选择了有效的区域
    if start_x == -1 or end_x == -1:
        print("未选择截图区域")
        cv2.destroyAllWindows()
        return None
    
    # 调整坐标顺序，确保start < end
    x1 = min(start_x, end_x)
    y1 = min(start_y, end_y)
    x2 = max(start_x, end_x)
    y2 = max(start_y, end_y)
    
    # 裁剪选定区域
    if x1 < x2 and y1 < y2:
        # 保存截图
        cropped_img = screenshot_np[y1:y2, x1:x2]
        cropped_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)
        cropped_pil = Image.fromarray(cropped_img)
        
        # 生成唯一的文件名
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
        
        cropped_pil.save(image_path)
        print(f"截图已保存为 {image_path} (区域: {x1},{y1} 到 {x2},{y2})")
        
        # 显示冻结的选择区域并添加按钮
        print("显示冻结的选择区域...")
        frozen_img = screenshot_np.copy()
        
        # 创建半透明覆盖层
        overlay = screenshot_np.copy()
        overlay = cv2.addWeighted(overlay, 0.3, np.zeros(overlay.shape, dtype=np.uint8), 0.7, 0)
        
        # 将选择区域从覆盖层中"挖"出来，使用原始亮度
        overlay[y1:y2, x1:x2] = screenshot_np[y1:y2, x1:x2]
        # 绘制选择框
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # 绘制辅助线
        cv2.line(overlay, (x1, y1), (x2, y1), (0, 255, 0), 1)
        cv2.line(overlay, (x1, y1), (x1, y2), (0, 255, 0), 1)
        cv2.line(overlay, (x2, y1), (x2, y2), (0, 255, 0), 1)
        cv2.line(overlay, (x1, y2), (x2, y2), (0, 255, 0), 1)
        
        frozen_img = overlay
        
        # 按钮参数 - 缩小按钮
        button_size = 40  # 减小按钮大小
        button_margin = 8  # 减小按钮间距
        button_y = y2 + 10  # 按钮位置在框选区域下方
        
        # 计算按钮位置 - 居中显示在框选区域下方
        total_button_width = 3 * button_size + 2 * button_margin
        start_x = x1 + (x2 - x1 - total_button_width) // 2
        
        ocr_button_x = start_x
        copy_button_x = start_x + button_size + button_margin
        cancel_button_x = start_x + 2 * button_size + 2 * button_margin
        
        # 按钮区域
        buttons = {
            "ocr": (ocr_button_x, button_y, ocr_button_x + button_size, button_y + button_size),
            "copy": (copy_button_x, button_y, copy_button_x + button_size, button_y + button_size),
            "cancel": (cancel_button_x, button_y, cancel_button_x + button_size, button_y + button_size)
        }
        
        # 获取字体
        font = get_font()
        
        # 绘制按钮
        def draw_buttons(img):
            # 转换为PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            
            # OCR按钮 - 蓝色
            draw.rectangle([buttons["ocr"][0], buttons["ocr"][1], buttons["ocr"][2], buttons["ocr"][3]], fill=(25, 118, 210))
            if font:
                draw.text((buttons["ocr"][0] + 10, buttons["ocr"][1] + 12), "OCR", font=font, fill=(255, 255, 255))
            else:
                draw.text((buttons["ocr"][0] + 10, buttons["ocr"][1] + 12), "OCR", fill=(255, 255, 255))
            
            # 复制按钮 - 绿色
            draw.rectangle([buttons["copy"][0], buttons["copy"][1], buttons["copy"][2], buttons["copy"][3]], fill=(76, 175, 80))
            if font:
                draw.text((buttons["copy"][0] + 6, buttons["copy"][1] + 12), "复制", font=font, fill=(255, 255, 255))
            else:
                draw.text((buttons["copy"][0] + 6, buttons["copy"][1] + 12), "复制", fill=(255, 255, 255))
            
            # 取消按钮 - 红色
            draw.rectangle([buttons["cancel"][0], buttons["cancel"][1], buttons["cancel"][2], buttons["cancel"][3]], fill=(244, 67, 54))
            if font:
                draw.text((buttons["cancel"][0] + 6, buttons["cancel"][1] + 12), "取消", font=font, fill=(255, 255, 255))
            else:
                draw.text((buttons["cancel"][0] + 6, buttons["cancel"][1] + 12), "取消", fill=(255, 255, 255))
            
            # 转换回OpenCV格式
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # 绘制按钮
        frozen_img_with_buttons = draw_buttons(frozen_img)
        
        # 鼠标点击处理
        button_clicked = None
        
        def frozen_mouse_callback(event, x, y, flags, param):
            nonlocal button_clicked
            if event == cv2.EVENT_LBUTTONDOWN:
                # 检查点击位置
                for button_name, (x1, y1, x2, y2) in buttons.items():
                    if x1 <= x <= x2 and y1 <= y <= y2:
                        button_clicked = button_name
                        break
        
        # 显示带按钮的冻结画面
        cv2.namedWindow("Frozen Screenshot", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Frozen Screenshot", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback("Frozen Screenshot", frozen_mouse_callback)
        cv2.imshow("Frozen Screenshot", frozen_img_with_buttons)
        
        # 处理按钮点击
        ocr_text = ""
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if button_clicked:
                if button_clicked == "ocr":
                    # OCR 识别
                    print("开始 OCR 识别...")
                    cv2.destroyAllWindows()
                    # 获取API配置
                    app_id, api_key, secret_key = get_baidu_api_config()
                    # 执行OCR
                    ocr_text = ocr_image(image_path, app_id, api_key, secret_key)
                    # 显示图片和OCR结果
                    show_image_with_copy_button(image_path, ocr_text)
                    # AI 分析
                    if ocr_text:
                        openai_api_key = get_openai_api_key()
                        if openai_api_key:
                            get_ai_response(ocr_text, openai_api_key)
                        else:
                            print("未提供 OpenAI API Key，跳过 AI 分析")
                    break
                elif button_clicked == "copy":
                    # 复制图片到剪贴板
                    print("复制图片到剪贴板...")
                    copy_image_to_clipboard(image_path)
                    # 显示复制成功提示
                    success_img = frozen_img_with_buttons.copy()
                    # 转换为PIL图像
                    pil_success = Image.fromarray(cv2.cvtColor(success_img, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_success)
                    # 绘制成功提示
                    if font:
                        draw.text((copy_button_x + 2, button_y + 12), "✓", font=font, fill=(255, 255, 255))
                    else:
                        draw.text((copy_button_x + 2, button_y + 12), "✓", fill=(255, 255, 255))
                    # 转换回OpenCV格式
                    success_img = cv2.cvtColor(np.array(pil_success), cv2.COLOR_RGB2BGR)
                    cv2.imshow("Frozen Screenshot", success_img)
                    cv2.waitKey(1000)
                    # 重绘按钮
                    frozen_img_with_buttons = draw_buttons(frozen_img)
                    cv2.imshow("Frozen Screenshot", frozen_img_with_buttons)
                    button_clicked = None
                elif button_clicked == "cancel":
                    # 取消
                    print("取消操作")
                    cv2.destroyAllWindows()
                    break
            elif key == 27:
                # 按ESC键取消
                print("取消操作")
                cv2.destroyAllWindows()
                break
        
        return image_path
    else:
        print("无效的截图区域")
        cv2.destroyAllWindows()
        return None

def main():
    print("=== 截图 OCR AI 分析工具 ===")
    
    # 1. 截图
    image_path = take_screenshot()
    
    if not image_path:
        print("截图失败，程序退出")
        return

if __name__ == "__main__":
    main()