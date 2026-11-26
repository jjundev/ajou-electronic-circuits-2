from sympy import prod
# Each sign is an incremental stage derivative, in the order in the corresponding physical path.
cases = [('12.28 변형', 'M1 드레인 전압↑ → X↑ → iD2↑ → iD1↓ → 다이오드 접속 PMOS M3의 |VSG3|↓ → M1 드레인 전압↑', [1, 1, -1, -1], '양귀환')]
for key, chain, incremental_signs, expected in cases:
    sign = prod(incremental_signs)
    result = '음귀환' if sign < 0 else '양귀환'
    assert expected == result
    print(key, chain, '=>', sign, result)
