# core/weight_manager.py
import json, os, math
from typing import Dict, Tuple, List, Set
import core.config as cfg


CFG_FILE = os.path.join(os.path.dirname(__file__), '..', 'resources', 'weights.json')

class WeightManager:
    """管理 CaseBaseWeight、ColorWeight、全局λ"""

    def __init__(self):
        self.case: Dict[Tuple[str, int, int], float] = {}
        self.load()

    # ---------- 读 ----------
    def load(self):
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.case = {tuple(json.loads(k)): v for k, v in data.get('case', {}).items()}
        else:
            self.case = {}

    def save(self):
        os.makedirs(os.path.dirname(CFG_FILE), exist_ok=True)
        with open(CFG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'case': {json.dumps(k): v for k, v in self.case.items()}
            }, f, indent=2)

    # ---------- 工具 ----------
    def time_factor(self, t: float) -> float:
        return max(min(t , 8) / 2 , 0.25 )       # 根据答题时间计算权重调整因子，时间大于8秒按8秒计算。

    # ---------- 写 + 立即保存 ----------
    def update(self, pll: str, state: int, color: int, is_correct: bool, time_taken: float):
        # 主颜色权重更新
        key = (pll, state, color)
        w = max(self.case.get(key, 1.0), cfg.CASE_MIN)

        if is_correct:
            factor = self.time_factor(time_taken)
        else:
            factor = self.time_factor(8)

        new_w = w + cfg.LAMBDA * (factor - 1) * w
        self.case[key] = max(min(new_w, cfg.CASE_MAX), cfg.CASE_MIN)

        # 同步更新其他颜色
        for c in range(1, 5):
            if c == color:
                continue
            sync_key = (pll, state, c)
            sync_w = max(self.case.get(sync_key, 1.0), cfg.CASE_MIN)
            sync_new = sync_w + cfg.COLOR_SYNC_FACTOR * (factor - 1) * sync_w
            self.case[sync_key] = max(min(sync_new, cfg.CASE_MAX), cfg.CASE_MIN)

        self.save()

    def _get_colors_for_state(self, state_key: Tuple[str, int, int]) -> Set[Tuple[str, int, int]]:
        return {k for k in self.color.keys() if k[:3] == state_key}  # 获取同一状态下的所有颜色键

    def forget(self):
        for k in list(self.case.keys()):
            self.case[k] = cfg.FORGET_RATE * self.case[k] + 1 - cfg.FORGET_RATE   
        self.save()  # 保存权重数据

    def build_weighted_list(self, all_files: List[Tuple[str, str, int, int]]):
        weighted = []
        for path, pll, color, state in all_files:
            key = (pll, state, color)
            w = max(self.case.get(key, 1.0), cfg.CASE_MIN)
            weighted.append((path, pll, color, state, w))
        return weighted
