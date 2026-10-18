"""2013-1 중간 Q4 — 기준: Q4.md '회로 — Fig Q4(a)', '회로 — Fig Q4(b)', '회로 — Fig Q4(c)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 0.0    # 세 패널 레일 높이
CAP_Y = -11.4   # 캡션 높이
LEAD = 1.2      # 입력 원까지 늘이는 가로선 (gate_terminal 앞)


def vdd_rail(d, x_left, x_right):
    rail(d, (x_left, RAIL_Y), (x_right, RAIL_Y))
    d.add(elm.Label().right().at((x_right + 0.2, RAIL_Y + 0.05)).label(r"$V_{DD}$", halign="left"))


def inputs(d, m1, m2):
    """V_in1 원 → 가로선 → M1 게이트, M2 게이트 → 가로선 → V_in2 원."""
    d.add(elm.Line().left().at(m1.gate).length(LEAD))
    gate_terminal(d, d.here, r"$V_\mathrm{in1}$", open_=True)
    d.add(elm.Line().right().at(m2.gate).length(LEAD))
    gate_terminal(d, d.here, r"$V_\mathrm{in2}$", open_=True, right=True)


def mid_label(d, xy, text):
    """두 출력 원 사이의 V_out 라벨."""
    d.add(elm.Label().right().at(xy).label(text))


def tail(d, m1, m2, xm, drop, iss_len):
    """두 소스 → 아래 → 가운데 접속점 → I_SS(화살표 아래) → 접지. 접속점을 돌려준다."""
    ybot = m1.source.y - drop
    d.add(elm.Line().down().at(m1.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(m2.source.x))
    d.add(elm.Line().up().toy(m2.source.y))
    iss = d.add(elm.SourceI().down().at(p.center).length(iss_len).scale(0.6)
                .label(r"$I_\mathrm{SS}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    return p


def panel_a(d, x0):
    xl, xr = x0 + 4.6, x0 + 9.5
    xm = (xl + xr) / 2
    vdd_rail(d, xl - 0.5, xr + 0.3)
    # 위 pmos: M3 좌우 반전(게이트 오른쪽), M4 보통. 소스에서 세로선이 위로 레일
    m3 = pmos(d, at=(xl, RAIL_Y - 0.4), anchor="source", mirror=True)
    m4 = pmos(d, at=(xr, RAIL_Y - 0.4), anchor="source", label=r"$M_\mathrm{4}$")
    for m in (m3, m4):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    d.add(elm.Label().right().at((xl - 0.3, m3.center.y + 0.3)).label(r"$M_\mathrm{3}$", halign="right"))
    # 게이트 공통선과 가운데 게이트 접속점, 아래로 A 높이에서 왼쪽 A 접속점 (다이오드 연결)
    xg = xm - 0.4
    d.add(elm.Line().at(m3.gate).tox(xg)); g = dot(d)
    d.add(elm.Line().at(g.center).tox(m4.gate))
    d.add(elm.Line().down().at(m3.drain).length(0.65)); a = dot(d)
    d.add(elm.Line().down().at(g.center).toy(a.center.y))
    d.add(elm.Line().left().tox(xl))
    d.add(elm.Label().right().at((xl - 0.3, a.center.y - 0.2)).label(r"$A$", halign="right", valign="top"))
    d.add(elm.Line().down().at(m4.drain).length(1.15)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(2.6))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(a.center).toy(RAIL_Y - 4.4))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Label().right().at((xl + 0.3, m1.center.y - 0.25)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Line().down().at(vout.center).toy(RAIL_Y - 4.4))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xr - 0.3, m2.center.y - 0.25)).label(r"$M_\mathrm{2}$", halign="right"))
    inputs(d, m1, m2)
    p = tail(d, m1, m2, xm, 0.45, 2.6)
    d.add(elm.Label().right().at((xm - 0.4, p.center.y - 0.25)).label(r"$P$", halign="right", valign="top"))
    caption(d, (xm - 0.4, CAP_Y), "(a)")


def panel_b(d, x0):
    xl, xr = x0 + 4.6, x0 + 9.6
    xm = (xl + xr) / 2
    vdd_rail(d, xl - 0.4, xr + 0.6)
    # 위 pmos: M3 보통(게이트 왼쪽), M4 좌우 반전. 소스에서 세로선이 위로 레일
    m3 = pmos(d, at=(xl, RAIL_Y - 0.9), anchor="source", label=r"$M_\mathrm{3}$")
    m4 = pmos(d, at=(xr, RAIL_Y - 0.9), anchor="source", mirror=True, label=r"$M_\mathrm{4}$")
    for m in (m3, m4):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    outs = []
    for m, sgn in ((m3, -1), (m4, 1)):
        # 드레인 → 첫 접속점 → 둘째 접속점. 게이트에서 바깥으로 나가 아래로 꺾여 첫 접속점 (다이오드 연결)
        x = m.drain.x
        d.add(elm.Line().down().at(m.drain).length(0.35)); first = dot(d)
        xo = m.gate.x + sgn * 0.5
        d.add(elm.Line().at(m.gate).tox(xo))
        d.add(elm.Line().toy(first.center.y))
        d.add(elm.Line().tox(x))
        d.add(elm.Line().down().at(first.center).length(0.75)); second = dot(d)
        outs.append(second)
    out1, out2 = outs
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.9)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.9)); dot(d, open_=True)
    mid_label(d, (xm, out1.center.y), r"$V_\mathrm{out}$")
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.3))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Label().right().at((xl + 0.3, m1.center.y - 0.25)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Line().down().at(out2.center).length(0.3))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xr - 0.3, m2.center.y - 0.25)).label(r"$M_\mathrm{2}$", halign="right"))
    inputs(d, m1, m2)
    tail(d, m1, m2, xm, 0.45, 2.2)
    caption(d, (xm - 0.4, CAP_Y), "(b)")


def half_c(d, x, mirror):
    """(c)의 한쪽 세로줄 위→아래: 전류원, 첫 접속점, 둘째 접속점, M1/M2, n1/n2 접속점, 전류원, 접지."""
    top = d.add(elm.SourceI().down().at((x, RAIL_Y)).length(2.0).scale(0.6))
    d.add(elm.Line().down().at(top.end).length(0.3)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(1.2)); tap = dot(d)
    d.add(elm.Line().down().at(tap.center).length(0.4))
    m = nmos(d, at=d.here, anchor="drain", mirror=mirror)
    d.add(elm.Line().down().at(m.source).length(0.35)); n = dot(d)
    bot = d.add(elm.SourceI().down().at(n.center).length(2.0).scale(0.6))
    d.add(elm.Ground().at(bot.end).scale(0.8))
    return out, tap, m, n


def panel_c(d, x0):
    xl, xr = x0 + 4.1, x0 + 8.9
    xm = (xl + xr) / 2
    vdd_rail(d, xl - 0.3, xr + 0.6)
    out1, tap1, m1, n1 = half_c(d, xl, False)
    out2, tap2, m2, n2 = half_c(d, xr, True)
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.9)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.9)); dot(d, open_=True)
    mid_label(d, (xm, out1.center.y), r"$V_\mathrm{out}$")
    d.add(Resistor().right().at(tap1.center).to(tap2.center).label(r"$R_\mathrm{DD}$", "bottom", ofst=0.25))
    d.add(Resistor().right().at(n1.center).to(n2.center).label(r"$R_\mathrm{SS}$", "bottom", ofst=0.25))
    d.add(elm.Label().right().at((xl + 0.3, m1.center.y - 0.25)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.3, m2.center.y - 0.25)).label(r"$M_\mathrm{2}$", halign="right"))
    inputs(d, m1, m2)
    caption(d, (xm - 0.4, CAP_Y), "(c)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 18.0)
    panel_c(d, 33.6)
    return d
