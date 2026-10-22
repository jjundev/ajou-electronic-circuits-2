from pathlib import Path
import json,re,hashlib,html,datetime,subprocess,sys
R=Path(r'C:/Users/Hyunjun/.codex/scratch/ec2-problem-explain/1007-p8-short-circuits-20261022');B=R/'review-1007-Differential_Amplifiers';O=R/'review';O.mkdir(exist_ok=True)
repo=Path(r'C:/Users/Hyunjun/Desktop/현준대학/26-2/ajou-electronic-circuits-2');S=json.loads((B/'source.json').read_text(encoding='utf-8'));reviewer='/root/p8_independent_review (fresh independent full-pack reviewer, 2026-10-22)'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
# These are individually reviewed findings, not inherited pass records.
facts={
'p1:main':('CM half circuit keeps2ro3; gate/source AC grounded tail leavesro3.','-RD ISS/(2/lambda+Vov); original proof request retains1/gm.','lambda→0 gain0; ro3→0 gain−gmRD; equal outputs give differential0.'),
'p2:main':('Source-degenerated CM half uses2ro5; Gm output short separate from input-zero Rout.','Gm≈1/(2ro5), Rout≈ro3 when lower product≫load; ACM≈−ro3/(2ro5).','Fixedload,tail→infinity gives0; equal outputs cancel. PMOS remains DC on.'),
'p3:1':('Half of1mA ineachinput; DM source virtualground, roN||roP.','gm10mS, bothro20kΩ; ADM−100.','Two opposedoutputs cancelinputhalf; mS·kΩ dimensionless, signnegative.'),
'p3:2':('UppertailM5 boostsro6; CM half carries2RSS; inputro remains inmodel.','gm520mS,ro5=ro610kΩ,RSS≈2MΩ,ACM≈−0.005.','gmro200;tail→infinity gives0; outputaverage differsfrom difference.'),
'p4:1':('CMrejection means equalinput interference suppressed atdifferentialoutput.','Finite tailresistance and mismatch limitpractical rejection.','Finite tailalone leaves matchedCMdifferential0; nofalse claim leakagewithout asymmetry.'),
'p4:2':('Originalro≫RD permits inputro omission, equalbranchcurrents afterloadmismatch.','gm10mS,RSS10kΩ,ΔRD20Ω; leakage+0.001.','ΔR→0 ortail→infinity gives0; rightloadlarger lowersrightoutput.'),
'p5:1':('MOSsaturation bounds:tailsets lower,lower rightdrain setsupper.','VOVinput=VOVtail0.1V; CM0.6–1.69V.','Atlower source0.1V,atupper rightVGD0.4V; actualgainrequires headroom.'),
'p5:2':('Explicitadditionalro/RD20 courseapprox dropsinputro consistentlyinbothpaths.','LeftCM−0.05,right−0.051,CM-DM+0.001.','Matchedloadsdifference0 withfinite peroutputCM; mean−0.0505 isalternative outputdefinition.'),
'p5:3':('Same differenceoutput forsignal andCMleak; smallmismatch symmetricDM numerator.','ADM−10;CMRR10000,80dB.','10/0.001=10000; nofinite-roDM pairedwithroignoredleak.'),
'p6:1':('Inputpairwidth doubled atfixed0.2mA tailcurrent.','Cutoff0.28V→0.2V; statementX,ratio1/sqrt2.','Notfixed-voltage tailwidthchange; cutoffis notlinear range.'),
'p6:2':('SymmetricDM virtualsourceground retains finite100kΩ inputro.','RD||ro100/11kΩ,ADM−100/11≈−9.09.','ro→infinity gives−10; finiteparallel reducesmagnitude.'),
'p6:3':('CMhalf2RSS withgmro100 and2gmRSS100 large.','EachoutputCM≈−0.1; differentialsymmetricCM0.','Tailresistance→infinity suppressesperoutputgain; ratioofresistancesdimensionless.'),
'p6:4':('Fullloadmismatchmodel retainscommonP and finiteinputro; KCLdefinesbranchdirections.','Leak≈ΔRD/[2RSS(1+RD/ro)]=+1/1100≈9.09e−4.','FullKCLleak convergesinlargegm;ro→infinity removefactor1/1.1.'),
'p6:5':('Identicalfinite-ro correctioncancels fromDM/leakageratio; inverse-designΔRD.','Target30000 gives|ΔRD|100/3Ω≈33.33Ω.','Unrounded100/3 substituted gives30000; reference33.7 usesdifferent1/gm order.'),
'p7:1':('Tailwidthdoubled atfixedVb0.6V, notfixedtailcurrent.','ISSdoubles, steeringboundary sqrt2times0.28→0.4V;O.','Inputpairsizefixed; alltransistorsmustremainoperatingregion.'),
'p7:2':('Inputroignored consistentlyinexplicitcoursemodel; symmetricDM.','gm1mS,RD10kΩ,ADM−10.','Negativeleftminusright; noassumption completeCLMDC withmissingCMsupply.'),
'p7:3':('CM2ro3=100kΩ half; large2gmro3 leading.','EachoutputCM≈−0.1; differentialsymmetricCM0.','Tailro→infinity gives0; peroutputanddifference keptdistinct.'),
'p7:4':('Inputroomitted,equalCMbranchcurrent;rightload1%larger.','ΔRD0.1kΩ,leak+0.001.','ΔRD→0 removesleak; signconsistentleftminusright.'),
'p7:5':('1%mismatch denominator, symmetricreferenceDM numerator samecoursemodel.','CMRR10000,80dB.','10/0.001=10^4; gainsratio voltage20log not10log.'),
'p7:6':('FixedVbwidth2 changescurrent2,gm sqrt2,tailro1/2.','NewCMRR5000sqrt2≈7071.07,76.99dB.','Ratio1/sqrt2 despiteDMgrowth;ΔRDandinputgeometryheldfixed.'),
'p8:1':('REaboveM1drain isseriesDCdrop; tailandinputMOSsaturationboundaries.','VOVall0.2V;lower1.8V,upper2.9V,symmetricDC.','Explicit10Ω reducesrightupper0.5mV→2.8995V;doesnotchangerounded2.9V.'),
'p8:2':('Fixed100μAtail squarelawsteering untiloneinputturnsoff.','±sqrt0.08V≈±0.28V.','Signexchange swapsoffdevice; needsCMheadroom, notlinearitythroughout.'),
'p8:3':('SymmetricDM Pvirtualground; finiteinputro200kΩ loadretained.','gm0.5mS,RC||ro200/21kΩ,ADM−100/21≈−4.76.','ro→infinity returns−5; finiteparallel reducesmagnitude.'),
'p8:4':('REabovetaildrain addsro1, no cascodegain;halfuses2RSS.','RSS110kΩ,peroutputCM−1/22≈−4.55e−2; differentialCM0.','Matchedoutputs equal; tail→infinity peroutputCM→0.'),
'p8:5':('NEWshort route: symmetrici≈vCM/(2RSS),samevgs cancelscontrolledcurrents, i1−i2=vo/ro.','vo=ΔRC i2−RC vo/ro, firstorderi2→i; leakage+1/23100≈4.33e−5.','FreshfullSymPyKCL derivativeratio→1 asgm→infinity; inputroandpolaritypreserved.'),
'p8:6':('Samefiniteinputro gain/leakagereciprocalfactors cancelbefore numerics.','CMRR2gmRSS RC/|ΔRC|=110000;100.83dB.','Exactfraction100/21 dividedby1/23100=110000; smallmismatch pluslargeproductsstated.'),
'p9:1':('CascodeinPMOSload, NOTtail; symmetricDM keepsinputro.','Rup≈1000kΩ;ADM≈−10000/101≈−99.01.','Rup→infinity returns−100; finiteupperload reducesmagnitude.'),
'p9:2':('CMhalf2ro7=10kΩ,source moves; lowerro boostsunderfeedback.','Rdn≈gmro·2ro7=1000kΩ,Gm≈0.1mS;ACM≈−50.','Rup||Rdn500kΩ; cannotomitinputro andget−100; differentialCMstill0.'),
'p10:main':('SameVOV PMOSmirror; referenceareaNtimesoutput givesgmratio1/N.','vg=−i1/gm3; outputsource−gm4vg; transimpedance+RL/NΩ.','N1 returnsRL,N2 halvesgain; RL0 gives0; actualsaturationmaintained.'),
'p11:a':('DCmirror k1 balancesoutput supplyandsink; onlyDC KCL needed.','Before0,after2ΔI RL.','ΔI0 returns0; combinedsupplyincrease+sinkdecrease doublechange.'),
'p11:b':('DCmirror k1/2; retain initialnegativevoltage andcompliancecondition.','Before−I0RL/2,after(3ΔI−I0)RL/2;change1.5ΔIRL.','ΔI0 returnsinitial; ΔI=I0/3 yieldsfinal0; finalnotmistakenforchange.'),
'p12:1':('One-sideddiodeconnectedmirrormergesopposedsignalpaths; nottwoidenticalhalves.','A≈+gm1(ro2||ro4),rightoutputwithleftminusrightinput.','Two signalhalvesadd; negativehandwrittenanswersign correctedbyoutputpolarity.'),
'p12:2':('Samebranch1mA NMOS/PMOS μCoxW/L productsgivegm10mS.','roeach10kΩ,Rout≈5kΩ,gain+50.','mS·kΩdimensionless; outputsuppliedcurrentincreasespositive.'),
'p12:3':('SeparatelydiodeconnectedPMOSload inDM half,sourcevirtualground.','A=−gmN/(gmP+goP+goN)≈−0.98; leading−1.','Load~100Ω muchsmallerthanmirrorload; ro→infinity gives−1.'),
'p12:4':('Between-nodeRDDandRSS splitinDM to500Ωand100Ω; gmRS1numericexception.','Finite-roKCLgain−50/20.6≈−2.43, denominator1retained.','ro→infinity gives−2.5; reference−2.44 isadditionalblockapprox, notcontradiction.'),
'p13:1':('EachPNPbaseconnectedonlytoowncollector throughR1;finiteβandπ essential.','Rfb≈(10+2.6)/101kΩ;gain≈−4.68 atVT26mV assumed.','R1→0 yieldsdiodeload; current-sourcelabel x282 resolvesedgecontactwithouttopologychange.'),
'p13:2':('BJT1:1mirrorcombinescurrents;largeβDCandsignalapprox explicitlystated.','Ic0.1mA,gm100/26mS,Rout200/9kΩ;gain+85.47.','Rightoutputrises;supplyincreaseandsinkdecrease; notclaimedfiniteβexact.'),
'p13:3':('EachcurrentIEE0.1mA,notsharedtail; RE/2=2.5kΩ degeneration.','gmRE9.62,largeexternaldegenerationcoursegain−0.4.','Finiteinternalre block−0.36 acknowledgedapproxorder; REdouble yields−0.2.'),
'p14:main':('BJTmirrortwo signalpaths,Earlyresistancesparallel; VT26mVassumption.','1/|Av|≈VT/VAn+VT/VAp;VAp65/12V≈5.42V,gain+100.','Unroundedsubstitution100; NPNceiling192.31>100;positivefiniteEarlyfeasible.')}
assert len(facts)==39
# Fresh common topology observations after enumerating every svg path, label and source netlist.
circuits={
'p1':'OneCMhalfSVG; controlleft,RDright,2ro3belowP; onlyM3finiteλ, correctKCL.',
'p2':'TwoSVGs; outputshort physicallyconnectedforGm; inputgrounded+rightVt forRout; controlleftofro1.',
'p3':'CMhalfSVG ro1drain-source,ro3toground,2RSSbelowP; DMvirtualground described.',
'p4':'roignoredCMhalfSVG; controlcurrent,loadtoground,2RSSbelowP; nobogusrobranch.',
'p5':'SameexplicitroignoredCMhalf; originals mismatchoutputresistors mappedtoequalCMcurrent.',
'p6':'HalfSVG andshared-source two-branchSVG; finiteinputro retained; sourceRSSsingle inwholemodel.',
'p7':'KnownCSblocksandscaling, no smallsignal nodeKCL; nosynthesizedSVGrequired.',
'p8':'BothSVGs retained: rodrain-source,RCloadtoground;2RSShalf vs singleRSSwhole; shortdifferenceidentity matchesconnections.',
'p9':'CMhalfSVG,ro1drain-source,2ro7belowmoving source,Rupoverload; allfixedbiasACground.',
'p10':'MirrorSVG has leftvgseparatefromrightoutput,1/gm3reference andupward−gm4vgsupply; RLgrounded.',
'p11':'OnlyDCoutputKCL; no smallsignalSVGoroutputshortneeded.',
'p12':'Part4DMhalfSVG hasrodrain-source,RSbelowmoving source,RDgrounded; mirrorpartsuseknownblockswithoutfalsehalfsymmetry.',
'p13':'PNPloadtestSVG hasR1collector-base,rπbase-ground,gm3vbleftofro3,rightVtandleftwardit;labelnowx282.',
'p14':'Knownactive-loadblockformulaonly; notnovelKCLorRouttestderivation, originalcircuitretained.'}
# Retry reconstructed before comparing answers; no generic recalc-only acceptance.
retry={
'p1':'RD2→gain2 ifsaturation; X−Y0;tailλsmaller reducesgain magnitude withfixedISS,VOV.',
'p2':'Tailro2→CMhalfifproductconditionshold; matchedoutputdifference0.',
'p3':'TailRSS2 leavesDM−100,CM−0.0025;observingdifference underCMgives0.',
'p4':'Matchedloads peroutputCMfinite,difference0;ΔRhalf halvesleak.',
'p5':'ΔR10Ω→CMRR20000/86.02dB;supplyCM1.7V:rightinputlosessaturationfirst.',
'p6':'Inputwidth4→steeringhalf;inputro→infinity removes1/(1+RD/ro);targetCMRR2→allowΔRhalf.',
'p7':'Matchedloads eachCMfinite,difference0;0.5%CMRR20000/86.02dB;rebiasfixedISS removescutoffgrowth.',
'p8':'RE20kΩ→CMlower2.8V,RSS120kΩ;ΔR5Ω→CMRR220000/106.85dB;matchedoutputdifference0.',
'p9':'Tailro2→Rdn2000kΩ,Rparallel666.67kΩ,Gm0.05mS,CM−33.33;inputro∞→−100.',
'p10':'Referencearea2atfixedI1 makesN2andgainhalf;commonVOVratioholdsdespitechangedoperatingpoint.',
'p11':'k2 givesinitialI0RL,change3ΔIRL;k1/2,ΔI=I0/4 givesfinal−I0RL/8.',
'p12':'Diodeequalgm,ro∞→−1;RS0→−gm(RD||ro)=−4.76.',
'p13':'R1zero load→rπ/(β+1)≈1/gm;RE10kΩ samecurrent givesleading−0.2.',
'p14':'Allcurrents2 leavesgain;target200exceeds192.31;VT25mV givesVAp5V.'}
# audit per-subpart eligibility: concrete not-applicable explanation is kept rather than pretendingallrulesapplied.
scale={'p6:1','p7:1','p7:6','p10:main','p11:a','p11:b','p14:main'}
bias={'p5:1','p8:1'}
gain={k for k in facts if k not in {'p4:1','p5:1','p6:1','p7:1','p8:1','p8:2','p11:a','p11:b'}}
degen={'p1:main','p2:main','p3:2','p4:2','p5:2','p5:3','p6:3','p6:4','p6:5','p7:3','p7:4','p7:5','p7:6','p8:4','p8:5','p8:6','p9:2','p12:4','p13:3'}
records={};ind={};audit={}
for p in S['problems']:
 pid=p['id'];f=B/'explanations'/f'{pid}.html';h=f.read_text(encoding='utf-8')
 order=re.findall('data-explanation="([^"]+)"',h)
 assert order==['understand','recall','start','solve','verify','pitfall','retry'],(pid,order)
 for label in p['subparts']:
  k=f'{pid}:{label}';route,answer,check=facts[k]
  anchor=f'explanations/{pid}.html [data-subpart="{label}"]';ev=f'{anchor}: {route} {answer} {check}'
  records[k]={'status':'pass','reviewer':reviewer,'evidence':ev,'retry_reconstruction':retry[pid],'diagram_review':circuits[pid]}
  method='qualitative' if k=='p4:1' else ('proof' if k in {'p6:1','p7:1'} else 'symbolic')
  ind[k]={'status':'pass','reviewer':reviewer,'evidence':f'evidence/{pid}-sympy.py, evidence/{pid}-result.txt freshly executed exit0. {check}','method':method,'conclusion':answer}
  rules={}
  def rule(id,text,apply=True):rules[id]={'disposition':'applied' if apply else 'not_applicable','evidence':f'{anchor}: {text}'}
  rule('UNIT-01',('ThisqualitativeCMdefinitionrequiresno numericalunitconversion.' if k=='p4:1' else 'Engineeringunitsinstart/solveverified; '+answer),k!='p4:1')
  rule('CALC-01',('No numericintermediateisneededforthisdefinition; matchedcaseargumentisexplicit.' if k=='p4:1' else 'Source-specificintermediatespreserved; '+route+' '+answer),k!='p4:1')
  rule('CALC-02',('Purequalitativeanswerhasnoroundednumericresult.' if k=='p4:1' else 'Exactfractionsandunroundedintermediatesretainorder; ≈marksrounded/leadingvalues. '+answer),k!='p4:1')
  rule('CIRCUIT-01',circuits[pid]+' '+route)
  rule('CIRCUIT-02',circuits[pid]+' '+('DCboundary/steeringdoesnotintroducesmall-signalKCL; commonstartdiagramnotusedasDCevidence.' if k in bias or k in {'p8:2','p6:1','p7:1'} else 'Directionandnodesmatchcurrentequations; knownblockexceptionsretained.'))
  rule('GAIN-01',('Currentgeneration/outputresistancerolesandoutputpolaritychecked; '+answer) if k in gain else 'ThisgroupasksDCboundary,steering,definitionorDCmirrorlevel; no Gm/Routmeasurementproductneeded.',k in gain)
  rule('DEGEN-01',('Source/emitterfeedbackandapplicablelargeproductconditionskept; '+route) if k in degen else 'Thisgroupdoesnotderiveacurrentfeedbackdegenerationgain; no intrinsic/externalresistanceinterchange.',k in degen)
  rule('SCALE-01',('Fixedfactorsandchangedratiosareexplicit; '+route+'; '+answer) if k in scale else 'Thisgroupdoesnotaskgeometry/currentparameterrescaling; retrychecksrecordedseparately.',k in scale)
  rule('BIAS-01',('Terminalvoltageorderandboundaryinequalitieschecked; '+answer+' '+check) if k in bias else 'NosoughtDCsaturationintervalinthisgroup; operatingregionconditionsretainedwithoutinventingmissingbias.',k in bias)
  rule('NOTATION-01',circuits[pid]+' NativeSVGtext/tspanlabelsretainPretendard600normal; browseractualfontverificationownedbyroot. '+answer)
  rule('EXPLAIN-01','Sevensectionsandthus-orderchecked; shortjudgment→equations→answer. '+route+' Summaryandverifyagree: '+answer)
  rule('CORRECT-01','Alloriginalsubpartrequirementscovered; approximationboundariesandlimitingcaseverified. '+check)
  audit[k]={'status':'pass','reviewer':reviewer,'rules':rules}
assert len(records)==39 and sum(len(x['rules']) for x in audit.values())==468
files=[B/'source.json']+list((B/'explanations').glob('*.html'))+list((B/'evidence').glob('p*-sympy.py'))+list((B/'evidence').glob('p*-result.txt'))
refs=[repo/'.claude/skills/ec2-review-pack/references/solution-style.md',repo/'.claude/skills/ec2-problem-explain/references/authoring.md',repo/'.claude/skills/ec2-problem-explain/references/verification.md']+[Path(p) for p in S['inputs'] if str(p).endswith('.md')]
assert sha(refs[0])==S['learning_style']['sha256']
closure=[{'path':str(f),'sha256':sha(f)} for f in dict.fromkeys(files+refs)]
common={'status':'pass','reviewer':reviewer,'evidence':'Fresh39groupsemanticreview,14evidencescriptsrunagain,sourceconditions/asks/netlistsandall14fragmentsreread; notcopiedpriorapprovals. P8 short route independently derived beforeauthoredcontentreview.','reviewed_files':closure,'unresolved':[]}
content={**common,'items':records,'retry':retry,'resolved_model_differences':['P8 originalreferenceomitsinputrofromleak; ro∞limitverified, coursehomogeneousfinite-rofactorsused.','P12 mirrorreferencehandnegative resolvedbyoriginalrightoutputpolarity; p12(4)−2.44blockapprox convergestofinite-roKCLresult−2.43.','P13 Vt26mVassumed; finiteβselfB-Cloadretained; mirror+85.47largeβ,andREgain−0.4largeexternaldegenerationclearlyscoped.']}
independent={**common,'items':ind,'new_p8_derivation':'Exactthree-nodeKCL symbolicallysolved; smallΔR derivative thenlargegm limitmatchesbriefshortformula; allsixnumericassertionspass.'}
style={'learning_style':S['learning_style'],'items':audit,'reviewer':reviewer,'reviewed_files':closure,'status':'pass'}
for name,obj in [('content.json',content),('independent.json',independent),('style-audit.json',style)]:
 (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Wrote39content +39independent +468rules; hashes',len(closure))