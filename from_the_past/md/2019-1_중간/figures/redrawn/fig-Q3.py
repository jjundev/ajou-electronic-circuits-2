"""2019-1 중간 Q3 — 기준: Q3.md '회로 — Fig Q3(a)', '회로 — Fig Q3(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, rail

GAP = 0.2           # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭
VDD_H = 0.32        # 0.8배 T 전원 기호 높이
RAIL_Y = 8.6        # (b) 레일 높이, (a) T 기호 높이 기준
CAP_Y = -0.2        # 캡션 높이


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


def panel_a(d, x0):
    top = RAIL_Y
    # 왼쪽 세로줄 위→아래: V_CC, I_1, Vout 접속점, Q1, n1 접속점, Q2, 접지
    d.add(elm.Vdd().at((x0, top - VDD_H)).scale(0.8).label(VCC, "right", ofst=GAP))
    i1 = d.add(elm.SourceI().down().at((x0, top - VDD_H)).length(1.5).scale(0.6)
               .label(r"$I_\mathrm{1}$", "top", ofst=0.3))
    d.add(elm.Line().down().at(i1.end).length(0.2)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.3))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(q1.emitter).length(0.6)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.45))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{2}$")
    gate_terminal(d, q2.base, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(q2.emitter).scale(0.8))
    # Q3: 오른쪽, Q1보다 조금 아래. pnp 좌우 반전(베이스 오른쪽, 이미터 왼쪽 위, 컬렉터 왼쪽 아래)
    xq = x0 + 4.4
    q3 = bjt(d, elm.BjtPnp, (xq, n1.center.y + 0.45), "collector", mirror=True)
    tag(d, (xq - 0.3, q3.center.y - 0.2), r"$Q_\mathrm{3}$", "right")
    d.add(elm.Line().up().at(q3.emitter).length(0.35))
    d.add(elm.Vdd().scale(0.8).label(VCC, "right", ofst=GAP))
    gate_terminal(d, q3.base, r"$V_\mathrm{b3}$", right=True)
    d.add(elm.Line().down().at(q3.collector).toy(n1.center.y))
    d.add(elm.Line().left().tox(x0))
    caption(d, (x0 + 2.2, CAP_Y), "(a)")


def half_b(d, x, left):
    """(b) 한쪽 세로줄 위→아래: 다이오드 연결 npn, R_C, 출력 접속점, 입력 npn, 이미터 접속점, I_EE, 접지."""
    s = 1 if left else -1
    q_top = bjt(d, elm.BjtNpn, (x, RAIL_Y - 0.3), "collector", mirror=not left,
                label=r"$Q_\mathrm{3}$" if left else r"$Q_\mathrm{4}$", loc="right" if left else "left")
    d.add(elm.Line().up().at(q_top.collector).toy(RAIL_Y))
    d.add(elm.Line().at(q_top.base).tox(q_top.base.x - s * 0.4))
    d.add(elm.Line().up().toy(RAIL_Y))
    d.add(elm.Line().down().at(q_top.emitter).length(0.2))
    d.add(Resistor().down().length(1.4)
          .label(r"$R_\mathrm{C}$", "top" if left else "bottom", ofst=GAP))
    d.add(elm.Line().down().length(0.2)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(0.3))
    q_in = bjt(d, elm.BjtNpn, d.here, "collector", mirror=not left)
    tag(d, (x + s * 0.3, q_in.center.y - 0.15), r"$Q_\mathrm{1}$" if left else r"$Q_\mathrm{2}$",
        "left" if left else "right")
    gate_terminal(d, q_in.base, r"$V_\mathrm{in1}$" if left else r"$V_\mathrm{in2}$", open_=True, right=not left)
    d.add(elm.Line().down().at(q_in.emitter).length(0.25)); ne = dot(d)
    iee = d.add(elm.SourceI().down().at(ne.center).length(1.5).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "top" if left else "bottom", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return out, ne


def panel_b(d, x0):
    xl, xr = x0, x0 + 4.4
    rail(d, (xl - 1.3, RAIL_Y), (xr + 1.3, RAIL_Y))
    tag(d, (xr + 1.45, RAIL_Y + 0.05), VCC, "left")
    out1, n3 = half_b(d, xl, True)
    out2, n4 = half_b(d, xr, False)
    d.add(elm.Line().right().at(out1.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(1.0)); dot(d, open_=True)
    tag(d, ((xl + xr) / 2, out1.center.y), r"$V_\mathrm{out}$", "center")
    d.add(Resistor().right().at(n3.center).to(n4.center).label(r"$R_\mathrm{E}$", "bottom", ofst=GAP))
    caption(d, ((xl + xr) / 2, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 1.5)
    panel_b(d, 11.6)
    return d
