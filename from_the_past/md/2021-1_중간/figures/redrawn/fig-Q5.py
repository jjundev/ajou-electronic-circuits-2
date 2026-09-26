"""2021-1 중간 Q5 — 기준: Q5.md '회로 — Fig Q5(a)', '회로 — Fig Q5(b)'."""
import schemdraw.elements as elm
from schem_style import Resistor, caption, dot, new_drawing, nmos

GAP = 0.2       # 소자 라벨과 기호 사이 간격
VDD_H = 0.32    # 0.8배 T 전원 기호 높이
WL = r"$\dfrac{W}{L}$"   # 원본처럼 본 글자 크기의 분수


def supply_iref(d, x, top, label):
    """위→아래: T 전원 기호, I_REF 전류원(화살표 아래). 전류원 아래 끝을 돌려준다."""
    d.add(elm.Vdd().at((x, top - VDD_H)).scale(0.8).label(label, "right", ofst=GAP))
    iref = d.add(elm.SourceI().down().at((x, top - VDD_H)).length(1.5).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.3))
    return iref.end


def i1_lead(d, xy):
    """출력 단자: 선 끝에서 아래로 I_1 화살표를 지나 xy(드레인/컬렉터)까지."""
    top = (xy[0], xy[1] + 1.8)
    d.add(elm.Arrow(arrowwidth=0.22, arrowlength=0.35).down().at(top).length(0.8)
          .label(r"$I_\mathrm{1}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().toy(xy[1]))


def panel_a(d, x0, top):
    y = supply_iref(d, x0, top, r"$V_{DD}$")
    d.add(elm.Line().down().at(y).length(0.45)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.3))
    # M_REF: nmos 좌우 반전(게이트 오른쪽), 다이오드 연결
    mref = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Ground().at(mref.source).scale(0.8))
    d.add(elm.Label().right().at((x0 + 0.4, mref.source.y - 0.45)).label(r"$M_\mathrm{REF}$", halign="left"))
    d.add(elm.Label().right().at((x0 - 0.35, mref.center.y - 0.1)).label(WL, halign="right"))
    # n1 → 오른쪽 → 게이트보다 조금 오른쪽에서 아래로 → 게이트 접속점
    xg = mref.gate.x + 0.3
    d.add(elm.Line().right().at(n1.center).tox(xg))
    d.add(elm.Line().down().toy(mref.gate.y)); g = dot(d)
    d.add(elm.Line().left().at(g.center).tox(mref.gate))
    d.add(elm.Line().right().at(g.center).length(1.6))
    m1 = nmos(d, at=d.here, anchor="gate")
    d.add(elm.Label().right().at((m1.drain.x - 0.3, m1.drain.y + 0.2)).label(r"$M_\mathrm{1}$", halign="right"))
    d.add(elm.Label().right().at((m1.drain.x + 0.35, m1.center.y - 0.25)).label(WL, halign="left"))
    i1_lead(d, m1.drain)
    rp = d.add(Resistor().down().at(m1.source).length(1.3).label(r"$R_\mathrm{P}$", "bottom", ofst=GAP))
    d.add(elm.Ground().at(rp.end).scale(0.8))
    return (x0 + m1.drain.x) / 2, rp.end.y


def panel_b(d, x0, top):
    y = supply_iref(d, x0, top, r"$V_{CC}$")
    d.add(elm.Line().down().at(y).length(0.35)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.35))
    # Q_REF: npn 좌우 반전(베이스 오른쪽), 다이오드 연결
    qref = d.add(elm.BjtNpn().right().reverse().anchor("collector").at(d.here))
    d.add(elm.Label().right().at((x0 - 0.3, qref.emitter.y + 0.25)).label(r"$Q_\mathrm{REF}$", halign="right"))
    rp = d.add(Resistor().down().at(qref.emitter).length(1.3).label(r"$R_\mathrm{P}$", "bottom", ofst=GAP))
    d.add(elm.Ground().at(rp.end).scale(0.8))
    xb = qref.base.x + 0.3
    d.add(elm.Line().right().at(n1.center).tox(xb))
    d.add(elm.Line().down().toy(qref.base.y)); b = dot(d)
    d.add(elm.Line().left().at(b.center).tox(qref.base))
    d.add(elm.Line().right().at(b.center).length(1.3))
    q1 = d.add(elm.BjtNpn().right().anchor("base").at(d.here).label(r"$Q_\mathrm{1}$", "right"))
    i1_lead(d, q1.collector)
    d.add(elm.Ground().at(q1.emitter).scale(0.8))
    return (x0 + q1.collector.x) / 2, rp.end.y


def draw():
    d = new_drawing()
    top = 7.0
    xa, ya = panel_a(d, 0, top)
    xb, yb = panel_b(d, 8.6, top)
    # 캡션: 가장 낮은 접지 기호 아래
    cap_y = min(ya, yb) - 1.1
    caption(d, (xa - 0.15, cap_y), "(a)")
    caption(d, (xb - 0.15, cap_y), "(b)")
    return d
