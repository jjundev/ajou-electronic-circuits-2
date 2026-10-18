"""2019-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2(a)', '회로 — Fig Q2(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.6    # 두 패널 레일 높이
CAP_Y = 0.0     # 캡션 높이


def tag(d, xy, text, halign, valign="center"):
    d.add(elm.Label().right().at(xy).label(text, halign=halign, valign=valign))


def panel_a(d, x0):
    xref, x5, xr = x0, x0 + 3.3, x0 + 6.0     # I_REF·M_REF 줄, M4·M5 줄, 오른쪽 세로줄
    rail(d, (xref, RAIL_Y), (xr + 0.35, RAIL_Y))
    tag(d, (xr + 0.45, RAIL_Y + 0.05), r"$V_{DD}\mathrm{\ =\ 1.8\ V}$", "left")
    # 오른쪽 세로줄 위→아래: M3, Vout 접속점, M1(좌우 반전), Vin 접속점, M2, 접지
    m3 = pmos(d, at=(xr, RAIL_Y - 0.25), anchor="source", label=r"$M_\mathrm{3}$")
    d.add(elm.Line().up().at(m3.source).toy(RAIL_Y))
    d.add(elm.Line().down().at(m3.drain).length(0.3)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.25))
    m1 = nmos(d, at=d.here, anchor="drain", mirror=True, label=r"$M_\mathrm{1}$")
    gate_terminal(d, m1.gate, r"$V_\mathrm{b}$", right=True)
    d.add(elm.Line().down().at(m1.source).length(0.3)); vin = dot(d)
    d.add(elm.Line().left().at(vin.center).length(0.9))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{in}$", "left", ofst=GAP))
    d.add(elm.Line().down().at(vin.center).length(0.25))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    d.add(elm.Ground().at(m2.source).scale(0.8))
    yg = m2.gate.y      # M_REF·M5·M2 게이트 높이
    dy = m2.drain.y - yg
    # 왼쪽 세로줄 위→아래: I_REF(화살표 아래), 위 n1 접속점, M_REF(좌우 반전), 접지
    mref = nmos(d, at=(xref, yg + dy), anchor="drain", mirror=True)
    tag(d, (xref - 0.35, yg), r"$M_\mathrm{REF}$", "right")
    d.add(elm.Ground().at(mref.source).scale(0.8))
    d.add(elm.Line().up().at(mref.drain).length(0.3)); n1_top = dot(d)
    iref = d.add(elm.SourceI().up().at(n1_top.center).length(1.6).scale(0.6).reverse()
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().up().at(iref.end).toy(RAIL_Y))
    # 다이오드 연결: 위 n1 → 오른쪽 → 아래로 M_REF 게이트 접속점
    xg = mref.gate.x + 0.45
    d.add(elm.Line().right().at(n1_top.center).tox(xg))
    d.add(elm.Line().down().toy(yg)); g_ref = dot(d)
    d.add(elm.Line().left().at(g_ref.center).tox(mref.gate.x))
    # 게이트 가로선: 게이트 접속점 → 아래 n1 접속점 → M5 게이트
    m5 = nmos(d, at=(x5, yg + dy), anchor="drain", label=r"$M_\mathrm{5}$")
    d.add(elm.Ground().at(m5.source).scale(0.8))
    xn1 = xg + 0.85
    d.add(elm.Line().right().at(g_ref.center).tox(xn1)); n1_bot = dot(d)
    d.add(elm.Line().right().at(n1_bot.center).tox(m5.gate.x))
    # 아래 n1 → M5 접지 아래로 → 오른쪽 → M2 왼쪽에서 위로 → M2 게이트
    yloop = m5.source.y - 0.9
    xloop = m2.gate.x - 0.45
    d.add(elm.Line().down().at(n1_bot.center).toy(yloop))
    d.add(elm.Line().right().tox(xloop))
    d.add(elm.Line().up().toy(yg))
    d.add(elm.Line().right().tox(m2.gate.x))
    # M4: 가운데 위 pmos 좌우 반전(다이오드 연결), 소스 → 레일. M4 게이트 접속점 → M3 게이트
    m4 = pmos(d, at=(x5, RAIL_Y - 0.25), anchor="source", mirror=True, label=r"$M_\mathrm{4}$")
    d.add(elm.Line().up().at(m4.source).toy(RAIL_Y))
    xg4 = m4.gate.x + 0.45
    d.add(elm.Line().right().at(m4.gate).tox(xg4)); g4 = dot(d)
    d.add(elm.Line().right().at(g4.center).tox(m3.gate.x))
    d.add(elm.Line().down().at(m4.drain).length(0.4)); n2 = dot(d)
    d.add(elm.Line().down().at(g4.center).toy(n2.center.y))
    d.add(elm.Line().left().tox(x5))
    # M5 드레인 → 긴 세로선 → n2
    d.add(elm.Line().up().at(m5.drain).toy(n2.center.y))
    caption(d, ((xref + xr) / 2, CAP_Y), "(a)")


def half_b(d, x, left):
    """(b) 한쪽 세로줄 위→아래: R_S, M3/M4, 출력 접속점, M1/M2, 소스 접속점, I_SS, 접지."""
    d.add(Resistor().down().at((x, RAIL_Y)).length(1.3)
          .label(r"$R_\mathrm{S}$", "top" if left else "bottom", ofst=GAP))
    mp = pmos(d, at=d.here, anchor="source")
    d.add(elm.Line().down().at(mp.drain).length(0.35)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(0.25))
    mn = nmos(d, at=d.here, anchor="drain", mirror=not left)
    d.add(elm.Line().down().at(mn.source).length(0.2)); ns = dot(d)
    iss = d.add(elm.SourceI().down().at(ns.center).length(1.6).scale(0.6)
                .label(r"$I_\mathrm{SS}$", "top" if left else "bottom", ofst=0.35))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    return mp, out, mn, ns


def panel_b(d, x0):
    xl, xr = x0, x0 + 4.0
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, RAIL_Y), (xr + 0.35, RAIL_Y))
    tag(d, (xr + 0.45, RAIL_Y + 0.05), r"$V_{DD}$", "left")
    m3, out1, m1, n3 = half_b(d, xl, True)
    m4, out2, m2, n4 = half_b(d, xr, False)
    # V_b → M3 게이트, 같은 높이로 M3 막대를 지나 M4 게이트 (게이트 공통선)
    gate_terminal(d, m3.gate, r"$V_\mathrm{b}$")
    d.add(elm.Line().at(m3.gate).to(m4.gate))
    tag(d, (m3.gate.x - 0.05, m3.gate.y + 0.25), r"$M_\mathrm{3}$", "right", "bottom")
    tag(d, (m4.gate.x - 0.05, m4.gate.y + 0.25), r"$M_\mathrm{4}$", "right", "bottom")
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.8)); dot(d, open_=True)
    tag(d, (xm, out1.center.y), r"$V_\mathrm{out}$", "center")
    tag(d, (xl + 0.3, m1.center.y - 0.25), r"$M_\mathrm{1}$", "left")
    tag(d, (xr - 0.3, m2.center.y - 0.25), r"$M_\mathrm{2}$", "right")
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    d.add(Resistor().right().at(n3.center).to(n4.center).label(r"$R_\mathrm{SS}$", "bottom", ofst=GAP))
    caption(d, (xm, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 1.5)
    panel_b(d, 14.0)
    return d
