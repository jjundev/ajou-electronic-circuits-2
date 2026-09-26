"""2023-1 기말 Q5 — 기준: Q5.md '회로 — Fig Q5'. −1 블록 둘레 점선 원과 점선은 인쇄된 것이라 그린다."""
import math

import schemdraw.elements as elm
from schemdraw.segments import Segment, SegmentCircle
from schem_style import DOT_R, LW, OPEN_R, Resistor, dot, new_drawing

GAP = 0.2       # 소자 라벨과 기호 사이 간격
TRI_W, TRI_H = 2.2, 2.1   # −1 블록 삼각형
RING_R = 1.55   # 점선 원 반지름


class Triangle(elm.Element):
    """−1 블록: 오른쪽을 향한 삼각형. 앵커 in(왼쪽 가운데), out(꼭짓점)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.segments.append(Segment([(0, 0), (0, TRI_H / 2), (TRI_W, 0), (0, -TRI_H / 2), (0, 0)]))
        self.anchors["in"] = (0, 0)
        self.anchors["out"] = (TRI_W, 0)
        self.params["drop"] = (TRI_W, 0)


class DottedRing(elm.Element):
    """점선 원과, 원 오른쪽 위에서 오른쪽 아래로 뻗는 점선."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.segments.append(SegmentCircle((0, 0), RING_R, ls=":", lw=LW))
        a = math.radians(25)
        p = (RING_R * math.cos(a), RING_R * math.sin(a))
        self.segments.append(Segment([p, (p[0] + 2.0, p[1] - 0.8)], ls=":", lw=LW))


def grounded_plus(d, oa):
    """+ 입력 → 왼쪽으로 짧게 → 아래 → 접지."""
    d.add(elm.Line().left().at(oa.in2).length(0.35))
    d.add(elm.Line().down().length(0.5))
    d.add(elm.Ground().scale(0.8))


def draw():
    d = new_drawing()
    xn1 = 4.1                        # n1 세로선
    xvo = 7.8                        # Vout 세로선
    y_c1, y_r3, y_r4 = 1.9, 3.7, 5.7
    # 첫째 연산증폭기: − 입력 위, + 입력 아래, 출력 높이 y=0
    oa1 = d.add(elm.Opamp(sign=True).right().anchor("in1").at((xn1 + 0.6, 0.625)))
    grounded_plus(d, oa1)
    # V_in 원 → R1 → n1 아래 접속점 → − 입력
    d.add(elm.Dot(open=True, radius=OPEN_R).at((0.9, oa1.in1.y)).label(r"$V_\mathrm{in}$", "left"))
    d.add(elm.Line().right().at((0.9, oa1.in1.y)).length(0.3))
    d.add(Resistor().right().tox(xn1).label(r"$R_\mathrm{1}$", "bottom", ofst=0.25)); n1b = dot(d)
    d.add(elm.Line().right().at(n1b.center).tox(oa1.in1.x))
    # n1 세로선: 맨 위 R4 높이 → R3 접속점 → C1 접속점 → 아래 접속점
    d.add(elm.Line().up().at(n1b.center).toy(y_c1)); n1m = dot(d)
    d.add(elm.Line().up().toy(y_r3)); n1t = dot(d)
    d.add(elm.Line().up().toy(y_r4))
    # R3, C1: n1 세로선과 Vout 세로선 사이
    d.add(Resistor().right().at(n1t.center).tox(xvo).label(r"$R_\mathrm{3}$", "top", ofst=0.25))
    d.add(elm.Line().down().toy(y_c1))
    d.add(elm.Capacitor().right().at(n1m.center).tox(xvo).label(r"$C_\mathrm{1}$", "top", ofst=0.25))
    vo_t = dot(d)
    d.add(elm.Line().right().at(vo_t.center).length(0.8))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vo_t.center).toy(oa1.out.y))
    d.add(elm.Line().left().tox(oa1.out.x))
    vo_b = (xvo, oa1.out.y)
    d.add(elm.Dot(radius=DOT_R).at(vo_b))
    # R2 → n2 → 둘째 연산증폭기 − 입력
    xn2 = xvo + 3.1
    d.add(Resistor().right().at(vo_b).tox(xn2).label(r"$R_\mathrm{2}$", "bottom", ofst=0.25)); n2 = dot(d)
    d.add(elm.Line().right().length(0.7))
    oa2 = d.add(elm.Opamp(sign=True).right().anchor("in1").at(d.here))
    grounded_plus(d, oa2)
    d.add(elm.Line().right().at(oa2.out).length(1.2)); y = dot(d)
    # Y: 둘째 연산증폭기 꼭짓점과 Y 접속점 사이, 출력선 위
    d.add(elm.Label().right().at((oa2.out.x + 0.6, y.center.y + 0.55)).label(r"$Y$"))
    # C2: n2 → 위 → 오른쪽 → 둘째 연산증폭기 위 → 아래 Y
    y_c2 = oa2.in1.y + 1.3
    d.add(elm.Line().up().at(n2.center).toy(y_c2))
    d.add(elm.Capacitor().right().tox(y.center.x).label(r"$C_\mathrm{2}$", "top", ofst=0.25))
    d.add(elm.Line().down().toy(y.center.y))
    # −1 블록과 점선 원
    d.add(elm.Line().right().at(y.center).length(0.9))
    tri = d.add(Triangle().right().anchor("in").at(d.here))
    d.add(elm.Label().right().at((tri.out.x - TRI_W * 0.72, tri.out.y)).label(r"$\mathrm{-1}$"))
    d.add(DottedRing().right().at((tri.out.x - TRI_W / 2, tri.out.y)))
    # X: 블록 출력 → 오른쪽 → 위 R4 높이 → 왼쪽 R4 → n1 세로선 위 끝
    xx = tri.out.x + 1.2
    d.add(elm.Line().right().at(tri.out).tox(xx))
    d.add(elm.Line().up().toy(y_r4))
    d.add(elm.Label().right().at((xx + 0.25, y_c2)).label(r"$X$", halign="left"))
    # R4는 왼쪽 끝에서 오른쪽으로 그린다(라벨 "bottom"이 아래에 오도록)
    x4 = (xn1 + xx) / 2
    d.add(elm.Line().left().tox(x4 + 0.8))
    d.add(elm.Line().right().at((xn1, y_r4)).tox(x4 - 0.8))
    d.add(Resistor().right().tox(x4 + 0.8).label(r"$R_\mathrm{4}$", "bottom", ofst=0.25))
    return d
