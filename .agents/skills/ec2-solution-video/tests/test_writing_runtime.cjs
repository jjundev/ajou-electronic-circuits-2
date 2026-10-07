const test=require('node:test'), assert=require('node:assert/strict');
test('draw/move endpoints and backward frameState',()=>{
 const {frameState}=require('../assets/writing.js');
 const t={writing_spans:[{kind:'move',start_frame:0,end_frame:1,id:'g'},{kind:'draw',start_frame:1,end_frame:6,id:'g'}]};
 assert.equal(frameState(t,{},0).progress,1);
 assert.deepEqual([1,3,5].map(f=>frameState(t,{},f).progress),[0,.5,1]);
 assert.equal(frameState(t,{},6).span,null);
 assert.equal(frameState(t,{},3).progress,.5);
});
