"""설계과제1 회로도(LTspice .asc) 생성. 소자값은 ../params.inc 와 같다 (Vb1 은 SPICE 조정값).

PMOS(M5·M6·M7)와 MSS 는 소스가 각각 VDD·GND 이므로 body 를 소스에 묶는 3단자 심볼을 쓴다
(보고서의 "NMOS body → GND, PMOS body → VDD" 와 같은 결선). M1~M4 는 body 를 GND 에 따로 잇는다.
DATAFLAG 는 글자 가운데가 지정 좌표에 오므로, 식을 직접 적어 배선과 겹치지 않는 곳에 둔다.
"""
from pathlib import Path

W = {"M1": "65.48u", "M2": "65.48u", "M3": "8.53u", "M4": "8.53u", "MSS": "17.56u",
     "M5": "16.22u", "M6": "16.22u", "M7": "16.07u"}
L = "0.18u"
VB1, VB2, VCM, VDD, I1 = "0.5966", "1", "0.7236", "1.5", "100u"

out = ["Version 4", "SHEET 1 1800 1200"]
wire = lambda *p: out.append("WIRE {} {} {} {}".format(*p))
flag = lambda x, y, n: out.append(f"FLAG {x} {y} {n}")
data = lambda x, y, e: out.append(f'DATAFLAG {x} {y} "{e}"')
text = lambda x, y, s, size=2: out.append(f"TEXT {x} {y} Left {size} {s}")


def mos(kind, name, x, y, rot, model, win=None):
    out.append(f"SYMBOL {kind} {x} {y} {rot}")
    out.append("WINDOW 3 0 0 Invisible 2")              # 모델 이름(CMOSN/CMOSP)은 숨긴다
    if win:
        (nx, ny), (vx, vy) = win
        out.append(f"WINDOW 0 {nx} {ny} Left 2")
        out.append(f"WINDOW 123 {vx} {vy} Left 2")
    else:
        out.append("WINDOW 123 56 64 Left 2")
    out.append(f"SYMATTR InstName {name}")
    out.append(f"SYMATTR Value {model}")
    out.append(f"SYMATTR Value2 l={L} w={W[name]}")


def vsrc(name, x, y, value, plus):
    out.append(f"SYMBOL voltage {x} {y} R0")
    out.append("WINDOW 0 24 16 Left 2")
    out.append("WINDOW 3 24 96 Left 2")
    out.append(f"SYMATTR InstName {name}")
    out.append(f"SYMATTR Value {value}")
    flag(x, y + 16, plus)
    flag(x, y + 96, "0")


LX, RX, MX = 560, 1200, 880           # 왼쪽·오른쪽 드레인 줄, 꼬리 전류원 드레인 x
NWIN = ((112, 24), (112, 56))          # M1~M4: 이름·W/L 을 body 접지 기호 오른쪽(안쪽)에
PWIN = ((56, 72), (56, 48))            # M5·M6: 뒤집힌 심볼에서 안쪽 위

# --- VDD 레일 ---
wire(160, 96, LX, 96); wire(LX, 96, RX, 96); flag(RX, 96, "vdd")
for x in (160, LX, RX):
    wire(x, 96, x, 144)

# --- M7 (다이오드 연결) + I1 ---
mos("pmos", "M7", 208, 240, "R180", "CMOSP")
wire(160, 240, 160, 304); wire(160, 304, 304, 304); wire(304, 304, 304, 160)
wire(208, 160, 304, 160); wire(304, 160, 512, 160); flag(304, 160, "g7")
data(408, 208, "V(g7)")
data(40, 272, "Id(M7)")
wire(160, 304, 160, 320)
out += ["SYMBOL current 160 320 R0", "SYMATTR InstName I1", f"SYMATTR Value {I1}"]
flag(160, 400, "0")

# --- 왼쪽 열: M5, M3, M1 ---
mos("pmos", "M5", 512, 240, "M180", "CMOSP", PWIN)
mos("nmos4", "M3", 512, 368, "R0", "CMOSN", NWIN)
mos("nmos4", "M1", 512, 592, "R0", "CMOSN", NWIN)
wire(LX, 240, LX, 304); wire(LX, 304, LX, 368); wire(LX, 304, 464, 304); flag(464, 304, "op")
wire(LX, 464, LX, 528); wire(LX, 528, LX, 592); wire(LX, 528, 464, 528); flag(464, 528, "x")
wire(512, 448, 464, 448); flag(464, 448, "vb2")
wire(512, 672, 464, 672); flag(464, 672, "in1")
wire(LX, 416, 592, 416); wire(592, 416, 592, 432); flag(592, 432, "0")
wire(LX, 640, 592, 640); wire(592, 640, 592, 656); flag(592, 656, "0")
data(680, 304, "V(op)"); data(680, 528, "V(x)")
data(680, 256, "Id(M5)"); data(720, 464, "Id(M3)"); data(720, 688, "Id(M1)")

# --- 오른쪽 열: M6, M4, M2 (좌우 대칭) ---
mos("pmos", "M6", 1248, 240, "R180", "CMOSP", PWIN)
mos("nmos4", "M4", 1248, 368, "M0", "CMOSN", NWIN)
mos("nmos4", "M2", 1248, 592, "M0", "CMOSN", NWIN)
wire(RX, 240, RX, 304); wire(RX, 304, RX, 368); wire(RX, 304, 1296, 304); flag(1296, 304, "on")
wire(RX, 464, RX, 528); wire(RX, 528, RX, 592); wire(RX, 528, 1296, 528); flag(1296, 528, "y")
wire(1248, 448, 1296, 448); flag(1296, 448, "vb2")
wire(1248, 672, 1296, 672); flag(1296, 672, "in2")
wire(1248, 160, 1296, 160); flag(1296, 160, "g7")
wire(RX, 416, 1168, 416); wire(1168, 416, 1168, 432); flag(1168, 432, "0")
wire(RX, 640, 1168, 640); wire(1168, 640, 1168, 656); flag(1168, 656, "0")
data(1080, 304, "V(on)"); data(1080, 528, "V(y)")
data(1080, 256, "Id(M6)"); data(1040, 464, "Id(M4)"); data(1040, 688, "Id(M2)")

# --- 꼬리: MSS ---
wire(LX, 688, LX, 752); wire(RX, 688, RX, 752)
wire(LX, 752, MX, 752); wire(MX, 752, RX, 752); flag(MX, 752, "s")
data(720, 784, "V(s)")
mos("nmos", "MSS", 832, 784, "R0", "CMOSN")
wire(MX, 752, MX, 784); wire(MX, 880, MX, 912); flag(MX, 912, "0")
wire(832, 864, 784, 864); flag(784, 864, "vb1")
data(1008, 912, "Id(MSS)")

# --- 전원 ---
vsrc("VDD", 160, 1008, VDD, "vdd")
vsrc("Vb1", 352, 1008, VB1, "vb1")
vsrc("Vb2", 544, 1008, VB2, "vb2")
vsrc("Vin1", 736, 1008, f"SINE({VCM} 0.5m 1Meg)", "in1")
vsrc("Vin2", 1088, 1008, f"SINE({VCM} 0.5m 1Meg 0 0 180)", "in2")

# --- 지시문·표기 ---
text(1392, 784, "!.include ../MOSFET_model.lib")
text(1392, 824, "!.op")
text(1392, 896, ";202220953 신현준", 3)
# 한글이 든 .asc 는 BOM 없는 UTF-16LE + CRLF 로 쓴다 (UTF-8 은 한글이 깨지고, BOM 이 있으면 열지 못한다)
Path(__file__).with_name("diffamp.asc").write_bytes(("\r\n".join(out) + "\r\n").encode("utf-16-le"))
print("wrote diffamp.asc")
