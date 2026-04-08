import os
import pyscreenshot as ImageGrab
import cv2
import numpy as np
from PIL import Image
from aip import AipOcr
import openai
import pyperclip
from config import BAIDU_OCR_CONFIG, OPENAI_API_KEY

def take_screenshot():
    print("请选择截图区域...")
    
    # 捕获整个屏幕
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    # 初始化变量
    start_x, start_y = -1, -1
    end_x, end_y = -1, -1
    drawing = False
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal start_x, start_y, end_x, end_y, drawing
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_x, start_y = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                end_x, end_y = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            end_x, end_y = x, y
    
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
        
        # 按Enter键确认选择
        if key == 13:
            break
        # 按ESC键取消
        elif key == 27:
            print("截图取消")
            cv2.destroyAllWindows()
            return None
    
    cv2.destroyAllWindows()
    
    # 确保选择了有效的区域
    if start_x == -1 or end_x == -1:
        print("未选择截图区域")
        return None
    
    # 调整坐标顺序，确保start < end
    x1 = min(start_x, end_x)
    y1 = min(start_y, end_y)
    x2 = max(start_x, end_x)
    y2 = max(start_y, end_y)
    
    # 裁剪选定区域
    if x1 < x2 and y1 < y2:
        cropped_img = screenshot_np[y1:y2, x1:x2]
        cropped_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2RGB)
        cropped_pil = Image.fromarray(cropped_img)
        cropped_pil.save('screenshot.png')
        print(f"截图已保存为 screenshot.png (区域: {x1},{y1} 到 {x2},{y2})")
        return 'screenshot.png'
    else:
        print("无效的截图区域")
        return None

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

def main():
    print("=== 截图 OCR AI 分析工具 ===")
    
    # 1. 截图
    image_path = take_screenshot()
    
    if not image_path:
        print("截图失败，程序退出")
        return
    
    # 2. OCR 识别 - 百度OCR
    app_id, api_key, secret_key = get_baidu_api_config()
    ocr_text = ocr_image(image_path, app_id, api_key, secret_key)
    
    # 3. AI 分析
    if ocr_text:
        openai_api_key = get_openai_api_key()
        if openai_api_key:
            get_ai_response(ocr_text, openai_api_key)
        else:
            print("未提供 OpenAI API Key，跳过 AI 分析")

if __name__ == "__main__":
    main()