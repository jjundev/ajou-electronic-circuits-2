"""2023-1 기말 Q4 — 기준: Q4.md '회로 — Fig Q4'. 답안지 손글씨("Y", "x", R1 아래 글자)는 그리지 않는다."""
import schemdraw.elements as elm
from schem_style import OPEN_R, Resistor, dot, new_drawing

GAP = 0.2      # 소자 라벨과 기호 사이 간격


def draw():
    d = new_drawing()
    xs, y0 = 1.7, 0          # 전압원 세로줄, + 입력 가로선 높이
    # V_in: 원형 전압원, 아래 접지, 위 단자 → 위 → 오른쪽 가로선
    src = d.add(elm.Source().up().at((xs, -2.0)).to((xs, -0.5)).scale(0.8))
    d.add(elm.Ground().at(src.start).scale(0.8))
    d.add(elm.Label().right().at((xs - 0.7, -1.25)).label(r"$V_\mathrm{in}$", halign="right"))
    d.add(elm.Label().right().at((xs + 0.45, -0.75)).label(r"$\mathrm{+}$", halign="left"))
    d.add(elm.Label().right().at((xs + 0.45, -1.75)).label(r"$\mathrm{-}$", halign="left"))
    d.add(elm.Line().up().at(src.end).toy(y0))
    d.add(elm.Line().right().tox(xs + 1.0))
    d.add(elm.Capacitor().right().length(1.6).label(r"$C_\mathrm{1}$", "bottom", ofst=0.25))
    d.add(elm.Line().right().length(0.4)); n2 = dot(d)
    d.add(elm.Line().right().length(0.3))
    d.add(elm.Capacitor().right().length(1.6).label(r"$C_\mathrm{2}$", "bottom", ofst=0.25))
    d.add(elm.Line().right().length(0.4)); n3 = dot(d)
    r1 = d.add(Resistor().down().at(n3.center).length(1.8).label(r"$R_\mathrm{1}$", "bottom", ofst=0.3))
    d.add(elm.Ground().at(r1.end).scale(0.8))
    # 연산증폭기: + 입력 위(flip), 출력 오른쪽
    d.add(elm.Line().right().at(n3.center).length(1.8))
    oa = d.add(elm.Opamp(sign=True).flip().right().anchor("in2").at(d.here))
    d.add(elm.Line().right().at(oa.out).length(0.5)); vout = dot(d)
    d.add(elm.Line().right().at(vout.center).length(0.7))
    d.add(elm.Dot(open=True, radius=OPEN_R).label(r"$V_\mathrm{out}$", "right", ofst=GAP))
    # R2: n2 → 위 → 오른쪽 R2 → 연산증폭기 위를 넘어 → 아래 Vout
    y_r2 = y0 + 1.75
    d.add(elm.Line().up().at(n2.center).toy(y_r2))
    r2 = d.add(Resistor().right().at((n2.center.x, y_r2)).tox(oa.in2.x + 1.2)
               .label(r"$R_\mathrm{2}$", "top", ofst=0.25))
    d.add(elm.Line().right().at(r2.end).tox(vout.center.x))
    d.add(elm.Line().down().toy(vout.center.y))
    # − 입력 → 왼쪽 → 아래 → 연산증폭기 아래 → 오른쪽 → 위 Vout
    y_fb = oa.in1.y - 1.0
    d.add(elm.Line().left().at(oa.in1).length(0.35))
    d.add(elm.Line().down().toy(y_fb))
    d.add(elm.Line().right().tox(vout.center.x))
    d.add(elm.Line().up().toy(vout.center.y))
    return d
