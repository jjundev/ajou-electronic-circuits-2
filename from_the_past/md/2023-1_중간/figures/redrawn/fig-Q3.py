"""2023-1 중간 Q3 — 기준: Q3.md '회로 — Fig Q3(a)', '회로 — Fig Q3(b)', '회로 — Fig Q3(c)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

L = 0.12        # 소자 사이 짧은 배선
GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.0    # 세 패널 레일 높이
CAP_Y = -0.75   # 캡션 높이


def vdd_rail(d, x_left, x_right):
    rail(d, (x_left, RAIL_Y), (x_right, RAIL_Y))
    d.add(elm.Label().right().at((x_right + 0.1, RAIL_Y + 0.05)).label(r"$V_{DD}$", halign="left"))


def panel_a(d, x0):
    x5, xs = x0, x0 + 3.2          # M5 줄, 오른쪽 세로줄
    vdd_rail(d, x5 - 0.3, xs + 0.3)
    # M5: 왼쪽 위 pmos, 소스가 레일
    m5 = pmos(d, at=(x5, RAIL_Y), anchor="source")
    gate_terminal(d, m5.gate, r"$V_\mathrm{in}$", open_=True)
    # M5 라벨: M5 아래, 드레인 선 왼쪽
    d.add(elm.Label().right().at((x5 - 0.3, m5.drain.y - 0.3))
          .label(r"$M_\mathrm{5}$", halign="right", valign="top"))
    # 오른쪽 세로줄 위→아래: M4, M3, Vout 접속점, M2, n1 접속점, M1, 접지
    m4 = pmos(d, at=(xs, RAIL_Y), anchor="source", label=r"$M_\mathrm{4}$")
    gate_terminal(d, m4.gate, r"$V_\mathrm{b4}$")
    m3 = pmos(d, at=m4.drain, anchor="source", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b3}$")
    d.add(elm.Line().down().at(m3.drain).length(0.3)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(L))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    gate_terminal(d, m2.gate, r"$V_\mathrm{b2}$")
    d.add(elm.Line().down().at(m2.source).length(0.25)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(L))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    gate_terminal(d, m1.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    # M5 드레인 → n1 높이 → 오른쪽 n1 접속점
    d.add(elm.Line().down().at(m5.drain).toy(n1.center))
    d.add(elm.Line().right().tox(xs))
    caption(d, (x0 + 1.25, CAP_Y), "(a)")


def panel_b(d, x0):
    xl, xr = x0, x0 + 3.3
    xm = (xl + xr) / 2
    vdd_rail(d, xl - 0.3, xr + 0.3)
    # 위 pmos 두 개: M3 좌우 반전(게이트 오른쪽), M4 보통. 소스가 레일
    m3 = pmos(d, at=(xl, RAIL_Y), anchor="source", mirror=True)
    m4 = pmos(d, at=(xr, RAIL_Y), anchor="source")
    d.add(elm.Label().right().at((xl - 0.3, m3.center.y - 0.3)).label(r"$M_\mathrm{3}$", halign="right"))
    d.add(elm.Label().right().at((xr + 0.3, m4.center.y - 0.3)).label(r"$M_\mathrm{4}$", halign="left"))
    # 게이트 공통선과 가운데 게이트 접속점, 아래로 A까지 (다이오드 연결)
    d.add(elm.Line().at(m3.gate).tox(xm)); g = dot(d)
    d.add(elm.Line().at(g.center).tox(m4.gate))
    d.add(elm.Line().down().at(m3.drain).length(0.45)); a = dot(d)
    d.add(elm.Line().down().at(g.center).toy(a.center))
    d.add(elm.Line().left().tox(xl))
    d.add(elm.Label().right().at((xl - 0.3, a.center.y - 0.2)).label(r"$A$", halign="right", valign="top"))
    d.add(elm.Line().down().at(m4.drain).length(0.45)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(a.center).length(0.5))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Label().right().at((xl + 0.3, m1.center.y - 0.25)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Line().down().at(vout.center).length(0.5))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xr - 0.3, m2.center.y - 0.25)).label(r"$M_\mathrm{2}$", halign="right"))
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 소스 → 아래 → 가운데 P 접속점 → I_SS → 접지
    ybot = m1.source.y - 0.35
    d.add(elm.Line().down().at(m1.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Label().right().at((xm - 0.6, ybot - 0.28)).label(r"$P$", halign="right", valign="top"))
    iss = d.add(elm.SourceI().down().at(p.center).length(1.3).scale(0.6)
                .label(r"$I_\mathrm{SS}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    caption(d, (xm - 0.4, CAP_Y), "(b)")


def half_c(d, x, mirror):
    """(c)의 한쪽 세로줄 위→아래: 전류원, 첫 접속점, 둘째 접속점, M1/M2, n1/n2 접속점, 전류원, 접지."""
    top = d.add(elm.SourceI().down().at((x, RAIL_Y)).length(1.2).scale(0.6))
    d.add(elm.Line().down().at(top.end).length(0.15)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(0.7)); tap = dot(d)
    d.add(elm.Line().down().at(tap.center).length(L))
    m = nmos(d, at=d.here, anchor="drain", mirror=mirror)
    d.add(elm.Line().down().at(m.source).length(0.25)); n = dot(d)
    bot = d.add(elm.SourceI().down().at(n.center).length(1.1).scale(0.6))
    d.add(elm.Ground().at(bot.end).scale(0.8))
    return out, tap, m, n


def panel_c(d, x0):
    xl, xr = x0, x0 + 4.0
    xm = (xl + xr) / 2
    vdd_rail(d, xl - 0.3, xr + 0.3)
    out1, tap1, m1, n1 = half_c(d, xl, False)
    out2, tap2, m2, n2 = half_c(d, xr, True)
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, out1.center.y)).label(r"$V_\mathrm{out}$"))
    d.add(Resistor().right().at(tap1.center).to(tap2.center).label(r"$R_\mathrm{DD}$", "bottom", ofst=0.25))
    d.add(Resistor().right().at(n1.center).to(n2.center).label(r"$R_\mathrm{SS}$", "bottom", ofst=0.25))
    d.add(elm.Label().right().at((xl + 0.3, m1.center.y - 0.25)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.3, m2.center.y - 0.25)).label(r"$M_\mathrm{2}$", halign="right"))
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    caption(d, (xm - 0.4, CAP_Y), "(c)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 9.9)
    panel_c(d, 19.9)
    return d
