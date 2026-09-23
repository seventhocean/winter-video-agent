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
