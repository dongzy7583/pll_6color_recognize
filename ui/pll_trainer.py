# ui/pll_trainer.py
import os
import time

from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from core.svg_scanner import build_standard_test_list
from core.stat_store import StatStore
from core import config as cfg

# ---------- 工具 ----------
def svg_to_pixmap(path: str, size: int = 32) -> QPixmap:
    renderer = QSvgRenderer(path)
    pm = QPixmap(QSize(size, size))
    pm.fill(Qt.transparent)
    with QPainter(pm) as p:
        renderer.render(p)
    return pm

# ---------- 左侧面板 ----------
class LeftPane(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 450)
        self.time_label = QLabel('0.00 s', self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont('Arial', 20))
        self.time_label.setGeometry(0, 0, 400, 30)
        self.svg_widget = QSvgWidget(self)
        self.svg_widget.setFixedSize(400, 400)
        self.svg_widget.move(0, 30)
        self.tip_label = QLabel(self)
        self.tip_label.setAlignment(Qt.AlignCenter)
        self.tip_label.setStyleSheet("color:red; font-size:16px;")
        self.tip_label.setGeometry(0, 30, 400, 20)
        self.tip_label.setVisible(False)

    def set_time(self, t: str):
        self.time_label.setText(t)

    def show_tip(self, text: str):
        self.tip_label.setText(text)
        self.tip_label.setVisible(bool(text))

    def load_svg(self, path: str):
        if path:
            self.svg_widget.load(path)
        else:
            self.svg_widget.renderer().load(b'')   # 直接清空内部 renderer

# ---------- 标准训练器 ----------
class PLLTrainer(QWidget):
    def __init__(self, parent=None, return_to_menu=None):
        super().__init__(parent)
        self.return_to_menu = return_to_menu
        self.corr_count = 0
        self.store = StatStore()

        self.all_files = build_standard_test_list()
        self.TOTAL = len(self.all_files)

        self.current_info = None
        self.wait_correct = False
        self.recorded = False
        self.start_time = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)

        # 左侧
        self.left_pane = LeftPane()
        self.counter_label = QLabel(f'0 / {self.TOTAL}')
        self.counter_label.setAlignment(Qt.AlignCenter)
        self.counter_label.setFont(QFont('Arial', 16))

        # 顶部按钮
        self.start_btn = QPushButton('开始')
        self.start_btn.setFixedSize(80, 30)
        self.start_btn.clicked.connect(self.start_test)
        restart_btn = QPushButton('重新开始')
        restart_btn.setFixedSize(80, 30)
        restart_btn.clicked.connect(self.restart_test)
        back_btn = QPushButton('返回主菜单')
        back_btn.setFixedSize(120, 30)
        back_btn.clicked.connect(self.go_back)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(restart_btn)
        top_layout.addWidget(back_btn)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_widget = QWidget()
        top_widget.setLayout(top_layout)
        left_box = QWidget()
        left_box.setFixedSize(400, 510)
        left_v = QVBoxLayout(left_box)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.addWidget(top_widget, alignment=Qt.AlignCenter)
        left_v.addWidget(self.counter_label)
        left_v.addWidget(self.left_pane)

        # 右侧表格
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(['图标', 'PLL', '用时/错误'])
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 60)
        header = self.table.horizontalHeader()
        for i in range(3):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
        self.table.setIconSize(QSize(96, 96))
        self.table.verticalHeader().setDefaultSectionSize(104)
        self.table.setFixedWidth(280)

        layout = QHBoxLayout(self)
        layout.addWidget(left_box)
        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(720, 510)

        self.records = []
        self.correct_count = 0
        self.idx = 0
        self.test_started = False
        self.restart_test()

    # ---------- 公共方法 ----------
    def go_back(self):
        self.stop_timer()
        self.restart_test()
        if self.return_to_menu:
            self.return_to_menu()
        else:
            print("返回函数未设置")

    def start_test(self):
        """首次点击开始按钮后才开始计时、加载图片"""
        if self.test_started:
            return
        self.test_started = True
        self.start_btn.setEnabled(False)   # 防止重复点击
        self.next_image()                  # 真正开始

    def restart_test(self):
        """重置到未开始状态"""
        self.records.clear()
        self.correct_count = 0
        self.idx = 0
        self.counter_label.setText('0 / {}'.format(self.TOTAL))
        self.table.setRowCount(0)

        # 新增：回到初始未开始状态
        self.test_started = False
        self.start_btn.setEnabled(True)
        self.left_pane.load_svg('')        # 清空图片
        self.left_pane.set_time('0.00 s')
        self.left_pane.show_tip('')
        self.stop_timer()
        self.all_files = build_standard_test_list()

    def next_image(self):
        if not self.test_started:          # 防止误触发
            return
        if self.idx >= self.TOTAL:
            self.show_end_dialog()
            return
        self.wait_correct = False
        self.recorded = False
        path, pll, color, state = self.all_files[self.idx]  # 按顺序抽取
        self.current_info = (path, pll, color, state)
        self.left_pane.load_svg(path)
        self.left_pane.set_time('0.00 s')
        self.reset_timer()
        self.left_pane.show_tip('')
        self.setFocus()
        self.idx += 1
        self.counter_label.setText(f'{self.idx} / {self.TOTAL}')

    def reset_timer(self):
        self.start_time = time.time()
        self.timer.start(50)

    def stop_timer(self):
        self.timer.stop()

    def elapsed(self):
        return time.time() - self.start_time

    def update_time(self):
        self.left_pane.set_time(f'{self.elapsed():.2f} s')

    def show_tip(self, text: str):
        self.left_pane.show_tip(text)

    def add_record(self, path, pll, result):
        row = self.table.rowCount()
        self.table.insertRow(row)

        icon_item = QTableWidgetItem()
        icon_item.setIcon(QIcon(svg_to_pixmap(path, 96)))
        icon_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, icon_item)

        pll_item = QTableWidgetItem(pll)
        pll_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, pll_item)

        result_item = QTableWidgetItem(result)
        result_item.setTextAlignment(Qt.AlignCenter)
        if result == '错误':
            result_item.setForeground(Qt.red)
        else:
            try:
                t = float(result.split()[0])
                color = Qt.green if t < 2.0 else QColor(255, 140, 0)
                result_item.setForeground(color)
            except ValueError:
                pass
        self.table.setItem(row, 2, result_item)

        self.records.append((path, pll, result))
        if result != '错误':
            self.correct_count += 1

    def show_end_dialog(self):
        total_time = sum(
            float(r[2].split()[0]) for r in self.records if r[2] != '错误'
        )
        avg = total_time / max(self.correct_count, 1)
        correct_str = f'{self.correct_count} / {self.TOTAL}'

        msg = QMessageBox(self)
        msg.setWindowTitle('训练结束')
        msg.setText(f'平均时间：{avg:.2f} 秒\n正确率：{correct_str}')
        msg.addButton('确定', QMessageBox.AcceptRole)
        msg.exec_()

        # 排序：错误优先，时间降序
        def sort_key(rec):
            res = rec[2]
            if res == '错误':
                return (0, 9999)
            return (1, -float(res.split()[0]))
        self.records.sort(key=sort_key)

        self.table.setRowCount(0)
        for path, pll, res in self.records:
            self._fill_row(path, pll, res)

    def _fill_row(self, path, pll, result):
        row = self.table.rowCount()
        self.table.insertRow(row)

        icon_item = QTableWidgetItem()
        icon_item.setIcon(QIcon(svg_to_pixmap(path, 96)))
        icon_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, icon_item)

        pll_item = QTableWidgetItem(pll)
        pll_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, pll_item)

        result_item = QTableWidgetItem(result)
        result_item.setTextAlignment(Qt.AlignCenter)
        if result == '错误':
            result_item.setForeground(Qt.red)
        else:
            try:
                t = float(result.split()[0])
                color = Qt.green if t < 2.0 else QColor(255, 140, 0)
                result_item.setForeground(color)
            except ValueError:
                pass
        self.table.setItem(row, 2, result_item)

    def keyPressEvent(self, event):
        ch = event.text().upper()
        if not ch.isalpha():
            return
        correct = self.current_info[1][0].upper()

        if self.wait_correct:
            if ch == correct:
                QTimer.singleShot(cfg.NEXT_DELAY_MS, self.next_image)
            return

        if ch == correct:
            self.stop_timer()
            t = self.elapsed()
            self.add_record(self.current_info[0], self.current_info[1], f'{t:.2f} s')
            pll = os.path.basename(self.current_info[0]).split('_')[0]
            self.store.push(pll, self.current_info[3], t, True)
            QTimer.singleShot(cfg.NEXT_DELAY_MS, self.next_image)
        else:
            self.stop_timer()
            self.add_record(self.current_info[0], self.current_info[1], '错误')
            correct_name = self.current_info[1]
            self.left_pane.show_tip(f'正确答案是 {correct_name}，输入 {correct} 继续')
            self.wait_correct = True
            pll = os.path.basename(self.current_info[0]).split('_')[0]
            self.store.push(pll, self.current_info[3], self.elapsed(), False)