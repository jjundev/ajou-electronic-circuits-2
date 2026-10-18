"""2013-1 중간 Q1 — 기준: Q1.md '회로 — Fig Q1'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 0.0    # V_DD 레일 높이


def draw():
    d = new_drawing()
    xl, xr = 0.0, 5.6            # M5 줄, 오른쪽 세로줄
    rail(d, (xl - 0.6, RAIL_Y), (xr + 2.2, RAIL_Y))
    d.add(elm.Label().right().at((xr + 2.2, RAIL_Y + 0.3))
          .label(r"$V_{DD}\mathrm{=1.8V}$", halign="right", valign="bottom"))
    # 위 두 pmos: M5 좌우 반전(게이트 오른쪽), M4 보통. 소스에서 세로선이 위로 레일
    ys = RAIL_Y - 0.7
    m5 = pmos(d, at=(xl, ys), anchor="source", mirror=True)
    m4 = pmos(d, at=(xr, ys), anchor="source", label=r"$M_\mathrm{4}$")
    for m in (m5, m4):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    d.add(elm.Label().right().at((xl - 0.3, m5.center.y + 0.15)).label(r"$M_\mathrm{5}$", halign="right"))
    # 게이트 공통선과 게이트 접속점, 다이오드 연결: n1 → 오른쪽 → 위 → 게이트 접속점
    xg = m5.gate.x + 0.9
    d.add(elm.Line().at(m5.gate).tox(xg)); g = dot(d)
    d.add(elm.Line().at(g.center).tox(m4.gate))
    d.add(elm.Line().down().at(m5.drain).length(0.6)); n1 = dot(d)
    d.add(elm.Line().right().at(n1.center).tox(xg))
    d.add(elm.Line().up().toy(g.center.y))
    # 왼쪽 세로줄 아래: I_REF(화살표 아래), 접지
    iref = d.add(elm.SourceI().down().at(n1.center).length(1.9).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().at(iref.end).length(0.8))
    d.add(elm.Ground().scale(0.8))
    # 오른쪽 세로줄 위→아래: M4, M3, Vout 접속점, M2, M1, 접지
    d.add(elm.Line().down().at(m4.drain).length(1.0))
    m3 = pmos(d, at=d.here, anchor="source", label=r"$M_\mathrm{3}$")
    d.add(elm.Line().down().at(m3.drain).length(0.9)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.4))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.9))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    d.add(elm.Line().down().at(m2.source).length(1.3))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # M3 게이트 → 왼쪽 → 아래로 Vb 접속점(Vout 높이) → M2 게이트 높이 → 오른쪽 M2 게이트
    xb = m3.gate.x - 0.75
    d.add(elm.Line().at(m3.gate).tox(xb))
    d.add(elm.Line().down().toy(vout.center.y)); vb = dot(d)
    d.add(elm.Line().down().at(vb.center).toy(m2.gate.y))
    d.add(elm.Line().right().tox(m2.gate))
    gate_terminal(d, vb.center, r"$V_\mathrm{b}$")
    # V_in 원 → 가로선 → M1 게이트
    d.add(elm.Line().left().at(m1.gate).length(1.0))
    gate_terminal(d, d.here, r"$V_\mathrm{in}$", open_=True)
    return d
