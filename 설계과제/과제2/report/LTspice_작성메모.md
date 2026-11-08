# 설계과제2 LTspice 회로도 작성 메모

보고서 Spice Problem (a) 의 회로도 캡처(`figs/03_schematic.png`)를 만들 때 쓰는 작업 메모다. 제출 본문에는 들어가지 않는다. 설치·인코딩·배치 실행·캡처 같은 일반 방법은 `.claude/skills/ec2-write-design-report/references/LTspice.md` 에 있고, 여기에는 과제2 값만 둔다.

## 회로도 작성 순서

회로도는 `sim/ltspice/make_asc.py` 가 `sim/ltspice/cascode.asc` 로 만든다. 소자값·바이어스는 `sim/params.inc` 를 읽어 채우므로 손계산을 바꾸면 회로도도 같이 바뀐다. 모델은 `.include ../MOSFET_model.lib` 로 과제 제공 CMOSN/CMOSP 를 그대로 쓴다. LTspice 전역 라이브러리(`standard.mos`)는 바꾸지 않는다.

1. `cd sim && python3 handcalc.py && cd ltspice && python3 make_asc.py` 로 `cascode.asc` 를 만든다.
2. 배치 실행으로 동작점을 확인한 뒤 GUI 에서 캡처해 `report/figs/03_schematic.png` 로 저장한다 (방법은 LTspice.md).
3. $M_1$(소스 GND)과 $M_3$(소스 VDD)은 body 를 소스에 묶는 3단자 기호를 쓴다(결선은 body → GND/VDD 와 같다). $M_2$ 는 소스가 $Y$ 에 떠 있으므로 `nmos4` 로 body 를 GND 에 따로 잇는다.
4. 모든 MOSFET 에 접합 면적·둘레를 넣는다: $AD = AS = 0.49\ \mu\text{m}\times W$, $PD = PS = W$ (ngspice `core.inc` 와 같다).

LTspice 배치 실행 결과(2026-11-08)는 ngspice 동작점과 표시 자릿수까지 같다: $V_X$ 0.55 V, $V_Y$ 0.299908 V, $V_{out}$ 0.600532 V, $I_{D1}$ 414.40 µA, $I_{D2}$ 207.14 µA, $|I_{D3}|$ 207.26 µA, $I_{VDD}$ 414.40 µA. 떠 있는 노드·floating 경고는 없다. 로그의 "Direct Newton iteration failed … Gmin stepping succeeded" 는 초기 수렴 방법이 바뀌었다는 뜻일 뿐 결과에는 영향이 없고, "Oxide thickness thinner / Length shorter than recommended for a level 1 MOSFET" 은 Level 1 모델에 0.18 µm 공정 값을 넣어 생기는 안내 문구다.

## 시뮬레이션 파일 (`sim/`)

| 파일 | 내용 |
|---|---|
| `handcalc.py` | Design Problem 손계산 → `params.inc`, `design.json` |
| `core.inc` | 그림 1 회로 넷리스트 (접합 C 포함) |
| `cascode.cir` | DC op / AC / pz → `op.txt`, `ac.txt`, `meas.txt`, `pz.txt` |
| `polemap.py` | 노드별 1 fF 섭동으로 pz 극점과 노드 대응 → `polemap.json` |
| `post.py` | Bode 그림, saturation 표, 설계-SPICE 비교표 |
| `spice_io.py` | ngspice 출력 파서 |
| `ltspice/make_asc.py` | LTspice 회로도 `cascode.asc` 생성 |

```bash
cd sim && python3 handcalc.py && ngspice -b cascode.cir && python3 polemap.py && python3 post.py
```

ngspice 가 모델의 `WD` 를 "unrecognized parameter (wd) - ignored" 로 알리는데, 모델 값이 `WD=0` 이라 무시해도 결과가 같다(모델 파일은 수정하지 않는다).

## 캡처 전 확인

- 회로도 빈 곳에 학번·이름 텍스트(`202220953 신현준`)가 보이는지 본다.
- `.op` 라벨(V(x), V(y), V(out), Id(M1), Id(M2), Id(M3))이 보고서 Spice Problem (a) 노드 표와 1 mV, 0.1 µA 안에서 맞는지 본다.
- 캡처는 `report/figs/03_schematic.png` 로 저장하고, 노션에서는 Spice Problem (a) 의 그림 자리에 넣는다.
