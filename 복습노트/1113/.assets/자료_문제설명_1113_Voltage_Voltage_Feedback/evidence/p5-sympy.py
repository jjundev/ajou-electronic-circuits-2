from sympy import prod
# Each sign is an incremental stage derivative, in the order in the corresponding physical path.
cases = [('12.29', 'vout↑ → X(소스1)↑ → iD1↓ → A↑ → 공통소스 M2 드레인 vout↓', [1, -1, -1, -1], '음귀환')]
for key, chain, incremental_signs, expected in cases:
    sign = prod(incremental_signs)
    result = '음귀환' if sign < 0 else '양귀환'
    assert expected == result
    print(key, chain, '=>', sign, result)
