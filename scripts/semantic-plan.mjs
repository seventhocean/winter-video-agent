import fs from 'node:fs';
import path from 'node:path';
import {read,atomic,hash,projectRoot,validatePlan,lockProject} from '../core/semantic-plan.mjs';
const [command,projectArg,input,...rest]=process.argv.slice(2);
try {
 const project=projectRoot(projectArg),file=path.join(project,'project.json');
 if(command==='check') {
  const plan=validatePlan(read(input||path.join(project,'input/semantic-plan.json')),read(file));
  console.log(JSON.stringify({valid:true,layers:plan.layers.length,beats:plan.beats.length}));
 } else if(command==='set') {
  const unlock=lockProject(project);
  try {
   const metadata=read(file),plan=validatePlan(read(input),metadata),fingerprint=hash(JSON.stringify(plan));
   const archive=path.join(project,'decisions/plans');fs.mkdirSync(archive,{recursive:true});
   atomic(path.join(archive,fingerprint+'.json'),plan);atomic(path.join(project,'input/semantic-plan.json'),plan);
   if(metadata.plan?.hash!==fingerprint) {
    metadata.plan={hash:fingerprint,path:'input/semantic-plan.json',review:'pending'};
    metadata.status='planned';
   }
   atomic(file,metadata);
   console.log(JSON.stringify({plan_hash:fingerprint,status:metadata.status}));
  } finally {unlock();}
 } else if(command==='review') {
  const [verdict,...comment]=rest;
  if(!['approved','changes-requested'].includes(verdict)||!comment.length)throw Error('review PROJECT PREVIEW_FILENAME approved|changes-requested USER_FEEDBACK');
  const unlock=lockProject(project);
  try {
   const metadata=read(file),artifact=metadata.artifacts.find(a=>path.basename(a.path)===input);
   if(!artifact)throw Error('Preview not found');
   const decision={artifact:artifact.path,sha256:artifact.sha256,plan_hash:artifact.plan_hash||null,verdict,feedback:comment.join(' '),at:new Date().toISOString()};
   metadata.decisions??=[];metadata.decisions.push(decision);artifact.review=verdict;
   if(metadata.plan && metadata.plan.hash===artifact.plan_hash)metadata.plan.review=verdict;
   atomic(file,metadata);console.log(JSON.stringify(decision));
  }finally{unlock();}
 } else throw Error('Usage: semantic-plan.mjs check|set PROJECT [PLAN_JSON]; review PROJECT PREVIEW_FILENAME VERDICT USER_FEEDBACK');
} catch(error){console.error(JSON.stringify({error:error.message}));process.exitCode=1;}
