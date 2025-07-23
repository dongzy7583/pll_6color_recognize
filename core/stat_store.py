# core/stat_store.py
import json, os
from collections import deque
from typing import Dict, Tuple
from core import config as cfg

Record = Tuple[float, bool]          # (time, is_correct)
Key = Tuple[str, int]                # (pll, state)

# ---------- 工具 ----------
def _curve_score(t: float) -> float:
    # if t <= 0.5:
    if t <= 1:
    # 1s=100, 2s=80, 3s=60, 8s=0
        return 100.0
    if t >= cfg.TIME_MAX:
        return 0.0
    a, b, c, d =4 / 21, -8 / 7, -376 / 21, 832 / 7
    # a, b, c, d = 0.855, -9.915, 34.060, 45.0
    score = d + c * t + b * t ** 2 + a * t ** 3
    print(f"t={t:.2f}s -> curve_score={score:.2f}")
    return max(0.0, min(100.0, score))


CONFIDENCE = {1: 0.80, 2: 0.85, 3: 0.90, 4: 0.95, 5: 1.00}

class StatStore:
    _file = os.path.join(os.path.dirname(__file__), '..', 'resources', 'stat.json')
    _max_hist = 5

    def __init__(self):
        self._hist: Dict[Key, deque] = {}
        self._load()

    def _load(self):
        if os.path.exists(self._file):
            with open(self._file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
                for k, v in raw.items():
                    pll, state = k.split('|')
                    self._hist[(pll, int(state))] = deque(v, maxlen=self._max_hist)

    def save(self):
        os.makedirs(os.path.dirname(self._file), exist_ok=True)
        to_save = {"|".join(map(str, k)): list(v) for k, v in self._hist.items()}
        with open(self._file, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, indent=2)

    def push(self, pll: str, state: int, time: float, ok: bool):
        key = (pll, state)
        if key not in self._hist:
            self._hist[key] = deque(maxlen=self._max_hist)
        self._hist[key].append((time, ok))
        self.save()

    def snapshot(self) -> Dict[Key, Dict]:
        """
        返回每个 case 的实时统计
        错误在掌握值里折算 8 秒；平均时间只统计正确记录
        无数据 case 掌握值默认 0
        """
        out = {}
        # 所有 84 个 (pll, state) 占位
        for pll in ["Aa", "Ab", "E", "F", "Ga", "Gb", "Gc", "Gd","H",
                    "Ja", "Jb", "Na", "Nb", "Ra", "Rb", "T", "Ua",
                    "Ub", "V", "Y", "Z"]:
            for state in range(1, 5):
                key = (pll, state)
                recs = list(self._hist.get(key, []))

                if not recs:
                    # 无数据 → 默认 0
                    out[key] = dict(avg_time=0.0,
                                    accuracy=0.0,
                                    mastery=0.0)
                    continue

                # 正确时间列表（平均时间只用这个）
                correct_times = [t for t, ok in recs if ok]
                avg_time = (sum(correct_times) / len(correct_times)
                            if correct_times else 0.0)

                # 掌握值：全部记录折算时间
                times_for_score = [t if ok else cfg.TIME_MAX for t, ok in recs]

                score_t = sum(times_for_score) / len(times_for_score)
                acc = sum(r[1] for r in recs) / len(recs)

                # 曲线分数 + 置信系数
                base = _curve_score(score_t)
                # print(score_t)
                # print(base)
                conf = CONFIDENCE.get(len(recs), 1.00)
                mastery = base * conf
                mastery = max(0.0, min(100.0, mastery))
                # print(f"{pll}-{state}: mastery = {base:.2f} * {conf:.2f} = {mastery:.2f}")

                out[key] = dict(avg_time=round(avg_time, 2),
                                accuracy=round(acc, 2),
                                mastery=round(mastery, 2))
        return out