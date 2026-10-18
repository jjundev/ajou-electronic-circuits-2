"""2017-1 중간 (C030) Q3 — 기준: Q3.md '회로 — Fig Q3'."""
import schemdraw.elements as elm
from schem_style import GATE_LEAD, dot, new_drawing, rail

GAP = 0.2           # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭
JOG = 0.3           # Q3·Q4 이미터와 Q1·Q2 컬렉터 사이 꺾인 선의 가로 폭


def bjt(d, cls, at, anchor, mirror=False):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    return d.add(e.anchor(anchor).at(at))


def wire_end(d, at, label, right=False):
    """단자 기호 없는 선 끝 (원본의 V_in1·V_in2). 선 끝 바깥에 라벨."""
    line = elm.Line().at(at).length(GATE_LEAD + 0.35)
    end = d.add(line.right() if right else line.left()).end
    d.add(elm.Label().right().at((end[0] + (0.2 if right else -0.2), end[1]))
          .label(label, halign="left" if right else "right"))


def tag(d, xy, text, halign):
    d.add(elm.Label().right().at(xy).label(text, halign=halign))


def base_pair(d, left, right, label):
    """두 베이스를 잇는 가로선과 그 위 가운데 바이어스 라벨 (단자 기호 없음)."""
    d.add(elm.Line().at(left.base).to(right.base))
    xm = (left.base.x + right.base.x) / 2
    d.add(elm.Label().right().at((xm, left.base.y + 0.2)).label(label, valign="bottom"))


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 3.7, 12.0
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, rail_y), (xr + 0.35, rail_y))
    d.add(elm.Label().right().at((xr + 0.45, rail_y - 0.15)).label(VCC, halign="left", valign="top"))
    # 위 pnp 두 개: Q7 좌우 반전, Q8 보통. 이미터 → 레일
    ye = rail_y - 0.6
    q7 = bjt(d, elm.BjtPnp, (xl, ye), "emitter", mirror=True)
    q8 = bjt(d, elm.BjtPnp, (xr, ye), "emitter")
    for q in (q7, q8):
        d.add(elm.Line().up().at(q.emitter).toy(rail_y))
    tag(d, (xl - 0.3, q7.center.y), r"$Q_\mathrm{7}$", "right")
    tag(d, (xr + 0.3, q8.center.y), r"$Q_\mathrm{8}$", "left")
    base_pair(d, q7, q8, r"$V_\mathrm{b3}$")
    # Q5 좌우 반전, Q6 보통 (npn, 이미터가 아래 출력 쪽)
    q5 = bjt(d, elm.BjtNpn, (xl, q7.collector.y - 1.0), "collector", mirror=True)
    q6 = bjt(d, elm.BjtNpn, (xr, q8.collector.y - 1.0), "collector")
    d.add(elm.Line().at(q7.collector).to(q5.collector))
    d.add(elm.Line().at(q8.collector).to(q6.collector))
    tag(d, (xl - 0.3, q5.center.y + 0.35), r"$Q_\mathrm{5}$", "right")
    tag(d, (xr + 0.3, q6.center.y + 0.35), r"$Q_\mathrm{6}$", "left")
    base_pair(d, q5, q6, r"$V_\mathrm{b2}$")
    # 출력 접속점과 마주 보는 짧은 출력선, 그 사이 + V_out −
    d.add(elm.Line().down().at(q5.emitter).length(0.8)); out1 = dot(d)
    d.add(elm.Line().down().at(q6.emitter).length(0.8)); out2 = dot(d)
    e1 = d.add(elm.Line().right().at(out1.center).length(0.35)).end
    e2 = d.add(elm.Line().left().at(out2.center).length(0.35)).end
    d.add(elm.Label().right().at((e1[0] + 0.03, e1[1])).label(r"$+$", halign="left"))
    d.add(elm.Label().right().at((e2[0] - 0.03, e2[1] + 0.1)).label(r"$-$", halign="right", valign="bottom"))
    d.add(elm.Label().right().at((xm + 0.05, e1[1])).label(r"$V_\mathrm{out}$"))
    # Q3 좌우 반전, Q4 보통
    q3 = bjt(d, elm.BjtNpn, (xl, out1.center.y - 0.8), "collector", mirror=True)
    q4 = bjt(d, elm.BjtNpn, (xr, out2.center.y - 0.8), "collector")
    d.add(elm.Line().at(out1.center).to(q3.collector))
    d.add(elm.Line().at(out2.center).to(q4.collector))
    tag(d, (xl - 0.3, q3.center.y - 0.35), r"$Q_\mathrm{3}$", "right")
    tag(d, (xr + 0.3, q4.center.y - 0.35), r"$Q_\mathrm{4}$", "left")
    base_pair(d, q3, q4, r"$V_\mathrm{b1}$")
    # Q3·Q4 이미터 → 꺾인 선 → Q1·Q2 컬렉터 (Q1·Q2는 바깥쪽으로 JOG만큼)
    yj = q3.emitter.y - 0.5
    q1 = bjt(d, elm.BjtNpn, (xl - JOG, yj - 0.7), "collector")
    q2 = bjt(d, elm.BjtNpn, (xr + JOG, yj - 0.7), "collector", mirror=True)
    for q_up, q_dn in ((q3, q1), (q4, q2)):
        d.add(elm.Line().down().at(q_up.emitter).toy(yj))
        d.add(elm.Line().tox(q_dn.collector.x))
        d.add(elm.Line().down().toy(q_dn.collector.y))
    tag(d, (q1.collector.x + 0.3, q1.center.y - 0.15), r"$Q_\mathrm{1}$", "left")
    tag(d, (q2.collector.x - 0.3, q2.center.y - 0.15), r"$Q_\mathrm{2}$", "right")
    wire_end(d, q1.base, r"$V_\mathrm{in1}$")
    wire_end(d, q2.base, r"$V_\mathrm{in2}$", right=True)
    # 두 이미터 → 아래 → 가운데 n5 접속점 → I_EE(화살표 아래) → 접지
    ybot = q1.emitter.y - 0.8
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n5 = dot(d)
    d.add(elm.Line().right().tox(q2.emitter.x))
    d.add(elm.Line().up().toy(q2.emitter.y))
    iee = d.add(elm.SourceI().down().at(n5.center).length(2.4).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return d
