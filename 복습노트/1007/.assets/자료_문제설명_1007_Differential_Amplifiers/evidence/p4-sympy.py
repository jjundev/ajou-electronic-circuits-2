from independent_circuits import *
# Original 2018-2 Q4: matched inputs share gate and source; unequal loads create differential output.
gm=.01;rss=10000.;rd=1000.;dr=20.
out({'source':'from_the_past/md/2018-2_중간/Q4.md','first_principles':'i=gm(vcm-vp), vp=2 RSS i; v1=-RD i, v2=-(RD+dRD)i','1':'이상 테일+대칭이면 CM 변화에 DC 가지 전류 불변. 현실에서 유한 테일과 비대칭이 CM→DM을 만든다.','2_leading_course':dr/(2*rss),'2_ro_ignored_unsimplified':dr/(1/gm+2*rss),'2_full_finite_input_ro':pair(gm,20000.,rss,rd,rd+dr),'scope':'ro≫RD 원문 가정: 강의 주도항9.999999e-4, 일반분모9.95025e-4. 완전회로 차이는 내부 검산.'})
