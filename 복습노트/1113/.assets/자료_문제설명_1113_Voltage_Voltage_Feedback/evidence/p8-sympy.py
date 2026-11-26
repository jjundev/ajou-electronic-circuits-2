from sympy import prod
# Each sign is an incremental stage derivative, in the order in the corresponding physical path.
cases = [('(a)', 'vout↑ → NMOS M2의 공급 전류↑ → X↑ → CS M1의 드레인 전압↓', [1, 1, -1], '음귀환'), ('(b)', 'vout↑ → PMOS M2의 공급 전류↓ → X↓ → CS M1의 드레인 전압↑', [-1, 1, -1], '양귀환'), ('(c)', 'vout↑ → 고정 게이트 PMOS M2의 VSG↑ → X로의 공급 전류↑ → X↑ → CS M1의 드레인 전압↓', [1, 1, 1, -1], '음귀환'), ('(d)', 'vout↑ → PMOS M2 공급 전류↓ → X(소스1)↓ → 고정 게이트 M1의 VGS↑ → vout↓', [-1, 1, -1, -1], '음귀환')]
for key, chain, incremental_signs, expected in cases:
    sign = prod(incremental_signs)
    result = '음귀환' if sign < 0 else '양귀환'
    assert expected == result
    print(key, chain, '=>', sign, result)
