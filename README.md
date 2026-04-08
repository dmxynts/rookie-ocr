# 截图 OCR AI 分析工具

一个功能强大的Python工具，可实现屏幕截图、百度OCR文本识别和AI文本分析的完整流程。

## 功能特点

- 🖼️ **拖拽截图**：支持鼠标拖拽选择截图区域
- 🔍 **OCR 识别**：使用百度OCR API识别截图中的文本（支持中文）
- 🤖 **AI 分析**：使用OpenAI API分析识别的文本
- 📋 **自动复制**：识别结果自动复制到剪贴板
- ⚙️ **配置管理**：API信息单独存储在配置文件中

## 环境要求

- Python 3.7+
- 百度OCR API账号（需要申请）

## 安装步骤

1. **安装Python依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **申请百度OCR API**：
   - 访问 [百度智能云](https://cloud.baidu.com/)
   - 注册/登录账号
   - 进入控制台 → 产品服务 → 人工智能 → OCR
   - 创建应用，获取 App ID、API Key、Secret Key

3. **配置API信息**：
   - 编辑 `config.py` 文件
   - 填入百度OCR API和OpenAI API信息

## 使用方法

1. **运行脚本**：
   ```bash
   python screenshot_ocr_ai.py
   ```

2. **操作流程**：
   - 程序会显示整个屏幕的预览
   - **拖拽选择截图区域**：按住鼠标左键拖动，松开鼠标完成选择
   - **确认选择**：按Enter键确认截图
   - **取消截图**：按ESC键取消
   - 如果 `config.py` 中已配置百度OCR API信息，则直接使用
   - 否则，提示输入百度OCR API信息（App ID、API Key、Secret Key）
   - 识别截图中的文本并显示
   - 如果 `config.py` 中已配置OpenAI API Key，则直接使用
   - 否则，提示输入OpenAI API Key（可选）
   - 使用AI分析识别的文本

## 配置文件说明

`config.py` 文件用于存储API信息，格式如下：

```python
# 百度OCR API配置信息
BAIDU_OCR_CONFIG = {
    "APP_ID": "your_app_id",  # 请输入您的App ID
    "API_KEY": "your_api_key",  # 请输入您的API Key
    "SECRET_KEY": "your_secret_key"  # 请输入您的Secret Key
}

# OpenAI API配置信息（可选）
OPENAI_API_KEY = "your_openai_api_key"  # 请输入您的OpenAI API Key
```

## 注意事项

- 确保百度OCR API账号有足够的调用次数
- OpenAI API Key需要自行申请
- 截图质量会影响OCR识别效果
- 百度OCR API有调用频率限制，请合理使用
- 配置文件中的API信息请妥善保管，不要公开分享

## 依赖说明

- Pillow：图像处理
- baidu-aip：百度OCR API
- pyscreenshot：屏幕截图
- opencv-python：图像处理和拖拽功能
- numpy：数组处理
- openai：AI接口
- pyperclip：剪贴板操作

## 示例输出

```
=== 截图 OCR AI 分析工具 ===
请拖拽选择截图区域...
截图已保存为 screenshot.png (区域: 100,100 到 500,300)

使用配置文件中的百度OCR API信息
OCR 识别结果:
这是一段测试文本
用于测试OCR功能

识别结果已复制到剪贴板
使用配置文件中的OpenAI API Key
AI 分析结果:
这段文本是一个简单的测试，用于验证OCR功能是否正常工作。它包含两行内容，表明这是一个测试文本，并且其目的是测试OCR（光学字符识别）功能。
```

## 百度OCR API配置

1. **免费额度**：百度OCR提供一定的免费调用额度
2. **计费方式**：超出免费额度后按调用次数计费
3. **文档参考**：[百度OCR API文档](https://ai.baidu.com/ai-doc/OCR/zk3h7xz52)

## 常见问题

### Q: 百度OCR API调用失败怎么办？
A: 检查API信息是否正确，网络连接是否正常，API调用次数是否超限

### Q: 截图区域如何选择？
A: 程序启动后会显示屏幕预览，按住鼠标左键拖动选择区域，松开鼠标完成选择，按Enter键确认

### Q: AI分析可以使用其他模型吗？
A: 可以修改 `get_ai_response()` 函数中的 `model` 参数，如使用 `gpt-4`