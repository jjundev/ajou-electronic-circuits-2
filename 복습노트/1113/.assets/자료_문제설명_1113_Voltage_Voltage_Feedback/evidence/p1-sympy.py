# Structural proof: a node shared by input source and return element sums their currents.
# Each feedback device is coupled to the output node voltage as given.
from sympy import symbols,diff
vo,vx,rf,g=symbols("Vout Vx RF gm",positive=True)
branches = [('(a)', '출력전압을 RF로 검출하고, 베이스와 Iin이 만나는 노드에 (vo−vb)/RF 전류를 병렬 귀환한다.'), ('(b)', 'RF 오른쪽 단자가 출력전압을 검출하며 왼쪽 단자는 M1 게이트와 Iin이 만나는 노드로 전류를 보낸다. 꼬리 노드와 RF 선의 교차에는 연결점이 없다.')]
for key, reasoning in branches:
    print(key, reasoning)
print('dI_return / dVout (input node fixed) =',diff((vo-vx)/rf,vo))
