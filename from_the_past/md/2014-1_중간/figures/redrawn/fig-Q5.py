"""2014-1 중간 Q5 — 기준: Q5.md '회로 — Fig Q5(a)', '회로 — Fig Q5(b)', '회로 — Fig Q5(c)', '회로 — Fig Q5(d)'."""
import schemdraw.elements as elm
from schem_style import Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 0.0    # 네 패널 레일 높이
CAP_Y = -10.9   # 캡션 높이
JOG = 0.45      # 레일·드레인에서 꺾여 들어가는 짧은 가로선


def vdd_rail(d, x_left, x_right):
    rail(d, (x_left, RAIL_Y), (x_right, RAIL_Y))
    d.add(elm.Label().right().at((x_right + 0.15, RAIL_Y + 0.1)).label(r"$V_{DD}$", halign="left", valign="bottom"))


def label(d, xy, text, ha="center", va="center"):
    d.add(elm.Label().right().at(xy).label(text, halign=ha, valign=va))


def facing_outputs(d, j1, j2):
    """두 출력 원이 가운데에서 마주 보고 그 사이에 V_out."""
    d.add(elm.Line().right().at(j1.center).length(0.6)); dot(d, open_=True)
    d.add(elm.Line().left().at(j2.center).length(0.6)); dot(d, open_=True)
    label(d, ((j1.center.x + j2.center.x) / 2, j1.center.y), r"$V_\mathrm{out}$")


def input_pair(d, top1, top2, gap=0.3):
    """top1/top2 아래로 gap만큼 내려 M1(보통)·M2(좌우 반전), V_in1·V_in2 원."""
    d.add(elm.Line().down().at(top1).length(gap))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Line().down().at(top2).length(gap))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    return m1, m2


def tail(d, m1, m2, drop, iss_len, text=r"$I_\mathrm{SS}$"):
    """두 소스 → 아래 → 가운데 접속점 → I_SS(화살표 아래) → 접지."""
    xm = (m1.source.x + m2.source.x) / 2
    ybot = m1.source.y - drop
    d.add(elm.Line().down().at(m1.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n = dot(d)
    d.add(elm.Line().right().tox(m2.source.x))
    d.add(elm.Line().up().toy(m2.source.y))
    iss = d.add(elm.SourceI().down().at(n.center).length(iss_len).scale(0.6)
                .label(text, "bottom", ofst=0.35))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    return n


def panel_a(d, x0):
    c5 = x0 + 2.4
    c3 = c5 + 1.9
    c4 = c3 + 3.0
    c6 = c4 + 1.9
    vdd_rail(d, c5 - 0.3, c6 + 0.3)
    # M5: pmos 보통(게이트 왼쪽 ← V_b), M6: pmos 좌우 반전(게이트 오른쪽 → V_b). 소스가 레일로
    ys = RAIL_Y - 0.4
    m5 = pmos(d, at=(c5, ys), anchor="source")
    m6 = pmos(d, at=(c6, ys), anchor="source", mirror=True)
    for m in (m5, m6):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    gate_terminal(d, m5.gate, r"$V_\mathrm{b}$")
    gate_terminal(d, m6.gate, r"$V_\mathrm{b}$", right=True)
    # M3: nmos 보통, M4: nmos 좌우 반전. 드레인이 레일로, 게이트도 레일에서 내려온 선
    m3 = nmos(d, at=(c3, ys), anchor="drain", label=r"$M_\mathrm{3}$")
    m4 = nmos(d, at=(c4, ys), anchor="drain", mirror=True, label=r"$M_\mathrm{4}$")
    for m, sgn in ((m3, -1), (m4, 1)):
        d.add(elm.Line().up().at(m.drain).toy(RAIL_Y))
        xg = m.gate.x + sgn * JOG
        d.add(elm.Line().down().at((xg, RAIL_Y)).toy(m.gate.y))
        d.add(elm.Line().tox(m.gate.x))
    # 출력 접속점: 위 M3/M4 소스, 옆 M5/M6 드레인 선, 아래 M1/M2, 안쪽 출력 원
    yo = m3.source.y - 0.45
    d.add(elm.Line().down().at(m3.source).toy(yo)); o1 = dot(d)
    d.add(elm.Line().down().at(m4.source).toy(yo)); o2 = dot(d)
    d.add(elm.Line().down().at(m5.drain).toy(yo)); d.add(elm.Line().right().tox(c3))
    d.add(elm.Line().down().at(m6.drain).toy(yo)); d.add(elm.Line().left().tox(c4))
    label(d, (c5 - 0.3, m5.drain.y - 0.1), r"$M_\mathrm{5}$", "right", "top")
    label(d, (c6 + 0.3, m6.drain.y - 0.1), r"$M_\mathrm{6}$", "left", "top")
    facing_outputs(d, o1, o2)
    m1, m2 = input_pair(d, o1.center, o2.center)
    label(d, (c3 + 0.3, m1.center.y - 0.25), r"$M_\mathrm{1}$", "left")
    label(d, (c4 - 0.3, m2.center.y - 0.25), r"$M_\mathrm{2}$", "right")
    tail(d, m1, m2, 0.35, 1.5)
    caption(d, ((c3 + c4) / 2 - 0.3, CAP_Y), "(a)")


def panel_b(d, x0):
    cl = x0 + 2.65
    cr = cl + 3.6
    xm = (cl + cr) / 2
    vdd_rail(d, cl - 0.3, cr + 0.3)
    # M3: pmos 좌우 반전, M4: pmos 보통. 레일에서 내려온 세로선이 꺾여 소스로
    ys = RAIL_Y - 0.4
    m3 = pmos(d, at=(cl + JOG, ys), anchor="source", mirror=True)
    m4 = pmos(d, at=(cr - JOG, ys), anchor="source")
    for m, x in ((m3, cl), (m4, cr)):
        d.add(elm.Line().down().at((x, RAIL_Y)).toy(ys))
        d.add(elm.Line().tox(m.source.x))
    label(d, (cl - 0.25, m3.center.y), r"$M_\mathrm{3}$", "right")
    label(d, (cr + 0.25, m4.center.y), r"$M_\mathrm{4}$", "left")
    # 게이트 공통선과 가운데 n1 위 접속점
    d.add(elm.Line().at(m3.gate).tox(xm)); n1t = dot(d)
    d.add(elm.Line().at(n1t.center).tox(m4.gate))
    # 드레인에서 바깥으로 꺾여 세로선 → out 위 접속점 (저항 줄)
    yr = m3.drain.y - 0.45
    tops = []
    for m, x in ((m3, cl), (m4, cr)):
        d.add(elm.Line().at(m.drain).tox(x))
        d.add(elm.Line().down().toy(yr)); tops.append(dot(d))
    d.add(elm.Line().down().at(n1t.center).toy(yr)); n1b = dot(d)
    d.add(Resistor().right().at(tops[0].center).to(n1b.center).label(r"$R_\mathrm{1}$", "bottom", ofst=0.25))
    d.add(Resistor().right().at(n1b.center).to(tops[1].center).label(r"$R_\mathrm{2}$", "bottom", ofst=0.25))
    # out 아래 접속점 (마주 보는 두 원)
    yo = yr - 1.5
    d.add(elm.Line().down().at(tops[0].center).toy(yo)); o1 = dot(d)
    d.add(elm.Line().down().at(tops[1].center).toy(yo)); o2 = dot(d)
    facing_outputs(d, o1, o2)
    m1, m2 = input_pair(d, o1.center, o2.center, 0.6)
    label(d, (cl + 0.3, m1.center.y - 0.25), r"$M_\mathrm{1}$", "left")
    label(d, (cr - 0.3, m2.center.y - 0.25), r"$M_\mathrm{2}$", "right")
    tail(d, m1, m2, 0.35, 1.5)
    caption(d, (xm - 0.3, CAP_Y), "(b)")


def panel_c(d, x0):
    cl = x0 + 2.65
    c3 = cl + 1.4
    c4 = c3 + 3.0
    cr = c4 + 1.4
    vdd_rail(d, cl - 0.3, cr + 0.3)
    # 두 세로줄 위: 전류원(화살표 아래), out 위 접속점(마주 보는 두 원), out 아래 접속점
    tops, bots = [], []
    for x in (cl, cr):
        src = d.add(elm.SourceI().down().at((x, RAIL_Y)).length(1.3).scale(0.6))
        d.add(elm.Line().down().at(src.end).length(0.25)); tops.append(dot(d))
        d.add(elm.Line().down().at(tops[-1].center).length(0.85)); bots.append(dot(d))
    facing_outputs(d, tops[0], tops[1])
    m1, m2 = input_pair(d, bots[0].center, bots[1].center)
    label(d, (cl - 0.3, m1.source.y + 0.05), r"$M_\mathrm{1}$", "right", "top")
    label(d, (cr + 0.3, m2.source.y + 0.05), r"$M_\mathrm{2}$", "left", "top")
    # M3: nmos 좌우 반전, M4: nmos 보통. 출력 아래 접속점에서 가로선 → 드레인 접속점 → 끝에서 아래로 게이트
    m3 = nmos(d, at=(c3, m1.drain.y), anchor="drain", mirror=True)
    m4 = nmos(d, at=(c4, m2.drain.y), anchor="drain")
    for m, b, sgn in ((m3, bots[0], 1), (m4, bots[1], -1)):
        d.add(elm.Line().at(b.center).tox(m.drain.x)); j = dot(d)
        d.add(elm.Line().down().at(j.center).toy(m.drain.y))
        xg = m.gate.x + sgn * JOG
        d.add(elm.Line().at(j.center).tox(xg))
        d.add(elm.Line().down().toy(m.gate.y))
        d.add(elm.Line().tox(m.gate.x))
    label(d, (c3 - 0.3, m3.center.y - 0.25), r"$M_\mathrm{3}$", "right")
    label(d, (c4 + 0.3, m4.center.y - 0.25), r"$M_\mathrm{4}$", "left")
    # M3·M4 소스 → 가로선 → Q 접속점 → I_SS2 → 접지
    yq = m3.source.y - 0.25
    d.add(elm.Line().down().at(m3.source).toy(yq))
    d.add(elm.Line().right().tox((c3 + c4) / 2)); q = dot(d)
    d.add(elm.Line().right().tox(c4))
    d.add(elm.Line().up().toy(m4.source.y))
    label(d, (q.center.x - 0.35, yq - 0.3), r"$Q$", "right", "top")
    # I_SS2는 P 가로선 아래에 둔다 (Q에서 내려가는 선이 P 가로선과 점 없이 교차)
    yp = yq - 1.3
    d.add(elm.Line().down().at(q.center).toy(yp - 0.35))
    iss2 = d.add(elm.SourceI().down().length(1.3).scale(0.6)
                 .label(r"$I_\mathrm{SS2}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iss2.end).scale(0.8))
    # M1 소스 → P 접속점 → I_SS1 → 접지. P에서 Q 아래 높이로 오른쪽 끝까지, 위로 M2 소스 (I_SS2 선과 점 없이 교차)
    d.add(elm.Line().down().at(m1.source).toy(yp)); p = dot(d)
    label(d, (cl - 0.35, yp + 0.05), r"$P$", "right", "bottom")
    d.add(elm.Line().right().at(p.center).tox(cr))
    d.add(elm.Line().up().toy(m2.source.y))
    iss1 = d.add(elm.SourceI().down().at(p.center).length(1.3).scale(0.6)
                 .label(r"$I_\mathrm{SS1}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iss1.end).scale(0.8))
    caption(d, ((cl + cr) / 2 - 0.3, CAP_Y), "(c)")


def panel_d(d, x0):
    cl = x0 + 2.65
    cr = cl + 3.2
    vdd_rail(d, cl - 0.3, cr + 0.3)
    ys = RAIL_Y - 0.7
    # 두 세로줄 위→아래: M7/M8, M5/M6, out 접속점, M3/M4, M1/M2
    m7 = pmos(d, at=(cl, ys), anchor="source")
    m8 = pmos(d, at=(cr, ys), anchor="source")
    for m in (m7, m8):
        d.add(elm.Line().up().at(m.source).toy(RAIL_Y))
    m5 = nmos(d, at=m7.drain, anchor="drain")
    m6 = nmos(d, at=m8.drain, anchor="drain")
    d.add(elm.Line().down().at(m5.source).length(0.4)); o1 = dot(d)
    d.add(elm.Line().down().at(m6.source).length(0.4)); o2 = dot(d)
    facing_outputs(d, o1, o2)
    d.add(elm.Line().down().at(o1.center).length(0.4))
    m3 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Line().down().at(o2.center).length(0.4))
    m4 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{4}$")
    m1 = nmos(d, at=m3.source, anchor="drain", label=r"$M_\mathrm{1}$")
    m2 = nmos(d, at=m4.source, anchor="drain", mirror=True, label=r"$M_\mathrm{2}$")
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 게이트 공통선 3개: 점 단자 → 왼쪽 소자 게이트 → 오른쪽 소자 게이트 (왼쪽 소자를 가로지름)
    for ml, mr, text in ((m7, m8, r"$V_\mathrm{b3}$"), (m5, m6, r"$V_\mathrm{b2}$"), (m3, m4, r"$V_\mathrm{b1}$")):
        gate_terminal(d, ml.gate, text)
        d.add(elm.Line().right().at(ml.gate).tox(mr.gate))
    # 라벨: M7·M8 위(게이트 판 왼쪽 위), M5·M6 아래, M3 위 왼쪽
    for m, text in ((m7, r"$M_\mathrm{7}$"), (m8, r"$M_\mathrm{8}$")):
        label(d, (m.gate.x + 0.2, m.gate.y + 0.65), text, "right")
    # M5·M6: 게이트 공통선 아래, 게이트 판 왼쪽. M3: 게이트 공통선 위, 게이트 판 왼쪽
    for m, text in ((m5, r"$M_\mathrm{5}$"), (m6, r"$M_\mathrm{6}$")):
        label(d, (m.gate.x + 0.2, m.gate.y - 0.65), text, "right")
    label(d, (m3.gate.x + 0.2, m3.gate.y + 0.5), r"$M_\mathrm{3}$", "right")
    tail(d, m1, m2, 0.25, 1.2)
    caption(d, ((cl + cr) / 2 - 0.3, CAP_Y), "(d)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 11.9)
    panel_c(d, 21.1)
    panel_d(d, 32.8)
    return d
