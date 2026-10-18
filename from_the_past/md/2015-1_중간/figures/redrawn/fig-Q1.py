"""2015-1 중간 Q1 — 기준: Q1.md '회로 — Fig Q1'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2   # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 5.0, 9.0
    rail(d, (xl - 0.3, rail_y), (xr + 0.35, rail_y))
    d.add(elm.Label().right().at((xr + 0.5, rail_y + 0.05)).label(r"$V_{DD}$", halign="left"))
    # 오른쪽 세로줄 위→아래: M3, Vout 접속점, M2, M1, 접지
    m3 = pmos(d, at=(xr, rail_y), anchor="source", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Line().down().at(m3.drain).length(0.35)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.15))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    gate_terminal(d, m2.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(m2.source).length(0.15))   # n2 (라벨 없음)
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # 왼쪽 세로줄: M_REF(좌우 반전), 게이트가 M1 게이트와 같은 높이
    mref = nmos(d, at=(xl, m1.source.y), anchor="source", mirror=True)
    d.add(elm.Ground().at(mref.source).scale(0.8))
    d.add(elm.Label().right().at((xl + 0.5, mref.source.y - 0.2))
          .label(r"$M_\mathrm{REF}$", halign="left", valign="top"))
    # 레일 → 긴 세로선 → I_REF(화살표 아래) → n1 위 접속점 → M_REF 드레인
    yn1 = mref.drain.y + 0.4
    d.add(elm.Line().down().at((xl, rail_y)).length(2.3))
    d.add(elm.SourceI().down().length(1.3).scale(0.6).label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().toy(yn1)); n1 = dot(d)
    d.add(elm.Line().down().toy(mref.drain.y))
    # 다이오드 연결: n1 위 → 오른쪽 → 아래 게이트 선의 n1 아래 접속점
    xd = mref.gate.x + 0.45
    d.add(elm.Line().right().at(n1.center).tox(xd))
    d.add(elm.Line().down().toy(mref.gate.y)); dot(d)
    d.add(elm.Line().at(mref.gate).to(m1.gate))
    return d
