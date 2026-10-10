# 설계과제1 LTspice 회로도 작성 메모

보고서 2-(a) 의 회로도 캡처(`figs/schematic.png`)를 만들 때 쓰는 작업 메모다. 제출 본문에는 들어가지 않는다.

## 회로도 작성 순서

회로도는 `sim/ltspice/make_asc.py` 가 `sim/ltspice/diffamp.asc` 로 만든다. 소자값·바이어스는 `sim/params.inc` 와 같고($V_{b1}$ 은 SPICE 조정값 0.5966 V), 모델은 `.include ../MOSFET_model.lib` 로 과제 제공 CMOSN/CMOSP 를 그대로 쓴다. LTspice 전역 라이브러리(`standard.mos`)는 바꾸지 않는다.

1. `cd sim/ltspice && python3 make_asc.py` 로 `diffamp.asc` 를 만든다. 한글 표기 때문에 파일은 BOM 없는 UTF-16LE 로 저장된다.
2. LTspice(Apple Silicon 은 Rosetta 2 필요)에서 `diffamp.asc` 를 열고 Run 을 누르면 `.op` 라벨(노드 전압, 각 MOSFET 의 Id)이 회로도에 표시된다.
3. `.op` 결과 창은 닫고 Space(Zoom to Fit) 후 창을 캡처해 `report/figs/schematic.png` 로 저장한다.
4. PMOS(M5·M6·M7)와 $M_{SS}$ 는 소스가 VDD·GND 라 body 를 소스에 묶는 3단자 기호를 쓴다(결선은 body → VDD/GND 와 같다). $M_1$~$M_4$ 는 body 를 GND 에 따로 잇는다.

LTspice 배치 실행 결과(2026-10-11)는 ngspice 동작점과 표시 자릿수까지 같다: $V_{out\pm}$ 0.949156 V, $V_{X,Y}$ 0.403345 V, $V_S$ 0.251259 V, $V_{G7}$ 0.903431 V, $I_{D1\sim6}$ 100.109 µA, $I_{SS}$ 200.218 µA, $I_{D7}$ 100.000 µA.

## 시뮬레이션 파일 (`sim/`)

| 파일 | 내용 |
|---|---|
| `handcalc.py` | 1)의 손계산 → `params.inc` 생성 |
| `core.inc` | 그림 1 회로 넷리스트 |
| `tune.cir` | $V_{b1}$ DC sweep (출력 CM 0.95 V 맞추기) |
| `diffamp.cir` | DC op / AC / Transient |
| `post.py` | 그래프와 saturation 표 생성 |
| `ltspice/make_asc.py` | LTspice 회로도 `diffamp.asc` 생성 |

```bash
cd sim && python3 handcalc.py && ngspice -b diffamp.cir && python3 post.py
```

## 캡처 전 확인

- 회로도 빈 곳에 학번·이름 텍스트(`202220953 신현준`)를 넣는다.
- `.op` 라벨 값이 보고서 2-(a) 노드 표와 1 mV 안팎으로 맞는지 본다. CMFB 가 없어 출력 CM 이 $V_{b1}$ 에 매우 민감하므로(약 −57 V/V), 출력이 0.95 V 에서 크게 벗어나면 $V_{b1}$ 값(0.5966 V)부터 확인한다.
- 캡처는 `report/figs/schematic.png` 로 저장하고, 노션에서는 2-(a) 의 그림 자리에 넣는다.
