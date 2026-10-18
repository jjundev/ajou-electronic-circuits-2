"""2015-1 중간 Q2 둘째 그림 — 기준: Q2.md '회로 — Fig Q2-2'."""
import schemdraw.elements as elm
from schem_style import dot, new_drawing, nmos, pmos, rail

RAIL_Y = 9.0


def text(d, xy, s, halign="left", valign="center"):
    return d.add(elm.Label().right().at(xy).label(s, halign=halign, valign=valign))


def wl(k, sub):
    """k(W/L)_sub 면적 라벨."""
    return r"$%s(W/L)_\mathrm{%s}$" % (k, sub)


def draw():
    d = new_drawing()
    R = RAIL_Y
    xl, xm, xr = 0, 5.0, 8.2       # M_REF, M2·M1, M3 세로줄
    rail(d, (xl - 0.3, R), (xr + 0.35, R))
    text(d, (xl - 0.65, R + 0.05), r"$V_{DD}$", halign="right")
    # 위 pmos: M2 좌우 반전(게이트 오른쪽), M3 보통. 소스가 레일
    m2 = pmos(d, at=(xm, R), anchor="source", mirror=True)
    m3 = pmos(d, at=(xr, R), anchor="source")
    text(d, (xm - 0.35, m2.center.y), wl(5, "p"), halign="right")
    text(d, (xr + 0.35, m3.center.y), wl(3, "p"))
    # n2: M2 드레인 아래 접속점. 다이오드 연결선이 오른쪽에서 위로 게이트 선의 n2 위 접속점
    d.add(elm.Line().down().at(m2.drain).length(0.8)); n2 = dot(d)
    xd = m2.gate.x + 0.45
    d.add(elm.Line().right().at(n2.center).tox(xd))
    d.add(elm.Line().up().toy(m2.gate.y)); dot(d)
    d.add(elm.Line().at(m2.gate).to(m3.gate))
    # M3 드레인 → 아래로 I_copy 화살표(선 끝 화살촉)
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at(m3.drain).length(1.7))
    text(d, (xr + 0.3, m3.drain.y - 1.35), r"$I_\mathrm{copy}$")
    # 가운데 세로줄: n2 → M1 → 접지
    d.add(elm.Line().down().at(n2.center).length(1.8))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    text(d, (xm + 0.35, m1.center.y - 0.1), wl(2, "n"))
    # 왼쪽 세로줄: M_REF(좌우 반전), 게이트가 M1 게이트와 같은 높이
    mref = nmos(d, at=(xl, m1.source.y), anchor="source", mirror=True)
    d.add(elm.Ground().at(mref.source).scale(0.8))
    text(d, (xl + 0.5, mref.source.y - 0.2), r"$M_\mathrm{REF}$", valign="top")
    text(d, (xl - 0.35, mref.center.y), wl(3, "n"), halign="right")
    # 레일 → I_REF(화살표 아래) → n1 위 접속점 → M_REF 드레인
    yn1 = mref.drain.y + 0.4
    d.add(elm.Line().down().at((xl, R)).length(0.9))
    d.add(elm.SourceI().down().length(1.3).scale(0.6).label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().toy(yn1)); n1 = dot(d)
    d.add(elm.Line().down().toy(mref.drain.y))
    # 다이오드 연결: n1 위 → 오른쪽 → 아래 게이트 선의 n1 아래 접속점
    xd1 = mref.gate.x + 0.45
    d.add(elm.Line().right().at(n1.center).tox(xd1))
    d.add(elm.Line().down().toy(mref.gate.y)); dot(d)
    d.add(elm.Line().at(mref.gate).to(m1.gate))
    return d
