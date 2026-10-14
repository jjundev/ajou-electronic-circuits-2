# ec2-interactive와 1014 첫 발행 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 독립적인 ec2-interactive 스킬을 만들고 1014 자료 두 개를 실제 발행하여 기존 정리노트의 관련 설명에 연결한다.

**Architecture:** bio-interactive 35d4732의 템플릿·런타임·검사·저장·최신 연결 도구를 전자회로 저장소로 이식한다. 대상 해석과 회로 수치 모델은 작은 독립 모듈로 두고, 첫 두 자료는 같은 모델을 소스 HTML에 내장해 화면과 패널을 연동한다. 발행 전 검토를 완료하며 연결은 저장 도구가 반환한 실제 경로로만 실행한다.

**Tech Stack:** Node.js 20+, CommonJS, node:test, Canvas 2D, 기존 x-dc 마크업과 DCLogic 런타임, Windows PowerShell, 기존 Python HTML 검사기, 내장 브라우저.

**Spec:** `docs/superpowers/specs/2026-10-14-ec2-interactive-design.md` — 반드시 이 계획과 함께 읽는다. 사용자 #1=② 확정; 실행 방식 선택 전에는 이 문서의 작업을 실행하지 않는다.

## Global Constraints

- Node.js 20 이상; Windows PowerShell과 macOS의 NFC/NFD 경로를 지원한다.
- 원본은 .agents/skills/ec2-interactive/; .claude/skills/ec2-interactive는 같은 원본을 가리킨다.
- 기본 화면은 회전 없는 2D 회로도·파형·보데 선도이며 의미 있는 과정만 재생한다.
- 공통 상단 바·좌우 패널·od-theme·모바일 서랍·단계 선택·테마 스크롤바를 유지한다.
- HTML은 팩 최상위, 원본·canvas.json·검토 기록은 .assets/자료_인터렉티브_NN_<이름>/에 둔다.
- 기존 인터랙티브 자료를 덮어쓰지 않는다. 새 번호의 저장은 순차 실행한다.
- 정리노트 HTML의 안내·링크만 수정한다. MD·PDF·기존 위젯·본문·스타일·스크립트는 유지한다.
- 수치·회로 그림·패널·설명은 동일 모델을 사용하며 Hz/rad/s, 선형 이득/dB, 반전 부호를 명시한다.
- 수업 밖 위상·정현파 해석은 패널과 근거 문서에 (교과서 보충)으로 표시한다.
- 모든 저장 대상은 기계 검사·독립 회로 검산·내용 검토·브라우저 확인을 통과해야 한다.
- 브라우저 검사는 1440×900과 375×812에서 라이트·다크 모두 수행한다.
- 새 링크는 상대 경로와 target="_blank" rel="noopener noreferrer"를 사용한다.
- 새 안내 표식은 data-ec2-interactive이며 (새 탭) 같은 표시 문구는 붙이지 않는다.
- 외부 게시·자동 커밋·영상·복습문제 생성·SPICE 시뮬레이터는 범위 밖이다.

## Review Focus

1. 한 날짜가 여러 범위 폴더에 포함됨: 정확한 날짜 폴더가 없으면 임의 팩에 저장하지 않는다. Task 2의 AMBIGUOUS_TARGET 테스트.
2. 극점이 겹침: 낮은 극점을 전체 -3 dB 대역폭으로 표시하지 않는다. Task 3의 동일 극점 검산과 Task 4 패널 테스트.
3. 잘못된 슬라이더 입력과 범위 끝값: NaN 좌표나 멈춘 화면 대신 마지막 유효 상태를 유지하고 유효 끝값은 계산한다. Task 4의 핸들러·캔버스 테스트.
4. 자료 번호가 이미 차지되었거나 저장 중 실패함: 기존 바이트를 유지하고 자신이 만든 부분 파일만 복구한다. Task 2의 배타적 생성·롤백 테스트.
5. 노트에 중복 ID, 스크립트 속 가짜 HTML, 기존 목적지 링크가 있음: 잘못된 절을 수정하지 않고 실제 연결만 추가/보정하며 나머지 바이트를 보존한다. Task 5의 연결 회귀와 Task 6의 실제 노트 비교.

---

## 위치와 근거

아래 변수는 **계획의 실행 때** PowerShell에서 설정한다. 현재 체크아웃에 사용자의 변경이 생겼다면 덮어쓰지 않고 실행 작업을 분리한다. 격리가 필요하면 using-git-worktrees를 먼저 적용하고 반환받은 경로를 Repo로 쓴다. 새 브랜치가 필요하면 codex/ec2-interactive를 사용한다.

```powershell
$Repo = (Get-Location).Path
$BioRepo = 'C:\Users\Hyunjun\Desktop\현준대학\26-2\생명과학'
$BioSkill = Join-Path $BioRepo '.agents/skills/bio-interactive'
$Skill = Join-Path $Repo '.agents/skills/ec2-interactive'
$Run = Join-Path ([IO.Path]::GetTempPath()) ('ec2-interactive-1014-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Run | Out-Null
node -v
git status --short
git -C $BioRepo rev-parse HEAD
```

Expected: Node >=20; source HEAD=35d47326830928444004fff3cb197a5991c075ae. 다른 HEAD면 해당 커밋의 로컬 파일과 현재 파일을 비교하고 최신 노트 연결 기능을 유지한다. BioRepo의 .scratch 등 사용자 파일은 건드리지 않는다.

**읽을 근거:**

- `$BioSkill/SKILL.md`, `references/scene-api.md`, `references/note-links.md`, `scripts/resolve.cjs`, `save.cjs`, `build.cjs`, `check.cjs`.
- `복습노트/1014/.assets/정리노트_1014_Frequency_Response.md`: 296–505(CS), 608–953(보데·두 극점), 1088(밀러 범위).
- `복습노트/1014/정리노트_1014_Frequency_Response.html`: s0-3db, s1-bode, s2-cs-two-poles 및 기존 widget-gainbw/widget-cs2p.
- `STT/1014 전회2.md`, `강의노트/2026F_Lec5_FrequencyResponse_rev4.pdf` s5–9, `교과서/마이크로전자회로/11장.pdf`의 해당 전달함수와 정현파 응답 설명.
- `.claude/skills/ec2-review-pack/scripts/check_html.py`, `tests/test_pack_layout.py`.

## 파일 지도

| 파일 | 책임 |
|---|---|
| .agents/skills/ec2-interactive/SKILL.md | 요청 라우팅·발행 절차·완료/실패 보고 |
| assets/template.dc.html, assets/dc-runtime.js | 재사용하는 공통 화면과 마크업 런타임 |
| scripts/harness.cjs, check.cjs, steps.cjs | 컴포넌트 로딩·장면 검사·단계 보고 |
| scripts/resolve.cjs | 실제 노트·STT·팩·기존 자료·번호 해석 |
| scripts/build.cjs, save.cjs | 실행 가능한 HTML 빌드와 충돌 없는 저장 |
| scripts/link-notes.cjs | 원문을 재직렬화하지 않는 설명 뒤 링크 삽입 |
| scripts/frequency-model.cjs | 첫 자료의 순수 회로 계산; DOM·파일 접근 없음 |
| scripts/frequency-topics.cjs | 두 자료의 설정·문구·조작·회로/그래프 장면 |
| scripts/make-frequency-example.cjs | 템플릿과 모델·주제 훅으로 Main.dc.html 조립 |
| references/scene-api.md, design.md | 공통 셸 계약과 전자회로 화면 원칙 |
| references/topic-selection.md | 수업 범위·기존 자료와 차별되는 선정 기준 |
| references/circuit-verification.md | 단위·모델 가정·독립 수치 검토 계약 |
| references/note-links.md | 최신 연결 명세·상태·중복 방지 |
| references/example-frequency-response.dc.html | 실행 가능한 회로 예제; 첫 CS 자료와 같은 생성기로 만듦 |
| tests/*.test.cjs | 이식한 회귀 및 새 대상·저장·모델·조작 검사 |
| .claude/skills/ec2-interactive | .agents 원본을 가리키는 상대 디렉터리 링크 |
| 복습노트/1014/인터렉티브_NN_CS_이득과_대역폭.html | 첫 실제 자료 |
| 복습노트/1014/인터렉티브_NN_두_극점과_보데_근사.html | 둘째 실제 자료 |
| 각 .assets/자료_인터렉티브_NN_이름/ | Main.dc.html, canvas.json, brief.md, validation.json |
| 복습노트/1014/정리노트_1014_Frequency_Response.html | 검증된 자료의 문맥 링크만 추가 |

NN은 실제 save 결과로 정한다. 시작 시 자료가 없어 01/02로 예상되지만 번호를 명세나 링크에 하드코딩하지 않는다. 공통 셸의 DEMO 예시는 셸 회귀용으로 유지하되 발행 자료에는 DEMO를 남기지 않는다. DNA 참고 예제는 Task 4에서 회로 예제로 교체한다.

### Task 1: 공통 도구·화면 이식과 로컬 등록

**Files:**
- Create: `.agents/skills/ec2-interactive/{assets,scripts,references,tests}` — bio 스킬에 있는 파일을 먼저 동일 구조로 이식.
- Create: `.claude/skills/ec2-interactive` 링크.
- Test: `.agents/skills/ec2-interactive/tests/{template,check,steps,build,save,link-notes,resolve,skill}.test.cjs`.
- Modify after copying: `scripts/build.cjs` 29, `assets/template.dc.html` 283, `scripts/link-notes.cjs` 129 및 스킬 이름을 검사하는 테스트.

**Interfaces:**
- Consumes: bio 35d4732의 파일·기존 테스트.
- Produces: `check(file:string,opts?:{allowTemplate:boolean}):{ok,errors,details}`; `loadComponent(file:string,opts?:object):{c,store,win}`; `makeCtx():{ctx,calls}`; `makeCanvas(ctx,w=800,h=600)`; `build(srcFile,outFile):string`; `save({src,dest,name}):{nn,html,dir}`; `linkNotes({note,links,dryRun=false}):{note,changed,results}`.

- [x] **Step 1: 새 위치에서 재사용 테스트가 아직 실행되지 않음을 확인한다.**

```powershell
Test-Path -LiteralPath $Skill
node --test "$Skill/tests/template.test.cjs"
```

Expected: 새 스킬이 없으면 False와 파일 누락. 이미 있으면 복사하지 말고 사용자 변경과 기존 구현을 읽는다.

- [x] **Step 2: 스킬 원본을 한 번 복사하고 도메인 식별자만 바꾼다.**

```powershell
Copy-Item -LiteralPath $BioSkill -Destination $Skill -Recurse
Get-ChildItem -LiteralPath $Skill -Recurse -File |
  Where-Object { $_.Extension -in '.md','.cjs','.html','.js' } |
  ForEach-Object {
    $body = [IO.File]::ReadAllText($_.FullName)
    $next = $body.Replace('bio-interactive','ec2-interactive')
    if ($next -ne $body) { [IO.File]::WriteAllText($_.FullName, $next, [Text.UTF8Encoding]::new($false)) }
  }
$Link = Join-Path $Repo '.claude/skills/ec2-interactive'
if (-not (Test-Path -LiteralPath $Link)) {
  New-Item -ItemType SymbolicLink -Path $Link -Target '../../.agents/skills/ec2-interactive' | Out-Null
}
```

지금은 생물학 문구·예제가 남아 있어도 공통 셸과 도구의 기준 회귀를 먼저 확인한다. Task 4–5 전에는 이 복사본을 완성된 스킬이라고 보고하지 않는다. Windows에서 링크 생성이 권한 오류면 전체 복사본을 또 만들지 않는다. 가능한 디렉터리 링크를 사용하고 `fs.realpathSync(Link) === fs.realpathSync(Skill)`를 검증한다. 절대 경로 junction을 썼다면 최종 이식 가능성 제한을 보고한다.

- [x] **Step 3: 새 도메인 안내 표식을 검사하는 회귀를 추가한다.**

```js
// tests/link-notes.test.cjs의 첫 contextual-link 테스트에 추가
assert.match(changed, /data-ec2-interactive=/);
assert.doesNotMatch(changed, /data-bio-interactive=/);
```

나머지 연결 fixture의 PCR·겔 같은 테스트 내용은 오프셋 파서 검증용이므로 바꾸지 않아도 된다. 단, 실제 문서와 참고 예제에는 생물학 전용 내용이 남으면 안 된다.

- [x] **Step 4: 공통 테스트를 실행한다.**

```powershell
$NodeTests = Get-ChildItem -LiteralPath "$Skill/tests" -Filter '*.test.cjs' | Select-Object -ExpandProperty FullName
node --test $NodeTests
node "$Skill/scripts/check.cjs" "$Skill/assets/template.dc.html" --allow-template
```

Expected: inherited suite PASS, template 검사 ok. node:test의 VM 배열을 host 배열과 비교하는 테스트는 기존처럼 map으로 host 결과를 만들어 비교한다. 실제 실패가 생긴 부분만 수정한다.

- [x] **Step 5: 작업 단위 상태를 확인한다.**

```powershell
git diff --check
git status --short
```

자동 커밋하지 않는다. 후속 커밋 요청 시 이 작업의 메시지는 `feat(ec2-interactive): port interactive shell and tools`.

### Task 2: EC2 대상 해석과 저장 무결성

**Files:**
- Modify: `scripts/resolve.cjs`의 sttFor 26–31, 날짜 분기 74–80, 반환부 99–107.
- Modify: `scripts/save.cjs`의 35–45, `scripts/build.cjs`의 CLI 인자 처리 64–69.
- Test: `tests/resolve.test.cjs`, `tests/save.test.cjs`, `tests/build.test.cjs`.

**Interfaces:**
- Consumes: Task 1의 resolve/save/build와 실제 파일 경로.
- Produces: `resolve({repo,arg}):{kind,folder,exists,date,notes,noteHtml,stt,stts,existing,next}`; 기존 `nextNumber(folder):string`, `save({src,dest,name})` 시그니처 유지.

- [x] **Step 1: STT fixture 이름을 전회2로 바꾸고 범위·모호성 테스트를 추가한다.**

```js
test('EC2 STT is returned with its real NFD path', () => {
  const repo = fixture({
    '복습노트/1014/.assets/정리노트_1014_주파수.md': '## 주파수 응답',
    'STT/1014 전회2.md': 'RC와 두 극점'
  });
  const r = resolve({repo, arg:'1014'});
  assert.ok(r.stt && fs.existsSync(r.stt));
  assert.ok(nfc(r.stt).endsWith('STT/1014 전회2.md'));
  assert.equal(r.stts.length, 1);
});
test('a range pack collects every actual transcript in its range', () => {
  const repo = fixture({
    '복습노트/1007-1014/.assets/정리노트_1007-1014_X.md': '',
    'STT/1007 전회2.md': '', 'STT/1014 전회2.md': '', 'STT/1002 전회2.md': ''
  });
  assert.equal(resolve({repo,arg:'1007-1014'}).stts.length,2);
  assert.equal(resolve({repo,arg:'1014'}).stts.length,2);
});
test('overlapping ranges do not select a random pack', () => {
  const repo = fixture({
    '복습노트/1007-1014/.assets/정리노트_1007-1014_X.md':'',
    '복습노트/1010-1016/.assets/정리노트_1010-1016_Y.md':''
  });
  assert.throws(() => resolve({repo,arg:'1014'}), {code:'AMBIGUOUS_TARGET'});
});
```

- [x] **Step 2: 새 테스트가 기존 코드에서 실패하는지 확인한다.**

```powershell
node --test "$Skill/tests/resolve.test.cjs"
```

Expected: 생명 STT regex와 누락된 stts 또는 모호성 정책 때문에 FAIL.

- [x] **Step 3: 실제 경로를 반환하는 STT 해석과 날짜 선택을 구현한다.**

```js
// sttFor의 정규식만 변경; child/list/nfc/fail은 이식한 resolve.cjs 정의를 사용한다.
function sttFor(repo, date) {
  if (!date) return null;
  const dir = child(repo, 'STT');
  const hit = dir && list(dir).find(d => d.isFile() &&
    new RegExp('^' + date + '[ _]전회2\\.md$').test(nfc(d.name)));
  return hit ? path.join(dir, hit.name) : null;
}
function sttsFor(repo, folder, date) {
  const name = path.basename(folder);
  const m = name.match(/^(\d{4})(?:-(\d{4}))?$/);
  const start = m ? m[1] : date, end = m ? (m[2] || m[1]) : date;
  if (!start) return [];
  const dir = child(repo, 'STT');
  if (!dir) return [];
  return list(dir).filter(d => d.isFile()).map(d => {
    const match = nfc(d.name).match(/^(\d{4})[ _]전회2\.md$/);
    return match ? {date:match[1],file:path.join(dir,d.name)} : null;
  }).filter(x => x && start <= x.date && x.date <= end)
    .sort((a,b) => a.date.localeCompare(b.date)).map(x => x.file);
}
// resolve의 단일 날짜 분기에서 기존 hit 선택을 교체한다.
const exact = folders.find(f => f.name === a);
const containing = folders.filter(f => f.start <= a && a <= f.end);
if (!exact && containing.length > 1) throw fail('AMBIGUOUS_TARGET');
const hit = exact || containing[0];
// 나머지 hit/STT/no-target 분기는 기존 그대로 유지한다.
// 반환 전에 계산하고 기존 반환 객체의 stt 행을 아래 두 행으로 교체한다.
const stts = sttsFor(repo,folder,date);
// return 객체 안:
// stt: sttFor(repo,date) || stts[0] || null,
// stts,
```

export를 `{resolve,nextNumber}`로 유지한다. AMBIGUOUS_TARGET 발생 시 스킬이 실제 폴더 후보 목록을 읽어 보고하게 한다. 기존 날짜·주제·NFD·heading 우선·번호 회귀는 유지한다.

- [x] **Step 4: 배타적 저장과 부분 파일 복구 테스트를 추가한다.**

```js
test('a file occupied after number resolution is never overwritten', () => {
  const {src,dest} = setup();
  const realOpen = fs.openSync;
  let occupied;
  try {
    fs.openSync = function(file, flags) {
      if (flags === 'wx' && path.dirname(file) === dest) {
        occupied = file;
        fs.writeFileSync(file, 'concurrent owner');
      }
      return realOpen.apply(this,arguments);
    };
    assert.throws(() => save({src,dest,name:'CS'}), {code:'EEXIST'});
  } finally { fs.openSync = realOpen; }
  assert.equal(fs.readFileSync(occupied,'utf8'),'concurrent owner');
  assert.ok(!fs.existsSync(path.join(dest,'.assets','자료_인터렉티브_01_CS')));
});
test('a failed write removes only the new partial HTML', () => {
  const {src,dest} = setup();
  const realWrite = fs.writeFileSync;
  try {
    fs.writeFileSync = function(file) {
      if (typeof file === 'number') throw new Error('simulated disk failure');
      return realWrite.apply(this,arguments);
    };
    assert.throws(() => save({src,dest,name:'CS'}), /disk failure/);
  } finally { fs.writeFileSync = realWrite; }
  assert.deepEqual(fs.readdirSync(dest),[]);
});
```

같은 파일 안의 fs mock 테스트는 병렬로 실행하지 않는다. mock은 반드시 finally에서 복구한다.

- [x] **Step 5: 먼저 실패를 확인한 뒤 save의 쓰기를 배타적으로 구현한다.**

```powershell
node --test "$Skill/tests/save.test.cjs"
```

기존 저장 시퀀스에 아래 구현을 적용한다. mkdir(dir)은 기존 비재귀 형태를 유지한다.

```js
let fd = null, ownsHtml = false;
try {
  const copy = path.join(dir,'Main.dc.html');
  fs.copyFileSync(src,copy);
  fs.writeFileSync(path.join(dir,'canvas.json'),
    canvasJson(titleOf(fs.readFileSync(copy,'utf8'))));
  const page = build(copy,html);
  fd = fs.openSync(html,'wx');
  ownsHtml = true;
  fs.writeFileSync(fd,page,'utf8');
  fs.closeSync(fd);
  fd = null;
} catch (e) {
  if (fd !== null) { try { fs.closeSync(fd); } catch {} }
  if (ownsHtml) { try { fs.unlinkSync(html); } catch {} }
  fs.rmSync(dir,{recursive:true,force:true});
  dropEmptyAssets();
  throw e;
}
```

build CLI는 인자를 존재 확인한 뒤 resolve하도록 바꾼다.

```js
const [srcArg,outArg] = process.argv.slice(2);
if (!srcArg || !outArg) {
  console.error('usage: node build.cjs <Main.dc.html> <out.html>');
  process.exit(2);
}
const srcFile = path.resolve(srcArg), outFile = path.resolve(outArg);
```

`tests/build.test.cjs`에서 spawnSync(process.execPath,[cli])의 status===2를 추가하고 실제 source+out 성공 회귀를 유지한다.

- [x] **Step 6: 도구 및 실제 읽기 전용 해석을 확인한다.**

```powershell
node --test "$Skill/tests/resolve.test.cjs" "$Skill/tests/save.test.cjs" "$Skill/tests/build.test.cjs"
node "$Skill/scripts/resolve.cjs" $Repo 1014
git diff --check
```

Expected: PASS; 실제 noteHtml 하나, .assets MD 하나, STT/1014 전회2.md와 stts 목록이 반환됨.

### Task 3: 회로 수치 모델과 독립 기준값

**Files:**
- Create: `scripts/frequency-model.cjs`.
- Create: `tests/frequency-model.test.cjs`.
- Create: `references/circuit-verification.md`.

**Interfaces:**
- Consumes: 1014의 한 극점·두 극점 전달함수.
- Produces: `createFrequencyModel():{cs,two,wave}`.
- `cs({gm,RD,CL},omega)`, `two({gm,RS,Cin,RD,CL},omega)` → `{A0,wp1,wp2,fp1,fp2,f3db,mag,db,bodeDb,phaseDeg,inputLossDb,outputLossDb}`.
- `wave(response,tOverT,inputPeak=1e-4)` → `{vin,vout,inputPeak,outputPeak}`; 모두 SI 단위, A0는 크기이며 저주파 전달이득의 부호는 -A0.

- [x] **Step 1: 이미 알려진 특수값으로 테스트를 작성한다.**

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const {createFrequencyModel} = require('../scripts/frequency-model.cjs');
const M = createFrequencyModel();
const near = (actual,expected,eps=1e-10) =>
  assert.ok(Math.abs(actual-expected) <= eps*Math.max(1,Math.abs(expected)),
    actual + ' != ' + expected);
const p = {gm:0.002,RD:10000,CL:1e-13};
test('single-pole cutoff, inversion phase and gain-bandwidth product', () => {
  const r = M.cs(p,1e9);
  near(r.A0,20); near(r.wp1,1e9); near(r.fp1,159154943.09189534);
  near(r.mag,14.14213562373095); near(r.phaseDeg,-225);
  near(r.db,23.010299956639813);
  const biggerR = M.cs({...p,RD:100000},0);
  near(biggerR.A0,200); near(biggerR.fp1,r.fp1/10);
  near(biggerR.A0*biggerR.fp1,r.A0*r.fp1);
});
test('coincident poles have minus-six dB at the pole and a lower cutoff', () => {
  const same = {gm:0.005,RS:2000,Cin:5e-13,RD:2000,CL:5e-13};
  const r = M.two(same,1e9);
  near(r.A0,10); near(r.mag,5);
  near(r.db,13.979400086720375);
  near(r.phaseDeg,-270);
  near(r.f3db,102431206.69545889);
  near(M.two(same,2*Math.PI*r.f3db).mag,r.A0/Math.SQRT2);
});
test('wave output preserves the signed CS response at the cutoff', () => {
  const r = M.cs(p,1e9);
  near(M.wave(r,0).vout,0.001);
  near(M.wave(r,0.25).vout,-0.001);
});
test('positive component limits produce finite results; invalid units fail', () => {
  for (const RD of [100,100000]) for (const CL of [1e-14,1e-12]) {
    const r = M.cs({...p,RD,CL},1e9);
    for (const key of ['A0','wp1','fp1','f3db','mag','db','phaseDeg'])
      assert.ok(Number.isFinite(r[key]),key);
  }
  for (const value of [0,-1,NaN,Infinity])
    assert.throws(() => M.cs({...p,RD:value},1e9),RangeError);
  assert.throws(() => M.cs(p,-1),RangeError);
});
```

- [x] **Step 2: 모델 모듈 누락으로 실패하는지 확인한다.**

```powershell
node --test "$Skill/tests/frequency-model.test.cjs"
```

Expected: MODULE_NOT_FOUND.

- [x] **Step 3: 다음 코드로 순수 회로 모델을 구현한다.**

```js
function createFrequencyModel() {
  function positive(value,name) {
    if (!Number.isFinite(value) || value <= 0) throw new RangeError(name + ' must be positive SI');
    return value;
  }
  function frequency(w) {
    if (!Number.isFinite(w) || w < 0) throw new RangeError('omega must be finite and nonnegative');
    return w;
  }
  function response(A0,wp1,wp2,omega) {
    frequency(omega);
    const x = omega/wp1, y = wp2 ? omega/wp2 : 0;
    const inputLossDb = wp2 ? -10*Math.log10(1+x*x) : 0;
    const outputLossDb = -10*Math.log10(1+(wp2 ? y*y : x*x));
    const db = 20*Math.log10(A0)+inputLossDb+outputLossDb;
    const bodeDb = 20*Math.log10(A0)-20*Math.max(0,Math.log10(x))
      -(wp2 ? 20*Math.max(0,Math.log10(y)) : 0);
    let w3 = wp1;
    if (wp2) {
      const a = 1/(wp1*wp1)+1/(wp2*wp2);
      const b = 1/((wp1*wp2)*(wp1*wp2));
      w3 = Math.sqrt(2/(a+Math.sqrt(a*a+4*b)));
    }
    return {
      A0,wp1,wp2:wp2 || null,fp1:wp1/(2*Math.PI),
      fp2:wp2 ? wp2/(2*Math.PI) : null,f3db:w3/(2*Math.PI),
      mag:10**(db/20),db,bodeDb,
      phaseDeg:-180-(Math.atan(x)+(wp2 ? Math.atan(y) : 0))*180/Math.PI,
      inputLossDb,outputLossDb
    };
  }
  function cs(p,w=0) {
    const A0=positive(p.gm,'gm')*positive(p.RD,'RD');
    return response(A0,1/(p.RD*positive(p.CL,'CL')),null,w);
  }
  function two(p,w=0) {
    const A0=positive(p.gm,'gm')*positive(p.RD,'RD');
    const wp1=1/(positive(p.RS,'RS')*positive(p.Cin,'Cin'));
    const wp2=1/(p.RD*positive(p.CL,'CL'));
    return response(A0,wp1,wp2,w);
  }
  function wave(r,t,inputPeak=1e-4) {
    if (!Number.isFinite(t)) throw new RangeError('t/T must be finite');
    positive(inputPeak,'inputPeak');
    const theta=2*Math.PI*t;
    return {vin:inputPeak*Math.sin(theta),
      vout:r.mag*inputPeak*Math.sin(theta+r.phaseDeg*Math.PI/180),
      inputPeak,outputPeak:r.mag*inputPeak};
  }
  return Object.freeze({cs,two,wave});
}
module.exports={createFrequencyModel};
```

- [x] **Step 4: 테스트를 통과시키고 독립 복소수 식으로 표를 검산한다.**

```powershell
node --test "$Skill/tests/frequency-model.test.cjs"
python -c "import cmath,math; h=-20/(1+1j); print(abs(h), math.degrees(cmath.phase(h))); w=1e9*math.sqrt(math.sqrt(2)-1); print(w/(2*math.pi)); print(abs(-10/(1+1j*w/1e9)**2))"
```

Expected: single mag 14.1421356237, principal phase +135°(표시 -225°와 360° 차이); equal-pole cutoff 약 102431206.695 Hz, gain 7.071067812. 독립 식은 frequency-model을 import하지 않는다.

- [x] **Step 5: circuit-verification.md를 다음 계약으로 작성한다.**

```markdown
# 회로 내용·수치 검토

브리프의 근거 절·강의자료·교재를 먼저 읽는다. 계산 모듈을 호출한 결과만으로 독립 검산이라고 하지 않는다.

1. 소신호 회로 연결, 종속원 방향, AC 접지, gm·ro·기생 커패시턴스 가정을 대조한다.
2. 독립 복소수 전달함수로 기본·대표 설정·끝값을 계산한다. Hz=ω/(2π), 전압 크기 dB=20log10|H|를 검증한다.
3. 단일 극점의 상대 -3.0103 dB, 동일 두 극점의 상대 -6.0206 dB와 전체 -3 dB 위치를 검증한다.
4. CS 부호와 위상 기준을 확인한다. -225°와 +135°는 같은 위상이며 교재 보충 표시를 확인한다.
5. 모든 조작에서 회로 라벨·현재 그래프 표식·패널 값·단계 설명이 같은 상태를 설명하는지 확인한다.
6. 파형의 t/T·V/V_peak 축과 실제 진폭 표시를 확인한다. 소신호 선형 모델·클리핑 미포함을 명시한다.

Critical/Important를 모아 한 차례 수정하고 기계·수치·브라우저 검사를 다시 수행한다. 남은 결함은 주제 보류다.
검토 기록에는 source SHA-256, 근거, 독립 계산식·기준값, 발견/수정, pass/fail/not_run을 적는다.
```

### Task 4: 1014의 두 주제 소스·조작·장면 만들기

**Files:**
- Create: `scripts/frequency-topics.cjs`, `scripts/make-frequency-example.cjs`.
- Create: `tests/frequency-topics.test.cjs`.
- Create: `references/example-frequency-response.dc.html`.
- Modify: `tests/build.test.cjs`의 참고 예제와 title 검사.
- Remove after replacement: `references/example-dna.dc.html`.

**Interfaces:**
- Consumes: `createFrequencyModel`, template의 네 훅과 두 슬롯, Task 1의 harness/check/build.
- Produces: `createTopic(kind:'cs'|'two'):{title,config,left,right,hooks,drawScene}`; `makeSource(kind):string`; CLI `node make-frequency-example.cjs cs|two OUT.dc.html`.
- config: `{kind,gm,title,initial,controls,presets,mistakes,steps}`.
- source 안 전역 선언은 `FM`(순수 모델), `CFG`(직렬화 config), `drawFrequencyScene`(자체 포함 함수); 네 훅은 이 선언과 this만 사용한다.

- [x] **Step 1: 산출 소스를 통한 동작 테스트를 작성한다.**

```js
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {makeSource}=require('../scripts/make-frequency-example.cjs');
const {check}=require('../scripts/check.cjs');
const {loadComponent,makeCtx,makeCanvas}=require('../scripts/harness.cjs');
function source(kind) {
  const file=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'ec2-topic-')),'Main.dc.html');
  fs.writeFileSync(file,makeSource(kind)); return file;
}
test('both topics satisfy the shell and render at slider endpoints',()=>{
  for(const kind of ['cs','two']) {
    const file=source(kind);
    assert.deepEqual(check(file).errors,[]);
    const {c}=loadComponent(file);
    const {ctx,calls}=makeCtx(); c.attachCanvas(makeCanvas(ctx,375,640));
    for(const control of c.extraVals(c.state).controls) {
      for(const value of [control.min,control.max]) {
        control.change({target:{value:String(value)}});
        c.renderVals(); c.draw(0.016,0);
      }
    }
    assert.ok(calls.some(x=>x.op==='lineTo'));
    assert.ok(!calls.some(x=>x.args.some(v=>typeof v==='number'&&!Number.isFinite(v))));
    assert.ok(c.T.MODES.every(m=>!m.rotatable&&!m.autoSpin));
  }
});
test('invalid slider input retains the last valid state',()=>{
  const {c}=loadComponent(source('cs'));
  const before=JSON.stringify(c.state);
  c.extraVals(c.state).controls[0].change({target:{value:'bad'}});
  assert.equal(JSON.stringify(c.state),before);
});
test('equal-pole preset updates the total cutoff and every panel from one model',()=>{
  const {c}=loadComponent(source('two'));
  c.extraVals(c.state).presets.find(x=>x.key==='equal').pick();
  const v=c.extraVals(c.state);
  assert.ok(Math.abs(v.numeric.fp1-v.numeric.fp2)<1e-5);
  assert.ok(Math.abs(v.numeric.f3db-102431206.69545889)<0.01);
  assert.ok(v.numeric.f3db<v.numeric.fp1);
  assert.ok(Math.abs(v.numeric.gainSigned+10)<1e-10);
});
```

- [x] **Step 2: 새 모듈 누락으로 실패하는지 확인한다.**

```powershell
node --test "$Skill/tests/frequency-topics.test.cjs"
```

Expected: MODULE_NOT_FOUND.

- [x] **Step 3: config와 네 훅을 구성한다.**

아래 내용은 `frequency-topics.cjs`의 확정 데이터다. controls의 값은 log10(SI), 슬라이더 step은 any, 주파수는 낮은 극점 대비 비율이다.

```js
const CS = {
  kind:'cs',gm:0.002,title:'CS 이득과 대역폭',
  initial:{logRD:4,logCL:-13,logRatio:0,showApprox:true},
  controls:[
    {key:'logRD',label:'R_D (Ω)',min:2,max:5},
    {key:'logCL',label:'C_L (F)',min:-14,max:-12},
    {key:'logRatio',label:'입력 주파수 / 극점',min:-2,max:2}
  ],
  presets:[
    {key:'base',label:'기본',state:{logRD:4,logCL:-13,logRatio:0}},
    {key:'rd10',label:'R_D 10배',state:{logRD:5,logCL:-13,logRatio:0}},
    {key:'cl10',label:'C_L 10배',state:{logRD:4,logCL:-12,logRatio:0}}
  ],
  mistakes:[
    {title:'큰 이득과 넓은 대역폭',text:'R_D를 키우면 이득은 커지고 극점은 낮아져요. g_m과 C_L가 고정일 때 비교해요.'},
    {title:'CS 반전과 추가 위상',text:'CS 자체의 반전 -180°에 RC 위상이 더해져요. (교과서 보충)'},
    {title:'파형의 높이와 실제 진폭',text:'파형은 각 진폭으로 정규화해요. 실제 입력·출력 진폭은 숫자로 비교해요.'}
  ],
  steps:[
    {mode:'bode',title:'저주파 이득',who:'g_m R_D',text:'커패시터의 영향이 작은 곳에서 전달이득은 -g_m R_D예요. 부호와 크기를 구별해요.'},
    {mode:'bode',title:'극점과 대역폭',who:'R_D C_L',text:'ω_p=1/(R_D C_L)예요. 이 한 극점 모델에서 f_p가 전체 -3 dB 대역폭이에요.'},
    {mode:'bode',title:'저항과 커패시턴스',who:'대표 설정',text:'R_D 10배와 C_L 10배를 차례로 눌러 보세요. 둘 다 극점은 낮아지지만 저주파 이득은 다르게 변해요.'},
    {mode:'wave',f:1,phase:'정현파',title:'출력 파형 읽기',who:'정현파 입력',text:'입력 주파수/극점 비율을 바꾸며 반전·추가 위상과 실제 출력 진폭을 함께 읽어요. (교과서 보충)'}
  ]
};
const TWO = {
  kind:'two',gm:0.005,title:'두 극점과 보데 근사',
  initial:{logRS:3,logCin:-13,logRD:Math.log10(2000),logCL:Math.log10(5e-13),logRatio:0,showApprox:true},
  controls:[
    {key:'logRS',label:'R_S (Ω)',min:2,max:4},
    {key:'logCin',label:'C_in (F)',min:-14,max:-12},
    {key:'logRD',label:'R_D (Ω)',min:2,max:5},
    {key:'logCL',label:'C_L (F)',min:-14,max:-12},
    {key:'logRatio',label:'관찰 주파수 / 낮은 극점',min:-2,max:2}
  ],
  presets:[
    {key:'base',label:'기본',state:{logRS:3,logCin:-13,logRD:Math.log10(2000),logCL:Math.log10(5e-13),logRatio:0}},
    {key:'input',label:'입력 극점 먼저',state:{logRS:4,logCin:-12,logRD:Math.log10(2000),logCL:-13,logRatio:0}},
    {key:'equal',label:'극점 겹침',state:{logRS:Math.log10(2000),logCin:Math.log10(5e-13),logRD:Math.log10(2000),logCL:Math.log10(5e-13),logRatio:0}},
    {key:'rd',label:'R_D 증가',state:{logRS:3,logCin:-13,logRD:4,logCL:Math.log10(5e-13),logRatio:0}}
  ],
  mistakes:[
    {title:'극점과 전체 대역폭',text:'극점이 겹치면 그 주파수에서 전체 -6 dB예요. 전체 -3 dB 대역폭은 더 낮아요.'},
    {title:'rad/s와 Hz',text:'Hz로 바꾸려면 2π로 나눠요. 그래프 축의 단위를 먼저 확인해요.'},
    {title:'정확식과 보데 근사',text:'점선은 직선 근사예요. 극점 근처의 실제 곡률과 오차를 실선에서 확인해요.'}
  ],
  steps:[
    {mode:'bode',title:'입력 노드',who:'R_S C_in',text:'입력 RC가 첫 번째 극점을 만들어요. 입력 값을 바꾸며 해당 표식을 확인해요.'},
    {mode:'bode',title:'출력 노드',who:'R_D C_L',text:'출력 RC가 두 번째 극점을 만들어요. R_D는 저주파 이득도 바꿔요.'},
    {mode:'parts',title:'노드별 손실',who:'dB 합',text:'노드별 dB 손실을 더하면 전체 상대 손실이 돼요. 이 모델에서는 두 RC가 독립이에요.'},
    {mode:'bode',title:'겹친 극점',who:'극점 겹침 설정',text:'극점 겹침을 누르고 극점과 전체 -3 dB 대역폭 숫자를 비교해 보세요.'}
  ]
};
```

네 훅은 다음 코드를 사용한다. `createTopic`에서 반환할 때 config는 CS/TWO에서 선택하고, hooks는 이 객체를 사용한다. 마지막 drawScene 필드는 다음 Step의 `drawFrequencyScene`이다.

```js
const hooks = {
  topic() {
    const other=CFG.kind==='cs'?'wave':'parts';
    const mode=(key,label)=>({
      key,label,cam:{yaw:0,pitch:0,zoom:1},fit:[16,14],D:60,
      autoSpin:false,rotatable:false,
      playback:key==='wave'?{fmax:4,rate:0.5,label:f=>'정현파 · '+f.toFixed(1)+' / 4'}:null,
      canvasLabel:()=>CFG.title+'의 '+label+' 화면. 회로와 그래프를 함께 비교해요.'
    });
    return {
      MODES:[mode('bode','응답'),mode(other,other==='wave'?'파형':'기여')],
      STEPS:CFG.steps.map(s=>Object.assign({c:'#1677ff'},s)),
      MISTAKES:{bode:CFG.mistakes,[other]:CFG.mistakes},
      TOGGLES:{bode:[['showApprox','보데 근사']]},
      PAL:{
        light:{bg:'#ffffff',labelBg:'#f7f8fa',ink:'#111111',ring:'#111111',a:'#1677ff',b:'#d92d20',link:'#6b7280',blobAlpha:0.3},
        dark:{bg:'#17171c',labelBg:'#212128',ink:'#f2f4f6',ring:'#f2f4f6',a:'#6ea4ff',b:'#ff8a7a',link:'#a3abb8',blobAlpha:0.42}
      }
    };
  },
  buildScene(mode,I,O) { drawFrequencyScene(this,mode,I,O,CFG,FM); },
  extraState() { return Object.assign({},CFG.initial); },
  extraVals(st) {
    const p={gm:CFG.gm,RD:10**st.logRD,CL:10**st.logCL};
    if(CFG.kind==='two') Object.assign(p,{RS:10**st.logRS,Cin:10**st.logCin});
    const base=FM[CFG.kind](p,0);
    const omega=Math.min(base.wp1,base.wp2||base.wp1)*10**st.logRatio;
    const r=FM[CFG.kind](p,omega);
    const fmt=(x,u)=>x.toPrecision(4)+' '+u;
    const controls=CFG.controls.map(def=>Object.assign({},def,{
      value:String(st[def.key]),
      display:def.key==='logRatio'?fmt(10**st[def.key],'배'):fmt(10**st[def.key],def.label.includes('(F)')?'F':'Ω'),
      change:e=>{
        const v=Number(e.target.value);
        if(!Number.isFinite(v)) return;
        this.setState({[def.key]:Math.max(def.min,Math.min(def.max,v)),step:-1});
      }
    }));
    return {
      controls,
      presets:CFG.presets.map(preset=>({key:preset.key,label:preset.label,
        pick:()=>this.setState(Object.assign({},preset.state,{playing:false,step:-1}))})),
      numeric:{gainSigned:-r.A0,fp1:r.fp1,fp2:r.fp2,f3db:r.f3db,omega,mag:r.mag,phaseDeg:r.phaseDeg},
      tiles:[
        {label:'저주파 전달이득',value:fmt(-r.A0,'V/V')},
        {label:'전체 -3 dB 대역폭',value:fmt(r.f3db,'Hz')},
        {label:'현재 주파수',value:fmt(omega/(2*Math.PI),'Hz')},
        {label:'현재 크기',value:fmt(r.mag,'V/V')}
      ],
      poles:'ω_p1='+fmt(r.wp1,'rad/s')+(r.wp2?' · ω_p2='+fmt(r.wp2,'rad/s'):''),
      waveInfo:'위상 '+r.phaseDeg.toFixed(1)+'° · 입력 0.1000 mV · 출력 '+(r.mag*0.1).toFixed(4)+' mV (교과서 보충)',
      assumptions:CFG.kind==='cs'?'소신호 선형 모델 · r_o=∞ · g_m 고정 · 클리핑 미포함':
        '입력·출력 RC 독립 · r_o=∞ · C_gd·몸체 효과 제외 · g_m 고정',
      legend:{a:this.pal().a,b:this.pal().b}
    };
  }
};
const left = '<div class="sec"><h2 class="sec-title">값 바꾸기</h2>'+
  '<sc-for list="{{controls}}" as="ctl"><div class="sub"><label for="ec2-{{ctl.key}}">{{ctl.label}} · {{ctl.display}}</label>'+
  '<input id="ec2-{{ctl.key}}" type="range" min="{{ctl.min}}" max="{{ctl.max}}" step="any" value="{{ctl.value}}" onChange="{{ctl.change}}"></div></sc-for></div>'+
  '<div class="sec"><h2 class="sec-title">대표 설정</h2><sc-for list="{{presets}}" as="pre">'+
  '<button class="btn" type="button" onClick="{{pre.pick}}">{{pre.label}}</button></sc-for></div>';
const right='<div class="sec"><div class="tiles"><sc-for list="{{tiles}}" as="tile">'+
  '<div class="tile"><b>{{tile.value}}</b><span>{{tile.label}}</span></div></sc-for></div>'+
  '<p class="sub">{{poles}}</p><p class="sub">{{assumptions}}</p>'+
  '<sc-if value="{{is.wave}}"><div><p class="sub">{{waveInfo}}</p><p class="sub">t/T와 각 V/V_peak로 정규화한 파형이에요.</p></div></sc-if>'+
  '<p class="sub">응답: 파랑 실선은 정확한 크기, 회색 점선은 보데 근사예요. 기여: 파랑은 입력, 빨강은 출력, 회색은 합이에요.</p></div>';
function createTopic(kind) {
  const config=kind==='cs'?CS:kind==='two'?TWO:null;
  if(!config) throw new RangeError('kind must be cs or two');
  const markupRight=kind==='cs'?right:right.replace(/<sc-if value="\{\{is\.wave\}\}">[\s\S]*?<\/sc-if>/,'');
  return {title:config.title,config,left,right:markupRight,hooks,drawScene:drawFrequencyScene};
}
module.exports={createTopic};
```

`is.wave`는 two의 modes에 없으므로 createTopic이 two용 right에서 sc-if 블록을 제거한다. 그래야 unknownHoles 검사를 통과한다.

- [x] **Step 4: drawFrequencyScene을 구현한다.**

아래 함수는 입력/출력 노드를 구분한 소신호 등가회로와 동일 모델의 그래프를 만든다. drawScene은 실행될 때 주입된 FM만 사용하며 require·DOM·window에 의존하지 않는다.

```js
function drawFrequencyScene(c,mode,I,O,cfg,M) {
  const st=c.state,pal=c.pal();
  const p={gm:cfg.gm,RD:10**st.logRD,CL:10**st.logCL};
  if(cfg.kind==='two') Object.assign(p,{RS:10**st.logRS,Cin:10**st.logCin});
  const base=M[cfg.kind](p,0), low=Math.min(base.wp1,base.wp2||base.wp1);
  const high=Math.max(base.wp1,base.wp2||base.wp1), w=low*10**st.logRatio;
  const r=M[cfg.kind](p,w);
  const line=(a,b,color=pal.link,width=0.035)=>I.push({k:1,p:[a[0],a[1],0],q:[b[0],b[1],0],w:width,c:color,flat:true});
  const text=(x,y,value,color=pal.ink)=>I.push({k:3,p:[x,y,0],text:value,size:0.38,c:color});
  const ground=(x,y)=>{line([x,y],[x,y-0.15]);for(let n=0;n<3;n++)line([x-0.3+n*0.07,y-0.15-n*0.1],[x+0.3-n*0.07,y-0.15-n*0.1]);};
  const resistor=(x,y)=>{line([x,y],[x,y-0.35]);let a=[x,y-0.35];for(let n=0;n<6;n++){const b=[x+(n%2?0.18:-0.18),y-0.5-n*0.15];line(a,b);a=b;}line(a,[x,y-1.55]);};
  const capacitor=(x,y)=>{line([x,y],[x,y-0.7]);line([x-0.35,y-0.7],[x+0.35,y-0.7]);line([x-0.35,y-0.9],[x+0.35,y-0.9]);line([x,y-0.9],[x,y-1.55]);};
  // Output R_D, C_L and downward gm*v_in/v_X controlled current source are parallel.
  line([2,4.8],[6,4.8]);line([2,2.5],[6,2.5]);
  resistor(4,4.8);line([4,3.25],[4,2.5]);
  capacitor(6,4.8);line([6,3.25],[6,2.5]);
  line([2,4.8],[2,4.2]);line([2,3.2],[2,2.5]);
  const diamond=[[2,4.2],[2.5,3.7],[2,3.2],[1.5,3.7],[2,4.2]];
  for(let n=1;n<diamond.length;n++)line(diamond[n-1],diamond[n]);
  line([2,4],[2,3.4],pal.b);I.push({k:4,p:[2,4,0],q:[2,3.4,0],c:pal.b});
  ground(4,2.5);text(4.2,5.5,'v_out');text(4.7,4,'R_D');text(6.4,4,'C_L');
  text(0.7,3,'g_m '+(cfg.kind==='two'?'v_X':'v_in'),pal.b);
  if(cfg.kind==='two') {
    line([-6,4.8],[-5.4,4.8]);
    let a=[-5.4,4.8];for(let n=0;n<6;n++){const b=[-5.2+n*0.22,4.8+(n%2?0.18:-0.18)];line(a,b);a=b;}
    line(a,[-2.5,4.8]);capacitor(-2.5,4.8);ground(-2.5,3.25);
    text(-5,5.5,'R_S');text(-2.1,4,'C_in');text(-2.5,5.5,'v_X');
  } else {line([-6,4.8],[-2.5,4.8]);text(-3.8,5.5,'v_in');}
  text(-6.2,4,'입력');text(0,6.2,'AC 접지 기준 소신호 등가회로');
  const x0=-6,x1=6,y0=-5.2,y1=0.8;
  line([x0,y0],[x1,y0]);line([x0,y0],[x0,y1]);
  if(mode==='wave') {
    text(0,1.25,'정규화 입출력 · 실제 진폭은 설명 패널');text(0,-6.1,'t/T');text(-6.4,0.2,'V/V_peak');
    let lastIn=null,lastOut=null;
    for(let n=0;n<=240;n++){
      const t=n/60, wave=M.wave(r,t);
      const a=[x0+(x1-x0)*n/240,-2.2+2*wave.vin/wave.inputPeak];
      const b=[a[0],-2.2+2*wave.vout/wave.outputPeak];
      if(lastIn)line(lastIn,a,pal.a);if(lastOut)line(lastOut,b,pal.b);
      lastIn=a;lastOut=b;
    }
    const now=x0+(x1-x0)*c.sim.f/4;line([now,y0],[now,y1],pal.link);
    text(-4.5,-5.7,'입력',pal.a);text(4.5,-5.7,'출력',pal.b);
    return;
  }
  const lf0=Math.log10(low)-2,lf1=Math.log10(high)+2;
  const maxDb=mode==='parts'?5:20*Math.log10(base.A0)+5,minDb=maxDb-85;
  const xOf=q=>x0+(Math.log10(q)-lf0)/(lf1-lf0)*(x1-x0);
  const yOf=db=>y0+(db-minDb)/(maxDb-minDb)*(y1-y0);
  for(let n=0;n<=4;n++){const lf=lf0+(lf1-lf0)*n/4,x=xOf(10**lf);line([x,y0],[x,y1],pal.link,0.015);text(x,-5.7,'10^'+lf.toFixed(1));}
  for(let n=0;n<=4;n++){const db=minDb+(maxDb-minDb)*n/4; text(-6.5,yOf(db),db.toFixed(0));}
  text(0,-6.3,'ω (rad/s, 로그 축)');text(-6.2,1.3,mode==='parts'?'손실 dB':'|H| dB');
  const curve=(key,color,dashed=false)=>{
    let last=null;
    for(let n=0;n<=240;n++){
      const q=10**(lf0+(lf1-lf0)*n/240),value=M[cfg.kind](p,q);
      const db=key==='sum'?value.inputLossDb+value.outputLossDb:value[key];
      if(db<minDb||db>maxDb){last=null;continue;}
      const point=[xOf(q),yOf(db)];
      if(last&&(!dashed||n%4<2))line(last,point,color);
      last=point;
    }
  };
  if(mode==='parts'){curve('inputLossDb',pal.a);curve('outputLossDb',pal.b);curve('sum',pal.link);}
  else {curve('db',pal.a);if(st.showApprox)curve('bodeDb',pal.link,true);}
  [base.wp1,base.wp2].filter(Boolean).forEach((q,n)=>{
    line([xOf(q),y0],[xOf(q),y1],n?pal.b:pal.a,0.025);
    text(xOf(q)+(n?0.45:-0.45),y1-(n?0.4:0),'ω_p'+(n+1),n?pal.b:pal.a);
  });
  const currentDb=mode==='parts'?r.inputLossDb+r.outputLossDb:r.db;
  const markerY=yOf(currentDb);
  if(markerY>=y0&&markerY<=y1)I.push({k:0,p:[xOf(w),markerY,0],r:0.1,c:pal.a,flat:true});
}
```

출력 회로의 R_D와 C_L 숫자는 설명 패널 controls와 대응한다. 브라우저 검토에서 표식·축·한글 라벨이 겹치면 좌표·fit·짧은 문구를 조정한다. 375px에서 축 글자가 너무 작으면 콘텐츠 모드를 나누거나 라벨을 줄인다. 그림의 전기적 연결·화살표·단위는 바꾸지 않는다.

- [x] **Step 5: makeSource를 구현해 모델·훅·슬롯을 내장한다.**

```js
const fs=require('node:fs'),path=require('node:path');
const {createFrequencyModel}=require('./frequency-model.cjs');
const {createTopic}=require('./frequency-topics.cjs');
function replaceOnce(src,re,value) {
  const hits=[...src.matchAll(new RegExp(re.source,'g'))];
  if(hits.length!==1)throw new Error('template anchor count '+hits.length);
  return src.replace(re,()=>value);
}
function makeSource(kind) {
  const topic=createTopic(kind);
  let src=fs.readFileSync(path.join(__dirname,'../assets/template.dc.html'),'utf8');
  src=src.replaceAll('__TITLE__',topic.title);
  for(const side of ['left','right']){
    const re=new RegExp('<!-- SLOT:'+side+' -->[\\s\\S]*?<!-- /SLOT:'+side+' -->');
    src=replaceOnce(src,re,'<!-- SLOT:'+side+' -->\n'+topic[side]+'\n<!-- /SLOT:'+side+' -->');
  }
  const methods=Object.values(topic.hooks).map(fn=>'  '+fn.toString()).join('\n\n');
  src=replaceOnce(src,/  topic\(\) \{[\s\S]*?(?=  \/\/ ================= 공통 셸)/,
    methods+'\n\n');
  const declarations=createFrequencyModel.toString()+'\nconst FM=createFrequencyModel();\nconst CFG='+
    JSON.stringify(topic.config)+';\n'+topic.drawScene.toString()+'\n';
  src=src.replace('class Component extends DCLogic {',declarations+'class Component extends DCLogic {');
  return src;
}
if(require.main===module){
  const [kind,out]=process.argv.slice(2);
  if(!['cs','two'].includes(kind)||!out){console.error('usage: node make-frequency-example.cjs cs|two OUT.dc.html');process.exit(2);}
  fs.writeFileSync(path.resolve(out),makeSource(kind));
}
module.exports={makeSource};
```

템플릿 훅 구간 교체는 공통 셸 구분 주석 앞에서 멈춘다. 문자열/brace 수를 추측하는 regex로 메서드 하나씩 파싱하지 않는다.

- [x] **Step 6: 소스 테스트와 회로 예제 빌드를 확인한다.**

```powershell
node --test "$Skill/tests/frequency-model.test.cjs" "$Skill/tests/frequency-topics.test.cjs"
node "$Skill/scripts/make-frequency-example.cjs" cs "$Skill/references/example-frequency-response.dc.html"
node "$Skill/scripts/check.cjs" "$Skill/references/example-frequency-response.dc.html"
```

build.test.cjs의 EX 경로를 example-frequency-response.dc.html로, DNA title 검사를 CS 이득과 대역폭으로 바꾼다. 새 예제 확인 후 이전 example-dna.dc.html만 제거한다. 기능을 검증하지 않는 생물학 문자열 포함 테스트를 늘리지 않는다.

### Task 5: 전자회로 스킬·레퍼런스 완성 및 연결 회귀

**Files:**
- Modify: `SKILL.md`, `references/{scene-api,design,topic-selection,note-links}.md`.
- Modify: `tests/skill.test.cjs`의 과목별 예제·경로 규칙.
- Test: `tests/link-notes.test.cjs`; Task 1에서 표식을 변경한 실제 도구 사용.

**Interfaces:**
- Consumes: Tasks 1–4의 도구 계약·회로 예제.
- Produces: 생성/연결 전용 요청을 구분하는 스킬, `RUN/note-links.json` 계약, 검토 결과 보고.

- [x] **Step 1: SKILL.md의 frontmatter와 기본 계약을 아래 내용으로 교체한다.**

```yaml
---
name: ec2-interactive
description: '전자회로2 복습노트 날짜나 주제로 회로도·파형·그래프를 연동하는 인터랙티브 HTML을 만들고 기존 정리노트의 관련 설명에 새 탭 링크를 연결한다. 인터랙티브 자료 제작, 움직이는 회로 자료, 기존 인터랙티브 링크 연결 또는 /ec2-interactive [MMDD|MMDD-MMDD|주제]에 사용한다. 정리노트·문제·PDF·영상 생성은 별도 스킬이다.'
---
```

본문은 bio의 0–9단계 순서를 유지하고 아래 차이를 적용한다.

| 구간 | 정확한 변경 |
|---|---|
| 준비 | 복습노트/, STT/, 강의노트/, 교과서/마이크로전자회로/와 Node>=20 확인; 미충족은 경로와 누락을 보고 |
| 경로 | SKILL은 실제 원본; RUN은 임시 실행 ID; PowerShell 변수는 호출마다 재설정하거나 절대 경로 사용 |
| 대상 | stt+stts 계약, NO_ARG/NO_TARGET/AMBIGUOUS_TARGET; 날짜 범위는 기존 통합 팩만 |
| 선정 | 기본 2–4개, 적합한 후보 1개면 1개; 기존 위젯과 동일 조작만 반복하면 제외 |
| 작성 | 네 훅·슬롯·FM 내장 예제; 평면 기본; 적합한 모델을 사용하고 빈 장면 금지 |
| 내용 검토 | 별도 검토자가 근거 자료와 단계를 대조; circuit-verification.md의 독립 계산 필수 |
| 모델 지정 | opus→sol 같은 고정 치환 문구 제거; 실제 도구·허용 모델을 따름 |
| 검사/브라우저 | check, steps, 4개 viewport/theme 조합, 콘솔·조작·극점·단위·파형 검증 |
| 저장 | save를 순차 실행; JSON 실제 경로 사용; Main.dc.html·canvas.json은 .assets/ 제작자료 |
| 연결 | 최신 note-links 기능, data-ec2-interactive, 실제 경로·절·관찰 포인트, dry-run→apply→idempotence |
| 보고 | 파일·선정 이유·보류·모델 가정·교과서 보충·검토·연결 상태·RUN; 자동 커밋 없음 |

중간 승인 요청을 스킬의 기본 생성 흐름에 추가하지 않는다. 근거·후보·검토가 부족하면 해당 자료만 보류한다. 별도 검토 도구가 없는 환경에서는 not_run을 pass로 바꾸지 않는다.

- [x] **Step 2: topic-selection.md를 다음 내용으로 작성한다.**

```markdown
# 전자회로 주제 선정

정리노트의 H2/H3 본문을 후보로 삼고, 이웃한 같은 회로 설명을 합친다. 노트가 없으면 STT와 강의자료 범위로 후보를 만든다.

| 기준 | 점수 |
|---|---|
| 값을 바꾸면 이득·파형·극점·전류가 달라지는 관계 | +2 |
| 동작점→소신호 모델→식처럼 단계별 해석이 필요한 과정 | +2 |
| 회로 연결·전류 경로·노드 역할을 비교하면 도움이 됨 | +2 |
| 기존 직접 해 보기에서 더 보여 줄 구체적 학습 목표가 있음 | +1 |

3점 이상을 우선하여 날짜당 2–4개, 명시 주제는 1개를 만든다. 적합한 후보가 1개면 1개만 만든다.
정의·역사·다음 시간 예고, 기존 자료와 동일한 대상·조작만 반복하는 후보는 제외한다. 후보 없음은 이유를 보고한다.

브리프에는 제목·이름·점수·모드·조작 범위·대표 설정·해석 단계·기억할 오개념 3개·수식과 모델 가정·단순화·근거 절/쪽·교과서 보충을 기록한다.
정리노트 연결에는 실제 noteHtml 경로·sectionId·필요한 anchorId·관찰 포인트를 담은 before/label/after를 기록한다.
```

- [x] **Step 3: 디자인·장면 계약을 과목에 맞게 바꾼다.**

design.md의 DNA 기준을 example-frequency-response로 교체한다. 공간 구조·분자 수·5′→3′ 규칙은 제거하고 전기적 연결·종속원 방향·AC 접지·부호·단위·근사 가정으로 대체한다. 공통 패널 순서, 44px 버튼, 색 외 라벨, 해요체, 토큰 색, 모바일 서랍은 유지한다.

scene-api.md에 아래 실제 사용 예를 추가한다.

```js
// 평면 회로 모드
{key:'bode',label:'응답',cam:{yaw:0,pitch:0,zoom:1},fit:[16,14],D:60,
 autoSpin:false,rotatable:false,playback:null,
 canvasLabel:()=> 'CS 소신호 회로와 주파수 크기 응답'}
// 스크립트 슬롯에서 입력 핸들러를 extraVals로 반환한다.
change:e=>{
  const value=Number(e.target.value);
  if(Number.isFinite(value)) this.setState({logRD:Math.max(2,Math.min(5,value))});
}
```

note-links.md는 생명과학 최신 명세를 그대로 유지하고 표식만 ec2로 바꾼다. “정리노트 MD는 수정하지 않음”을 경계로 명시한다. source reference에 외부 저장소 실행 경로를 남기지 않는다.

- [x] **Step 4: 문서 회귀의 과목 전용 기대값을 바꾸고 전체 검사한다.**

`tests/skill.test.cjs`의 lac_오페론_스위치 예시 기대값은 CS_이득과_대역폭으로, 생명과학 저장소 경계는 교과서/마이크로전자회로/로 변경한다. 과거 문구만 맞추려고 실제 계약을 왜곡하지 않는다. referenced-file-exists 테스트는 새 circuit-verification과 회로 예제를 포함한다.

```powershell
$NodeTests = Get-ChildItem -LiteralPath "$Skill/tests" -Filter '*.test.cjs' | Select-Object -ExpandProperty FullName
node --test $NodeTests
python 'C:/Users/Hyunjun/.codex/skills/.system/skill-creator/scripts/quick_validate.py' $Skill
git diff --check
```

Python이 없으면 load_workspace_dependencies로 bundled runtime 경로를 찾는다. validator가 출력한 SKILL 오류만 수정하고 일반 문서 전체를 재작성하지 않는다.

### Task 6: 1014 실제 생성·검토·발행·노트 연결

**Files:**
- Create: `RUN/{cs,two}/brief.md`, `Main.dc.html`, `preview.html`, `validation.json`.
- Create: 실제 `복습노트/1014/인터렉티브_NN_CS_이득과_대역폭.html`, `인터렉티브_NN_두_극점과_보데_근사.html`.
- Create: 두 `.assets/자료_인터렉티브_NN_이름/` 제작자료.
- Modify: `복습노트/1014/정리노트_1014_Frequency_Response.html`의 문맥 안내·링크.
- Test/evidence: `RUN/note-links.json`, `links-dry.json`, `links-applied.json`, `links-again.json`, 원자료 해시와 브라우저 검토 기록.

**Interfaces:**
- Consumes: `make-frequency-example.cjs`, `check`, `stepsReport`, `build`, `save`, `linkNotes`, 실제 1014 노트.
- Produces: 실제 발행 HTML/제작자료 경로, 검증된 세 문맥 연결, added/unchanged 보고.

- [x] **Step 1: 1014 원자료를 읽고 브리프·원본 백업을 만든다.**

```powershell
$TargetJson = node "$Skill/scripts/resolve.cjs" $Repo 1014
$TargetJson | Set-Content -LiteralPath "$Run/target.json" -Encoding utf8
$Target = $TargetJson | ConvertFrom-Json
$Note = $Target.noteHtml[0]
New-Item -ItemType Directory -Path "$Run/backup" | Out-Null
Copy-Item -LiteralPath $Note -Destination "$Run/backup/note.html"
New-Item -ItemType Directory -Path "$Run/cs","$Run/two" | Out-Null
Get-Content -LiteralPath $Target.notes[0]
Get-Content -LiteralPath $Target.stt
```

각 brief.md의 내용은 Spec의 두 자료 절을 사용한다. CS는 L05 s5–6, two는 s8–9의 원본 화면을 보고 연결·조건·공식을 대조한다. 교재의 위상·정현파 근거 쪽을 확인해 실제 쪽 번호를 기록한다. 근거를 찾지 못하면 위상/파형 보충 내용 검토를 not_run으로 유지하고 해당 자료를 발행하지 않는다.

원래 MD·PDF·SVG의 해시는 `Get-FileHash -Algorithm SHA256`으로 RUN에 저장한다. 정리노트 HTML은 byte 원본을 별도 백업했으므로 최종에 삽입 안내를 제거한 결과와 비교한다.

- [x] **Step 2: 두 원본과 임시 미리보기를 생성·검사한다.**

```powershell
node "$Skill/scripts/make-frequency-example.cjs" cs "$Run/cs/Main.dc.html"
node "$Skill/scripts/make-frequency-example.cjs" two "$Run/two/Main.dc.html"
node "$Skill/scripts/check.cjs" "$Run/cs/Main.dc.html"
node "$Skill/scripts/check.cjs" "$Run/two/Main.dc.html"
node "$Skill/scripts/steps.cjs" "$Run/cs/Main.dc.html"
node "$Skill/scripts/steps.cjs" "$Run/two/Main.dc.html"
node "$Skill/scripts/build.cjs" "$Run/cs/Main.dc.html" "$Run/cs/preview.html"
node "$Skill/scripts/build.cjs" "$Run/two/Main.dc.html" "$Run/two/preview.html"
```

Expected: 모두 ok; 단계/패널이 동일 상태를 설명한다. build가 RUN에 만든 canvas.json은 나중에 save가 별도로 생성하므로 source 폴더에 생성되어도 문제없다.

- [x] **Step 3: 독립 검토자가 내용과 수치를 검토한다.**

작성자가 아닌 검토자에게 두 Main.dc.html, 브리프, 실제 근거 파일, steps 결과와 circuit-verification.md를 전달한다. 계산 모듈의 구현이나 사전 결론을 정답으로 제시하지 않는다. 검토자는 수치·단위·회로 연결·문구를 독립 계산으로 대조한다. Native 실행에서도 자료의 독립 검산은 생략하지 않는다.

validation.json의 필드는 다음과 같다. 아직 하지 않은 검토는 not_run이며, 실제 완료 뒤에만 pass와 증거를 기록한다.

```json
{
  "source_sha256": null,
  "reviews": {
    "machine": {"status":"not_run","evidence":[]},
    "content": {"status":"not_run","evidence":[]},
    "numeric_independent": {"status":"not_run","evidence":[]},
    "browser": {"status":"not_run","evidence":[]}
  },
  "assumptions": [],
  "supplements": [],
  "findings": []
}
```

source_sha256의 초기 null은 아직 생성되지 않은 기록 상태다. 기록 파일을 생성하는 순간 실제 `Get-FileHash` 값으로 설정한다. final pass 기록에는 실제 hash와 각 검토의 증거가 있어야 한다. 수정하면 hash와 해당 검토 증거를 갱신하고 check→내용/수치→브라우저를 다시 수행한다.

- [x] **Step 4: 내장 브라우저로 네 화면 조합을 검증한다.**

RUN에서 `python -m http.server 8765 --bind 127.0.0.1 --directory "$Run"`를 비표시 background process로 시작한다. Start-Process를 사용하면 -WindowStyle Hidden을 지정한다. 사용 중인 포트면 다른 포트를 골라 실제 URL을 기록한다. 프로세스 ID를 보관하고 자신이 띄운 서버만 최종에 종료한다.

computer-use 도구를 사용하기 전 해당 SKILL.md와 반환 API 문서를 읽는다. cs/preview.html과 two/preview.html에 대해 다음을 수행한다.

1. 1440×900 라이트·다크, 375×812 라이트·다크. 가로 스크롤·라벨 겹침·자른 글자·콘솔 오류가 없어야 한다.
2. 모든 슬라이더를 최소/최대, 기본, 각 preset으로 이동. 표시값과 곡선·표식이 갱신되며 커서 조작 중 input이 망가지지 않아야 한다.
3. CS 파형: 재생·정지·속도·스크럽, 정규화 축·실제 진폭·반전 확인.
4. two 극점 겹침: 동일 극점 표식과 서로 다른 전체 대역폭, 노드별 손실 합 확인.
5. 좁은 화면의 조작·설명 서랍, Escape, 넓은 화면의 패널 너비·테마 스크롤바 확인.
6. 검토 스크린샷과 실제 조작 증거를 RUN에 기록. 점검하지 못한 viewport는 pass로 기록하지 않는다.

renderer의 폰트 크기·좌표·문구를 고치면 source hash와 기계/내용 검토를 갱신한다. 브라우저에서 실제 입력 이벤트까지 확인한다; VM draw 테스트만으로 browser PASS를 기록하지 않는다.

- [x] **Step 5: 검토 완료 자료를 순차 저장하고 실제 발행 파일을 확인한다.**

```powershell
$CsSaved = node "$Skill/scripts/save.cjs" "$Run/cs/Main.dc.html" $Target.folder CS_이득과_대역폭 | ConvertFrom-Json
$TwoSaved = node "$Skill/scripts/save.cjs" "$Run/two/Main.dc.html" $Target.folder 두_극점과_보데_근사 | ConvertFrom-Json
Copy-Item -LiteralPath "$Run/cs/brief.md","$Run/cs/validation.json" -Destination $CsSaved.dir
Copy-Item -LiteralPath "$Run/two/brief.md","$Run/two/validation.json" -Destination $TwoSaved.dir
@($CsSaved,$TwoSaved) | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath "$Run/saved.json" -Encoding utf8
```

실행 전 validation의 source hash가 현재 Main.dc.html과 일치하고 네 검토 상태가 모두 pass임을 확인한다. 하나만 통과하면 그 하나만 save한다. 실제 html을 브라우저로 다시 열어 콘솔·핵심 조작을 확인한다.

- [x] **Step 6: 실제 저장 경로로 문맥 연결 명세를 작성·실행한다.**

```powershell
$Links = @{
  notes = @(@{
    note = $Note
    links = @(
      @{sectionId='s0-3db'; html=$CsSaved.html; label='CS 이득과 대역폭';
        before='저항과 커패시턴스를 바꾸며 이득·대역폭·출력 파형을 ';
        after='에서 함께 비교해 보세요.'},
      @{sectionId='s2-cs-two-poles'; html=$TwoSaved.html; label='두 극점과 보데 근사';
        before='입력·출력 RC를 바꾸며 각 극점과 전체 대역폭의 차이를 ';
        after='에서 확인해 보세요.'},
      @{sectionId='s1-bode'; html=$TwoSaved.html; label='두 극점과 보데 근사';
        before='정확한 곡선과 직선 근사가 극점 근처에서 얼마나 다른지 ';
        after='에서 비교해 보세요.'}
    )
  })
}
$Links | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath "$Run/note-links.json" -Encoding utf8
node "$Skill/scripts/link-notes.cjs" "$Run/note-links.json" --dry-run |
  Set-Content -LiteralPath "$Run/links-dry.json" -Encoding utf8
node "$Skill/scripts/link-notes.cjs" "$Run/note-links.json" |
  Set-Content -LiteralPath "$Run/links-applied.json" -Encoding utf8
node "$Skill/scripts/link-notes.cjs" "$Run/note-links.json" |
  Set-Content -LiteralPath "$Run/links-again.json" -Encoding utf8
```

dry-run 결과의 세 연결이 added/updated/unchanged 중 하나인지 확인한 뒤 실제 apply한다. skipped는 이유를 해결하거나 해당 연결을 보류하고 보고한다. 하나의 자료만 저장되었으면 그 자료의 링크만 명세에 넣는다. rerun은 changed:false여야 한다.

- [x] **Step 7: 실제 노트 보존·연결·팩 구조를 검사한다.**

```powershell
python "$Repo/.claude/skills/ec2-review-pack/scripts/check_html.py" $Note
python -m unittest discover -s "$Repo/.claude/skills/ec2-review-pack/tests" -p test_pack_layout.py
$NodeTests = Get-ChildItem -LiteralPath "$Skill/tests" -Filter '*.test.cjs' | Select-Object -ExpandProperty FullName
node --test $NodeTests
git diff --check
git diff --stat
git status --short
```

원자료 해시를 다시 계산해 MD·PDF·기존 SVG 바이트가 같음을 확인한다. 원 노트 HTML과 수정 노트에서 `<p class="interactive-note" data-ec2-interactive=...>...</p>` 세 블록을 제거한 결과가 byte-equivalent인지 확인한다. 노트/자료의 actual path는 UTF-8 JSON으로 읽어 경로를 손으로 다시 만들지 않는다.

브라우저에서 실제 s0-3db, s2-cs-two-poles, s1-bode 설명과 안내를 읽는다. 대표 링크를 눌러 새 탭에 올바른 자료가 열리고 원 노트는 유지되는지 확인한다. 세 링크 모두 URL decode 후 실제 파일 존재를 검사한다.

- [x] **Step 8: 완료 보고와 리뷰 증거를 정리한다.**

보고에 실제 두 HTML 절대 경로, 사용한 예제·조작·가정·보충, 테스트 및 독립 검산·브라우저 증거, 연결 상태, RUN/백업을 적는다. 성공하지 않은 자료나 링크는 보류 이유를 구분한다. 작업은 로컬 변경으로 남기고 커밋은 요청이 있을 때만 한다.

## 계획 자체 검토 기록

- Spec coverage: 입력·실패(Task 2/5), 화면·모델(Task 1/3/4), 과목별 스킬(Task 5), 1014 첫 발행과 최신 노트 연결(Task 6), 원자료 보존(Task 2/6).
- Type consistency: resolve에 stts만 추가; 기존 save/link/check 계약 유지. source의 FM/CFG/drawFrequencyScene 선언과 네 훅이 연결된다. makeSource export를 테스트·CLI 모두 사용한다.
- Review Focus: 다섯 조건 모두 각 소유 Task에 동작 테스트 또는 실제 artifact 보존/브라우저 확인을 배치했다.
- Placeholder scan: 미정 작업은 없다. __TITLE__는 기존 템플릿의 실제 치환 계약이다. 검토 기록의 초기 not_run은 검토하지 않은 상태를 정직하게 나타내며 최종 pass 증거와 hash가 발행 조건이다.
- 실행 방식 추천: Native. 기존 도구 이식이 많고 회로 모델·훅·자료가 같은 인터페이스를 공유하므로 한 구현자가 이어서 작업하기 쉽다. 자료의 독립 내용/수치 검토와 최종 전체 변경 리뷰는 별도로 수행한다.

## 실행 결과

Native 실행 완료. 검증119/119, 독립423+184, 브라우저4조합×2, 노트 링크3개와 보존 검사 PASS. 상세 기록은 두 제작 폴더의 completion.md. 자동 커밋 없음.
