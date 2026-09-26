"""2023-1 기말 Q2 — 기준: Q2.md '회로 — Fig Q2'. 답안지 손글씨(×, n2 아래 저항·접지 등)는 그리지 않는다."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2      # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 3.8, 0
    rail(d, (xl - 0.3, rail_y), (xr + 0.5, rail_y))
    d.add(elm.Label().right().at((xr + 0.65, rail_y + 0.05)).label(r"$V_{DD}$", halign="left"))
    # 왼쪽 세로줄: R_D, n1, M1(좌우 반전), n2
    rd = d.add(Resistor().down().at((xl, rail_y)).length(3.0).label(r"$R_\mathrm{D}$", "top", ofst=0.3))
    n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.6))
    m1 = nmos(d, at=d.here, anchor="drain", mirror=True)
    gate_terminal(d, m1.gate, r"$V_\mathrm{b}$", right=True)
    # M1 라벨: 왼쪽, 소스 화살표 높이
    d.add(elm.Label().right().at((xl - 0.3, m1.source.y + 0.3)).label(r"$M_\mathrm{1}$", halign="right"))
    d.add(elm.Line().down().at(m1.source).length(0.7)); n2 = dot(d)
    # 오른쪽 세로줄: M2, Vout, R_M, 접지
    m2 = pmos(d, at=(xr, rail_y), anchor="source", label=r"$M_\mathrm{2}$")
    # M2 게이트 → 왼쪽 → 아래 n1 높이 → 왼쪽 n1
    d.add(elm.Line().left().at(m2.gate).length(0.35))
    d.add(elm.Line().down().toy(n1.center.y))
    d.add(elm.Line().left().tox(xl))
    d.add(elm.Line().down().at(m2.drain).toy(n2.center.y)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    rm = d.add(Resistor().down().at(vout.center).length(2.0).label(r"$R_\mathrm{M}$", "bottom", ofst=0.3))
    d.add(elm.Ground().at(rm.end).scale(0.8))
    # n2 → 가로 R_F → Vout
    d.add(Resistor().right().at(n2.center).to(vout.center).label(r"$R_\mathrm{F}$", "bottom", ofst=0.3))
    # n2 → 왼쪽 → 아래 I_in(화살표 위) → 접지
    xi = xl - 1.0
    d.add(elm.Line().left().at(n2.center).tox(xi))
    d.add(elm.Line().down().length(0.2))
    top = d.here
    bot = (xi, top[1] - 1.6)
    d.add(elm.SourceI().up().at(bot).to(top).scale(0.6)
          .label(r"$I_\mathrm{in}$", "top", ofst=0.3))
    d.add(elm.Ground().at(bot).scale(0.8))
    return d
