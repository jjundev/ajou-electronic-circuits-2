"""2017-1 중간 (D반) Q4 둘째 그림 — 기준: Q4.md '회로 — Fig Q4(c)'."""
import schemdraw.elements as elm
from schem_style import OPEN_R, caption, dot, gate_terminal, new_drawing, nmos, pmos, rail

GAP = 0.2       # 소자 라벨과 기호 사이 간격
RAIL_Y = 8.5    # V_DD 레일 높이
DROP = 0.3      # 레일에서 소스(M3·M4는 드레인)까지 세로선
CAP_DY = 1.5    # 전류원 아래 끝에서 캡션까지 (원본처럼 접지 아래가 넉넉함)


def open_terminal(d, at, label, length, right=False):
    """게이트에서 가로선을 긋고 끝에 개방 원과 라벨."""
    line = elm.Line().at(at).length(length)
    d.add(line.right() if right else line.left())
    d.add(elm.Dot(open=True, radius=OPEN_R).label(label, "right" if right else "left", ofst=GAP))


def half(d, x, mirror):
    """한쪽: 바깥 pmos(M5/M6), 안쪽 nmos(M3/M4), out 접속점. mirror면 오른쪽 반쪽."""
    side = 1 if mirror else -1                    # 바깥쪽 방향
    xp = x + side * 1.7                           # M5/M6 줄
    mp = pmos(d, at=(xp, RAIL_Y - DROP), anchor="source", mirror=mirror)
    d.add(elm.Line().up().at(mp.source).toy(RAIL_Y))
    gate_terminal(d, mp.gate, r"$V_\mathrm{b}$", right=mirror)
    mn = nmos(d, at=(x, RAIL_Y - DROP), anchor="drain", mirror=mirror)
    d.add(elm.Line().up().at(mn.drain).toy(RAIL_Y))
    # 안쪽 nmos 게이트: 바깥쪽으로 나가 위로 꺾여 레일
    d.add(elm.Line().at(mn.gate).tox(mn.gate.x + side * 0.3))
    d.add(elm.Line().up().toy(RAIL_Y))
    # 안쪽 nmos 소스 ↓ out 접속점, 바깥 pmos 드레인 ↓ → 안쪽으로 꺾여 out 접속점
    d.add(elm.Line().down().at(mn.source).length(0.9)); out = dot(d)
    d.add(elm.Line().down().at(mp.drain).toy(out.center.y))
    d.add(elm.Line().tox(x))
    return mp, mn, out


def draw():
    d = new_drawing()
    xl, xr = 0.0, 3.6                 # M3·M1 줄, M4·M2 줄
    xm = (xl + xr) / 2
    m5, m3, out1 = half(d, xl, False)
    m6, m4, out2 = half(d, xr, True)
    rail(d, (m5.source.x - 0.3, RAIL_Y), (m6.source.x + 0.3, RAIL_Y))
    d.add(elm.Label().right().at((m6.source.x + 0.4, RAIL_Y + 0.05)).label(r"$V_{DD}$", halign="left"))
    d.add(elm.Label().right().at((m5.drain.x - 0.3, m5.drain.y - 0.1))
          .label(r"$M_\mathrm{5}$", halign="right", valign="top"))
    d.add(elm.Label().right().at((m6.drain.x + 0.3, m6.drain.y - 0.1))
          .label(r"$M_\mathrm{6}$", halign="left", valign="top"))
    d.add(elm.Label().right().at((xl + 0.25, m3.center.y)).label(r"$M_\mathrm{3}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.25, m4.center.y)).label(r"$M_\mathrm{4}$", halign="right"))
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Line().left().at(out2.center).length(0.8)); dot(d, open_=True)
    d.add(elm.Label().right().at((xm, out1.center.y)).label(r"$V_\mathrm{out}$"))
    # 입력 쌍: M1 보통, M2 좌우 반전
    d.add(elm.Line().down().at(out1.center).length(0.6))
    m1 = nmos(d, at=d.here, anchor="drain")
    d.add(elm.Line().down().at(out2.center).length(0.6))
    m2 = nmos(d, at=d.here, anchor="drain", mirror=True)
    d.add(elm.Label().right().at((xl + 0.25, m1.center.y)).label(r"$M_\mathrm{1}$", halign="left"))
    d.add(elm.Label().right().at((xr - 0.25, m2.center.y)).label(r"$M_\mathrm{2}$", halign="right"))
    open_terminal(d, m1.gate, r"$V_\mathrm{in1}$", 0.6)
    open_terminal(d, m2.gate, r"$V_\mathrm{in2}$", 0.6, right=True)
    # 두 소스 → 아래 → 가운데 n1 → I_SS → 접지
    yt = m1.source.y - 0.7
    d.add(elm.Line().down().at(m1.source).toy(yt))
    d.add(elm.Line().right().tox(xm)); n1 = dot(d)
    d.add(elm.Line().right().tox(xr))
    d.add(elm.Line().up().toy(m2.source.y))
    d.add(elm.Line().down().at(n1.center).length(0.4))
    iss = d.add(elm.SourceI().down().length(1.5).scale(0.6).label(r"$I_\mathrm{SS}$", "bottom", ofst=0.3))
    d.add(elm.Ground().at(iss.end).scale(0.8))
    caption(d, (xm, iss.end.y - CAP_DY), "(c)")
    return d
