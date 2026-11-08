"""설계과제2 ngspice 출력 파서: print 스칼라, show m 표, pz 결과, wrdata AC 파일."""
import math
import re
from pathlib import Path

import numpy as np

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
_SCALAR = re.compile(rf"^\s*([\w().#:\-]+)\s*=\s*({_NUM})\s*$", re.M)
_PZ = re.compile(rf"^\s*(pole|zero)\((\d+)\)\s*=\s*({_NUM})\s*,\s*({_NUM})", re.M | re.I)


def parse_scalars(text: str) -> dict:
    """`name = value` 줄 → {소문자 이름: float}."""
    return {k.lower(): float(v) for k, v in _SCALAR.findall(text)}


def _num(tok: str) -> float:
    try:
        return float(tok)
    except ValueError:
        return math.nan                    # '?????????' 등 보고되지 않은 값


def parse_devices(text: str) -> dict:
    """`show m` 표(여러 블록 가능) → {'M1': {'id': ..., ...}}. 이름은 대문자."""
    out, names = {}, []
    for line in text.splitlines():
        tok = line.split()
        if not tok:
            continue
        if tok[0] == "device":
            names = [t.upper() for t in tok[1:]]
            for n in names:
                out.setdefault(n, {})
        elif names and len(tok) == len(names) + 1 and tok[0] != "model":
            for n, v in zip(names, tok[1:]):
                out[n][tok[0].lower()] = _num(v)
    return out


def parse_pz(text: str):
    """`pole(n) = re,im` / `zero(n) = re,im` → (poles, zeros), complex rad/s."""
    poles, zeros = [], []
    for kind, _, re_, im in _PZ.findall(text):
        (poles if kind.lower() == "pole" else zeros).append(complex(float(re_), float(im)))
    return poles, zeros


def load_ac(path):
    """wrdata 4열(f, dB, f, phase) → (f, dB, phase[deg])."""
    a = np.loadtxt(Path(path))
    return a[:, 0], a[:, 1], a[:, 3]
