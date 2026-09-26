"""2021-1 기말 Q5 — 기준: Q5.md '회로 — Fig Q5', '회로 — Fig Q5(eq)'."""
import schemdraw.elements as elm
from schem_style import DOT_R, OPEN_R, Resistor, dot, new_drawing

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def opamp(d, in1):
    """오른쪽을 향한 연산증폭기. − 입력(in1) 위, + 입력(in2) 아래."""
    return d.add(elm.Opamp().right().anchor("in1").at(in1))


def terminal(d, xy, label, left):
    """개방 원 단자와 라벨."""
    return d.add(elm.Dot(open=True, radius=OPEN_R).at(xy)
                 .label(label, "left" if left else "right", ofst=GAP))


def grounded_plus(d, oa, dx):
    """+ 입력에서 왼쪽으로 dx 나가 아래로 꺾여 접지."""
    d.add(elm.Line().left().at(oa.in2).length(dx))
    d.add(elm.Line().down().length(0.45))
    d.add(elm.Ground().scale(0.8))


def main_circuit(d):
    xn = 4.2                     # n1, n2 세로줄
    top = 3.1                    # 맨 위 R3 선 높이
    # 첫째 연산증폭기: − 입력 높이 0
    o1 = opamp(d, (xn + 0.8, 0))
    n2 = d.add(elm.Dot(radius=DOT_R).at((xn, o1.in2.y)))
    d.add(elm.Line().right().at(n2.center).to(o1.in2))
    d.add(Resistor().left().at(n2.center).length(1.9).label(r"$R_\mathrm{4}$", "top", ofst=0.25))
    terminal(d, d.here, r"$V_\mathrm{in}$", left=True)
    # n1: − 입력 왼쪽 위. 위로 R3 선, 아래로 − 입력
    n1 = d.add(elm.Dot(radius=DOT_R).at((xn, 1.3)))
    d.add(elm.Line().down().at(n1.center).toy(o1.in1))
    d.add(elm.Line().right().to(o1.in1))
    xv = o1.out.x + 0.55
    rf = d.add(Resistor().right().at(n1.center).tox(xv).label(r"$R_\mathrm{6}$", "top", ofst=0.25))
    vt = dot(d)
    d.add(elm.Line().right().at(vt.center).length(0.9))
    terminal(d, d.here, r"$V_\mathrm{out}$", left=False)
    d.add(elm.Line().down().at(vt.center).toy(o1.out)); vb = dot(d)
    d.add(elm.Line().left().at(vb.center).tox(o1.out))
    # 둘째 연산증폭기: − 입력이 첫째 출력 높이
    d.add(Resistor().right().at(vb.center).length(3.2).label(r"$R_\mathrm{1}$", "bottom", ofst=0.25))
    n3 = dot(d)
    o2 = opamp(d, (n3.center.x + 0.8, n3.center.y))
    d.add(elm.Line().right().at(n3.center).to(o2.in1))
    grounded_plus(d, o2, 0.6)
    xx = o2.out.x + 0.5
    d.add(elm.Line().right().at(o2.out).tox(xx)); x = dot(d)
    d.add(elm.Label().right().at((xx + 0.2, x.center.y + 0.5)).label(r"$X$", halign="left"))
    # C1: n3 위로 → 오른쪽 (연산증폭기 위) → 아래로 X
    yc1 = n3.center.y + 1.3
    d.add(elm.Line().up().at(n3.center).toy(yc1))
    d.add(elm.Line().right().tox(o2.center.x - 0.5))
    d.add(elm.Capacitor().right().label(r"$C_\mathrm{1}$", "top", ofst=GAP))
    d.add(elm.Line().right().tox(xx))
    d.add(elm.Line().down().toy(x.center))
    # 셋째 연산증폭기
    d.add(Resistor().right().at(x.center).length(2.3).label(r"$R_\mathrm{2}$", "bottom", ofst=0.25))
    n4 = dot(d)
    o3 = opamp(d, (n4.center.x + 0.8, n4.center.y))
    d.add(elm.Line().right().at(n4.center).to(o3.in1))
    grounded_plus(d, o3, 0.6)
    xy = o3.out.x + 0.5
    yy = n4.center.y + 1.4
    # C2: n4 위로 → 오른쪽 → Y 접속점
    d.add(elm.Line().up().at(n4.center).toy(yy))
    d.add(elm.Line().right().tox(o3.center.x - 0.5))
    d.add(elm.Capacitor().right().label(r"$C_\mathrm{2}$", "top", ofst=GAP))
    d.add(elm.Line().right().tox(xy)); y = dot(d)
    # 셋째 출력 → 오른쪽 → 위로 Y
    d.add(elm.Line().right().at(o3.out).tox(xy))
    d.add(elm.Line().up().toy(y.center))
    d.add(elm.Label().right().at((xy + 0.2, o3.out.y - 0.3)).label(r"$Y$", halign="left"))
    # Y → 맨 위 → 왼쪽 R3 → n1 위 세로선 → n1
    d.add(elm.Line().up().at(y.center).toy(top))
    d.add(elm.Line().left().tox(11.8))
    d.add(Resistor().left().length(1.2).label(r"$R_\mathrm{3}$", "bottom", ofst=0.25))
    d.add(elm.Line().left().tox(xn))
    d.add(elm.Line().down().toy(n1.center))
    # n2 → 아래 → 맨 아래 R5 → X 아래 → 위로 X
    ybot = n2.center.y - 2.2
    d.add(elm.Line().down().at(n2.center).toy(ybot))
    d.add(elm.Line().right().tox(7.5))
    d.add(Resistor().right().length(1.2).label(r"$R_\mathrm{5}$", "top", ofst=0.25))
    d.add(elm.Line().right().tox(xx))
    d.add(elm.Line().up().toy(x.center))
    return rf


def eq_circuit(d, x0):
    """오른쪽 등가 회로: 입력 V_Y, V_in, V_X (위→아래), 연산증폭기 하나."""
    xn = x0 + 2.6          # n1, n2 세로줄
    o = opamp(d, (xn + 0.8, 0))
    # V_Y → R3 → n1 → − 입력
    d.add(elm.Line().right().at((xn, 0)).to(o.in1))
    n1 = d.add(elm.Dot(radius=DOT_R).at((xn, 0)))
    d.add(Resistor().left().at(n1.center).length(2.0).label(r"$R_\mathrm{3}$", "top", ofst=0.25))
    terminal(d, d.here, r"$V_\mathrm{Y}$", left=True)
    # V_in → R4 → n2 → 위로 + 입력
    yin = o.in2.y - 0.35
    n2 = d.add(elm.Dot(radius=DOT_R).at((xn, yin)))
    d.add(Resistor().left().at(n2.center).length(2.0).label(r"$R_\mathrm{4}$", "bottom", ofst=0.25))
    terminal(d, d.here, r"$V_\mathrm{in}$", left=True)
    d.add(elm.Line().up().at(n2.center).toy(o.in2))
    d.add(elm.Line().right().to(o.in2))
    # V_X → R5 → 모서리 → 위로 n2
    yx = yin - 1.7
    d.add(Resistor().left().at((xn, yx)).length(2.0).label(r"$R_\mathrm{5}$", "bottom", ofst=0.25))
    terminal(d, d.here, r"$V_\mathrm{X}$", left=True)
    d.add(elm.Line().up().at((xn, yx)).toy(n2.center))
    # 출력 → Vout 접속점 → Vout 원. R6 귀환: n1 위로 → 오른쪽 R6 → 아래로 Vout
    xo = o.out.x + 0.35
    d.add(elm.Line().right().at(o.out).tox(xo)); vo = dot(d)
    d.add(elm.Line().right().at(vo.center).length(0.6))
    terminal(d, d.here, r"$V_\mathrm{out}$", left=False)
    yr = 1.4
    d.add(elm.Line().up().at(n1.center).toy(yr))
    d.add(Resistor().right().tox(xo).label(r"$R_\mathrm{6}$", "top", ofst=0.25))
    d.add(elm.Line().down().toy(vo.center))


def draw():
    d = new_drawing()
    main_circuit(d)
    eq_circuit(d, 22.2)
    return d
