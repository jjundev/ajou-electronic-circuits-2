For P1–3 set S=R1+R2, K=R2/S, L=RD (P1 negligible loading), RD||S (P2), S (P3 ideal current source). A=gm L, D=1+KA. Closed gain A/D, closed Zin=D/gm, closed Zout=L/D. P1's four functions: drain voltage sampling, divider attenuation, source-gate subtraction, transistor/load forward amplification.

P4. Define P=R1||R2, L=RC||S and positive j=gm(ve-vb). The divider tap returns vb=K*y+P*j/beta; output KCL gives y/L=(1+K/beta)j+it. H=(1+K/beta)L/(1/gm+P/beta), D=1+KH. Closed gain H/D, Zin=(1/gm+P/beta)D/(1+1/beta), Zout=L/D. Neglecting K/beta gives textbook unilateral forward gain, and large beta allows 1+1/beta≈1.

P6. Current mirror and matched MOS differential pair give A≈gm*(roP||roN||S), K=R2/S, D=1+KA. Gain A/D, Zin infinite, Rout=(roP||roN||S)/D.

P7–11 common two-port form: U and V are grounded open input and output resistances after feedback loading, b is the transconductance from output to input injected into the input, m is signed output current delivered by the forward active device per volt at input. z=UV*m is unilateral open transimpedance; retaining passive forward transfer gives z*=UV*(m+b). Use D=1-b*z with chosen z; closed gain z/D, Zin=U/D, Zout=V/D. For the usual negative-return convention use feedback factor -b if standard denominator 1+K*z is specified. This sign convention applies to every row, including the positive-feedback row P9.
P7: U=1/gm1||RF, V=RD2||RF, b=1/RF, m=-gm1*RD1*gm2.
P8: same with RD1→RD, RD2→RM. PMOS common source inverts.
P9: U=1/gm1||RF, V=RM||RF||1/gm2, b=1/RF, m=+gm1*RD*gm2. Source follower preserves sign and D can approach zero; no forced absolute value is allowed.
P10: U=rpi||RF, V=RC||ro||RF, b=1/RF, m=-gm. Finite Early voltage appears as ro.
P11: J=R1*R2+RF*(R1+R2), F=RF+(R1||R2), E=R1+(RF||R2), b=R2/J. Common gate drain voltage per source volt q=(gm1+1/ro1)*(RD1||ro1). Its input resistance is (RD1+ro1)/(1+gm1*ro1). U=F||[(RD1+ro1)/(1+gm1*ro1)], V=E||ro2, m=-gm2*q. Ideal output current source supplies zero AC incremental current.
