"""기출 회로도 다시 그리기 공통 스타일 (Razavi 시험지 모양). 규칙은 FORMAT-EXAM.md '다시 그린 그림'.

그림은 원본과 같은 인쇄 크기(1:1)로 그린다. INCHES_PER_UNIT이 도면 단위의 실제 길이를 정하고,
글씨(FONT_SIZE pt)와 선 굵기(LW pt)는 그 크기 그대로 인쇄된다.
"""
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
from schemdraw.segments import Segment

schemdraw.use("matplotlib")
DPI = 432               # 크롭 144 dpi의 3배
FONT_SIZE = 9           # 인쇄 글자 크기(pt)
LW = 0.8                # 배선(pt)
RAIL_LW = 1.8           # 전원 레일(pt)
GATE_LEAD = 0.55        # 게이트에서 단자까지 가로선 길이(단위)
INCHES_PER_UNIT = 0.2   # 도면 1단위의 인쇄 길이
DOT_R = 0.08            # 접속점 반지름(단위)
OPEN_R = 0.07           # 개방 단자 반지름(단위)

# 원본 라벨: 굵은 Arial. 본 글자는 굵은 이탤릭, 첨자는 \mathrm{}으로 굵은 정자체
matplotlib.rcParams.update({
    "mathtext.fontset": "custom",
    "mathtext.it": "Arial:bold:italic",
    "mathtext.rm": "Arial:bold",
    "mathtext.bf": "Arial:bold",
    "mathtext.sf": "Arial:bold",
    "mathtext.cal": "Arial:bold",
    "mathtext.tt": "Arial:bold",
})
schemdraw.config(fontsize=FONT_SIZE, lw=LW, font="Arial", unit=1.6, inches_per_unit=INCHES_PER_UNIT)


class Resistor(elm.Element2Term):
    """원본처럼 짧고 좁은 지그재그 (기본 ResistorIEEE보다 짧고 낮다)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        w, h = 0.55 / 6, 0.11
        self.segments.append(Segment(
            [(0, 0), (0.5*w, h), (1.5*w, -h), (2.5*w, h), (3.5*w, -h),
             (4.5*w, h), (5.5*w, -h), (6*w, 0)]))


def new_drawing():
    return schemdraw.Drawing(show=False)


def _fet(d, cls, at, anchor, mirror, label, label_loc):
    # d.add 전에 방향·위치를 정한다. add 뒤의 .anchor().at()은 위치를 바꾸지 않는다.
    # .right()를 꼭 준다: 안 주면 앞 요소의 진행 방향(예: Line().up())을 물려받아 기호가 돈다.
    # 크기는 scale()이 아니라 INCHES_PER_UNIT으로 줄인다. scale()은 화살표 머리를 줄이지 않는다.
    e = cls(offset_gate=False, source_arrow=True).right()
    if not mirror:
        e = e.reverse()
    if at is not None:
        e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=label_loc or ("left" if mirror else "right"))
    return d.add(e)


def nmos(d, at=None, anchor="drain", mirror=False, label=None, label_loc=None):
    """게이트 왼쪽(mirror면 오른쪽), 드레인 위, 소스 아래, 소스 화살표 바깥. 벌크 없음."""
    return _fet(d, elm.AnalogNFet, at, anchor, mirror, label, label_loc)


def pmos(d, at=None, anchor="source", mirror=False, label=None, label_loc=None):
    """게이트 왼쪽(mirror면 오른쪽), 소스 위, 드레인 아래, 소스 화살표 안쪽. 벌크 없음."""
    return _fet(d, elm.AnalogPFet, at, anchor, mirror, label, label_loc)


def dot(d, open_=False):
    """접속점(채운 점) 또는 개방 단자(빈 원)."""
    return d.add(elm.Dot(open=open_, radius=OPEN_R if open_ else DOT_R))


def gate_terminal(d, gate, label, open_=False, right=False):
    """게이트에서 가로선을 긋고 끝에 단자(점, open_이면 개방 원)와 라벨을 단다."""
    line = elm.Line().at(gate).length(GATE_LEAD)
    d.add(line.right() if right else line.left())
    return d.add(elm.Dot(open=open_, radius=OPEN_R if open_ else DOT_R)
                 .label(label, "right" if right else "left"))


def rail(d, start, end):
    """굵은 전원 레일 (V_DD 가로선)."""
    return d.add(elm.Line().at(start).to(end).linewidth(RAIL_LW))


def caption(d, xy, text):
    """패널 캡션 (a), (b). 원본처럼 굵지 않은 글씨로 패널 아래 가운데에 둔다.

    .right()를 꼭 준다: 안 주면 앞 요소의 진행 방향을 물려받아 라벨 위치가 흔들린다.
    """
    return d.add(elm.Label().right().at(xy).label(text, font="Arial", fontsize=FONT_SIZE + 2))


def save_png(drawing, path, dpi=DPI):
    """흰 배경, 여백 최소, 메타데이터 없이 1:1 인쇄 크기로 저장한다.

    getfig()가 figure 크기를 INCHES_PER_UNIT × 도면 범위로 맞춘다. .fig를 바로 저장하면
    matplotlib 기본 6.4×4.8인치 캔버스에 그려져 인쇄 크기가 무시된다.
    Drawing.save()는 매번 다른 바이트를 내서 쓰지 않는다.
    """
    mfig = drawing.draw(show=False).getfig()
    mfig.subplots_adjust(0, 0, 1, 1)
    mfig.savefig(Path(path), dpi=dpi, facecolor="white", bbox_inches="tight",
                 pad_inches=0.02, metadata={"Software": None})
    plt.close(mfig)
