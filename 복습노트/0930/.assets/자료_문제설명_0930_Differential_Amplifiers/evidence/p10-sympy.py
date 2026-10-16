import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
V=s.Rational(5,2);B=2;I=s.Rational(1,1000);print('strict Rmax',(V-B)/I);print('with allowable VBC=.4',(V-B+s.Rational(4,10))/I);print('1V differential -> Q1 carries essentially full tail')
print("Independent conclusion: RCmax500ohm strict BC cutoff; common course .4V BC criterion900ohm")
