# Structural proof: a node shared by input source and return element sums their currents.
# Each feedback device is coupled to the output node voltage as given.
from sympy import symbols,diff
vo,vx,rf,g=symbols("Vout Vx RF gm",positive=True)
branches = [('(a)', 'M2 NMOS 게이트가 출력전압을 검출하고 소스가 M1 게이트 노드에 전류를 돌려준다.'), ('(b)', 'M2 PMOS 게이트가 출력전압을 검출하고 드레인이 M1 게이트 노드에 전류를 돌려준다.'), ('(c)', 'M2 PMOS의 소스가 출력전압을 검출한다. Vb가 고정되어 VSG2가 변하고 드레인 전류가 M1 게이트 노드로 돌아간다.'), ('(d)', 'M2 PMOS 게이트가 출력전압을 검출하고 드레인 전류가 Iin 및 M1 소스의 공통 노드에 합쳐진다.')]
for key, reasoning in branches:
    print(key, reasoning)

# Positive feedback-current direction is current delivered into X. Hold X fixed for sampling.
entry={'(a)':g*(vo-vx),'(b)':-g*vo,'(c)':g*vo,'(d)':-g*vo}
for key,current in entry.items():
    print(key,'dI_delivered_to_X / dVout =',diff(current,vo))
