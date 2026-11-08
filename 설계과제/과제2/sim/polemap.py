"""설계과제2 극점-노드 대응: 각 노드(X, Y, out)에 1 fF를 더해 pz를 다시 돌리고, 상대 이동의 합이 최대인 일대일 대응으로 노드의 극점을 정한다."""
import json
import math
import subprocess
from itertools import permutations
from pathlib import Path

from spice_io import parse_pz

SIM = Path(__file__).resolve().parent
NODES = {"X": "x", "Y": "y", "out": "out"}


def run_pz(node=None, c_probe=1e-15):
    """core.inc(+ 선택 노드에 Cprobe)로 pz를 돌려 극점 목록(rad/s)을 돌려준다."""
    tmp = SIM / "_pz_tmp.cir"
    probe = f"Cprobe {node} 0 {c_probe}\n" if node else ""
    tmp.write_text("* pz probe\n.include core.inc\n" + probe +
                   ".control\npz in 0 out 0 vol pz\nprint all\n.endc\n.end\n")
    try:
        r = subprocess.run(["ngspice", "-b", tmp.name], cwd=SIM, check=True,
                           capture_output=True, text=True)
    finally:
        tmp.unlink(missing_ok=True)
    poles, _ = parse_pz(r.stdout)
    return poles


def shift_matrix(base, shifted):
    """노드별 상대 이동 |Δp|/|p| (|p| 오름차순 인덱스)."""
    b = sorted(base, key=abs)
    rel = {}
    for name, ps in shifted.items():
        s = sorted(ps, key=abs)
        if len(s) != len(b):
            raise ValueError(f"{name}: pole count {len(s)} != {len(b)}")
        rel[name] = [abs(s[i] - b[i]) / abs(b[i]) for i in range(len(b))]
    return rel


MIN_MARGIN = 0.05        # 최선 대응이 차선보다 이만큼(상대) 이상 나아야 대응으로 인정한다


def assignment_scores(base, shifted):
    """[(점수, 순열), ...] 내림차순. 점수 = 노드별로 최댓값 1로 정규화한 상대 이동의 합.

    정규화는 1 fF가 작은 노드에서 더 크게 보이는 1/C_node 가중을 없앤다.
    """
    rel = shift_matrix(base, shifted)
    names = list(rel)
    norm = {n: [x / max(rel[n]) for x in rel[n]] for n in names}
    return names, sorted(((sum(norm[n][i] for n, i in zip(names, perm)), perm)
                          for perm in permutations(range(len(base)), len(names))), reverse=True)


def map_poles(base, shifted):
    """노드 → 극점 인덱스의 일대일 대응. 정규화한 상대 이동의 합이 최대인 순열을 고른다.

    X와 Y는 CGD1로 결합되어 있어 노드마다 따로 argmax를 하면 같은 극점을 고를 수
    있다. 그래서 전체 순열 중 합이 가장 큰 것을 고르고, 차선과의 차이가
    MIN_MARGIN보다 작으면 대응을 정할 수 없으므로 ValueError를 낸다.
    켤레 복소 극점 쌍은 |p|가 같아 항상 동점이 되므로 역시 ValueError가 된다.
    """
    if not base:
        raise ValueError("no poles from pz analysis")
    names, scored = assignment_scores(base, shifted)
    if len(scored) > 1 and scored[0][0] - scored[1][0] < MIN_MARGIN * scored[0][0]:
        raise ValueError(f"ambiguous pole mapping: {shift_matrix(base, shifted)}")
    return dict(zip(names, scored[0][1]))


if __name__ == "__main__":
    base = run_pz()
    shifted = {k: run_pz(n) for k, n in NODES.items()}
    idx = map_poles(base, shifted)
    b = sorted(base, key=abs)
    rel = shift_matrix(base, shifted)
    _, scored = assignment_scores(base, shifted)
    margin = (scored[0][0] - scored[1][0]) / scored[0][0]
    pm = {k: {"index": i, "f_hz": abs(b[i]) / (2 * math.pi), "rel_shift": rel[k],
              "assign_margin": margin} for k, i in idx.items()}
    (SIM / "polemap.json").write_text(json.dumps(pm, indent=2) + "\n")
    print(f"assignment margin over runner-up: {margin*100:.1f} %")
    for k, v in pm.items():
        s = sorted(shifted[k], key=abs)[v["index"]]
        print(f"{k:3s}: pole #{v['index']}  f = {v['f_hz']/1e9:.4f} GHz  "
              f"(+1 fF -> {abs(s)/(2*math.pi)/1e9:.4f} GHz)")
