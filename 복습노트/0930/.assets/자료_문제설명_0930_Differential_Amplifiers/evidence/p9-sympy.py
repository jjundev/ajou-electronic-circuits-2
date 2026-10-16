import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
I=s.Rational(1,1000);R=1000;print('collector drop',I*R/2);print('strict BC nonforward bound VCM<=VCC-.5V; allowing .4V base-collector forward headroom yields VCC-.1V; need explicit criterion')
print("Independent conclusion: active bound VCM <=VCC-.5V (or course .4V permitted BC forward margin)")
