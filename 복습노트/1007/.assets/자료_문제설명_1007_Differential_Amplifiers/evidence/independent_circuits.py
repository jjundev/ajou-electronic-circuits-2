import sympy as s
import math,json

def pair(gm,ro,rss,r1,r2,rpi=s.oo,common=True):
    a,b,p=s.symbols('a b p');v1=1 if common else s.Rational(1,2);v2=1 if common else -s.Rational(1,2)
    go=0 if ro==s.oo else 1/ro;gp=0 if rpi==s.oo else 1/rpi
    eq=[a/r1+go*(a-p)+gm*(v1-p),b/r2+go*(b-p)+gm*(v2-p),p/rss+go*(2*p-a-b)-gm*(v1+v2-2*p)+gp*(2*p-v1-v2)]
    q=s.solve(eq,[a,b,p]);return {'left':float(q[a]),'right':float(q[b]),'diff':float(q[a]-q[b]),'avg':float((q[a]+q[b])/2),'tail_node':float(q[p])}

def mos_mirror(gm,gn,gp,gmp):
    a,o,p=s.symbols('a o p');v=s.Rational(1,2);w=-v
    q=s.solve([gm*(v-p)+gn*(a-p)+(gmp+gp)*a,gm*(w-p)+gn*(o-p)+gp*o+gmp*a,gm*(-2*p)+gn*(a+o-2*p)],[a,o,p]);return {str(k):float(v) for k,v in q.items()}

def out(row):print(json.dumps(row,ensure_ascii=False,indent=2))
