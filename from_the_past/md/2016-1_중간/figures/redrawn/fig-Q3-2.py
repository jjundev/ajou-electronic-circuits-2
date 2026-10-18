"""2016-1 중간 Q3 둘째 그림 — 기준: Q3.md '회로 — Fig Q3-2'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.3    # V_CC 레일 높이


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽), 컬렉터 위, 이미터 아래."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def open_terminal(d, at, label, length, right=False):
    """베이스에서 가로선을 긋고 끝에 개방 원과 라벨."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    d.add(elm.Dot(open=True, radius=OPEN_R).label(label, "right" if right else "left", ofst=GAP))


def column(d, x, mirror):
    """한쪽 세로줄 위→아래: Q3/Q4, R_C, out 접속점, Q1/Q2, n3/n4 접속점, I_EE, 접지."""
    qt = bjt(d, elm.BjtNpn, (x, RAIL_Y - 0.4), "collector", mirror=mirror)
    d.add(elm.Line().up().at(qt.collector).toy(RAIL_Y))
    # 베이스 → 바깥쪽 가로선 → 위로 레일
    d.add(elm.Line().at(qt.base).length(0.4).right() if mirror else
          elm.Line().at(qt.base).length(0.4).left())
    d.add(elm.Line().up().toy(RAIL_Y))
    rc = d.add(Resistor().down().at(qt.emitter).length(1.4)
               .label(r"$R_\mathrm{C}$", "bottom" if mirror else "top", ofst=GAP))
    d.add(elm.Line().down().at(rc.end).length(0.35)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(0.3))
    qb = bjt(d, elm.BjtNpn, d.here, "collector", mirror=mirror)
    d.add(elm.Line().down().at(qb.emitter).length(0.45)); n = dot(d)
    iee = d.add(elm.SourceI().down().at(n.center).length(1.4).scale(0.6)
                .label(r"$I_\mathrm{EE}$", "bottom" if mirror else "top", ofst=0.3))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    return qt, out, qb, n


def draw():
    d = new_drawing()
    xl, xr = 3.6, 7.5
    q3, out1, q1, n3 = column(d, xl, False)
    q4, out2, q2, n4 = column(d, xr, True)
    rail(d, (xl - 1.15, RAIL_Y), (xr + 1.75, RAIL_Y))
    d.add(elm.Label().right().at((xr + 1.85, RAIL_Y - 0.1)).label(r"$V_{CC}$", halign="left"))
    d.add(elm.Label().right().at((xl + 0.3, q3.center.y)).label(r"$Q_\mathrm{3}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.3, q4.center.y)).label(r"$Q_\mathrm{4}$", halign="right"))
    d.add(elm.Label().right().at((xl + 0.3, q1.center.y)).label(r"$Q_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.3, q2.center.y)).label(r"$Q_\mathrm{2}$", halign="right"))
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Label().right().at(((xl + xr) / 2, out1.center.y)).label(r"$V_\mathrm{out}$"))
    open_terminal(d, q1.base, r"$V_\mathrm{in1}$", 0.6)
    open_terminal(d, q2.base, r"$V_\mathrm{in2}$", 0.6, right=True)
    d.add(Resistor().right().at(n3.center).to(n4.center).label(r"$R_\mathrm{E}$", "bottom", ofst=GAP))
    return d
