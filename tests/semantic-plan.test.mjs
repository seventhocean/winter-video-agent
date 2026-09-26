import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {read,validatePlan} from '../core/semantic-plan.mjs';

const example=read(new URL('../library/recipes/progressive-explanation/example.json',import.meta.url));
const metadata={primary_workflow:'talking-head',format:{width:1280,height:720,fps:30},clip:{start:0,duration:6},assets:{}};
test('no-mask plan rejects panels and text backgrounds',()=>{
 const p=structuredClone(example);p.no_mask=true;
 p.layers=[{...p.layers.find(l=>l.type==='text'),style:{background:'#0008'}}];
 assert.throws(()=>validatePlan(p,metadata),/no_mask/);
 p.layers[0].style={};validatePlan(p,metadata);
 p.layers[0].type='panel';assert.throws(()=>validatePlan(p,metadata),/no_mask/);
});
test('shot ranges cover clip and align to frames',()=>{
 const p=structuredClone(example);p.shots=[{id:'first',start:0,end:2},{id:'second',start:2,end:6}];
 validatePlan(p,metadata);
 p.shots[1].start=2.1;assert.throws(()=>validatePlan(p,metadata),/gaps/);
 p.shots[1].start=2.01;p.shots[0].end=2.01;assert.throws(()=>validatePlan(p,metadata),/frame boundary/);
});
test('invalid timing and missing media stop a render before work starts',()=>{
 const bad=structuredClone(example);bad.layers[0].end=20;
 assert.throws(()=>validatePlan(bad,metadata),/timing/);
 bad.layers[0]={...example.layers[0],type:'image',asset:'not-registered'};
 assert.throws(()=>validatePlan(bad,metadata),/Missing asset/);
});
test('protected face/subtitle region rejects overlapping layout',()=>{
 const bad=structuredClone(example);bad.protected_regions=[{x:700,y:100,width:50,height:50}];
 assert.throws(()=>validatePlan(bad,metadata),/protected region/);
});
test('moving media cannot sweep through protected regions, connectors require live endpoints',()=>{
 const p=structuredClone(example);p.protected_regions=[{x:880,y:100,width:20,height:50}];
 const assetPath=new URL('../library/recipes/progressive-explanation/stage.html',import.meta.url).pathname;
 const project={...metadata,assets:{sample:{path:assetPath}}};
 const moving={id:'moving',beat:p.beats[0].id,type:'image',asset:'sample',x:700,y:100,width:50,height:50,start:0,end:6,keyframes:[{t:0,x:700,y:100,width:50,height:50},{t:3,x:1000,y:100,width:50,height:50}]};
 p.layers=[moving];assert.throws(()=>validatePlan(p,project),/Motion intersects/);
 p.protected_regions=[];
 const target={id:'target',beat:p.beats[0].id,type:'text',text:'Result',x:1000,y:400,width:100,height:50,start:0,end:6};
 const connector={id:'connection',beat:p.beats[0].id,type:'connector',x:690,y:90,width:430,height:400,start:0,end:6,active_at:1,from:{layer:'moving',anchor:'bottom'},to:{layer:'target',anchor:'top'}};
 p.layers.push(target,connector);validatePlan(p,project);
 target.end=5;assert.throws(()=>validatePlan(p,project),/outlives/);
 target.end=6;connector.to.layer='missing';assert.throws(()=>validatePlan(p,project),/endpoint/);
});
test('timed face protection permits a layout only outside its active shot',()=>{
 const p=read(new URL('../library/recipes/progressive-explanation/relations-example.json',import.meta.url));
 validatePlan(p,metadata);
 p.protected_regions=[{x:620,y:140,width:100,height:50,start:0,end:1}];
 // Connectors conservatively contain their endpoints, so omit them for this layout check.
 p.layers=p.layers.filter(l=>l.type!=='connector');validatePlan(p,metadata);
 p.protected_regions[0].end=2;assert.throws(()=>validatePlan(p,metadata),/protected region/);
});
test('same plan keeps review, changing plan invalidates approval, old review cannot approve new plan',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'wva-plan-'));
 try {
  fs.mkdirSync(path.join(dir,'input'));fs.writeFileSync(path.join(dir,'project.json'),JSON.stringify({...metadata,artifacts:[]}));
  const input=path.join(dir,'draft.json'),projectFile=path.join(dir,'project.json');
  fs.writeFileSync(input,JSON.stringify(example));
  const run=(...args)=>{const r=spawnSync(process.execPath,['scripts/semantic-plan.mjs',...args],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);};
  run('set',dir,input);let p=read(projectFile);const oldHash=p.plan.hash;
  p.artifacts.push({path:path.join(dir,'preview.mp4'),sha256:'test-artifact',plan_hash:oldHash});fs.writeFileSync(projectFile,JSON.stringify(p));
  run('review',dir,'preview.mp4','approved','Explicit test feedback');
  run('set',dir,input);assert.equal(read(projectFile).plan.review,'approved');
  const changed=structuredClone(example);changed.layers[0].text='Another explanation';fs.writeFileSync(input,JSON.stringify(changed));
  run('set',dir,input);assert.notEqual(read(projectFile).plan.hash,oldHash);
  run('review',dir,'preview.mp4','approved','Old preview only');assert.equal(read(projectFile).plan.review,'pending');
 } finally {fs.rmSync(dir,{recursive:true,force:true});}
});
