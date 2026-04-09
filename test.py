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

    # 情况1：正在拖拽中 -> 画一个简单的虚线矩形框
        if self.is_selecting:
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
            painter.drawRect(rect)
            return

    # 情况2：选区已确认 -> 画遮罩 + 实线白边 + 尺寸标签
        if self.selection_finished and not self.selected_rect.isNull():
            path = QPainterPath()
            path.addRect(QRectF(self.rect()))
            path.addRect(QRectF(self.selected_rect))
            painter.fillPath(path, QColor(0, 0, 0, 120))

            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.SolidLine))
            painter.drawRect(self.selected_rect)

            painter.setPen(QColor(255, 255, 255))
            size_text = f"{self.selected_rect.width()} x {self.selected_rect.height()}"
            painter.drawText(self.selected_rect.bottomRight() + QPoint(5, -5), size_text)

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
        self.toolbar.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self.toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        btn_ok = QPushButton("✓")
        btn_ok.clicked.connect(self.confirm_screenshot)
        btn_ok.setFixedSize(24, 24)
        btn_ok.setStyleSheet('QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 4px; font-size: 12px; font-weight: bold; }')
        
        btn_cancel = QPushButton("✗")
        btn_cancel.clicked.connect(self.cancel_screenshot)
        btn_cancel.setFixedSize(24, 24)
        btn_cancel.setStyleSheet('QPushButton { background-color: #f44336; color: white; border: none; border-radius: 4px; font-size: 12px; font-weight: bold; }')
        
        layout.addWidget(btn_cancel)
        layout.addWidget(btn_ok)
        
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
        self.selection_finished = False
        self.selected_rect = QRect()
        if self.toolbar:
            self.toolbar.hide()
        self.update()

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