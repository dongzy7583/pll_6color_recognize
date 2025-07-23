# core/svg_scanner.py
"""
扫描 SVG 目录，返回 (path, pll, color, state) 列表。
"""

import os
import random
from glob import iglob
from typing import List, Tuple

# 允许外部覆盖，也可直接放这里
try:
    from core.config import EXCLUDE_RULES
except ImportError:
    EXCLUDE_RULES: List[Tuple[str, str, int]] = []

# 相对于本文件向上两级，再进入 resources/SVG
SVG_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'resources', 'SVG'
)


def _match_exclude(pll: str, color: int, state: int) -> bool:
    """
    根据 EXCLUDE_RULES 判断是否跳过该文件。
    规则格式: (pll_name, 'color'|'state', value)
    """
    for rule_pll, rule_key, rule_val in EXCLUDE_RULES:
        if rule_pll.lower() != pll.lower():
            continue
        if rule_key == 'color' and color == rule_val:
            return True
        if rule_key == 'state' and state == rule_val:
            return True
    return False


def scan_all_svg() -> List[Tuple[str, str, int, int]]:
    """
    遍历 SVG_DIR，返回：
        (完整文件路径, pll简称, color编号, state编号)
    已自动剔除被排除的文件。
    """
    all_files: List[Tuple[str, str, int, int]] = []

    if not os.path.isdir(SVG_DIR):
        return all_files

    for pll_folder in os.listdir(SVG_DIR):
        folder_path = os.path.join(SVG_DIR, pll_folder)
        if not os.path.isdir(folder_path):
            continue

        pll_name = pll_folder.split('_')[0]

        for path in iglob(os.path.join(folder_path, '*.svg')):
            basename = os.path.basename(path)
            name_part, _ = os.path.splitext(basename)
            parts = name_part.split('_')
            if len(parts) != 4:
                continue

            _, _, color_part, state_part = parts
            try:
                color = int(color_part.replace('color', ''))
                state = int(state_part.replace('state', ''))
            except ValueError:
                continue

            if not _match_exclude(pll_name, color, state):
                all_files.append((path, pll_name, color, state))

    return all_files

def build_standard_test_list() -> List[Tuple[str, str, int, int]]:
    all_files = scan_all_svg()  # 拿到所有文件
    from collections import defaultdict

    groups = defaultdict(list)
    for path, pll, color, state in all_files:
        key = (pll, state)  # 按 (pll, state) 分组
        groups[key].append((path, pll, color, state))  # 同组的路径都存起来

    standard = []
    for key in sorted(groups):  # 遍历所有分组
        chosen = random.choice(groups[key])  # 每组随机选 1 个颜色
        standard.append(chosen)

    random.shuffle(standard)  # 打乱顺序
    # print(len(standard))
    return standard