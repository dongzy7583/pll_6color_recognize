# ui/mastery_view.py
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QHBoxLayout, QMessageBox)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QColor
from core.stat_store import StatStore

class MasteryView(QWidget):
    def __init__(self, return_to_menu):
        super().__init__()
        self.return_to_menu = return_to_menu
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        # 表格
        self.table = QTableWidget(84, 5)
        self.table.setHorizontalHeaderLabels(
            ["", "PLL", "平均时间", "正确率", "掌握值"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(110)  # 行高
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 缩略图
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # PLL
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 平均时间
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 正确率
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 掌握值
        self.table.setColumnWidth(0, 110)  # 缩略图列宽
        # 填充 84 行空占位
        root = os.path.join(os.path.dirname(__file__), "..", "resources", "SVG")
        idx = 0
        for pll in ["Aa", "Ab", "E", "F", "Ga", "Gb", "Gc", "Gd",
                    "Ja", "Jb", "Na", "Nb", "Ra", "Rb", "T", "Ua",
                    "Ub", "V", "Y", "Z"]:
            for state in range(1, 5):
                # 缩略图（96×96）
                svg_path = os.path.join(
                    root, f"{pll}_pern", f"{pll}_pern_color1_state{state}.svg")
                svg_w = QSvgWidget(svg_path)
                svg_w.setFixedSize(96, 96)
                self.table.setCellWidget(idx, 0, svg_w)
                self.table.setItem(idx, 1, QTableWidgetItem(pll))
                self.table.setItem(idx, 2, QTableWidgetItem("–"))
                self.table.setItem(idx, 3, QTableWidgetItem("–"))
                self.table.setItem(idx, 4, QTableWidgetItem("–"))
                idx += 1
        layout.addWidget(self.table)
        # 按钮行
        btn_row = QWidget()
        h = QHBoxLayout(btn_row)
        h.setContentsMargins(0, 0, 0, 0)
        self.btn_sort = QPushButton("按掌握值排序")
        self.btn_sort.setCheckable(True)
        self.btn_sort.toggled.connect(self.toggle_sort)
        self.btn_clear = QPushButton("清空数据")
        self.btn_clear.clicked.connect(self.clear_data)
        h.addWidget(self.btn_sort)
        h.addWidget(self.btn_clear)
        layout.addWidget(btn_row, alignment=Qt.AlignCenter)
        # 返回按钮
        back = QPushButton("返回主菜单")
        back.setFixedSize(150, 40)
        back.clicked.connect(self.return_to_menu)
        layout.addWidget(back, alignment=Qt.AlignCenter)

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh_table()

    def refresh_table(self):
        # 拉取数据
        try:
            data = StatStore().snapshot()
        except Exception:
            data = {}
        # 生成 84 条 (pll, state) 原始顺序
        base = [(pll, st) for pll in
                ["Aa", "Ab", "E", "F", "Ga", "Gb", "Gc", "Gd", "H",
                 "Ja", "Jb", "Na", "Nb", "Ra", "Rb", "T", "Ua",
                 "Ub", "V", "Y", "Z"]
                for st in range(1, 5)]
        # 排序开关
        if getattr(self, '_sort_by_mastery', False):
            base.sort(key=lambda k: data.get(k, {}).get('mastery', 0))
        # 默认顺序就是 (pll, state) 原序，无需再排
        # 清空并一次性重建表格
        # print("Data loaded from stat.json:", data)
        self.table.setRowCount(0)
        root = os.path.join(os.path.dirname(__file__), "..", "resources", "SVG")
        for pll, state in base:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # 缩略图
            svg_path = os.path.join(root, f"{pll}_pern", f"{pll}_pern_color1_state{state}.svg")
            svg_w = QSvgWidget(svg_path)
            svg_w.setFixedSize(96, 96)
            self.table.setCellWidget(row, 0, svg_w)
            self.table.setItem(row, 1, QTableWidgetItem(f"{pll}-{state}"))
            info = data.get((pll, state), {})
            # print(f"key={pll}|{state}, info={info}")
            self.table.setItem(row, 2, QTableWidgetItem(str(info.get("avg_time", "-"))))
            self.table.setItem(row, 3, QTableWidgetItem(
                f"{info.get('accuracy', 0) * 100:.0f}%" if info.get("accuracy") else "–"))
            self.table.setItem(row, 4, QTableWidgetItem(
                f"{info.get('mastery', '–'):.1f}" if isinstance(info.get("mastery"), (int, float)) else "–"))
            if info.get("mastery") == 100:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:                           # 单元格有 QTableWidgetItem 再设置
                        item.setBackground(QColor("#c8e6c9"))
            # print("StatStore._file =", StatStore._file)
            # print("exists?", os.path.exists(StatStore._file))
            # print("Data loaded from stat.json:", data)

    def toggle_sort(self, checked):
        self._sort_by_mastery = checked
        self.refresh_table()

    def clear_data(self):
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有统计数据吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 直接删除持久化文件即可
            try:
                os.remove(StatStore._file)
            except FileNotFoundError:
                pass
            self.refresh_table()   # 刷新空表
