from sympy import prod
# Each sign is an incremental stage derivative, in the order in the corresponding physical path.
cases = [('12.30', 'vout↑ → 접지 소스 NMOS M2의 싱크 전류↑ → 입력 노드 X↓ → M1 드레인 vout↑', [1, -1, -1], '양귀환')]
for key, chain, incremental_signs, expected in cases:
    sign = prod(incremental_signs)
    result = '음귀환' if sign < 0 else '양귀환'
    assert expected == result
    print(key, chain, '=>', sign, result)
