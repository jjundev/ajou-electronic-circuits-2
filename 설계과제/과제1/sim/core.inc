* 그림 1 차동 증폭기 (노드: op=M3/M5 드레인, on=M4/M6 드레인, x/y=캐스코드 소스, s=tail, g7=미러 게이트)
.include MOSFET_model.lib
.include params.inc
VDD vdd 0 1.5
I1  g7 0 {I1V}
M7  g7 g7  vdd vdd CMOSP W={W7} L=0.18u
M5  op g7  vdd vdd CMOSP W={W5} L=0.18u
M6  on g7  vdd vdd CMOSP W={W5} L=0.18u
M3  op vb2 x   0   CMOSN W={W3} L=0.18u
M4  on vb2 y   0   CMOSN W={W3} L=0.18u
M1  x  in1 s   0   CMOSN W={W1} L=0.18u
M2  y  in2 s   0   CMOSN W={W1} L=0.18u
MSS s  vb1 0   0   CMOSN W={WSS} L=0.18u
Vb2 vb2 0 {VB2}
