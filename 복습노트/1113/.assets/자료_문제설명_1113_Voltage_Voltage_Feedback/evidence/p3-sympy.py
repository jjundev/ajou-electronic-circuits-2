from sympy import prod
# Each sign is an incremental stage derivative, in the order in the corresponding physical path.
cases = [('12.28', 'vout↑ → X↑ → iD2↑·iD1↓ → 출력의 풀다운 증가·M4 미러 공급 감소 → vout↓', [1, 1, -1], '음귀환')]
for key, chain, incremental_signs, expected in cases:
    sign = prod(incremental_signs)
    result = '음귀환' if sign < 0 else '양귀환'
    assert expected == result
    print(key, chain, '=>', sign, result)
