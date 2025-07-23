# core/config.py
"""
全局配置：排除规则、路径、常量等。
如需新增排除规则，直接在 EXCLUDE_RULES 列表里追加即可。
格式：(pll简称, 'color'|'state', 要排除的值)
"""

# 示例：排除 T-perm 的 color=1 及 state=3
EXCLUDE_RULES = [
    # ('T', 'color', 1),
    # ('T', 'state', 3),
    # ('Ua', 'color', 2),
]

# 全局可改参数
FORGET_RATE = 1.00# 遗忘率
COLOR_SYNC_FACTOR = 1.00# 颜色同步因子
CUSTOM_TRAIN_COUNT = 20# 每轮定制训练抽多少张
NEXT_DELAY_MS = 100# 下一张图的延迟（毫秒）
LAMBDA = 1.00# 全局收敛速率：短期突破1 长期跟踪防遗忘0.2
CASE_MAX = 10.00# 最大案例权重
CASE_MIN = 0.10# 最小案例权重
COLOR_MIN = 0.10# 最小颜色权重
TIME_MAX = 8.00# 最大时间
MAX_PERFECT = 0.50# 满分时间

# 时间分段影响因子，线性
TIME_K = {
    0.5: 0.6,
    1.5: 1.0,
    2.5: 1.4,
    4.0: 2.0,
    999: 2.5
}

# --------------------------------------------------
# 新增：把当前内存值写回文件（覆盖原文件）
import os
_CFG_FILE = os.path.abspath(__file__)

def save():
    """
    仅持久化简单标量（int/float/str/bool），
    列表/字典等多行字面量保持不变，避免格式被破坏。
    """
    import re
    simple_keys = {
        'FORGET_RATE', 'COLOR_SYNC_FACTOR', 'CUSTOM_TRAIN_COUNT',
        'NEXT_DELAY_MS', 'LAMBDA', 'CASE_MIN', 'COLOR_MIN',
        'TIME_MAX', 'MAX_PERFECT'
    }

    with open(_CFG_FILE, 'r', encoding='utf-8') as f:
        src = f.read()

    # 用正则逐行匹配：KEY = VALUE  # 注释
    def repl(m):
        key = m.group(1)
        if key not in simple_keys:
            return m.group(0)          # 不改动多行字面量
        val = globals()[key]
        if isinstance(val, float):
            val_str = f'{val:.2f}'
        else:
            val_str = str(val)
        return f'{key} = {val_str}{m.group(2)}'

    new_src = re.sub(r'^(FORGET_RATE|COLOR_SYNC_FACTOR|CUSTOM_TRAIN_COUNT|'
                     r'NEXT_DELAY_MS|LAMBDA|CASE_MIN|COLOR_MIN|'
                     r'TIME_MAX|MAX_PERFECT)\s*=\s*[^#\n]*(.*)$',
                     repl, src, flags=re.MULTILINE)

    tmp = _CFG_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(new_src)
    os.replace(tmp, _CFG_FILE)