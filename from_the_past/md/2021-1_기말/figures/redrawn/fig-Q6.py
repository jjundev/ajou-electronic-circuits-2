"""2021-1 기말 Q6 — 기준: Q6.md '회로 — Fig Q6'."""
import schemdraw.elements as elm
from schem_style import FONT_SIZE, OPEN_R, Resistor, dot, new_drawing

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xv, xy, xx = 0, 3.5, 8.0      # V_in 세로줄, Y 접속점, X 접속점
    # 왼쪽 V_in (원형 전압원, 부호는 원 오른쪽), 아래 접지
    vin = d.add(elm.Source().down().at((xv, -1.0)).label(r"$V_\mathrm{in}$", "top", ofst=GAP))
    d.add(elm.Ground().at(vin.end).scale(0.8))
    for dx, dy, sign in ((0.5, 0.35, "+"), (0.58, -0.4, "−")):
        d.add(elm.Label().right().at((xv + dx, vin.center.y + dy))
              .label(sign, font="Arial", fontsize=FONT_SIZE + 1, halign="left"))
    # 위 단자 → 위로 → 오른쪽 R1, Y, R2, X, + 입력 (한 가로선)
    d.add(elm.Line().up().at(vin.start).toy(0))
    d.add(Resistor().right().tox(xy).label(r"$R_\mathrm{1}$", "bottom", ofst=0.25))
    y = dot(d)
    d.add(elm.Label().right().at((xy, -0.65)).label(r"$Y$", halign="center"))
    d.add(Resistor().right().tox(xx).label(r"$R_\mathrm{2}$", "bottom", ofst=0.25))
    x = dot(d)
    d.add(elm.Label().right().at((xx, 0.5)).label(r"$X$", halign="center"))
    # 연산증폭기: 뒤집어 + 입력(in2)이 위. + 입력이 X 선 높이
    oa = d.add(elm.Opamp().right().flip().anchor("in2").at((xx + 2.3, 0)))
    d.add(elm.Line().right().at(x.center).to(oa.in2))
    xo = oa.out.x + 0.55
    d.add(elm.Line().right().at(oa.out).tox(xo)); vo = dot(d)
    d.add(elm.Line().right().at(vo.center).length(1.2))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    # C1: Y 위로 → 오른쪽 (연산증폭기 위) → 아래로 Vout
    yc = 1.5
    d.add(elm.Line().up().at(y.center).toy(yc))
    d.add(elm.Line().right().tox(xx - 0.4))
    d.add(elm.Capacitor().right().label(r"$C_\mathrm{1}$", "top", ofst=GAP))
    d.add(elm.Line().right().tox(xo))
    d.add(elm.Line().down().toy(vo.center))
    # C2: X 아래로, 접지
    c2 = d.add(elm.Capacitor().down().at(x.center).length(2.3).label(r"$C_\mathrm{2}$", "top", ofst=GAP))
    d.add(elm.Ground().at(c2.end).scale(0.8))
    # − 입력 → 왼쪽 → 아래 n2. n2 → R4 → 접지, n2 → R3 → 위로 Vout
    d.add(elm.Line().left().at(oa.in1).length(0.8))
    d.add(elm.Line().down().toy(-2.55)); n2 = dot(d)
    r4 = d.add(Resistor().down().at(n2.center).length(2.0).label(r"$R_\mathrm{4}$", "bottom", ofst=GAP))
    d.add(elm.Ground().at(r4.end).scale(0.8))
    d.add(elm.Line().right().at(n2.center).length(1.6))
    d.add(Resistor().right().tox(xo).label(r"$R_\mathrm{3}$", "bottom", ofst=0.25))
    d.add(elm.Line().up().toy(vo.center))
    return d
