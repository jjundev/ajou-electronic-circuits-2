"""2017-1 중간 (C030) Q3 2) — 기준: Q3.md '회로 — Fig Q3-2'."""
import schemdraw.elements as elm
from schem_style import GATE_LEAD, Resistor, dot, new_drawing, rail

GAP = 0.2           # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭
RAIL_Y = 10.0       # 레일 높이
LOOP = 1.45         # 세로줄에서 베이스–컬렉터 고리 바깥 세로선까지 가로 거리


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


def tag(d, xy, text, halign, valign="center"):
    d.add(elm.Label().right().at(xy).label(text, halign=halign, valign=valign))


def half(d, x, sign):
    """한쪽 세로줄 위→아래: pnp, 첫 접속점(고리 R_1), 둘째 접속점, npn, 이미터 접속점, I_EE, 접지.

    sign = +1 왼쪽(Q7·Q1), −1 오른쪽(Q8·Q2). Q7은 좌우 반전, Q1은 보통; 오른쪽은 그 반대.
    """
    left = sign > 0
    qp = bjt(d, elm.BjtPnp, (x, RAIL_Y - 0.7), "emitter", mirror=left)
    d.add(elm.Line().up().at(qp.emitter).toy(RAIL_Y))
    d.add(elm.Line().down().at(qp.collector).length(1.3)); first = dot(d)
    # 베이스 → 가로선 → 아래로 꺾여 첫 접속점 높이 → 가로 R_1 → 첫 접속점 (사각 고리)
    xo = x + sign * LOOP
    d.add(elm.Line().at(qp.base).tox(xo))
    d.add(elm.Line().toy(first.center.y))
    d.add(Resistor().at(first.center).tox(xo).label(r"$R_\mathrm{1}$", "top", ofst=0.15))
    d.add(elm.Line().down().at(first.center).length(0.9)); second = dot(d)
    d.add(elm.Line().down().at(second.center).length(1.2))
    qn = bjt(d, elm.BjtNpn, d.here, "collector", mirror=not left)
    d.add(elm.Line().down().at(qn.emitter).length(0.45)); ne = dot(d)
    iee = d.add(elm.SourceI().down().at(ne.center).length(2.4).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "top" if left else "bottom", ofst=0.35))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return qp, second, qn, ne


def draw():
    d = new_drawing()
    xl, xr = 0, 4.3
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, RAIL_Y), (xr + 0.35, RAIL_Y))
    d.add(elm.Label().right().at((xr + 0.45, RAIL_Y - 0.15)).label(VCC, halign="left", valign="top"))
    q7, out1, q1, n3 = half(d, xl, +1)
    q8, out2, q2, n4 = half(d, xr, -1)
    tag(d, (xl - 0.3, q7.center.y - 0.1), r"$Q_\mathrm{7}$", "right")
    tag(d, (xr + 0.3, q8.center.y - 0.1), r"$Q_\mathrm{8}$", "left")
    tag(d, (xl + 0.3, q1.center.y - 0.15), r"$Q_\mathrm{1}$", "left")
    tag(d, (xr - 0.3, q2.center.y - 0.15), r"$Q_\mathrm{2}$", "right")
    # 둘째 접속점의 마주 보는 짧은 출력선, 그 아래 + V_out −
    e1 = d.add(elm.Line().right().at(out1.center).length(0.6)).end
    e2 = d.add(elm.Line().left().at(out2.center).length(0.6)).end
    yl = out1.center.y - 0.2
    tag(d, (e1[0] - 0.1, yl), r"$+$", "left", "top")
    tag(d, (e2[0] + 0.1, yl), r"$-$", "right", "top")
    tag(d, (xm, yl), r"$V_\mathrm{out}$", "center", "top")
    wire_end(d, q1.base, r"$V_\mathrm{in1}$")
    wire_end(d, q2.base, r"$V_\mathrm{in2}$", right=True)
    d.add(Resistor().right().at(n3.center).to(n4.center).label(r"$R_\mathrm{2}$", "top", ofst=GAP))
    return d
