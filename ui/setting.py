# ui/setting.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import core.config as cfg


class SettingsPage(QWidget):
    def __init__(self, return_to_menu):
        super().__init__()
        self.return_to_menu = return_to_menu
        self.sliders = []  # 存储滑块及标签的引用
        self.init_ui()

    def init_ui(self):
        # 标题
        title = QLabel('设置')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24))
        title.setStyleSheet('font-weight:bold;')

        # 滑块组定义
        slider_defs = [
            {
                "label": "遗忘率",
                "value": cfg.FORGET_RATE,
                "min": 0.9,
                "max": 1.0,
                "step": 0.01
            },
            {
                "label": "颜色同步因子",
                "value": cfg.COLOR_SYNC_FACTOR,
                "min": 0.9,
                "max": 1.0,
                "step": 0.01
            },
            {
                "label": "定制训练每轮张数",
                "value": cfg.CUSTOM_TRAIN_COUNT,
                "min": 10,
                "max": 100,
                "step": 10
            },
            {
                "label": "下一张图延迟（毫秒）",
                "value": cfg.NEXT_DELAY_MS,
                "min": 0,
                "max": 1000,
                "step": 100
            },
            {
                "label": "全局收敛速度",
                "value": cfg.LAMBDA,
                "min": 0.1,
                "max": 1.0,
                "step": 0.1
            }
        ]

        # 创建滑块界面
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignCenter)  # 整体居中
        vbox.setContentsMargins(40, 40, 40, 40)  # 设置外边距
        vbox.setSpacing(20)  # 设置控件间距
        vbox.addWidget(title)

        for item in slider_defs:
            slider_container = QWidget()
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)  # 滑块容器无内边距
            hbox.setSpacing(10)  # 滑块内部控件间距

            label = QLabel(item["label"])
            label.setFont(QFont("Arial", 14))
            hbox.addWidget(label)

            # 设置滑块固定长度
            slider = QSlider(Qt.Horizontal)
            slider.setFixedWidth(300)  # 滑块固定长度
            slider.setMinimum(int(item["min"] / item["step"]))
            slider.setMaximum(int(item["max"] / item["step"]))
            slider.setValue(int(item["value"] / item["step"]))
            slider.setTickInterval(1)

            value_label = QLabel(f"{item['value']:.2f}" if isinstance(item['value'], float) else f"{item['value']}")
            value_label.setFont(QFont("Arial", 14))
            value_label.setFixedWidth(60)  # 值标签固定宽度

            slider.valueChanged.connect(
                lambda value, lbl=value_label, s=slider, i=item: 
                self.update_slider_value(value, lbl, s, i)
            )

            hbox.addWidget(slider)
            hbox.addWidget(value_label)
            slider_container.setLayout(hbox)
            vbox.addWidget(slider_container)

            # 存储引用，避免提前回收
            self.sliders.append({
                "slider": slider,
                "value_label": value_label,
                "config_key": item["label"],
                "step": item["step"]
            })

        # 按钮区域
        button_container = QWidget()
        hbox_buttons = QHBoxLayout()
        hbox_buttons.setContentsMargins(0, 0, 0, 0)
        hbox_buttons.setSpacing(20)

        save_button = QPushButton("保存设置")
        save_button.setFixedSize(120, 40)
        save_button.setFont(QFont("Arial", 14))
        save_button.clicked.connect(self.save_settings)

        back_button = QPushButton("返回")
        back_button.setFixedSize(120, 40)
        back_button.setFont(QFont("Arial", 14))
        back_button.clicked.connect(self.return_to_menu)

        hbox_buttons.addWidget(save_button)
        hbox_buttons.addWidget(back_button)
        button_container.setLayout(hbox_buttons)
        vbox.addWidget(button_container)

        self.setLayout(vbox)

    def update_slider_value(self, value, label, slider, item):
        actual_value = value * item["step"]
        if isinstance(item["value"], float):
            label.setText(f"{actual_value:.2f}")
        else:
            label.setText(f"{actual_value:.0f}")

    def save_settings(self):
        for slider_info in self.sliders:
            value = slider_info["slider"].value() * slider_info["step"]
            if slider_info["config_key"] == "遗忘率":
                cfg.FORGET_RATE = value
            elif slider_info["config_key"] == "颜色同步因子":
                cfg.COLOR_SYNC_FACTOR = value
            elif slider_info["config_key"] == "定制训练每轮张数":
                cfg.CUSTOM_TRAIN_COUNT = int(value)
            elif slider_info["config_key"] == "下一张图延迟（毫秒）":
                cfg.NEXT_DELAY_MS = int(value)
            elif slider_info["config_key"] == "全局收敛速度":
                cfg.LAMBDA = value

        from PyQt5.QtWidgets import QMessageBox
        cfg.save()
        QMessageBox.information(self, "保存成功", "设置已保存!", QMessageBox.Ok)