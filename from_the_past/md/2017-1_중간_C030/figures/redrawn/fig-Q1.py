"""2017-1 중간 (C030) Q1 — 기준: Q1.md '회로 — Fig Q1'."""
import schemdraw.elements as elm
from schem_style import GATE_LEAD, Resistor, dot, new_drawing, nmos

GAP = 0.2       # 소자 라벨과 기호 사이 간격
VDD_H = 0.32    # 0.8배 T 전원 기호 높이


def wire_end(d, at, label, right=False):
    """단자 기호 없는 선 끝 (원본의 Vin·Vout). 선 끝 바깥에 라벨."""
    line = elm.Line().at(at).length(GATE_LEAD + 0.35)
    end = d.add(line.right() if right else line.left()).end
    d.add(elm.Label().right().at((end[0] + (0.2 if right else -0.2), end[1]))
          .label(label, halign="left" if right else "right"))


def draw():
    d = new_drawing()
    xl, xr, top = 0, 6.0, 10.0
    # 왼쪽 세로줄 위→아래: T 전원 기호(라벨 없음), I_REF(화살표 아래), n1 접속점, M1(좌우 반전), R_S, 접지
    d.add(elm.Vdd().at((xl, top - VDD_H)).scale(0.8))
    iref = d.add(elm.SourceI().down().at((xl, top - VDD_H)).length(2.4).scale(0.6)
                 .label(r"$I_\mathrm{REF}$", "top", ofst=0.35))
    d.add(elm.Line().down().at(iref.end).length(0.35)); n1 = dot(d)
    d.add(elm.Line().down().at(n1.center).length(0.4))
    m1 = nmos(d, at=d.here, anchor="drain", mirror=True, label=r"$M_\mathrm{1}$")
    rs = d.add(Resistor().down().at(m1.source).length(2.2).label(r"$R_\mathrm{S}$", "top", ofst=GAP))
    d.add(elm.Ground().at(rs.end).scale(0.8))
    # 다이오드 연결: n1 → 오른쪽 → 아래로 게이트 접속점. 게이트 선은 M1 게이트에서 M3 게이트까지
    xg = m1.gate.x + 0.9
    d.add(elm.Line().right().at(n1.center).tox(xg))
    d.add(elm.Line().down().toy(m1.gate.y)); g = dot(d)
    d.add(elm.Line().left().at(g.center).tox(m1.gate.x))
    # 오른쪽 세로줄 위→아래: T 전원 기호(라벨 없음), R_D, Vout 접속점, M3, M2, 접지
    d.add(elm.Vdd().at((xr, top - VDD_H)).scale(0.8))
    rd = d.add(Resistor().down().at((xr, top - VDD_H)).length(2.4)
               .label(r"$R_\mathrm{D}$", "bottom", ofst=GAP))
    vout = dot(d)
    wire_end(d, vout.center, r"$Vout$", right=True)
    m3 = nmos(d, at=(xr, m1.drain.y), anchor="drain", label=r"$M_\mathrm{3}$")   # 게이트가 M1 게이트 높이
    d.add(elm.Line().down().at(vout.center).toy(m3.drain.y))
    d.add(elm.Line().right().at(g.center).tox(m3.gate.x))
    d.add(elm.Line().down().at(m3.source).length(0.9))
    m2 = nmos(d, at=d.here, anchor="drain", label=r"$M_\mathrm{2}$")
    wire_end(d, m2.gate, r"$Vin$")
    d.add(elm.Ground().at(m2.source).scale(0.8))
    return d
