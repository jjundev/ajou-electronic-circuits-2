* 설계과제2 그림 1 캐스코드 증폭기 (노드: x=M1 게이트, y=M1 드레인/M2 소스/M3 드레인, out=M2 드레인)
.include MOSFET_model.lib
.include params.inc
VDD vdd 0 1
Vin in 0 DC {VIN} AC 1
RS  in x 500
RL  vdd out {RLV}
Vb1 vb1 0 {VB1}
Vb2 vb2 0 {VB2}
M1  y   x   0   0   CMOSN W={W1} L=0.18u AD={XJ*W1} AS={XJ*W1} PD={W1} PS={W1}
M2  out vb1 y   0   CMOSN W={W2} L=0.18u AD={XJ*W2} AS={XJ*W2} PD={W2} PS={W2}
M3  y   vb2 vdd vdd CMOSP W={W3} L=0.18u AD={XJ*W3} AS={XJ*W3} PD={W3} PS={W3}
