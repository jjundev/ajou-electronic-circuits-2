const fs=require('node:fs'),path=require('node:path');
const {createFrequencyModel}=require('./frequency-model.cjs');
const {createTopic}=require('./frequency-topics.cjs');
function replaceOnce(src,re,value) {
  const hits=[...src.matchAll(new RegExp(re.source,'g'))];
  if(hits.length!==1)throw new Error('template anchor count '+hits.length);
  return src.replace(re,()=>value);
}
function makeSource(kind) {
  const topic=createTopic(kind);
  let src=fs.readFileSync(path.join(__dirname,'../assets/template.dc.html'),'utf8');
  src=src.replaceAll('__TITLE__',topic.title);
  for(const side of ['left','right']){
    const re=new RegExp('<!-- SLOT:'+side+' -->[\\s\\S]*?<!-- /SLOT:'+side+' -->');
    src=replaceOnce(src,re,'<!-- SLOT:'+side+' -->\n'+topic[side]+'\n<!-- /SLOT:'+side+' -->');
  }
  const methods=Object.values(topic.hooks).map(fn=>'  '+fn.toString()).join('\n\n');
  src=replaceOnce(src,/  topic\(\) \{[\s\S]*?(?=  \/\/ ================= 공통 셸)/,
    methods+'\n\n');
  const declarations=createFrequencyModel.toString()+'\nconst FM=createFrequencyModel();\nconst CFG='+
    JSON.stringify(topic.config)+';\n'+topic.drawScene.toString()+'\n';
  src=src.replace('class Component extends DCLogic {',declarations+'class Component extends DCLogic {');
  return src;
}
if(require.main===module){
  const [kind,out]=process.argv.slice(2);
  if(!['cs','two'].includes(kind)||!out){console.error('usage: node make-frequency-example.cjs cs|two OUT.dc.html');process.exit(2);}
  fs.writeFileSync(path.resolve(out),makeSource(kind));
}
module.exports={makeSource};
