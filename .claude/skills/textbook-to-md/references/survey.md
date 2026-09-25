# 0단계 조사 — <<N>>장

당신은 조사 에이전트다. 저장소 파일을 만들거나 고치지 않고 git 상태도 바꾸지 않는다. 결과는 `<<SCRATCH>>/survey-ch<<N>>.md` 한 파일에만 쓴다. 확대 이미지도 `<<SCRATCH>>/` 아래에 둔다.

- 작업 루트: `<<REPO>>` (셸 명령은 이 폴더에서 실행)
- 원본: `<<PDF>>` (Razavi 마이크로전자회로 <<N>>장, 스캔본. 텍스트 레이어가 없으므로 페이지를 이미지로 렌더링해 읽는다)
- 먼저 `교과서/마이크로전자회로/FORMAT.md`를 전부 읽는다. 앞 장 README(`교과서/마이크로전자회로/ch09/README.md`)를 훑어 산출물 규모를 가늠한다.

## 도구
```bash
# 페이지 크기 — 너비 약 1100pt 이상이면 두 쪽 펼침
python3 -c "import fitz; d=fitz.open('<<PDF>>'); print([(i+1, round(p.rect.width), round(p.rect.height)) for i,p in enumerate(d)])"
# 페이지 전체 저해상도 (훑기용, 72–100 dpi)
python3 -c "import fitz,sys; d=fitz.open('<<PDF>>'); d[int(sys.argv[1])-1].get_pixmap(dpi=int(sys.argv[3])).save(sys.argv[2])" PAGE <<SCRATCH>>/pPAGE.png 90
# 부분 확대 (좌표 PDF pt, 왼쪽 위 원점)
python3 -c "import fitz,sys; d=fitz.open('<<PDF>>'); d[int(sys.argv[1])-1].get_pixmap(dpi=int(sys.argv[7]), clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" PAGE X0 Y0 X1 Y1 <<SCRATCH>>/OUT.png DPI
```

## 조사 순서
1. 페이지 크기로 펼침 페이지와 한 쪽 페이지를 가른다.
2. 모든 페이지를 90 dpi로 훑는다. 쪽 머리 번호로 PDF 페이지 ↔ 교재 쪽 대응을 만든다. 펼침 페이지는 왼쪽·오른쪽 쪽 번호를 둘 다 적는다.
3. 예제마다 위치(PDF 페이지, 교재 쪽, 펼침이면 왼쪽/오른쪽), 절, 문제 그림, 풀이 그림, 바로 뒤 연습문제 유무를 적는다. 연습문제가 없으면 그 자리를 확대해서 확인한다.
4. 장말 PROBLEMS를 조사한다.
   - 페이지별 문제 번호 범위, 절 머리(`Sec. N.x`) 위치, 그림 번호 범위
   - 별표(*) 개수와 SOL 표시: 여백을 200 dpi로 확인한다
   - Design Problems 머리와 공통 가정 머리말이 있는지, 있으면 위치
   - SPICE Problems 시작 위치 (범위 밖)
   - 마지막 문제가 다음 페이지로 이어지는지
5. FORMAT이 다루지 않는 그림 유형을 찾는다. FORMAT이 다루는 것은 회로, 등가회로, 회로 없이 그래프·파형·영상뿐인 그림, 회로와 파형 패널이 섞인 그림이다(FORMAT `## 본문 절` 5·6). 그 밖의 것(예: 스미스 차트, 표, 블록도)을 적는다.

## 산출물 (`<<SCRATCH>>/survey-ch<<N>>.md`)
```
# <<N>>장 조사

## 장 제목
<교재 인쇄 제목 (한국어)>

## 쪽 대응
| PDF | 교재 쪽 | 구성 (펼침/한 쪽, 본문/요약/PROBLEMS) |

## 예제
| 예제 | PDF | 교재 쪽 | 절 | 문제 그림 | 풀이 그림 | 연습문제 |

## 장말문제
| PDF | 교재 쪽 | 문제 번호 | 절 머리 | 그림 번호 |
- 별표: <번호: 개수 …>
- SOL: <번호 …>
- Design Problems: <머리 위치> / 공통 가정 머리말: 있음(PDF p, y 범위) | 없음
- SPICE Problems 시작: <위치>
- 마지막 문제의 끝: <위치>

## 새 그림 유형
<없음> 또는 <그림 번호, 모양, 어느 문제가 쓰는지>

## 묶음 제안
| 묶음 | 대상 | PDF 페이지 | 개수 |
(12–18개씩. 예제와 연습문제를 먼저 예제 순으로, 장말문제는 PDF 페이지 경계로 나눈다. 이름은 A, B, C …)
```
최종 메시지에는 산출물 경로와 다섯 줄 요약(예제 수, 연습문제 수, 장말문제 수, 새 그림 유형 유무, 묶음 수)만 적는다.
