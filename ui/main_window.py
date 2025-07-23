# ui/main_window.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QStackedWidget, QLabel
from PyQt5.QtGui import QFont
from ui.pll_trainer import PLLTrainer
from ui.custom_trainer import CustomTrainer
from ui.mastery_view import MasteryView
from ui.setting import SettingsPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('六格观察法')
        self.setFixedSize(800, 500)
        # 存储训练器实例
        self.pll_trainer = None
        self.custom_trainer = None
        self.menu_widget = None  # 存储主菜单实例
        # 标题
        title = QLabel('六格观察法')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24))
        title.setStyleSheet('font-weight:bold;')
        # 按钮
        btn_std = QPushButton('标准训练')
        btn_std.setFixedSize(180, 70)
        btn_std.setFont(QFont("Arial", 18))
        btn_std.setStyleSheet('border-radius:10px;')
        btn_custom = QPushButton('定制训练')
        btn_custom.setFixedSize(180, 70)
        btn_custom.setFont(QFont("Arial", 18))
        btn_custom.setStyleSheet('border-radius:10px;')
        btn_stats = QPushButton('统计')
        btn_stats.setFixedSize(180, 70)
        btn_stats.setFont(QFont("Arial", 18))
        btn_stats.setStyleSheet('border-radius:10px;')
        btn_set = QPushButton('设置')
        btn_set.setFixedSize(180, 70)
        btn_set.setFont(QFont("Arial", 18))
        btn_set.setStyleSheet('border-radius:10px;')
        # 绑定槽函数
        btn_stats.clicked.connect(self.show_stats)
        btn_std.clicked.connect(self.show_pll_trainer)
        btn_custom.clicked.connect(self.show_custom_trainer)
        btn_set.clicked.connect(self.show_settings)
        # 主布局
        vbox = QVBoxLayout()
        vbox.addWidget(title)
        vbox.addStretch()
        vbox.addWidget(btn_std, alignment=Qt.AlignCenter)
        vbox.addWidget(btn_custom, alignment=Qt.AlignCenter)
        vbox.addWidget(btn_stats, alignment=Qt.AlignCenter)
        vbox.addWidget(btn_set, alignment=Qt.AlignCenter)
        vbox.addStretch()
        menu = QWidget()
        menu.setLayout(vbox)
        self.menu_widget = menu  # 保存主菜单引用
        # 堆栈
        self.stack = QStackedWidget()
        self.stack.addWidget(menu)
        self.setCentralWidget(self.stack)
    
    def show_menu(self):
        """返回主菜单"""
        if self.stack.indexOf(self.menu_widget) == -1:
            self.stack.addWidget(self.menu_widget)
        self.stack.setCurrentWidget(self.menu_widget)
        self.menu_widget.setFocus()

    def show_pll_trainer(self):
        # 每次都创建新实例，确保读取最新 cfg
        if self.pll_trainer is not None:
            # 如果旧实例存在，先从堆栈里移除并销毁
            self.stack.removeWidget(self.pll_trainer)
            self.pll_trainer.deleteLater()
        self.pll_trainer = PLLTrainer(return_to_menu=self.show_menu)
        self.stack.addWidget(self.pll_trainer)    
        self.stack.setCurrentWidget(self.pll_trainer)
        self.pll_trainer.setFocus()
    
    def show_custom_trainer(self):
        # 每次都创建新实例，确保读取最新 cfg
        if self.custom_trainer is not None:
            # 如果旧实例存在，先从堆栈里移除并销毁
            self.stack.removeWidget(self.custom_trainer)
            self.custom_trainer.deleteLater()
        self.custom_trainer = CustomTrainer(return_to_menu=self.show_menu)
        self.stack.addWidget(self.custom_trainer)
        self.stack.setCurrentWidget(self.custom_trainer)
        self.custom_trainer.setFocus()

    def show_stats(self):
        if not hasattr(self, 'mastery_view') or self.mastery_view is None:
            self.mastery_view = MasteryView(return_to_menu=self.show_menu)
            self.stack.addWidget(self.mastery_view)
        self.stack.setCurrentWidget(self.mastery_view)
        self.mastery_view.setFocus()
    
    def show_settings(self):
        if not hasattr(self, 'settings_view') or self.settings_view is None:
            self.settings_view = SettingsPage(return_to_menu=self.show_menu)
            self.stack.addWidget(self.settings_view)
        self.stack.setCurrentWidget(self.settings_view)
        self.settings_view.setFocus()