"""설계과제2 회로도(LTspice .asc) 생성. 소자값·바이어스는 ../params.inc 에서 읽는다.

M1(소스 GND)과 M3(소스 VDD)은 body 를 소스에 묶는 3단자 심볼을 쓴다(결선은 body → GND/VDD 와 같다).
M2 는 소스가 Y 에 떠 있으므로 nmos4 로 body 를 GND 에 따로 잇는다.
DATAFLAG 는 글자 가운데가 지정 좌표에 오므로, 식을 직접 적어 배선과 겹치지 않는 곳에 둔다.
MOSFET 옆에 보이는 Value2 는 l, w 만 둔다. ad/as/pd/ps 까지 넣으면 글자가 길어져 RL 값과 Id 라벨을 덮으므로
접합 파라미터는 화면에 보이지 않는 SpiceLine 속성에 넣는다 (넷리스트 줄 끝에 그대로 붙는다).
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = dict(re.findall(r"(\w+)=([^\s]+)", (HERE.parent / "params.inc").read_text()))
L, VDD = "0.18u", "1"
XJ = float(P["XJ"].rstrip("u"))                          # µm
W = {"M1": P["W1"], "M2": P["W2"], "M3": P["W3"]}       # "62.14u"

out = ["Version 4", "SHEET 1 1400 960"]
wire = lambda *p: out.append("WIRE {} {} {} {}".format(*p))
flag = lambda x, y, n: out.append(f"FLAG {x} {y} {n}")
data = lambda x, y, e: out.append(f'DATAFLAG {x} {y} "{e}"')
text = lambda x, y, s, size=2: out.append(f"TEXT {x} {y} Left {size} {s}")


def mos(kind, name, x, y, rot, model, win=None):
    w = float(W[name].rstrip("u"))
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
    out.append(f"SYMATTR Value2 l={L} w={W[name]}")       # 화면에 보이는 것은 l, w만 (과제1과 같다)
    # 접합 면적·둘레는 SpiceLine 으로: 넷리스트에는 붙고 회로도에는 보이지 않아 라벨과 겹치지 않는다
    out.append(f"SYMATTR SpiceLine ad={XJ*w:.4g}p as={XJ*w:.4g}p pd={W[name]} ps={W[name]}")


def res(name, x, y, rot, value):
    out.append(f"SYMBOL res {x} {y} {rot}")
    if rot == "R90":
        out.extend(["WINDOW 0 0 56 VBottom 2", "WINDOW 3 32 56 VTop 2"])
    out.append(f"SYMATTR InstName {name}")
    out.append(f"SYMATTR Value {value}")


def vsrc(name, x, y, value, plus):
    out.append(f"SYMBOL voltage {x} {y} R0")
    out.append("WINDOW 0 24 16 Left 2")
    out.append("WINDOW 3 24 96 Left 2")
    out.append(f"SYMATTR InstName {name}")
    out.append(f"SYMATTR Value {value}")
    flag(x, y + 16, plus)
    flag(x, y + 96, "0")


LX, RX = 448, 880                     # M3 드레인 줄, M1·M2 드레인 줄
NWIN = ((112, 24), (112, 56))         # nmos4: 이름·W/L 을 body 접지 기호 오른쪽에
PWIN = ((56, 72), (56, 48))           # 뒤집힌 pmos: 안쪽 위

# --- VDD 레일 ---
wire(LX, 96, RX, 96); flag(RX, 96, "vdd")

# --- M3 (PMOS 전류원, 게이트 Vb2, 드레인 Y) ---
mos("pmos", "M3", 400, 240, "M180", "CMOSP", PWIN)
wire(LX, 96, LX, 144)
wire(400, 160, 352, 160); flag(352, 160, "vb2")
wire(LX, 240, LX, 416); wire(LX, 416, RX, 416)
data(LX - 128, 320, "Id(M3)")

# --- RL, M2 (cascode), out ---
res("RL", 864, 112, "R0", P["RLV"])
wire(RX, 96, RX, 128); wire(RX, 208, RX, 272)
wire(RX, 272, 976, 272); flag(976, 272, "out")
mos("nmos4", "M2", 832, 272, "R0", "CMOSN", NWIN)
wire(832, 352, 784, 352); flag(784, 352, "vb1")
wire(RX, 320, 912, 320); wire(912, 320, 912, 336); flag(912, 336, "0")
data(1056, 240, "V(out)")
data(1088, 368, "Id(M2)")          # M2 이름·W/L 아래

# --- Y, M1 (CS 입력단), RS, X ---
wire(RX, 368, RX, 416); wire(RX, 416, RX, 464); flag(RX, 416, "y")
data(976, 416, "V(y)")
mos("nmos", "M1", 832, 464, "R0", "CMOSN")
wire(RX, 560, RX, 592); flag(RX, 592, "0")
res("RS", 752, 528, "R90", "500")
wire(736, 544, 832, 544); flag(784, 544, "x")
wire(656, 544, 576, 544); flag(576, 544, "in")
data(720, 624, "V(x)")            # RS 값 아래, M1 소스 접지 기호와 떨어지게
data(1040, 584, "Id(M1)")         # M1 이름·W/L 아래 (3단자 기호라 W/L 줄이 M2보다 아래에 있다)

# --- 전원 ---
vsrc("VDD", 160, 704, VDD, "vdd")
vsrc("Vin", 352, 704, f"{P['VIN']} AC 1", "in")
vsrc("Vb1", 576, 704, P["VB1"], "vb1")
vsrc("Vb2", 768, 704, P["VB2"], "vb2")

# --- 지시문·표기 ---
text(1040, 704, "!.include ../MOSFET_model.lib")
text(1040, 744, "!.op")
text(1040, 816, ";202220953 신현준", 3)
# 한글이 든 .asc 는 BOM 없는 UTF-16LE + CRLF 로 쓴다 (UTF-8 은 한글이 깨지고, BOM 이 있으면 열지 못한다)
(HERE / "cascode.asc").write_bytes(("\r\n".join(out) + "\r\n").encode("utf-16-le"))
print("wrote cascode.asc")
