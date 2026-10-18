"""2018-2 중간 Q2 — 기준: Q2.md '회로 — Fig Q2'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 3.6, 9.5
    rail(d, (xl - 0.3, rail_y), (xr + 0.4, rail_y))
    d.add(elm.Label().right().at((xr - 0.9, rail_y + 0.2))
          .label(r"$V_{DD}\ \mathrm{=1.8V}$", halign="left", valign="bottom"))
    # 위 pmos 두 개: M5 좌우 반전(다이오드 연결), M4 보통. 소스 → 레일
    m5 = pmos(d, at=(xl, rail_y - 0.3), anchor="source", mirror=True, label=r"$M_\mathrm{5}$")
    m4 = pmos(d, at=(xr, rail_y - 0.3), anchor="source", label=r"$M_\mathrm{4}$")
    for m in (m5, m4):
        d.add(elm.Line().up().at(m.source).toy(rail_y))
    # 게이트 공통선과 M5 게이트 바로 오른쪽 게이트 접속점, 아래로 n1 높이 → 왼쪽 n1 접속점
    xg = m5.gate.x + 0.35
    d.add(elm.Line().at(m5.gate).tox(xg)); g = dot(d)
    d.add(elm.Line().at(g.center).tox(m4.gate.x))
    d.add(elm.Line().down().at(m5.drain).length(0.7)); n1 = dot(d)
    d.add(elm.Line().down().at(g.center).toy(n1.center.y))
    d.add(elm.Line().left().tox(xl))
    # n1 → I_REF(화살표 아래) → 접지
    iref = d.add(elm.SourceI().down().at(n1.center).length(1.6).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Ground().at(iref.end).scale(0.8))
    # 오른쪽 세로줄 위→아래: M4, M3, Vout 접속점, M2, M1, 접지
    d.add(elm.Line().down().at(m4.drain).length(0.55))
    m3 = pmos(d, at=d.here, anchor="source", label=r"$M_\mathrm{3}$")
    d.add(elm.Line().down().at(m3.drain).length(0.6)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.6))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    d.add(elm.Line().down().at(m2.source).length(0.6))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    gate_terminal(d, m1.gate, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # V_b 점 단자 → Vb 접속점 → 위로 M3 게이트, 아래로 M2 게이트
    xb = m3.gate.x - 0.45
    d.here = (xb, vout.center.y); vb = dot(d)
    gate_terminal(d, vb.center, r"$V_\mathrm{b}$")
    d.add(elm.Line().up().at(vb.center).toy(m3.gate.y))
    d.add(elm.Line().right().tox(m3.gate.x))
    d.add(elm.Line().down().at(vb.center).toy(m2.gate.y))
    d.add(elm.Line().right().tox(m2.gate.x))
    return d
