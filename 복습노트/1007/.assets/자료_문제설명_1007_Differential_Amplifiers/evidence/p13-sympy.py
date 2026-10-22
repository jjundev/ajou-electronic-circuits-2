from independent_circuits import *
vt=.026;be=100.;ic=.001;gm=ic/vt;rp=be/gm;ro=10000.;R=10000.
# Base voltage divider vb=vo rpi/(R+rpi); output current = vo/ro +vo/(R+rpi)+gm vb.
load=s.simplify(1/(1/ro+(1+gm*rp)/(R+rp)));av=-gm/(1/ro+1/load)
icm=.0001;gmm=icm/vt;ron=5/icm;rop=4/icm
# Small signal mirror lead DC beta ignored; finitebeta copy current factor=beta/(beta+2).
Rout=1/(1/ron+1/rop);copy=be/(be+2);G=gmm*(1+copy)/2
g3=.0001/vt;re=2500.;rd=1000.
out({'source':'from_the_past/md/2015-1_중간/Q3.md','VT_assumption':vt,'1_load':float(load),'1_gain':float(av),'2_course_Gm':gmm,'2_course_Rout':Rout,'2_course_gain':gmm*Rout,'2_finitebeta_mirror_Gm_correction_only':G,'2_finitebeta_mirror_gain_correction_only':G*Rout,'3_unsimplified_degenerated_gain':-rd/(1/g3+re),'3_large_gmRe_course':-rd/re,'3_gmRe':g3*re,'note':'미러 부분 보통β≫1 주도항에 따른85.47. 실제DC+finitebeta+ro 동시해석은 별도전체노드모델필요;소신호보정만정확이라고부르지않는다.축퇴정밀참고-0.3623 vs큰곱주도항-0.4 차이구분.'})

# Course leading external degeneration versus source retains intrinsic re; gmRE->infinity proves same approximation family.
G,E,C=s.symbols('G E C',positive=True);gain=-C/(1/G+E);lead=-C/E
print('limit finite-degeneration/source to leading as gmRE grows:',s.limit(gain/lead,G,s.oo));assert s.limit(gain/lead,G,s.oo)==1
