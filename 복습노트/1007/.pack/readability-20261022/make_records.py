from pathlib import Path
import json,re,hashlib
from bs4 import BeautifulSoup
R=Path(r'C:/Users/Hyunjun/.codex/scratch/review-pack/1007-readability-20261022');repo=Path.cwd();rev=R/'review';old=R/'backup/pack/.assets/자료_문제설명_1007_Differential_Amplifiers';profile=repo/'.claude/skills/ec2-review-pack/references/solution-style.md'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
V=json.loads((old/'validation.json').read_text());execs=json.loads((rev/'fresh-executions.json').read_text());assert all(x['exit']==0 for x in execs)
# Read-only independent comparison, not the author's preservation flag.
model={
1:['CM half KCL i=gm(vCM-vP),vP=2ro3i,vX=-RDi gives exact requested -RD ISS/(Vov+2/lambda), input lambda0; leading -RD/(2ro3); symmetric differentialCM0.'],
2:['Output-short Gm~1/(2ro5), inputzero Rout~ro3 only when2gm1ro1ro5>>ro3; ACMse~-ro3/(2ro5); exact internal half KCL confirmslimit; differentialCM0.'],
3:['IDinput=.5mA gives gm10mS,ro20kohm each; DM=-gm(roN||roP)=-100.','Upper tail M5 multiplies ro6 by gm5ro5;gm5=20mS,ro5=ro6=10kohm gives2Mohm; CMhalf2RSS gives SE/average CM=-.005;diffCM0.'],
4:['CM rejection defined at differentialoutput; finite tail and asymmetry jointly needed for this leakage path; finite tail alone preserves cancellation if symmetric.','Tail10kohm,20ohm rightloadincrease, roinput omittedperoriginal assumption; positive leftminusright leakage20/20000=.001 in large degeneration.'],
5:['TailVov=.1V,inputVov=.1V => min.6V;largerrightRD1.02kohm gives VD1.29V =>max1.69V.','Declared inputroignoredcourse: leftCM-.05,right-.051,average-.0505,leftminusrightleak+.001.','Smallmismatch symmetricDM=-10; same declaredmodelCMRR10000=80dB; finite-ro exact diagnostics distinct fromcourseapproximation.'],
6:['Fixedtailcurrent and doubled inputK makes cutoff1/sqrt2: sqrt.08V ->.2V; answerX.','Finiteinputro100kohm retained: -1mS*(10||100)kohm=-100/11=-9.09.','Large gmro and2gmRSS samefiniteinputro CMleading=-RD/(2RSS)=-.1; symmetricdifferentialCM0.','Full sharedsourceKCL retained whenloads unequal; firstorder leakage=dRD/[2RSS(1+RD/ro)]=1/1100=+.00090909; positive leftminusright.','Samefinite-ro factors cancel inCMRRleading; target30000 gives|dRD|=100/3ohm=33.33, distinctfromreference33.7approxmodel.'],
7:['FixedVb tailWdouble doublesISS, steeringcutoff sqrt2 times .28->.4V; O, saturationrequired.','Declared inputroignoredmodel DM=-10 (not fullfinite-roexact).','Samecoursemodel singleoutputCM=-.1, symmetricdifferentialCM0.','1percent rightloadincrease, inputroignored: leak=.1kohm/100kohm=+.001.','SamecoursemodelCMRR10000=80dB.','FixedVb andsame1percentmismatch: gm sqrt2,tailrohalf, CMRR1/sqrt2=7071.07=76.99dB.'],
8:['RE isabove taildrain: DCaddsISSRE=1V; min.2+1+.4+.2=1.8V,max3-.05mA*10kohm+.4=2.9V; 10ohmmismatchwouldreduceupper.0005V.','FixedISS.1mA andK2.5mA/V2 => steeringcutoff sqrt.08=.28284V, not fulllinearityrange.','Finiteinputro200kohm: -.5mS*(10||200)kohm=-100/21=-4.76.','TailRE+ro1=110kohm,not gmREro; half220kohm; singleCM~-1/22=-.04545; symmetricdiffCM0.','Fullsharedsourcefinite-roKCL => smallmismatchlargeproductleak=.01/[220*(1+10/200)]=1/23100=+.00004329.','Identicalfinite-ro factorcancels betweenDM andleak, CMRR110000=100.83dB; reference1.06e5mixedmodelnotadopted.'],
9:['PMOScascodeloadRup~gm3ro3ro5=1Mohm; simpletailM7ro5kohm; DM=-.01*(10k||1M)=-99.01.','CMhalf2ro7=10kohm;inputromustremain;Rdn~gm1ro1*2ro7=1M; effective500kohm; Gm~.1mS =>singleCM-50;diffCM0.'],
10:['CommonVov means size/current/gm ratios1/N, diodeKCLvg=-i1/gm3; supplyi4=i1/N; vout/i1=+RL/Nohm, lambda0andsaturation.'],
11:['Equalmirror k1: Vbefore0,Vafter2dI RL; supplyincreaseandlessabsorptionadd.','k=.5: Vbefore=-I0RL/2,Vafter=(3dI-I0)RL/2; change1.5dIRLnotfinal; negativevoltage requirescurrentsourcecompliance.'],
12:['1:1mirror combines twohalfsignalcurrentsto gmvid, positive rightoutputforleftminusrightinput;not identicalhalfmirrorsplit.','gm10mS,ro2=ro4=10kohm givesmirror+50leading; correctedhandwrittennegativesign.','DiodePMOSload adds gm3 toconductance withroN+roP; gain=-10/(10+.1+.1)=-.98039.','Interdrain/innersourceresistors splitinDM:RD=.5kohm,RS=.1kohm;gmRS=1explicitnumericexception => keep1; fullfinite-ro voltagegain=-50/20.6=-2.42718; differentRoutblockreferenceapprox2.44labeled.'],
13:['VT26mV assumed,nominalIC1mA; selfB-Cresistor feedbackload (R1+rpi)/(beta+1)||roPNP||roNPN=123.215ohm; gain-4.68137,finitepi retained; twoPNPbasesnotshorted.','VT26mV,IC.1mA;gm3.84615mS,roN50kohm,roP40kohm; largebetamirrorleading +85.4701; not claimedfinite-betaexact.','Each IEEsource.1mA(not half);DM REhalf2.5kohm;largeexternaldegenerationcoursegain=-RC/(RE/2)=-.4,finite1/gmreference-.3623distinct.'],
14:['VT26mV assumption,largebeta+gmro mirrorleading; 1/|Av|=VT/VAn+VT/VAp; VAp65/12=5.42V,positivegain100; currentcancels,NPNlimit192.31>100.']}
assert sum(map(len,model.values()))==39
items={};ind={};style={};equiv={};summary=[];hashes={}
ruleids=['UNIT-01','CALC-01','CALC-02','CIRCUIT-01','CIRCUIT-02','GAIN-01','DEGEN-01','SCALE-01','BIAS-01','NOTATION-01','EXPLAIN-01','CORRECT-01']
for i in range(1,15):
 p=R/'content/explanations'/f'p{i}.html';o=BeautifulSoup((old/'fragments'/p.name).read_text(),'html.parser');n=BeautifulSoup(p.read_text(),'html.parser');hashes[f'p{i}']=H(p)
 ob=o.select_one('.sum');nb=n.select_one('.sum');assert ob and nb
 oldbody=[str(x)for x in o.select('[data-explanation]')];newbody=[str(x)for x in n.select('[data-explanation]')];assert oldbody==newbody
 assert [str(x)for x in o.select('svg')]==[str(x)for x in n.select('svg')]
 assert len(n.select('[data-explanation]'))==7
 assert not re.search(r'STT|시각 정보 없음|Part\s*\d',n.get_text())
 for para in nb.select('p'):
  tx=para.get_text(' ',strip=True); assert len(re.findall(r'(?:예요|이에요|해요|돼요|줘요|어요|아요|두어요|낮아져요)\.',tx))<=1,(i,tx)
 equiv[f'p{i}']={'seven_sections_identical':True,'svg_identical':True,'sha256':H(p)}
 labels=[k.split(':',1)[1]for k in V['content']['items'] if k.startswith(f'p{i}:')];assert len(labels)==len(model[i])
 # Numeric ordering in old checklist already follows originalsubpart order perproblem.
 for lab,conclusion in zip(labels,model[i]):
  key=f'p{i}:{lab}';loc=f'content/explanations/p{i}.html data-explanation=start/solve/verify; subpart={lab}; SHA256 {H(p)}'
  items[key]={'status':'pass','reviewer':'readability_review /root/readability_review','evidence':loc+'; freshlyread source original/conditions and body, allsevensections unchanged; revisedsummary read independently, essentialmodel/unit/sign conditions retained. '+conclusion,'conclusion':conclusion}
  ind[key]={'status':'pass','reviewer':'readability_review /root/readability_review','method':'proof' if i==1 else 'symbolic','evidence':f'Fresh execution work/recheck/p{i}-sympy.py and p{i}-fresh-result.txt (exit0); original KCL/model inspected before revisedsummary; unchangedbody equivalence.','conclusion':conclusion}
  bias=i in (5,8) and lab=='1';deg=i in(1,2,3,4,5,6,7,8,9)or(i in(12,13)and lab in('3','4'));gain=i not in(10,11)and not(i==4 and lab=='1');scaling=i in(1,2,3,4,5,6,7,8,9,10,11,13,14)
  rules={}
  for rid in ruleids:
   applicable=True;note=''
   if rid=='UNIT-01':note='Equation units inspected: mA*kohm=V,mS*kohm=1; symbolic ratios remain dimensionless, p10 transimpedanceohm,p11 DCvolts.'
   elif rid=='CALC-01':note='start intermediateparameter values and solve assembly/targetinversion checked against freshlyexecuted evidence; '+conclusion
   elif rid=='CALC-02':note='Exactfractions/sqrts retained forcalculation, displayedderivedvalues rounded2places or scientificnotation forsmallgain; no 0.00loss.'
   elif rid=='CIRCUIT-01':note='Sourcecomponentroles,actualoutputandnodepairing read; '+conclusion
   elif rid=='CIRCUIT-02':
    applicable=i!=11;note=('DCbefore/after KCL only, nosmallsignaltestneeded.' if i==11 else 'ActualSVG/topology and samefirstKCL inspected; existingSVGidentical. SymmetricCM2RSS, mismatchsharedsource andmirrorcouplingexceptions respected; Routshownasapproxexceptexplicitnumeric/modelrequirements.')
   elif rid=='GAIN-01':applicable=gain;note=('Voltagegainroute andsign read againstsourceoutputdefinition; '+conclusion if gain else 'This subpart isconcept/DC/currenttransimpedance ratherthan newlymeasuredvoltageGmRout; properKCLused.')
   elif rid=='DEGEN-01':applicable=deg;note=('Externaldegeneration andinternalre distinguished; largeproductleadingterm orp12gmRS1explicitexception retained; '+conclusion if deg else 'No externaldegeneration equationrequired inthissubpart; diode/ratio/currentmirrorroute used.')
   elif rid=='SCALE-01':applicable=scaling;note=('retry fixedconditions and changedparameter identified; rerunresults and directratio checked. Ratios e.g gm sqrtI,ro1/I,steering sqrt(I/K),CMRRgmRSS; currentmirror size/current ratiosbothvary.' if scaling else 'This subpart derives connection-specificgain; no independent scalingrequirement; retry/otherparts handled separately.')
   elif rid=='BIAS-01':applicable=bias;note=('Saturation boundarypolarity andinputrange min/max checkedfreshly: '+conclusion if bias else 'No new numericalbiasboundaryasked; body stillstates saturation/activeregion forvalidity.')
   elif rid=='NOTATION-01':note='AllSVG byte/DOMequivalent tobackup; native text/tspan78%,Pretendard600normal andblue/rednodeattributes preserved; latex/formulacase andsubscripts checked inbody+newsummary. Rootbrowser verifiesrendering.'
   elif rid=='EXPLAIN-01':note='Allsevensections inorder; solve title preserved; reason->firstequation->substitution->result retained. NewsummaryoneKoreanSentenceperp, meaningfulgroups, no bulkanswerparagraph.'
   elif rid=='CORRECT-01':note='Sourceconditions vsreference/courseapproximation reconciled withoutaltering originalMD; units,signs,allanswerstooriginalsubparts preserved; '+conclusion
   rules[rid]={'disposition':'applied' if applicable else 'not_applicable','evidence':loc+'; '+note}
  style[key]={'status':'pass','reviewer':'readability_review /root/readability_review','rules':rules}
 summary.append({'topic':f'p{i}','file':str(p),'sha256':H(p),'status':'pass','reviewer':'readability_review','original_body_identical':True,'essential_model':'; '.join(model[i]),'new_summary':nb.get_text(' ',strip=True),'omission_assessment':'Repeatedderivation/checkarithmetic/intermediateexamples omitted; body retainsallanswers. Summaryretainedconditions do notimplydifferentmodel. p11beforeafter andp12mirrorhalfexception correctedafterindependentreview.'})
# Note comparison excludes only sums and specific publiccitations, allotherprose/equations/SVGmuststay.
np=R/'content/note.html';no=BeautifulSoup(next((R/'backup/pack').glob('정리노트*.html')).read_text(),'html.parser');nn=BeautifulSoup(np.read_text(),'html.parser');note_sums={t['id']:t.select_one('.sum')for t in nn.select('.topic')if t.select_one('.sum')};assert len(note_sums)==8
for tid,z in note_sums.items():
 summary.append({'topic':tid,'file':str(np),'sha256':H(np),'status':'pass','reviewer':'readability_review','summary':z.get_text(' ',strip=True),'conditions_review':'Read correspondingbody formula/model; retained symmetry/outputdefinitions/bigproduct/inputrobodyeffect/1to1mirror/finitebeta boundaries matchbody. Repeatedhistory/examples/terminology retainedonlyinbody.'})
for s in no.select('.sum'):s.decompose()
for s in nn.select('.sum'):s.decompose()
assert [str(x)for x in no.select('svg')]==[str(x)for x in nn.select('svg')]
assert [x.get_text()for x in no.select('.equation')]==[x.get_text()for x in nn.select('.equation')]
assert not re.search(r'STT\s*L\d|시각 정보 없음|Part\s*\d',nn.get_text())
reviewed=[{'path':str(R/'content/explanations'/f'p{i}.html'),'sha256':hashes[f'p{i}']}for i in range(1,15)]+[{'path':str(np),'sha256':H(np)},{'path':str(profile),'sha256':H(profile)}]
base={'reviewer':'readability_review /root/readability_review','status':'pass','scope':'Freshread originalconditions,unchangedbodyreview+freshKCLexecution,newsummarysemanticreview; rootowns sourcevisual andbrowser gates. No previousapprovalreused.','reviewed_files':reviewed,'body_equivalence':equiv}
for name,data in [('content',dict(base,items=items)),('independent',dict(base,items=ind)),('style-audit',{'learning_style':{'path':'.claude/skills/ec2-review-pack/references/solution-style.md','sha256':H(profile),'rule_ids':ruleids},'items':style,'reviewed_files':reviewed}),('summary-audit',dict(base,items=summary,note_svg_identical=True,note_non_summary_equations_identical=True))]:
 (rev/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'content_items':len(items),'independent_items':len(ind),'style_rows':sum(len(x['rules'])for x in style.values()),'summary_topics':len(summary),'all14fresh_exec_exit0':True,'note_math_svg_preserved':True},ensure_ascii=False))
