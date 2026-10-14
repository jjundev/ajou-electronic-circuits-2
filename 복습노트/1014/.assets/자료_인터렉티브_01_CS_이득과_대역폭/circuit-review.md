# Independent circuit/content/numeric review

Verdict: FAIL pending Important fixes below. Numeric model PASS. Browser review not_run (owned by parent).

## Reviewed sources and identity
- cs/Main.dc.html SHA256 f9b0bc07f3e2c30a0810fb65574354db077893f0c7fc7f06a3af7f4c17eb8aff
- two/Main.dc.html SHA256 d8f12026a2a3b9ab111913393e6f98c21cb8f55b10a657b4e8e9b2e7be71ae4f
- STT/1014 전회2.md SHA256 a57669366e120f15c87681a6df05abd622c7d111154c89736363362daf440b67
- 복습노트/1014/.assets/정리노트_1014_Frequency_Response.md SHA256 e68bcb93de4f61af087c47096154032e286d58e67110d9ae140b29ea13fd2593
- Both brief.md; circuit-verification.md; actual STT Parts02–07 and notes; L05-5/6/8/9.png; book-3/4/5/6.png (printed pp574–581). Hashes rechecked after calculations and before verdict, unchanged.

## Findings
1. Important — two/Main.dc.html:348 and :373. Equal poles at frequency ratio=100 produce relative magnitude −80.0008685455 dB. The graph floor is exactly −80 dB relative (also −80 dB in contribution mode). Consequently the exact curve endpoint is removed by the range test and the current-frequency marker disappears at an allowed slider endpoint. Increase plot range with margin or derive limits from the displayed frequency span, preserving visible current marker. This is a visual synchronization failure, not a numeric transfer-function error.
2. Important — cs/Main.dc.html:432 and two/Main.dc.html:432 (also :322–328). User-facing assumptions say only gm is fixed: the actual gm=2mS / 5mS exists in CFG and private brief but is never displayed. Thus the displayed −20 V/V or −10 V/V gain cannot be independently reproduced from visible settings. Show fixed gm explicitly. Circuit labels contain only static RD/CL/RS/Cin names, with no live values, weakening the required circuit/state linkage; add current values at these labels and retain same parameter state as plots/panels.
3. Minor — two/brief.md:3. The stated pp578–580 range does not contain Figure11.11 or its explicit pole equations: book-6.png shows them on printed p581. Cite pp579–581 for Bode + two-node example (or identify p580 section start and p581 formulas).
4. Minor — cs/Main.dc.html:233. Shared legend describes a “기여” mode that does not exist in CS. Restrict contribution legend to the two-node artifact; show input/output wave colors in wave mode.

## Independent derivation and calculations
Expected values were computed without calling the author model. Output-node KCL gives Hout=−gm/(1/RD+jωCL). Input nodal division independently gives HX=1/(1+jωRS Cin). Two-node H=Hout HX. Complex division computes real/imaginary parts; hypot gives magnitude; atan2 gives phase. A separate bisection solves |H|=gm RD/sqrt(2), rather than reusing the author's quadratic cutoff formula. Author functions are invoked only as the actual side of comparisons.

Run independent-numeric.cjs; evidence independent-numeric.json. 423 assertions across 7 presets and all 40 slider endpoint combinations (8 CS,32 two), including 5 normalized-wave sample times each. Maximum relative/normed error 1.53143e−15. PASS.

| preset | H at selected ω | f3dB Hz | phase ° |
|---|---|---:|---:|
| CS base | −10+j10 |159154943.091895|−225|
| CS RD10 | −100+j100 |15915494.309190|−225|
| CS CL10 | −10+j10 |15915494.309190|−225|
| two base | −4.455445545+j5.445544554 |157601880.529202|−230.710593|
| two input first | −4.898040784+j5.097960816 |15909134.469019|−226.145763|
| two equal | j5 |102431206.695459|−270|
| two RD increase | −24.490203918+j25.489804078 |31818268.938038|−226.145763|

Single pole at ωp gives relative −3.01029995664dB. Equal poles give −6.02059991328dB at ωp and total cutoff sqrt(sqrt(2)−1)ωp =0.643594252906ωp. Both are implemented correctly; total bandwidth is not confused numerically with a node pole. Hz conversion /2π and voltage 20log10 are correct.

## Circuit and content checks
PASS: RD,CL and downward dependent current source share output and ground rails. Input two-node capacitor is grounded and RS series. Using gm vX rather than gm vin for the two-node current source is correct. CS input is high impedance, so disconnected control and output meshes are appropriate for a dependent-source equivalent circuit. No direct gate-to-output wire is required. Assumptions ro infinite and no Cgd match independent two-RC model. The AC ground label covers all ground symbols. Additional voltage polarity/reference markers would improve pedagogy but no incorrect connection identified.

PASS: phase −225° equals +135°, consistent with inverse output; waveform computes Im[H exp(jωt)] for sine input and divides each wave by its own positive peak. Input peak is 0.1mV, output peak |H|×0.1mV. t/T and V/V_peak labels plus normalized-wave warning and linear/clipping warning are present; supplement attribution is present. Time cursor is normalized phase, not physical GHz animation. Steps do not assert state-dependent numeric facts; changing controls clears selected steps. Bode knees and negative slopes match STT Part04–06, notes, L05 s8–9, printed p579–581. No unsupported Miller formula introduced.

Fix verification required: repeat numeric script, review changed labels and graph-boundary code, then browser owner verifies marker and labels visually. No repository mutations performed by reviewer.

## Final fix-pass re-review

Final circuit/content/numeric verdict: PASS. All four prior findings resolved; no remaining Critical/Important issue in reviewed scope. Browser/layout verdict remains not_run by this reviewer and belongs to main agent.

Re-read both current Main.dc.html source implementations and corrected brief. Re-ran independent-numeric.cjs: 423 assertions PASS, max error 1.53143e−15. Added independent-scene.cjs: 184 scene/state assertions PASS over presets, all endpoint combinations, and explicit ratio100 equal-pole case. Verified one in-bounds current marker for each response/contribution state and live circuit R/C-value text for both artifacts.

- Dynamic floor uses lowest endpoint response with at least 5dB margin. Because these transfer magnitudes decrease monotonically, all current points in allowed frequency range are in bounds, including equal-pole ratio100. Verified actual drawing outputs.
- gm=2mS / 5mS now visible in assumptions. RD/CL and RS/Cin live engineering-unit labels use same p state as response. Input voltage polarity and grounded negative reference are now explicit. Wave tick values −1/0/+1 and t/T 0…4 agree with the plotted normalization.
- Context-specific legend matches response, contribution, and wave modes. The two-node artifact contains no waveform panel.
- Brief now includes p581, covering fig11.11 and equations11.16–11.18.
- Numerical formulas and prior circuit/content PASS checks remain valid.

Final source SHA256:
- cs/Main.dc.html: 86d016ba2d70609f782d55dca5c13a5c9ec3abced216f90b1b1aa19fc23761e2
- two/Main.dc.html: 9b86b3f4903797cd8a78e054fea963b350b9e94c791d8bb3891f9cd656e946fd

### Final typography edit recheck
Concurrent typography edit detected by hash recheck; re-read updated scene code, confirmed CS/two shared scene functions identical, reran numeric (423 PASS) and scene/state (184 PASS) assertions. Label size changed to 13 and does not alter units/positions/circuit topology or numeric behavior. Final circuit/content/numeric verdict remains PASS on these final hashes (superseding the immediately preceding pair):
- cs/Main.dc.html: 9d842502caf6b1f142506c10ee1dba62776edcfe0757797d7dd92f2cc103948d
- two/Main.dc.html: 4401e6b3fa040e6818668db94a48d3dba3c353eb6abbb1c2939cb8cb7bc9bc18

### Final browser-driven coordinate pass
Re-read final coordinate/pole-label logic in both artifacts. Wave t/T label at y=−6.55 and C_in label at (−1.2,3.1) do not change circuit or data interpretation. Nearby poles retain separate vertical markers; text coalesces only to prevent overlap and uses a dot for distinct poles, equals sign only at floating-point equality tolerance (log10 ratio <1e−9). No false equal-pole claim at perceptually close but different poles. Reran 423 independent numeric and184 scene/state assertions: all PASS, unchanged max numerical error1.53143e−15. Final circuit/content/numeric verdict PASS; browser visual verification remains parent responsibility.

Final source hashes superseding prior entries:
- cs/Main.dc.html: 210ef4e2433016f662919579c6865e16301ad5e7b762104b8ae61814d0a8301c
- two/Main.dc.html: 9e7785d895c943b9ce2fd8b4fd7bf7b3b400e38ec7a6b24b01eead43d0515ae6

### Final control-layout source binding
Re-read cs/two Main.dc.html:181. Both controls now use block labels with minimum height2.8em and full-width block range inputs; for/id association, min/max/step/value, onChange binding and numeric values remain intact. These markup changes introduce no content/model issue. Reran independent-numeric.cjs (423 PASS, max error1.53143e−15) and independent-scene.cjs (184 PASS). Final circuit/content/numeric verdict PASS on following hashes, superseding all prior source hashes:
- cs/Main.dc.html: b92ed567735171ad29c805c08ee49f15cc641917846bb2305d690ac0385ce86e
- two/Main.dc.html: 94c2c9bf42e62de064f6133b2c5e7af51f3000f2d427eff7b86a716bb9766961
Browser drag/layout evidence is owned by parent, not independently claimed here.
