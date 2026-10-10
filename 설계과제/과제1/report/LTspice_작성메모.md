# 설계과제1 LTspice 회로도 작성 메모

보고서 2-(a) 의 회로도 캡처(`figs/schematic.png`)를 만들 때 쓰는 작업 메모다. 제출 본문에는 들어가지 않는다.

## 회로도 작성 순서

1. 과제 가이드대로 `standard.mos`를 교체한다(macOS: `~/Library/Application Support/LTspice/lib/cmp/`).
2. 소자: `nmos4` / `pmos4`, Value = `NMOS` / `PMOS`. 모든 소자에 L = 0.18u를 넣고, W는 보고서 1-(b) W 표를 따른다.
   Body는 NMOS → GND, PMOS → VDD에 연결한다(GAMMA = 0이라 결과에는 영향이 없다).
3. 전원: VDD = 1.5 V, $V_{b1}$ = 0.5966 V, $V_{b2}$ = 1.0 V, I1 = 100 µA (VDD 쪽이 아니라 $M_7$ 드레인 → GND 방향).
4. 입력: Vin1 = `SINE(0.7236 0.5m 1Meg)`. Vin2는 Advanced 탭에서 Phase = 180으로 둔다. AC 해석에는 각각 AC 0.5 / AC 0.5 (위상 180)을 넣는다.
5. `.op`를 실행한 뒤 노드에 마우스를 대거나 우클릭 → "Place .op Data Label"로 회로도 위에 전압·전류를 표시한다.
6. `.tran 0 5u 0 1n`으로 transient를, `.ac dec 50 1k 10G`으로 AC를 확인한다. 이득은 `V(op)-V(on)`으로 본다.

## 시뮬레이션 파일 (`sim/`)

| 파일 | 내용 |
|---|---|
| `handcalc.py` | 1)의 손계산 → `params.inc` 생성 |
| `core.inc` | 그림 1 회로 넷리스트 |
| `tune.cir` | $V_{b1}$ DC sweep (출력 CM 0.95 V 맞추기) |
| `diffamp.cir` | DC op / AC / Transient |
| `post.py` | 그래프와 saturation 표 생성 |

```bash
cd sim && python3 handcalc.py && ngspice -b diffamp.cir && python3 post.py
```

## 캡처 전 확인

- 회로도 빈 곳에 학번·이름 텍스트(`202220953 신현준`)를 넣는다.
- `.op` 라벨 값이 보고서 2-(a) 노드 표와 1 mV 안팎으로 맞는지 본다. CMFB 가 없어 출력 CM 이 $V_{b1}$ 에 매우 민감하므로(약 −57 V/V), 출력이 0.95 V 에서 크게 벗어나면 $V_{b1}$ 값(0.5966 V)부터 확인한다.
- 캡처는 `report/figs/schematic.png` 로 저장하고, 노션에서는 2-(a) 의 그림 자리에 넣는다.
