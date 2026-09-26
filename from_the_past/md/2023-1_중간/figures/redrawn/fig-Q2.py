"""2023-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2(a)', '회로 — Fig Q2(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, caption, dot, gate_terminal, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭
VDD_H = 0.32    # 0.8배 T 전원 기호 높이
RAIL_Y = 6.3    # (a) 레일 높이. 접지는 0 근처
CAP_Y = -0.9    # 캡션 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def panel_a(d, x0):
    R = RAIL_Y
    xref, xdio, xm = x0, x0 + 1.0, x0 + 3.0        # I_REF·Q_REF1 줄, 다이오드 연결선, Q_M 줄
    xr2, xx2, xq = x0 + 5.0, x0 + 6.05, x0 + 7.6   # Q_REF2 줄, X2 세로선, Q2·Q1 줄
    rail(d, (xref - 0.3, R), (xq + 0.35, R))
    d.add(elm.Label().right().at((xq + 0.6, R + 0.05)).label(VCC, halign="left"))
    # 왼쪽 세로줄 위→아래: I_REF(화살표 아래), 위 X1 접속점, Q_REF1(좌우 반전), 접지
    iref = d.add(elm.SourceI().down().at((xref, R)).length(1.6).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().at(iref.end).toy(R - 3.9)); x1_top = dot(d)
    d.add(elm.Line().down().at(x1_top.center).length(0.3))
    qref1 = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True)
    d.add(elm.Ground().at(qref1.emitter).scale(0.8))
    d.add(elm.Label().right().at((xref - 0.35, qref1.base.y)).label(r"$Q_\mathrm{REF1}$", halign="right"))
    # Q_M: 보통 방향, 컬렉터가 Q_REF1 컬렉터와 같은 높이
    qm = bjt(d, elm.BjtNpn, (xm, qref1.collector.y), "collector")
    d.add(elm.Ground().at(qm.emitter).scale(0.8))
    d.add(elm.Label().right().at((xm + 0.35, qm.emitter.y + 0.1)).label(r"$Q_\mathrm{M}$", halign="left"))
    # 베이스 공통선 (아래 X1 접속점을 지남) + 다이오드 연결
    d.add(elm.Line().at(qref1.base).tox(xdio)); x1_bot = dot(d)
    d.add(elm.Line().at(x1_bot.center).tox(qm.base))
    d.add(elm.Line().at(x1_top.center).tox(xdio))
    d.add(elm.Line().down().toy(x1_bot.center.y))
    d.add(elm.Label().right().at((xdio + 0.15, x1_bot.center.y - 0.35))
          .label(r"$X_\mathrm{1}$", halign="left", valign="top"))
    # Q_REF2(좌우 반전), Q2(보통): pnp, 이미터가 레일에서 조금 아래
    ye = R - 0.5
    qref2 = bjt(d, elm.BjtPnp, (xr2, ye), "emitter", mirror=True)
    q2 = bjt(d, elm.BjtPnp, (xq, ye), "emitter")
    for q in (qref2, q2):
        d.add(elm.Line().up().at(q.emitter).toy(R))
    d.add(elm.Label().right().at((xr2 - 0.35, qref2.base.y + 0.1)).label(r"$Q_\mathrm{REF2}$", halign="right"))
    d.add(elm.Label().right().at((xq + 0.35, q2.collector.y + 0.15)).label(r"$Q_\mathrm{2}$", halign="left"))
    # X2: 두 pnp 베이스 공통선 가운데 접속점
    d.add(elm.Line().at(qref2.base).tox(xx2)); x2 = dot(d)
    d.add(elm.Line().at(x2.center).tox(q2.base))
    d.add(elm.Label().right().at((xx2 + 0.2, x2.center.y - 0.5))
          .label(r"$X_\mathrm{2}$", halign="left", valign="top"))
    # Q_M 컬렉터 ↑ (I_C,M 화살표) → 오른쪽 → Q_REF2 컬렉터 아래 접속점 → X2 아래에서 위로 X2
    yj = R - 2.7
    d.add(elm.Line().down().at(qref2.collector).toy(yj)); dot(d)
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at((xm, yj)).length(1.0)
          .label(r"$I_\mathrm{C{,}M}$", "top", ofst=GAP))
    d.add(elm.Line().down().toy(qm.collector.y))
    d.add(elm.Line().right().at((xm, yj)).tox(xx2))
    d.add(elm.Line().up().toy(x2.center.y))
    # 오른쪽 세로줄: Q2 컬렉터 → vout 접속점 → Q1 → 접지
    d.add(elm.Line().down().at(q2.collector).length(0.6)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$v_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.7))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    gate_terminal(d, q1.base, r"$v_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(q1.emitter).scale(0.8))
    caption(d, (x0 + 2.9, CAP_Y), "(a)")


def panel_b(d, x0):
    top = RAIL_Y + 1.3
    # 왼쪽 세로줄 위→아래: V_CC, I_1, Vout 접속점, Q1, n1 접속점, Q2, 접지
    d.add(elm.Vdd().at((x0, top - VDD_H)).scale(0.8).label(VCC, "right", ofst=GAP))
    i1 = d.add(elm.SourceI().down().at((x0, top - VDD_H)).length(1.3).scale(0.6)
               .label(r"$I_\mathrm{1}$", "top", ofst=0.3))
    d.add(elm.Line().down().at(i1.end).length(0.2)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.3))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(q1.emitter).length(0.7)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.45))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{2}$")
    gate_terminal(d, q2.base, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(q2.emitter).scale(0.8))
    # Q3: 오른쪽, Q1보다 조금 아래. pnp 좌우 반전(베이스 오른쪽, 이미터 왼쪽 위, 컬렉터 왼쪽 아래)
    xq = x0 + 3.6
    q3 = bjt(d, elm.BjtPnp, (xq, n1.center.y + 0.15), "collector", mirror=True)
    d.add(elm.Label().right().at((xq - 0.35, q3.center.y - 0.2)).label(r"$Q_\mathrm{3}$", halign="right"))
    d.add(elm.Line().up().at(q3.emitter).length(0.35))
    d.add(elm.Vdd().scale(0.8).label(VCC, "right", ofst=GAP))
    gate_terminal(d, q3.base, r"$V_\mathrm{b3}$", right=True)
    d.add(elm.Line().down().at(q3.collector).toy(n1.center))
    d.add(elm.Line().left().tox(n1.center))
    caption(d, (x0 + 3.2, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 13.5)
    return d
