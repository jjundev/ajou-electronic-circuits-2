# p2: f_T ∝ mu*Vov/L^2 (C_GS=(2/3)WLCox, C_GD neglected), mu same
L1,L2=1e-6,65e-9; V1,V2=0.4,0.1
ratio=(V2/V1)*(L1/L2)**2
print("L ratio^2 =", (L1/L2)**2)
print("f_T ratio = (Vov2/Vov1)*(L1/L2)^2 =", ratio)
# alternate form with I_D fixed: f_T = 3*2*I_D/(Vov*2*pi*(2/3)... ) not used: W free
