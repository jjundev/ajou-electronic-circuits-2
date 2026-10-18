"""2015-1 중간 Q3 셋째 그림 — 기준: Q3.md '회로 — Fig Q3-3'."""
import schemdraw.elements as elm
from schem_style import Resistor, dot, gate_terminal, new_drawing, rail

GAP = 0.2
RAIL_Y = 9.0


def bjt(d, cls, at, anchor, mirror=False, label=None, loc=None):
    """베이스 왼쪽(mirror면 오른쪽). npn은 컬렉터 위, pnp는 이미터 위."""
    e = cls().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def draw():
    d = new_drawing()
    R = RAIL_Y
    xl, xr = 0, 4.2
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, R), (xr + 0.35, R))
    d.add(elm.Label().right().at((xr + 0.5, R + 0.05)).label(r"$V_{CC}$", halign="left"))
    # 부하 저항: 아래로 그리는 소자의 라벨은 loc="top"이면 왼쪽, "bottom"이면 오른쪽
    d.add(Resistor().down().at((xl, R)).length(1.5).label(r"$R_\mathrm{C}$", "top", ofst=GAP))
    out1 = dot(d)
    d.add(Resistor().down().at((xr, R)).length(1.5).label(r"$R_\mathrm{C}$", "bottom", ofst=GAP))
    out2 = dot(d)
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.7)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.7)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, out1.center.y)).label(r"$V_\mathrm{out}$"))
    # 입력 쌍: Q1 보통, Q2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.45))
    q1 = bjt(d, elm.BjtNpn, d.here, "collector", label=r"$Q_\mathrm{1}$")
    d.add(elm.Line().down().at(out2.center).length(0.45))
    q2 = bjt(d, elm.BjtNpn, d.here, "collector", mirror=True, label=r"$Q_\mathrm{2}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, q2.base, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 이미터 바로 아래 n1, n2 접속점과 그 사이 R_E
    d.add(elm.Line().down().at(q1.emitter).length(0.35)); n1 = dot(d)
    d.add(elm.Line().down().at(q2.emitter).length(0.35)); n2 = dot(d)
    d.add(Resistor().right().at(n1.center).to(n2.center).label(r"$R_\mathrm{E}$", "bottom", ofst=0.25))
    # 전류원(화살표 아래)과 접지. I_EE 라벨은 왼쪽 것 왼쪽, 오른쪽 것 오른쪽
    i1 = d.add(elm.SourceI().down().at(n1.center).length(1.5).scale(0.6)
               .label(r"$I_\mathrm{EE}$", "top", ofst=0.35))
    d.add(elm.Ground().at(i1.end).scale(0.8))
    i2 = d.add(elm.SourceI().down().at(n2.center).length(1.5).scale(0.6)
               .label(r"$I_\mathrm{EE}$", "bottom", ofst=0.35))
    d.add(elm.Ground().at(i2.end).scale(0.8))
    return d
