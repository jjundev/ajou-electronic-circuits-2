from sympy import prod
# Each sign is an incremental stage derivative, in the order in the corresponding physical path.
cases = [('12.29 변형', 'vout↑ → X(소스1)↑ → iD1↓ → A(소스2)↑ → 공통게이트 M2의 iD2↓ → vout↑', [1, -1, -1, -1, -1], '양귀환')]
for key, chain, incremental_signs, expected in cases:
    sign = prod(incremental_signs)
    result = '음귀환' if sign < 0 else '양귀환'
    assert expected == result
    print(key, chain, '=>', sign, result)
