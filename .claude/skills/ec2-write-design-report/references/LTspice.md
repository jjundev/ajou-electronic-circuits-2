# LTspice 회로도 만들기 (Mac)

보고서의 회로도 그림(`report/figs/NN_schematic.png`)을 만드는 방법이다. 과제마다 다른 값은 그 과제의 `report/LTspice_작성메모.md` 에 적고, 여기에는 과제와 무관한 방법만 둔다. 2026-10-11 설계과제1 에서 확인한 내용이다.

## 설치

- `brew install --cask ltspice` 는 sudo 가 필요해 사용자가 터미널에서 직접 실행한다. 설치가 꼬이면 `brew reinstall --cask ltspice`.
- Mac 판 LTspice(26.x)는 Windows 판을 Wine 으로 감싼 것이라 Apple Silicon 에서는 Rosetta 2 가 필요하다 ("bad CPU type" 이 나오면 `softwareupdate --install-rosetta`, 사용자가 실행).
- `open -a LTspice` 가 -10669 로 실패할 수 있다. 아래 Wine CLI 로 띄운다.
- LTspice 창은 화면 제어 도구에 보이지 않는다. 회로도 캡처는 사용자에게 맡긴다.

## 회로도는 스크립트로 만든다

손으로 그리지 않고 `sim/ltspice/make_asc.py` 가 `.asc` 를 쓴다. 템플릿은 `설계과제/과제1/sim/ltspice/make_asc.py` 다 (`wire`·`flag`·`data`·`text`·`mos`·`vsrc` 도우미, 열 좌표 상수).

- **인코딩**: 한글(학번·이름)이 든 `.asc` 는 **BOM 없는 UTF-16LE + CRLF** 로 쓴다. UTF-8 은 한글이 깨지고, BOM 이 있으면 LTspice 가 열지 못한다.
  ```python
  Path("x.asc").write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-16-le"))
  ```
- **모델**: 과제 제공 라이브러리를 `.include ../MOSFET_model.lib` 로 넣고 그 안의 모델 이름(CMOSN/CMOSP)을 쓴다. `NMOS`·`PMOS` 같은 이름은 LTspice 내장 모델과 부딪친다. 전역 `standard.mos` 는 고치지 않는다.
- **심볼**: 소스가 VDD·GND 에 붙은 MOSFET 은 3단자 `nmos`/`pmos` 심볼을 쓴다 (body 가 소스에 묶임 = body → VDD/GND 결선과 같다). 소스가 떠 있는 MOSFET 은 `nmos4` 로 body 를 GND 에 따로 잇는다.
- **`.op` 라벨**: `DATAFLAG x y "V(op)"`, `"Id(M1)"` 처럼 식을 직접 적는다. 글자 가운데가 (x, y) 에 오므로 배선과 겹치지 않는 빈 곳에 둔다. 모델 이름은 `WINDOW 3 0 0 Invisible 2` 로 숨긴다.
- **소자 글자는 짧게**: MOSFET 옆에 보이는 `SYMATTR Value2` 에는 `l=… w=…` 만 둔다. `ad/as/pd/ps` 같은 추가 인스턴스 파라미터는 `SYMATTR SpiceLine` 에 넣는다. SpiceLine 도 넷리스트 줄 끝에 그대로 붙지만 회로도에는 보이지 않는다. Value2 에 다 넣으면 글자가 길어져 옆 소자 값과 `.op` 라벨을 덮는다 (2026-11-08 설계과제2: M3 글자가 RL 값을, M1·M2 글자가 Id 라벨을 덮었다).
- **표기**: 학번·이름은 `TEXT x y Left 3 ;<학번> <이름>` (주석 텍스트).

## 배치 실행으로 먼저 검증

GUI 를 열기 전에 배치로 돌려 배선 누락과 동작점을 확인한다. 경로는 `Z:\` + Mac 절대경로(`/` → `\`). macOS 에는 `timeout` 이 없어 `perl -e 'alarm N; exec @ARGV'` 로 감싼다.

```bash
perl -e 'alarm 120; exec @ARGV' "/Applications/LTspice.app/Contents/SharedSupport/ltspice/bin/wine" \
  --enable-alt-loader=macdrv --bottle=default --wait-children \
  --workdir 'C:/Program Files/ADI/LTspice' 'C:/Program Files/ADI/LTspice/LTspice.exe' \
  -b -ascii "Z:\Users\...\sim\ltspice\diffamp.asc"
```

- `diffamp.log` 에 떠 있는 노드·floating 경고가 없어야 한다 (설계과제1 에서 꼬리 전류원 드레인 배선 누락을 여기서 잡았다).
- `-ascii` 로 만든 `.raw` 의 동작점이 ngspice `op.txt` 와 표시 자릿수까지 맞는지 본다. `.raw` 를 읽을 때 `No. Variables:` 줄은 `rsplit` 으로 값만 떼어 낸다.

## 캡처

1. GUI 는 같은 명령에서 `-b -ascii` 대신 `-Run` 을 주고 `nohup … &` 로 띄운다.
2. `.op` 결과 창을 닫고 Space(Zoom to Fit) 한 뒤 사용자가 창을 캡처한다.
3. 캡처를 회로 영역만 남게 잘라 `report/figs/NN_schematic.png` 로 저장한다 (`NN` 은 본문 그림 순서, 양식.md §서식).
4. 확인: 학번·이름이 보이는지, 라벨이 배선이나 서로 겹치지 않는지, 라벨 값이 보고서 노드 표와 맞는지.

`.asc` 와 `make_asc.py` 는 커밋하고, LTspice 가 만드는 `.log`·`.net`·`.raw` 는 산출물이다.
