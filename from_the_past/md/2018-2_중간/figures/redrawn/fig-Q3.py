"""2018-2 중간 Q3 — 기준: Q3.md '회로 — Fig Q3'."""
import schemdraw.elements as elm
from schem_style import dot, gate_terminal, new_drawing, nmos, pmos, rail

L = 0.12   # 소자 사이 짧은 배선


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 4.4, 9.0
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, rail_y), (xr + 0.35, rail_y))
    d.add(elm.Label().right().at((xr + 0.45, rail_y - 0.05)).label(r"$V_{DD}$", halign="left"))
    # 위 두 pmos: 소스 → 레일. V_b1 → M3 게이트, 같은 높이로 M3 막대를 지나 M4 게이트 (게이트 공통선)
    m3 = pmos(d, at=(xl, rail_y - 0.3), anchor="source")
    m4 = pmos(d, at=(xr, rail_y - 0.3), anchor="source", label=r"$M_\mathrm{4}$")
    for m in (m3, m4):
        d.add(elm.Line().up().at(m.source).toy(rail_y))
    gate_terminal(d, m3.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Line().right().at(m3.gate).tox(m4.gate.x))
    # 드레인 → 출력 접속점. M3 라벨은 M3 아래, 드레인 선 왼쪽
    d.add(elm.Line().down().at(m3.drain).length(0.85)); out1 = dot(d)
    d.add(elm.Label().right().at((xl - 0.3, m3.drain.y - 0.3)).label(r"$M_\mathrm{3}$", halign="right"))
    d.add(elm.Line().down().at(m4.drain).length(0.85)); out2 = dot(d)
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(1.0)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, out1.center.y)).label(r"$V_\mathrm{out}$"))
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(L))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Label().right().at((xl + 0.25, m1.center.y)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Line().down().at(out2.center).length(L))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xr - 0.25, m2.center.y)).label(r"$M_\mathrm{2}$", halign="right"))
    gate_terminal(d, m1.gate, r"$V_\mathrm{in1}$", open_=True)
    gate_terminal(d, m2.gate, r"$V_\mathrm{in2}$", open_=True, right=True)
    # 두 소스 → 아래 → 가운데 n1 접속점
    ybot = m1.source.y - 0.45
    d.add(elm.Line().down().at(m1.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n1 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    # 테일: M5, M6, 접지 (가운데 세로줄)
    d.add(elm.Line().down().at(n1.center).length(0.3))
    m5 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{5}$")
    gate_terminal(d, m5.gate, r"$V_\mathrm{b2}$")
    m6 = nmos(d, at=m5.source, anchor="drain", label=r"$M_\mathrm{6}$")
    gate_terminal(d, m6.gate, r"$V_\mathrm{b3}$")
    d.add(elm.Ground().at(m6.source).scale(0.8))
    return d
