import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QRect, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QPainterPath
import win32gui
import win32ui
import win32con
from PIL import Image

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