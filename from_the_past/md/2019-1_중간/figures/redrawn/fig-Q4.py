"""2019-1 중간 Q4 — 기준: Q4.md '회로 — Fig Q4'."""
import schemdraw.elements as elm
from schem_style import dot, gate_terminal, new_drawing, nmos, pmos, rail

L = 0.12   # 소자 사이 짧은 배선


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 4.0, 9.0
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, rail_y), (xr + 0.35, rail_y))
    d.add(elm.Label().right().at((xr + 0.45, rail_y + 0.05)).label(r"$V_{DD}$", halign="left"))
    # 위 pmos 두 쌍: M5·M6 (소스 → 레일), 그 아래 M3·M4. 각 쌍의 게이트 공통선은 왼쪽 기호 막대를 지난다
    m5 = pmos(d, at=(xl, rail_y - 0.25), anchor="source")
    m6 = pmos(d, at=(xr, rail_y - 0.25), anchor="source", label=r"$M_\mathrm{6}$")
    for m in (m5, m6):
        d.add(elm.Line().up().at(m.source).toy(rail_y))
    gate_terminal(d, m5.gate, r"$V_\mathrm{b3}$")
    d.add(elm.Line().right().at(m5.gate).tox(m6.gate.x))
    d.add(elm.Label().right().at((xl + 0.3, m5.drain.y - 0.05)).label(r"$M_\mathrm{5}$", halign="left"))
    m3 = pmos(d, at=m5.drain, anchor="source")
    m4 = pmos(d, at=m6.drain, anchor="source", label=r"$M_\mathrm{4}$")
    gate_terminal(d, m3.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Line().right().at(m3.gate).tox(m4.gate.x))
    d.add(elm.Label().right().at((xl - 0.3, m3.drain.y - 0.15)).label(r"$M_\mathrm{3}$", halign="right"))
    # 드레인 → 출력 접속점
    d.add(elm.Line().down().at(m3.drain).length(0.6)); out1 = dot(d)
    d.add(elm.Line().down().at(m4.drain).length(0.6)); out2 = dot(d)
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.9)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.9)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, out1.center.y)).label(r"$V_\mathrm{out}$"))
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.3))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Label().right().at((xl + 0.25, m1.center.y)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Line().down().at(out2.center).length(0.3))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xr - 0.25, m2.center.y)).label(r"$M_\mathrm{2}$", halign="right"))
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 소스 → 아래 → 가운데 n3 접속점 → M7 → 접지
    ybot = m1.source.y - 0.45
    d.add(elm.Line().down().at(m1.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n3 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Line().down().at(n3.center).length(0.3))
    m7 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{7}$")
    gate_terminal(d, m7.gate, r"$V_\mathrm{b2}$")
    d.add(elm.Ground().at(m7.source).scale(0.8))
    return d
