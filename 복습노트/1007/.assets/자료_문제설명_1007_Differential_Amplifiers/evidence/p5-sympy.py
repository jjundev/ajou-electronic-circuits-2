from independent_circuits import *
gm=.01;rd=1000.;dr=20.;rss=10000.;ro=20000.
# DC balanced current=.5mA; K=0.1*(200/.2)=.1 A/V², Ktail=.2 -> both Vov=.1V.
cm=pair(gm,ro,rss,rd,rd+dr);dm=pair(gm,ro,rss,rd,rd+dr,common=False)
out({'source':'from_the_past/md/2023-1_중간/Q4.md','1':{'min':.4+.1+.1,'max':1.8-.0005*(rd+dr)+.4},'2_course_leading':{'ACM_left':-rd/(2*rss),'ACM_right':-(rd+dr)/(2*rss),'ACM_mean':-(rd+dr/2)/(2*rss),'ACM_DM':dr/(2*rss)},'3_course':{'ADM_small_mismatch':-gm*rd,'CMRR':gm*rd/(dr/(2*rss)),'dB':20*math.log10(gm*rd/(dr/(2*rss)))},'full_linear_cm':cm,'full_linear_dm':dm,'full_linear_CMRR':abs(dm['diff']/cm['diff']),'note':'출력 정의를 반드시 선언; 입력ro=20RD의 수치 영향과 부하 불일치 ADM 보정은 강의 근사와 분리.'})
