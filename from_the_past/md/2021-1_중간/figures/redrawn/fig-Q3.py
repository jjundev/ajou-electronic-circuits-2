"""2021-1 중간 Q3 — 기준: Q3.md '회로 — Fig Q3(a)', '회로 — Fig Q3(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
CAP_Y = -1.2    # 캡션 높이
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭
VDD_H = 0.32    # 0.8배 T 전원 기호 높이


def npn(d, at, anchor, mirror=False, label=None, loc=None):
    """npn: 베이스 왼쪽(mirror면 오른쪽), 컬렉터 위, 이미터 아래·화살표 바깥."""
    e = elm.BjtNpn().right()
    if mirror:
        e = e.reverse()
    e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=loc or ("left" if mirror else "right"))
    return d.add(e)


def panel_a(d, x0, top):
    # 왼쪽 세로줄 위→아래: V_CC, I_1, Vout 접속점, Q1, n1 접속점, Q2, 접지
    d.add(elm.Vdd().at((x0, top - VDD_H)).scale(0.8).label(VCC, "right", ofst=GAP))
    i1 = d.add(elm.SourceI().down().at((x0, top - VDD_H)).length(1.3).scale(0.6)
               .label(r"$I_\mathrm{1}$", "top", ofst=0.3))
    d.add(elm.Line().down().at(i1.end).length(0.2)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(1.1))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(elm.Line().down().at(vout.center).length(0.3))
    q1 = npn(d, at=d.here, anchor="collector", label=r"$Q_\mathrm{1}$")
    gate_terminal(d, q1.base, r"$V_\mathrm{b1}$")
    d.add(elm.Line().down().at(q1.emitter).length(0.7)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.45))
    q2 = npn(d, at=d.here, anchor="collector", label=r"$Q_\mathrm{2}$")
    gate_terminal(d, q2.base, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Ground().at(q2.emitter).scale(0.8))
    # Q3: 오른쪽, Q1보다 조금 아래. pnp 좌우 반전(베이스 오른쪽, 이미터 왼쪽 위, 컬렉터 왼쪽 아래)
    xq = x0 + 3.0
    q3 = d.add(elm.BjtPnp().right().reverse().anchor("collector").at((xq, n1.center.y + 0.15)))
    # Q3 라벨: 컬렉터 선 왼쪽 (오른쪽 끝을 선에서 0.35 띄운다)
    d.add(elm.Label().right().at((xq - 0.35, q3.center.y - 0.2)).label(r"$Q_\mathrm{3}$", halign="right"))
    d.add(elm.Line().up().at(q3.emitter).length(0.35))
    d.add(elm.Vdd().scale(0.8).label(VCC, "right", ofst=GAP))
    gate_terminal(d, q3.base, r"$V_\mathrm{b3}$", right=True)
    d.add(elm.Line().down().at(q3.collector).toy(n1.center))
    d.add(elm.Line().left().tox(n1.center))
    caption(d, (x0 + 0.1, CAP_Y), "(a)")


def half_b(d, x, rail_y, mirror):
    """(b)의 한쪽 세로줄 위→아래: 전류원, out 첫 접속점, out 둘째 접속점, Q3/Q4, n1/n2 접속점, Q1/Q2."""
    inner = -1 if mirror else 1        # 가운데 쪽
    src = d.add(elm.SourceI().down().at((x, rail_y)).length(1.0).scale(0.6))
    d.add(elm.Line().down().at(src.end).length(0.15)); out = dot(d)
    d.add(elm.Line().down().at(out.center).length(0.45)); tap = dot(d)
    d.add(elm.Line().down().at(tap.center).length(0.45))
    qc = npn(d, at=d.here, anchor="collector", mirror=mirror)
    d.add(elm.Line().down().at(qc.emitter).length(0.25)); n = dot(d)
    d.add(elm.Line().down().at(n.center).length(0.25))
    qi = npn(d, at=d.here, anchor="collector", mirror=mirror,
             label=r"$Q_\mathrm{2}$" if mirror else r"$Q_\mathrm{1}$")
    # R_P 가지: 둘째 접속점 → 안쪽 → 아래 R_P(Q3/Q4 높이) → n1/n2 접속점
    xr = x + inner * 0.55
    d.add(elm.Line().at(tap.center).tox(xr))
    rp = d.add(Resistor().down().at((xr, tap.center.y)).toy(n.center)
               .label(r"$R_\mathrm{P}$", "top" if mirror else "bottom", ofst=GAP))
    d.add(elm.Line().at(rp.end).tox(x))
    return out, qc, qi


def panel_b(d, x0, rail_y):
    xl, xr = x0, x0 + 4.4
    rail(d, (xl - 0.3, rail_y), (xr + 0.3, rail_y))
    d.add(elm.Label().right().at((xr + 0.4, rail_y + 0.05)).label(VCC, halign="left"))
    out1, q3, q1 = half_b(d, xl, rail_y, False)
    out2, q4, q2 = half_b(d, xr, rail_y, True)
    # Q3는 컬렉터 선 왼쪽 위, Q4는 컬렉터 선 오른쪽 위
    d.add(elm.Label().right().at((xl - 0.35, q3.collector.y + 0.2)).label(r"$Q_\mathrm{3}$", halign="right"))
    d.add(elm.Label().right().at((xr + 0.3, q4.collector.y + 0.2)).label(r"$Q_\mathrm{4}$", halign="left"))
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Label().right().at(((xl + xr) / 2, out1.center.y)).label(r"$V_\mathrm{out}$"))
    # 두 V_b 점 단자는 따로 (선으로 이어지지 않음)
    gate_terminal(d, q3.base, r"$V_\mathrm{b}$")
    gate_terminal(d, q4.base, r"$V_\mathrm{b}$", right=True)
    gate_terminal(d, q1.base, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, q2.base, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 이미터 → 아래 → 가운데 n3 접속점 → I_EE → 접지
    ybot = q1.emitter.y - 0.35
    d.add(elm.Line().down().at(q1.emitter).toy(ybot))
    d.add(elm.Line().right().tox((xl + xr) / 2)); n3 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(q2.emitter))
    iee = d.add(elm.SourceI().down().at(n3.center).length(1.0).scale(0.6))
    # I_EE: 전류원 오른쪽, 위 테일 가로선과 0.2 넘게 떨어지도록 원 중심보다 아래
    d.add(elm.Label().right().at((n3.center.x + 0.55, n3.center.y - 0.72)).label(r"$I_\mathrm{EE}$", halign="left"))
    d.add(elm.Ground().at(iee.end).scale(0.8))
    caption(d, ((xl + xr) / 2 - 0.15, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    top = 6.9
    panel_a(d, 0, top)
    panel_b(d, 8.2, top)
    return d
