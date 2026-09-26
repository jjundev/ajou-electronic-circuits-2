"""기출 회로도 다시 그리기 공통 스타일 (Razavi 시험지 모양). 규칙은 FORMAT-EXAM.md '다시 그린 그림'."""
from pathlib import Path

import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm

schemdraw.use("matplotlib")
DPI = 432          # 크롭 144 dpi의 3배
FONT_SIZE = 12
LW = 1.2
GATE_LEAD = 1.0    # 게이트에서 단자까지 가로선 길이
schemdraw.config(fontsize=FONT_SIZE, lw=LW, font="DejaVu Sans")


def new_drawing():
    return schemdraw.Drawing(show=False, unit=2.0)


def _fet(d, cls, at, anchor, mirror, label, label_loc):
    # d.add 전에 방향·위치를 정한다. add 뒤의 .anchor().at()은 위치를 바꾸지 않는다.
    # .right()를 꼭 준다: 안 주면 앞 요소의 진행 방향(예: Line().up())을 물려받아 기호가 돈다.
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


def gate_terminal(d, gate, label, open_=False, right=False):
    """게이트에서 가로선을 긋고 끝에 단자(점, open_이면 개방 원)와 라벨을 단다."""
    line = elm.Line().at(gate).length(GATE_LEAD)
    d.add(line.right() if right else line.left())
    return d.add(elm.Dot(open=open_).label(label, "right" if right else "left"))


def caption(d, xy, text):
    """패널 캡션 (a), (b). 원본처럼 패널 아래 가운데에 둔다.

    .right()를 꼭 준다: 안 주면 앞 요소의 진행 방향을 물려받아 라벨 위치가 흔들린다.
    """
    return d.add(elm.Label().right().at(xy).label(text))


def save_png(drawing, path, dpi=DPI):
    """흰 배경, 여백 최소, 메타데이터 없이 저장한다. Drawing.save()는 매번 다른 바이트를 내서 쓰지 않는다."""
    fig = drawing.draw(show=False)
    fig.fig.savefig(Path(path), dpi=dpi, facecolor="white", bbox_inches="tight",
                    pad_inches=0.05, metadata={"Software": None})
    plt.close(fig.fig)
