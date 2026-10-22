import sympy as s

gm,ro,rL,rt,v,d,z=s.symbols('gm ro rL rt v d z')
x=s.solve([d/rL+(d-z)/ro+gm*(v-z),z/(2*rt)+(z-d)/ro-gm*(v-z)],(d,z));A=s.factor(x[d]/v)
G=s.factor(-s.solve([z/(2*rt)+z/ro-gm*(v-z)],z)[z]/(2*rt)/v)
print('CM full half-circuit gain:',A)
print('Specified method: output short Gm=gm/(1+2rt(gm+1/ro)); inputzero Rout=rL||[ro+2rt(1+gmro)]')
print('For gmro>>1 and 2gmro rt >>rL, Gm~1/(2rt), Rout~rL; ACM~-rL/(2rt). Matched CM differential0.')
