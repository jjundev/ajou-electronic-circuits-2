# 검증·재개·게시

`verify`는 최종 자막본 `renders/final.mp4`를 검사한다. 마스터만 있으면 완료가 아니다. HyperFrames check와 전체 디코드, 1920×1080/30fps, 실측 WAV 샘플/해시, 최종 A/V 길이 차이 ≤1프레임을 검사한다. 자막은 Pretendard Bold FontSize14/Alignment2/MarginV22/Outline4/Shadow0/BorderStyle3, 흰 글자/약70% 검정 박스다. 한 줄 약34자로 분리하며 자막 중간 프레임을 마스터와 비교해 상단 PDF 침범과 하단 표시를 검사한다. 현재 source_hashes와 gate 증거 해시도 확인한다.

자동 검사는 내용·발음·회로 의미의 승인이 아니다. 동결 PDF/MD와 완성 프레임을 대조하고 최종 영상의 발음·수식·음성 동기화를 직접 검토한다. `verification/audio-review.json`, `visual-review.json`에 `{status:passed,input_hash,notes,evidence:{relative_path:sha256}}`를 작성한다. input_hash는 `verification_fingerprint(run)`으로 구한다. audio-review의 mode는 실제 청취한 경우에만 `live-listened`다. fake PCM은 live 음성 검토로 승인하지 않는다. 실제 음성 검토가 없으면 complete=false/live_audio=unverified이며 게시하지 않는다.

상태 순서: inputs → layers → script → voice → timing → composition → render → captions → verify → publish. `resume-set`은 각 단계 입력/출력 SHA256과 사용 도구 지문으로 처음 무효 단계를 돌려준다. map 변경은 layers부터, 음성 설정은 voice부터, 자막본 변조는 captions부터 재개한다. `source/manifest.json` 변경 후 검토 input_hash도 새로 작성한다. 성공 WAV는 물리적으로 삭제하지 않는다.

게시 직전에 최종 파일/검증 지문을 다시 확인한다. 같은 파일시스템 staging, 이전버전 backup, journal로 파일과 latest를 교체한다. 이동 실패 시 이미 교체한 파일도 복구한다. 중단된 pending journal은 다음 게시 때 복구한다. 같은 제목/문항 키 충돌은 오류다. 부분 성공은 현재 검증된 파일만 게시하되 latest를 유지한다. 기존 결과는 이전버전에 남고 마스터는 run에 남는다.

개발 수용 테스트는 실제 1002 E10.11/E10.13/2021-1_중간-Q3와 로컬 PCM을 별도 scratch에서 만든다. 개발 미디어 검사 통과와 실제 Aoede 청취 통과를 분리하여 기록한다. 승인 없는 유료 테스트·가짜 audio review로 게시하지 않는다.

수용 테스트 명령:

```sh
python3 .agents/skills/ec2-solution-video/tests/acceptance.py --dest /ABS/SCRATCH --hyperframes-entry /ABS/hyperframes/dist/cli.js
EC2_ACCEPTANCE_BATCH=/ABS/SCRATCH/문제풀이영상/1002/1002_제작자료/실행/RUN_ID python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v
```

기본 suite의 실제 미디어 수용 테스트는 명시적 scratch batch가 없으면 skip한다. 출력 로그의 BATCH 경로를 지정하면 세 문항의 전체 글자 공개·미디어·최종 해시와 비용 0을 검사한다. 입력 원본과 기존 스킬 해시 보존도 검사하고 fake PCM을 production publish가 거부해야 통과한다.

검증된 Manifest.title을 실제 파일명에 사용하며 금지된 파일명 문자는 공백으로 정리한다. 게시 영수증은 실제 MP4와 catalog SHA256을 저장한다. 정상 게시 후 재개는 완료로 판정하며, 게시된 파일이 바뀌면 publish 단계부터 다시 확인한다. 명시적 카메라도 마지막 전체 답안 hold를 덮을 수 없다.
