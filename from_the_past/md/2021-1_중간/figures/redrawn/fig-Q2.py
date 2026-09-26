"""2021-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2(a)', '회로 — Fig Q2(b)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

L = 0.12       # 소자 사이 짧은 배선
GAP = 0.2      # 소자 라벨과 기호 사이 간격
CAP_Y = -1.2   # 캡션 높이
ISS = dict(label=r"$I_\mathrm{SS}$")


def panel_a(d, x0):
    m1 = nmos(d, at=(x0, 0), anchor="source", label=r"$M_\mathrm{1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    gate_terminal(d, m1.gate, r"$V_\mathrm{in}$", open_=True)
    d.add(elm.Line().up().at(m1.drain).length(L)); n1 = dot(d)
    m2 = nmos(d, at=n1.center, anchor="source")
    gate_terminal(d, m2.gate, r"$V_\mathrm{b2}$")
    # M2 라벨이 Vout 접속점과 M2 기호 사이에 들어가도록 드레인 배선을 길게 둔다
    d.add(elm.Line().up().at(m2.drain).length(0.42)); vout = dot(d)
    # 원본처럼 드레인 배선 왼쪽, Vout 접속점 바로 아래. 오른쪽 끝을 배선에서 0.3 떨어뜨린다
    d.add(elm.Label().right().at((m2.drain.x - 0.3, vout.center.y - 0.3))
          .label(r"$M_\mathrm{2}$", halign="right"))
    m3 = pmos(d, at=vout.center, anchor="drain", label=r"$M_\mathrm{3}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b3}$")
    m4 = pmos(d, at=m3.source, anchor="drain", label=r"$M_\mathrm{4}$")
    gate_terminal(d, m4.gate, r"$V_\mathrm{b4}$")
    d.add(elm.Vdd().at(m4.source).scale(0.8).label(r"$V_{DD}$", "right", ofst=GAP))
    d.add(elm.Line().right().at(vout.center).length(0.5)); tap = dot(d)
    d.add(elm.Line().right().length(0.6))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    d.add(Resistor().down().at(tap.center).toy(n1.center).label(r"$R_\mathrm{P}$", "bottom", ofst=GAP))
    d.add(elm.Line().left().tox(n1.center))
    caption(d, (x0 - 0.15, CAP_Y), "(a)")
    return m4.source.y


def half_b(d, x, rail_y, mirror):
    """(b)의 한쪽 세로줄 위→아래: R_S, M3/M4, 출력 접속점, M1/M2, 소스 접속점, I_SS, 접지."""
    # 아래로 그리는 소자의 라벨: loc="bottom"이면 오른쪽, "top"이면 왼쪽
    side = "bottom" if mirror else "top"
    rs = d.add(Resistor().down().at((x, rail_y)).length(1.2).label(r"$R_\mathrm{S}$", side, ofst=0.3))
    mp = pmos(d, at=rs.end, anchor="source")
    d.add(elm.Line().down().at(mp.drain).length(0.5)); out = dot(d)
    mn = nmos(d, at=out.center, anchor="drain", mirror=mirror)
    # M1은 드레인 선 오른쪽, M2는 왼쪽. 기본 라벨보다 0.05 더 띄운다
    d.add(elm.Label().right().at((x - 0.25 if mirror else x + 0.25, mn.center.y))
          .label(r"$M_\mathrm{2}$" if mirror else r"$M_\mathrm{1}$", halign="right" if mirror else "left"))
    d.add(elm.Line().down().at(mn.source).length(0.3)); src = dot(d)
    iss = d.add(elm.SourceI().down().at(src.center).length(1.6).scale(0.6).label(**ISS, loc=side, ofst=0.35))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    return mp, out, mn, src


def panel_b(d, x0, rail_y):
    xl, xr = x0, x0 + 4.8
    rail(d, (xl - 0.3, rail_y), (xr + 0.3, rail_y))
    d.add(elm.Label().right().at((xr + 0.4, rail_y + 0.3)).label(r"$V_{DD}$", halign="left"))
    m3, out1, m1, n3 = half_b(d, xl, rail_y, False)
    m4, out2, m2, n4 = half_b(d, xr, rail_y, True)
    # M3, M4 라벨: 게이트 판 왼쪽 위. 오른쪽 끝을 게이트 판에서 0.2 넘게 띄운다
    for m, text in ((m3, r"$M_\mathrm{3}$"), (m4, r"$M_\mathrm{4}$")):
        d.add(elm.Label().right().at((m.gate.x + 0.15, m.gate.y + 0.6)).label(text, halign="right"))
    # V_b → M3 게이트, 같은 높이로 M4 게이트까지 (게이트 공통선)
    gate_terminal(d, m3.gate, r"$V_\mathrm{b}$")
    d.add(elm.Line().right().at(m3.gate).tox(m4.gate))
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Label().right().at(((xl + xr) / 2, out1.center.y)).label(r"$V_\mathrm{out}$"))
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    d.add(Resistor().right().at(n3.center).to(n4.center).label(r"$R_\mathrm{SS}$", "bottom", ofst=0.25))
    caption(d, ((xl + xr) / 2 - 0.15, CAP_Y), "(b)")


def draw():
    d = new_drawing()
    top = panel_a(d, 0)
    panel_b(d, 7.4, top)
    return d
