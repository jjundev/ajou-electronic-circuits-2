"""2018-2 중간 Q1 — 기준: Q1.md '회로 — Fig Q1(a)', '회로 — Fig Q1(b)', '회로 — Fig Q1(c)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, rail

GAP = 0.2           # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭
VDD_H = 0.32        # 0.8배 T 전원 기호 높이
RAIL_Y = 9.0        # (a)·(b) 레일 높이
CAP_Y = 0.4         # 캡션 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def tag(d, xy, text, halign, valign="center"):
    d.add(elm.Label().right().at(xy).label(text, halign=halign, valign=valign))


def vcc_rail(d, x_left, x_right):
    rail(d, (x_left, RAIL_Y), (x_right, RAIL_Y))
    tag(d, (x_right + 0.15, RAIL_Y + 0.05), VCC, "left")


def facing_outputs(d, out1, out2, length):
    """두 출력 접속점에서 가로선이 안쪽 개방 원으로, 두 원 사이 가운데에 V_out."""
    d.add(elm.Line().right().at(out1.center).length(length)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(length)); dot(d, open_=True)
    tag(d, ((out1.center.x + out2.center.x) / 2, out1.center.y), r"$V_\mathrm{out}$", "center")


def half_a(d, x, left):
    """(a) 한쪽 세로줄 위→아래: 다이오드 연결 npn, R_C, 출력 접속점, 입력 npn, 이미터 접속점, I_EE, 접지."""
    s = 1 if left else -1
    q_top = bjt(d, elm.BjtNpn, (x, RAIL_Y - 0.3), "collector", mirror=not left,
                label=r"$Q_\mathrm{3}$" if left else r"$Q_\mathrm{4}$", loc="right" if left else "left")
    d.add(elm.Line().up().at(q_top.collector).toy(RAIL_Y))
    d.add(elm.Line().at(q_top.base).tox(q_top.base.x - s * 0.4))
    d.add(elm.Line().up().toy(RAIL_Y))
    d.add(elm.Line().down().at(q_top.emitter).length(0.2))
    d.add(Resistor().down().length(1.5)
          .label(r"$R_\mathrm{C}$", "top" if left else "bottom", ofst=GAP))
    d.add(elm.Line().down().length(0.2)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(0.35))
    q_in = bjt(d, elm.BjtNpn, d.here, "collector", mirror=not left)
    tag(d, (x + s * 0.3, q_in.center.y - 0.15), r"$Q_\mathrm{1}$" if left else r"$Q_\mathrm{2}$",
        "left" if left else "right")
    gate_terminal(d, q_in.base, r"$V_\mathrm{in1}$" if left else r"$V_\mathrm{in2}$", open_=True, right=not left)
    d.add(elm.Line().down().at(q_in.emitter).length(0.25)); ne = dot(d)
    iee = d.add(elm.SourceI().down().at(ne.center).length(1.6).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "top" if left else "bottom", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return out, ne


def panel_a(d, x0):
    xl, xr = x0, x0 + 4.4
    vcc_rail(d, xl - 1.3, xr + 1.3)
    out1, n3 = half_a(d, xl, True)
    out2, n4 = half_a(d, xr, False)
    facing_outputs(d, out1, out2, 1.0)
    d.add(Resistor().right().at(n3.center).to(n4.center).label(r"$R_\mathrm{E}$", "bottom", ofst=GAP))
    caption(d, ((xl + xr) / 2, CAP_Y), "(a)")


def panel_b(d, x0):
    xl, xr = x0, x0 + 4.2
    xm = (xl + xr) / 2
    vcc_rail(d, xl - 0.3, xr + 0.3)
    # Q3, Q4: pnp 보통 방향, 이미터 → 레일. V_b → Q3 베이스 → Q3 막대를 지나 Q4 베이스 (공통선)
    q3 = bjt(d, elm.BjtPnp, (xl, RAIL_Y - 0.3), "emitter")
    q4 = bjt(d, elm.BjtPnp, (xr, RAIL_Y - 0.3), "emitter")
    for q in (q3, q4):
        d.add(elm.Line().up().at(q.emitter).toy(RAIL_Y))
    gate_terminal(d, q3.base, r"$V_\mathrm{b}$")
    d.add(elm.Line().at(q3.base).to(q4.base))
    tag(d, (xl - 0.3, q3.collector.y - 0.1), r"$Q_\mathrm{3}$", "right", "top")
    tag(d, (xr - 0.3, q4.collector.y - 0.1), r"$Q_\mathrm{4}$", "right", "top")
    # 첫 접속점(출력 원), 둘째 접속점(R_1–R_2)
    d.add(elm.Line().down().at(q3.collector).length(1.05)); out1 = dot(d)
    d.add(elm.Line().down().at(q4.collector).length(1.05)); out2 = dot(d)
    facing_outputs(d, out1, out2, 0.8)
    d.add(elm.Line().down().at(out1.center).length(1.2)); s1 = dot(d)
    d.add(elm.Line().down().at(out2.center).length(1.2)); s2 = dot(d)
    d.add(Resistor().right().at(s1.center).tox(xm).label(r"$R_\mathrm{1}$", "top", ofst=0.15))
    d.add(Resistor().right().tox(xr).label(r"$R_\mathrm{2}$", "top", ofst=0.15))
    # 입력 쌍: Q1 보통, Q2 좌우 반전
    d.add(elm.Line().down().at(s1.center).length(0.3))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector")
    d.add(elm.Line().down().at(s2.center).length(0.3))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True)
    tag(d, (xl + 0.3, q1.center.y - 0.15), r"$Q_\mathrm{1}$", "left")
    tag(d, (xr - 0.3, q2.center.y - 0.15), r"$Q_\mathrm{2}$", "right")
    gate_terminal(d, q1.base, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, q2.base, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 이미터 → 아래 → 가운데 P → I_EE → 접지
    ybot = q1.emitter.y - 0.45
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox(xm)); p = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q2.emitter.y))
    tag(d, (xm - 0.7, ybot - 0.3), r"$P$", "right", "top")
    iee = d.add(elm.SourceI().down().at(p.center).length(1.2).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    caption(d, (xm, CAP_Y), "(b)")


def panel_c(d, x0):
    top = RAIL_Y - 0.2
    d.add(elm.Vdd().at((x0, top - VDD_H)).scale(0.8).label(VCC, "right", ofst=GAP))
    i1 = d.add(elm.SourceI().down().at((x0, top - VDD_H)).length(1.6).scale(0.6)
               .label(r"$I_\mathrm{1}$", "top", ofst=0.35))
    d.add(elm.Line().down().at(i1.end).length(0.25)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.0))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$v_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.45))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{2}$")
    gate_terminal(d, q2.base, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(q2.emitter).length(0.9))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    gate_terminal(d, q1.base, r"$v_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(q1.emitter).scale(0.8))
    caption(d, (x0, CAP_Y), "(c)")


def draw():
    d = new_drawing()
    panel_a(d, 2.2)
    panel_b(d, 12.6)
    panel_c(d, 22.0)
    return d
