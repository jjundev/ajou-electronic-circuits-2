"""2021-1 기말 Q1 — 기준: Q1.md '회로 — Fig Q1'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 4.0, 8.0
    rail(d, (xl - 0.4, rail_y), (xr + 0.5, rail_y))
    d.add(elm.Label().right().at((xr + 0.7, rail_y + 0.15)).label(r"$V_{DD}$", halign="left"))
    # 왼쪽: M3 (pmos, 소스가 레일), 게이트 ← V_b2
    d.add(elm.Line().down().at((xl, rail_y)).length(0.5))
    m3 = pmos(d, at=d.here, anchor="source", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b2}$")
    # 오른쪽 세로줄 위→아래: R_L, Vout 접속점, M2, Y 접속점, M1, 접지
    rl = d.add(Resistor().down().at((xr, rail_y)).length(2.0)
               .label(r"$R_\mathrm{L}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().at(rl.end).length(0.2)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.3))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    gate_terminal(d, m2.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(m2.source).length(0.45)); y = dot(d)
    # Y: 접속점 오른쪽 아래
    d.add(elm.Label().right().at((xr + 0.25, y.center.y - 0.4)).label(r"$Y$", halign="left"))
    # M3 드레인 → Y 높이까지 내려가 오른쪽으로 → Y 접속점
    d.add(elm.Line().down().at(m3.drain).toy(y.center))
    d.add(elm.Line().right().tox(y.center))
    d.add(elm.Line().down().at(y.center).length(0.35))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # M1 게이트(X) ← 가로 R_S ← V_in 원
    d.add(elm.Line().left().at(m1.gate).length(0.9))
    d.add(Resistor().left().length(1.2).label(r"$R_\mathrm{S}$", "top", ofst=GAP))
    d.add(elm.Line().left().length(0.7))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{in}$", "left", ofst=GAP))
    # X: 게이트 선 아래, R_S와 게이트 사이
    d.add(elm.Label().right().at((m1.gate.x - 0.55, m1.gate.y - 0.62)).label(r"$X$", halign="center"))
    return d
