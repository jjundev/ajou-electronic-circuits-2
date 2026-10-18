"""2017-1 중간 (C030) Q2 — 기준: Q2.md '회로 — Fig Q2'."""
import schemdraw.elements as elm
from schem_style import GATE_LEAD, Resistor, dot, new_drawing, nmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
VCC = r"$V_{CC}$"   # 원본은 V_DD처럼 첨자까지 이탤릭


def wire_end(d, at, label, right=False):
    """단자 기호 없는 선 끝 (원본의 V_in1·V_in2·V_b1). 선 끝 바깥에 라벨."""
    line = elm.Line().at(at).length(GATE_LEAD + 0.35)
    end = d.add(line.right() if right else line.left()).end
    d.add(elm.Label().right().at((end[0] + (0.2 if right else -0.2), end[1]))
          .label(label, halign="left" if right else "right"))


def draw():
    d = new_drawing()
    xl, xr, rail_y = 0, 5.4, 12.0
    xm = (xl + xr) / 2
    rail(d, (xl - 0.35, rail_y), (xr + 0.9, rail_y))
    d.add(elm.Label().right().at((xr + 1.0, rail_y + 0.1)).label(VCC, halign="left", valign="bottom"))
    # 부하 저항: 레일 → 출력 접속점. R_C는 왼쪽, R_C + ΔR_C는 오른쪽
    d.add(Resistor().down().at((xl, rail_y)).length(2.6).label(r"$R_\mathrm{C}$", "top", ofst=GAP))
    out1 = dot(d)
    d.add(Resistor().down().at((xr, rail_y)).length(2.6)
          .label(r"$R_\mathrm{C} + \Delta R_\mathrm{C}$", "bottom", ofst=GAP))
    out2 = dot(d)
    # 출력선: 두 짧은 가로선이 가운데에서 마주 보고 끝남, 그 사이에 + V_out −
    e1 = d.add(elm.Line().right().at(out1.center).length(0.85)).end
    e2 = d.add(elm.Line().left().at(out2.center).length(0.85)).end
    d.add(elm.Label().right().at((e1[0] + 0.05, e1[1] + 0.25)).label(r"$+$", halign="left", valign="bottom"))
    d.add(elm.Label().right().at((e2[0] - 0.05, e2[1] + 0.25)).label(r"$-$", halign="right", valign="bottom"))
    d.add(elm.Label().right().at((xm, e1[1] + 0.25)).label(r"$V_\mathrm{out}$", valign="bottom"))
    # 입력 쌍: M2 보통, M3 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.5))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    d.add(elm.Line().down().at(out2.center).length(0.5))
    m3 = nmos(d, at=d.here, anchor="drain", mirror=True, label=r"$M_\mathrm{3}$")
    wire_end(d, m2.gate, r"$V_\mathrm{in1}$")
    wire_end(d, m3.gate, r"$V_\mathrm{in2}$", right=True)
    # 두 소스 → 아래 → 가운데 n1 접속점 → R_E → M1 → 접지
    ybot = m2.source.y - 0.6
    d.add(elm.Line().down().at(m2.source).toy(ybot))
    d.add(elm.Line().right().tox(xm)); n1 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m3.source.y))
    re = d.add(Resistor().down().at(n1.center).length(2.3).label(r"$R_\mathrm{E}$", "bottom", ofst=GAP))
    d.add(elm.Line().down().at(re.end).length(0.4))
    m1 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{1}$")
    wire_end(d, m1.gate, r"$V_\mathrm{b1}$")
    d.add(elm.Ground().at(m1.source).scale(0.8))
    return d
