import sys
import os
import base64
import json
import requests
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QRect, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QPainterPath
import win32gui
import win32ui
import win32con
from PIL import Image
from config import BAIDU_OCR_CONFIG

class SnippingTool(QWidget):
    def __init__(self):
        super().__init__()
        # 1. 获取全屏截图
        self.screen_pixmap = self.grab_full_screen()
        
        # 2. 状态变量初始化
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False          # 必须存在！
        self.selection_finished = False    # 必须存在！
        self.selected_rect = QRect()       # 必须存在！
        
        self.toolbar = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        
        # 3. 窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background:transparent;")
        self.showFullScreen()

    def grab_full_screen(self):
        """使用 win32api 获取全屏截图并转为 QPixmap"""
        hdesktop = win32gui.GetDesktopWindow()
        left, top, right, bottom = win32gui.GetWindowRect(hdesktop)
        width = right - left
        height = bottom - top
        
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()
        
        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(img_dc, width, height)
        mem_dc.SelectObject(screenshot)
        mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)
        
        bmpinfo = screenshot.GetInfo()
        bmpstr = screenshot.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), 
                               bmpstr, 'raw', 'BGRX', 0, 1)
        
        win32gui.DeleteObject(screenshot.GetHandle())
        mem_dc.DeleteDC()
        img_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, desktop_dc)
        
        img.save("temp_ss.png")
        pixmap = QPixmap("temp_ss.png")
        return pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.screen_pixmap)

    # 情况1：正在拖拽中 -> 画遮罩 + 蓝色边框
        if self.is_selecting:
            rect = QRect(self.start_point, self.end_point).normalized()
            # 画半透明遮罩
            path = QPainterPath()
            path.addRect(QRectF(self.rect()))
            path.addRect(QRectF(rect))
            painter.fillPath(path, QColor(0, 0, 0, 100))
            # 画蓝色边框
            painter.setPen(QPen(QColor(0, 122, 255), 2, Qt.SolidLine))
            painter.drawRect(rect)
            return

    # 情况2：选区已确认 -> 画遮罩 + 蓝色边框 + 控制点
        if self.selection_finished and not self.selected_rect.isNull():
            # 画半透明遮罩
            path = QPainterPath()
            path.addRect(QRectF(self.rect()))
            path.addRect(QRectF(self.selected_rect))
            painter.fillPath(path, QColor(0, 0, 0, 100))

            # 画蓝色边框
            painter.setPen(QPen(QColor(0, 122, 255), 2, Qt.SolidLine))
            painter.drawRect(self.selected_rect)

            # 画四个角落的控制点
            corner_size = 6
            corners = [
                (self.selected_rect.topLeft(), corner_size),
                (self.selected_rect.topRight(), corner_size),
                (self.selected_rect.bottomLeft(), corner_size),
                (self.selected_rect.bottomRight(), corner_size)
            ]
            painter.setBrush(QColor(0, 122, 255))
            for pos, size in corners:
                painter.drawRect(pos.x() - size//2, pos.y() - size//2, size, size)



    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.is_selecting = True
            self.selection_finished = False
            if self.toolbar:
                self.toolbar.hide()
                self.toolbar = None

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self.is_selecting = False
            self.selection_finished = True
            
            x1, y1 = self.start_point.x(), self.start_point.y()
            x2, y2 = self.end_point.x(), self.end_point.y()
            self.selected_rect = QRect(QPoint(min(x1,x2), min(y1,y2)), 
                                       QPoint(max(x1,x2), max(y1,y2)))
            
            self.update()
            self.show_toolbar()

    def show_toolbar(self):
        if self.toolbar:
            self.toolbar.hide()
        
        self.toolbar = QWidget(self)
        self.toolbar.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.toolbar.setStyleSheet('''
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
        ''')
        
        layout = QHBoxLayout(self.toolbar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        
        # 复制按钮
        btn_copy = QPushButton("📋")
        btn_copy.setToolTip("复制到剪贴板")
        btn_copy.setFixedSize(28, 28)
        btn_copy.setStyleSheet('''
            QPushButton {
                background: none;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        ''')
        
        # 保存按钮
        btn_save = QPushButton("💾")
        btn_save.setToolTip("保存到文件")
        btn_save.setFixedSize(28, 28)
        btn_save.setStyleSheet('''
            QPushButton {
                background: none;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        ''')
        btn_save.clicked.connect(self.confirm_screenshot)
        
        # 分隔线
        separator = QWidget()
        separator.setFixedSize(1, 20)
        separator.setStyleSheet('background-color: #e0e0e0;')
        
        # 标注工具
        btn_pen = QPushButton("✏️")
        btn_pen.setToolTip("画笔")
        btn_pen.setFixedSize(28, 28)
        btn_pen.setStyleSheet('''
            QPushButton {
                background: none;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        ''')
        
        btn_text = QPushButton("T")
        btn_text.setToolTip("文本")
        btn_text.setFixedSize(28, 28)
        btn_text.setStyleSheet('''
            QPushButton {
                background: none;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        ''')
        
        # 分隔线
        separator2 = QWidget()
        separator2.setFixedSize(1, 20)
        separator2.setStyleSheet('background-color: #e0e0e0;')
        
        # OCR按钮
        btn_ocr = QPushButton("📝")
        btn_ocr.setToolTip("OCR识别")
        btn_ocr.setFixedSize(28, 28)
        btn_ocr.setStyleSheet('''
            QPushButton {
                background: none;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        ''')
        btn_ocr.clicked.connect(self.perform_ocr)
        
        # 取消按钮
        btn_cancel = QPushButton("✕")
        btn_cancel.setToolTip("取消")
        btn_cancel.setFixedSize(28, 28)
        btn_cancel.setStyleSheet('''
            QPushButton {
                background: none;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        ''')
        btn_cancel.clicked.connect(self.cancel_screenshot)
        
        layout.addWidget(btn_copy)
        layout.addWidget(btn_save)
        layout.addWidget(separator)
        layout.addWidget(btn_pen)
        layout.addWidget(btn_text)
        layout.addWidget(separator2)
        layout.addWidget(btn_ocr)
        layout.addWidget(btn_cancel)
        
        self.toolbar.adjustSize()
        
        pos = self.mapToGlobal(self.selected_rect.bottomRight() - QPoint(self.toolbar.width(), 0))
        if pos.y() + self.toolbar.height() > QApplication.desktop().height():
            pos = self.mapToGlobal(self.selected_rect.topRight() - QPoint(self.toolbar.width(), self.toolbar.height()))
        self.toolbar.move(pos)
        self.toolbar.show()

    def confirm_screenshot(self):
        cropped = self.screen_pixmap.copy(self.selected_rect)

        screenshot_dir = "screenshots"
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(screenshot_dir, filename)

        cropped.save(filepath)
        print(f"截图已保存为 {filepath}")

        if os.path.exists("temp_ss.png"):
            os.remove("temp_ss.png")

        self.close()

    def cancel_screenshot(self):
        self.close()

    def perform_ocr(self):
        """使用百度OCR API识别截图中的文字"""
        # 从配置文件读取密钥
        api_key = BAIDU_OCR_CONFIG.get("API_KEY", "")
        secret_key = BAIDU_OCR_CONFIG.get("SECRET_KEY", "")
        
        if not api_key or not secret_key:
            QMessageBox.critical(self, "错误", "请在config.py中配置百度OCR的API_KEY和SECRET_KEY")
            return
        
        # 获取选区截图
        cropped = self.screen_pixmap.copy(self.selected_rect)
        
        # 保存为临时文件
        temp_ocr_path = "temp_ocr.png"
        cropped.save(temp_ocr_path)
        
        # 读取图片并转为base64
        with open(temp_ocr_path, 'rb') as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')
        
        try:
            # 获取access_token
            token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
            token_response = requests.post(token_url, timeout=10)
            access_token = token_response.json().get("access_token")
            
            if not access_token:
                QMessageBox.critical(self, "错误", "获取access_token失败，请检查API Key和Secret Key")
                return
            
            # 调用OCR接口
            ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            params = {"image": img_data}
            
            response = requests.post(ocr_url, headers=headers, data=params, timeout=30)
            result = response.json()
            
            if 'words_result' in result and len(result['words_result']) > 0:
                # 提取识别的文字
                text_lines = [item['words'] for item in result['words_result']]
                recognized_text = '\n'.join(text_lines)
                
                # 显示结果
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("OCR识别结果")
                msg_box.setText(recognized_text)
                msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
                msg_box.exec_()
                
                # 复制到剪贴板
                clipboard = QApplication.clipboard()
                clipboard.setText(recognized_text)
                QMessageBox.information(self, "提示", "识别结果已复制到剪贴板")
            else:
                QMessageBox.information(self, "提示", "未识别到文字")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"OCR识别失败: {str(e)}")
        finally:
            # 清理临时文件
            if os.path.exists(temp_ocr_path):
                os.remove(temp_ocr_path)

    def closeEvent(self, event):
        if os.path.exists("temp_ss.png"):
            os.remove("temp_ss.png")
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = SnippingTool()
    sys.exit(app.exec_())