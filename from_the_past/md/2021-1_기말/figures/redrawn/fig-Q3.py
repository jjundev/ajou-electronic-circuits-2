"""2021-1 기말 Q3 — 기준: Q3.md '회로 — Fig Q3'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, gate_terminal, new_drawing, nmos, rail

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 4.2, 9.0
    rail(d, (xl - 0.45, rail_y), (xr + 0.6, rail_y))
    d.add(elm.Label().right().at((xr + 0.8, rail_y + 0.05)).label(r"$V_{DD}$", halign="left"))
    # 왼쪽 세로줄 위→아래: R_D, n1 접속점, M1 (게이트 오른쪽), n2 접속점
    rd = d.add(Resistor().down().at((xl, rail_y)).length(2.3)
               .label(r"$R_\mathrm{D}$", "top", ofst=GAP))
    d.add(elm.Line().down().at(rd.end).length(0.2)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.9))
    m1 = nmos(d, at=d.here, anchor="drain", mirror=True)
    # M1: 왼쪽, 소스 화살표 높이
    d.add(elm.Label().right().at((xl - 0.3, m1.source.y + 0.35)).label(r"$M_\mathrm{1}$", halign="right"))
    d.add(elm.Line().right().at(m1.gate).length(0.8))
    gate_terminal(d, d.here, r"$V_\mathrm{b}$", right=True)
    d.add(elm.Line().down().at(m1.source).length(0.3)); n2 = dot(d)
    # 오른쪽 세로줄: M2 (게이트가 n1 높이, 드레인 위로 레일), Vout 접속점, R_M, 접지
    m2 = nmos(d, at=(xr - 0.92, n1.center.y), anchor="gate", label=r"$M_\mathrm{2}$")
    d.add(elm.Line().right().at(n1.center).tox(m2.gate))
    d.add(elm.Line().up().at(m2.drain).toy(rail_y))
    d.add(elm.Line().down().at(m2.source).toy(n2.center)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    rm = d.add(Resistor().down().at(vout.center).length(2.4).label(r"$R_\mathrm{M}$", "bottom", ofst=GAP))
    d.add(elm.Ground().at(rm.end).scale(0.8))
    # n2 → 가로 R_F → Vout
    d.add(Resistor().right().at(n2.center).to(vout.center).label(r"$R_\mathrm{F}$", "bottom", ofst=0.25))
    # n2 → 왼쪽 → 아래 I_in (화살표 위) → 접지
    xi = xl - 1.4
    d.add(elm.Line().left().at(n2.center).tox(xi))
    d.add(elm.Line().down().length(0.5))
    iin = d.add(elm.SourceI().down().length(1.8).scale(0.6).reverse()
                .label(r"$I_\mathrm{in}$", "top", ofst=0.35))
    d.add(elm.Ground().at(iin.end).scale(0.8))
    return d
