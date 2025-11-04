import sys
import threading
import json
import markdown
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QScrollArea, QLabel,
    QFrame, QSplitter, QListWidget, QListWidgetItem, QMenuBar,
    QMenu, QStatusBar, QMessageBox, QToolBar, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QAction, QPixmap, QPainter, QColor, QTextCharFormat, QSyntaxHighlighter
from PyQt6.QtWebEngineWidgets import QWebEngineView
from openai import OpenAI

class MessageBubble(QLabel):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setText(text)
        self.setWordWrap(True)
        self.setContentsMargins(15, 10, 15, 10)
        self.setMinimumWidth(200)
        self.setMaximumWidth(600)
        
        # استایل‌های مختلف برای کاربر و دستیار
        if is_user:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #007bff;
                    color: white;
                    border-radius: 18px;
                    border-bottom-right-radius: 5px;
                    font-size: 14px;
                    padding: 12px 16px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #f1f3f4;
                    color: #333333;
                    border-radius: 18px;
                    border-bottom-left-radius: 5px;
                    font-size: 14px;
                    padding: 12px 16px;
                }
            """)

class ChatWorker(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client, model, conversation_history, user_message):
        super().__init__()
        self.client = client
        self.model = model
        self.conversation_history = conversation_history
        self.user_message = user_message

    def run(self):
        try:
            # افزودن پیام کاربر به تاریخچه
            self.conversation_history.append({"role": "user", "content": self.user_message})
            
            # ارسال درخواست به API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history
            )
            
            response = completion.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": response})
            self.response_received.emit(response)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class ModernChatGPTUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = OpenAI(
            base_url="https://ai.liara.ir/api/6908faa2074e6ee121bb4f97/v1",
            api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTA4ZmM3MGE1NTg3OTIxZmZiYzQxNzMiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYyMTk2NTkyfQ.CoJbzBYg_wh1zrxtL7jDdIacU9yt3aqxFU6teDrZZCw",
        )
        self.model = "openai/gpt-4o-mini"
        self.conversation_history = []
        self.chat_sessions = []
        self.current_session = []
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("ChatGPT Pro - PyQt6")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # تنظیم تم تاریک
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #444444;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #444444;
            }
            QListWidget::item:selected {
                background-color: #007bff;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 20px;
                padding: 12px 20px;
                font-size: 14px;
                selection-background-color: #007bff;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QFrame {
                background-color: #1e1e1e;
            }
        """)
        
        self.setup_menu_bar()
        self.setup_tool_bar()
        self.setup_central_widget()
        self.setup_status_bar()
        
    def setup_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-bottom: 1px solid #444444;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #007bff;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444444;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #007bff;
            }
        """)
        
        # منوی فایل
        file_menu = menubar.addMenu('فایل')
        
        new_chat_action = QAction('چت جدید', self)
        new_chat_action.setShortcut('Ctrl+N')
        new_chat_action.triggered.connect(self.new_chat)
        file_menu.addAction(new_chat_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('خروج', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # منوی ویرایش
        edit_menu = menubar.addMenu('ویرایش')
        
        clear_action = QAction('پاک کردن چت', self)
        clear_action.setShortcut('Ctrl+L')
        clear_action.triggered.connect(self.clear_chat)
        edit_menu.addAction(clear_action)
        
    def setup_tool_bar(self):
        toolbar = QToolBar("ابزارهای اصلی")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        new_chat_btn = QAction("💬 چت جدید", self)
        new_chat_btn.triggered.connect(self.new_chat)
        toolbar.addAction(new_chat_btn)
        
        toolbar.addSeparator()
        
        clear_btn = QAction("🗑️ پاک کردن", self)
        clear_btn.triggered.connect(self.clear_chat)
        toolbar.addAction(clear_btn)
        
    def setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # اسپلیتر برای نوار کناری و ناحیه چت
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # نوار کناری
        self.setup_sidebar(splitter)
        
        # ناحیه اصلی چت
        self.setup_chat_area(splitter)
        
        splitter.setSizes([300, 1100])
        main_layout.addWidget(splitter)
        
    def setup_sidebar(self, parent):
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        
        # دکمه چت جدید
        self.new_chat_btn = QPushButton("+ چت جدید")
        self.new_chat_btn.clicked.connect(self.new_chat)
        sidebar_layout.addWidget(self.new_chat_btn)
        
        # لیست چت‌های قبلی
        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.load_chat_session)
        sidebar_layout.addWidget(self.chat_list)
        
        # اطلاعات مدل
        model_info = QLabel(f"مدل: {self.model}")
        model_info.setStyleSheet("color: #888888; font-size: 12px; padding: 10px;")
        sidebar_layout.addWidget(model_info)
        
        parent.addWidget(sidebar_widget)
        
    def setup_chat_area(self, parent):
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        # ناحیه نمایش پیام‌ها
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()
        
        self.scroll_area.setWidget(self.chat_container)
        chat_layout.addWidget(self.scroll_area)
        
        # ناحیه ورودی
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("پیام خود را اینجا تایپ کنید... (Enter برای ارسال)")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_btn = QPushButton("ارسال")
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        chat_layout.addWidget(input_widget)
        
        parent.addWidget(chat_widget)
        
    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("آماده")
        
    def add_message(self, text, is_user=True):
        message_bubble = MessageBubble(text, is_user)
        
        # تنظیم تراز بر اساس نوع کاربر
        if is_user:
            alignment = Qt.AlignmentFlag.AlignRight
            margin = "0px 0px 5px 50px;"
        else:
            alignment = Qt.AlignmentFlag.AlignLeft
            margin = "0px 50px 5px 0px;"
        
        message_bubble.setStyleSheet(message_bubble.styleSheet() + f"margin: {margin}")
        
        # ایجاد ویجت برای ترازبندی
        message_widget = QWidget()
        message_widget_layout = QHBoxLayout(message_widget)
        message_widget_layout.addWidget(message_bubble)
        message_widget_layout.setAlignment(alignment)
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, message_widget)
        
        # اسکرول به پایین
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def send_message(self):
        message = self.message_input.text().strip()
        if not message or hasattr(self, 'worker') and self.worker.isRunning():
            return
            
        self.message_input.clear()
        self.add_message(message, True)
        
        # غیرفعال کردن ورودی در حین پردازش
        self.message_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.status_bar.showMessage("در حال تولید پاسخ...")
        
        # اجرای درخواست در thread جداگانه
        self.worker = ChatWorker(self.client, self.model, self.conversation_history, message)
        self.worker.response_received.connect(self.handle_response)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
        
    def handle_response(self, response):
        self.add_message(response, False)
        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_bar.showMessage("آماده")
        
        # ذخیره session
        self.current_session.append(("user", response))
        if not self.chat_list.findItems("چت جدید", Qt.MatchFlag.MatchContains):
            self.chat_list.addItem(f"چت {len(self.chat_sessions) + 1}")
        
    def handle_error(self, error_message):
        self.add_message(f"خطا: {error_message}", False)
        self.message_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.status_bar.showMessage("خطا در ارتباط")
        
    def new_chat(self):
        if self.conversation_history:
            self.chat_sessions.append(self.conversation_history.copy())
            self.conversation_history.clear()
            
        # پاک کردن نمایش چت
        for i in reversed(range(self.chat_layout.count() - 1)):
            widget = self.chat_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        self.add_message("سلام! من ChatGPT هستم. چگونه می‌توانم کمک کنم؟", False)
        self.status_bar.showMessage("چت جدید ایجاد شد")
        
    def clear_chat(self):
        reply = QMessageBox.question(self, 'تأیید', 'آیا از پاک کردن تاریخچه چت مطمئن هستید؟',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.new_chat()
            
    def load_chat_session(self, item):
        # پیاده‌سازی بارگذاری چت‌های قبلی
        pass

def main():
    app = QApplication(sys.argv)
    
    # تنظیم فونت برای پشتیبانی از فارسی
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ModernChatGPTUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()