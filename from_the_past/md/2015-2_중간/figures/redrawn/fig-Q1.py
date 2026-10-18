"""2015-2 중간 Q1 — 기준: Q1.md '회로 — Fig Q1'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 9.0
ARROW = dict(arrowwidth=0.22, arrowlength=0.35)


def text(d, xy, s, halign="left", valign="center"):
    return d.add(elm.Label().right().at(xy).label(s, halign=halign, valign=valign))


def draw():
    d = new_drawing()
    R = RAIL_Y
    xl, xm, xr = 0, 4.4, 9.0        # M_REF, M4·M5, M3·M1·M2 세로줄
    rail(d, (xl, R), (xr + 0.6, R))
    text(d, (xr + 0.75, R + 0.05), r"$V_{DD}$")
    text(d, (xm - 0.3, R + 0.15), r"$(W/L)_\mathrm{4}$", halign="center", valign="bottom")
    text(d, (xr - 0.5, R + 0.15), r"$2(W/L)_\mathrm{3}$", halign="center", valign="bottom")
    # 위 pmos: M4 좌우 반전(게이트 오른쪽), M3 보통. 소스가 레일
    m4 = pmos(d, at=(xm, R), anchor="source", mirror=True)
    m3 = pmos(d, at=(xr, R), anchor="source", label=r"$M_\mathrm{3}$")
    text(d, (xm - 0.35, m4.center.y), r"$M_\mathrm{4}$", halign="right")
    # M4 게이트 오른쪽 접속점 → M3 게이트, 같은 접속점에서 아래로 n2 (다이오드 연결)
    xg = m4.gate.x + 0.35
    d.add(elm.Line().at(m4.gate).tox(xg)); g = dot(d)
    d.add(elm.Line().at(g.center).tox(m3.gate.x))
    d.add(elm.Line().down().at(m4.drain).length(0.5)); n2 = dot(d)
    d.add(elm.Line().down().at(g.center).toy(n2.center.y))
    d.add(elm.Line().left().tox(xm))
    # 오른쪽 세로줄: M3 → I_copy2 화살표 → Vout 접속점 → M1(좌우 반전) → 긴 세로선 → M2 → 접지
    d.add(elm.Arrow(**ARROW).down().at(m3.drain).length(0.75))
    text(d, (xr - 0.4, m3.drain.y - 0.35), r"$I_\mathrm{copy2}$", halign="right")
    d.add(elm.Line().down().length(0.25)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.15))
    m1 = nmos(d, at=d.here, anchor="drain", mirror=True)
    text(d, (xr - 0.3, m1.center.y + 0.2), r"$M_\mathrm{1}$", halign="right")
    gate_terminal(d, m1.gate, r"$V_\mathrm{b}$", right=True)
    d.add(elm.Line().down().at(m1.source).length(1.8))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    gate_terminal(d, m2.gate, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(m2.source).scale(0.8))
    # 가운데 세로줄 아래: n2 → I_copy1 화살표가 붙은 긴 세로선 → M5 → 접지 (M5는 M2와 같은 높이)
    m5 = nmos(d, at=(xm, m2.source.y), anchor="source", label=r"$M_\mathrm{5}$")
    d.add(elm.Ground().at(m5.source).scale(0.8))
    ya = (n2.center.y + m5.drain.y) / 2 + 0.4
    d.add(elm.Line().down().at(n2.center).toy(ya))
    d.add(elm.Arrow(**ARROW).down().length(0.8))
    d.add(elm.Line().down().toy(m5.drain.y))
    text(d, (xm - 0.25, ya + 0.05), r"$I_\mathrm{copy1}$", halign="right")
    # 왼쪽 세로줄: M_REF(좌우 반전), 게이트가 M5 게이트와 같은 높이
    mref = nmos(d, at=(xl, m5.source.y), anchor="source", mirror=True)
    d.add(elm.Ground().at(mref.source).scale(0.8))
    text(d, (xl - 0.3, mref.center.y - 0.2), r"$M_\mathrm{REF}$", halign="right")
    # 접지 아래 면적 라벨
    text(d, (xl, mref.source.y - 0.95), r"$5(W/L)_\mathrm{REF}$", halign="center", valign="top")
    text(d, (xm, m5.source.y - 0.95), r"$3(W/L)_\mathrm{5}$", halign="center", valign="top")
    # 레일 → 긴 세로선 → I_REF(화살표 아래) → n1 접속점 → M_REF 드레인
    yn1 = mref.drain.y + 0.45
    d.add(elm.Line().down().at((xl, R)).toy(yn1 + 1.65))
    d.add(elm.SourceI().down().length(1.3).scale(0.6).label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().toy(yn1)); n1 = dot(d)
    d.add(elm.Line().down().toy(mref.drain.y))
    # 다이오드 연결: n1 → 오른쪽 → 아래 게이트 높이 접속점 → M5 게이트
    xd = mref.gate.x + 0.45
    d.add(elm.Line().right().at(n1.center).tox(xd))
    d.add(elm.Line().down().toy(mref.gate.y)); dot(d)
    d.add(elm.Line().at(mref.gate).to(m5.gate))
    return d
