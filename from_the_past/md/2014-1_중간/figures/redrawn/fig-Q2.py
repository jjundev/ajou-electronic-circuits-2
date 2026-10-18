"""2014-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 0.0


def draw():
    d = new_drawing()
    xl, xr = 0.0, 4.2               # M_REF 줄, 오른쪽 세로줄
    xj = xl - 0.45                  # 레일에서 M_REF 소스로 내려오는 세로선
    rail(d, (xj - 0.3, RAIL_Y), (xr + 0.3, RAIL_Y))
    d.add(elm.Label().right().at((xr + 0.5, RAIL_Y + 0.15))
          .label(r"$V_{DD}\mathrm{=1.8\ V}$", halign="left", valign="bottom"))
    # M_REF: pmos 좌우 반전. 레일에서 세로선이 내려와 오른쪽으로 꺾여 소스
    ys = RAIL_Y - 0.35
    mref = pmos(d, at=(xl, ys), anchor="source", mirror=True)
    d.add(elm.Line().down().at((xj, RAIL_Y)).toy(ys))
    d.add(elm.Line().right().tox(xl))
    d.add(elm.Label().right().at((xj - 0.3, mref.center.y)).label(r"$M_\mathrm{REF}$", halign="right"))
    # M2: pmos 보통, 소스에서 세로선이 위로 레일
    m2 = pmos(d, at=(xr, ys), anchor="source", label=r"$M_\mathrm{2}$")
    d.add(elm.Line().up().at(m2.source).toy(RAIL_Y))
    # n1 위 접속점: M_REF 게이트 → 접속점 → M2 게이트, 아래로 n1 아래 접속점 (다이오드 연결)
    xg = mref.gate.x + 0.45
    d.add(elm.Line().right().at(mref.gate).tox(xg)); n1t = dot(d)
    d.add(elm.Line().right().at(n1t.center).tox(m2.gate))
    d.add(elm.Line().down().at(mref.drain).length(0.4)); n1b = dot(d)
    d.add(elm.Line().down().at(n1t.center).toy(n1b.center.y))
    d.add(elm.Line().left().tox(xl))
    # 왼쪽 세로줄 아래: I_REF(화살표 아래), 접지
    iref = d.add(elm.SourceI().down().at(n1b.center).length(1.9).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Ground().at(iref.end).scale(0.8))
    # 오른쪽 세로줄: M2 드레인 → Vout 접속점 → M1 → 접지
    d.add(elm.Line().down().at(m2.drain).length(0.4)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.3))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    gate_terminal(d, m1.gate, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(m1.source).scale(0.8))
    return d
