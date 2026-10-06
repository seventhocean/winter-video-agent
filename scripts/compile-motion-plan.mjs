// Compile a JSON construction plan; no arbitrary code or expressions are executed.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {atomic,read,projectRoot,validatePlan,lockProject,hash} from '../core/semantic-plan.mjs';
import {builders} from '../library/motion/choreography.mjs';

const [projectArg,input]=process.argv.slice(2);
let unlock;
try {
 const project=projectRoot(projectArg);unlock=lockProject(project);
 const construction=read(input),{motions=[],...base}=construction;
 if(!Array.isArray(motions))throw Error('motions must be an array');
 const layers=[...(base.layers||[])],used=new Set();
 for(const spec of motions) {
  if(!Object.hasOwn(builders,spec.method))throw Error('Unknown motion method: '+spec.method);
  used.add(spec.method);layers.push(...builders[spec.method](spec));
 }
 const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
 const catalog=read(path.join(root,'library/motion/catalog.json'));
 const plan=validatePlan({...base,layers,motion_sources:[...used].map(id=>{
  const record=catalog.items.find(item=>item.id===id);
  return {id,implementation:catalog.implementation,design_reference:record.design_reference};
 }),construction_hash:hash(fs.readFileSync(input))},read(path.join(project,'project.json')));
 const fingerprint=hash(JSON.stringify(plan)),archive=path.join(project,'decisions/constructions');
 fs.mkdirSync(archive,{recursive:true});
 atomic(path.join(archive,fingerprint+'.json'),construction);
 const output=path.join(project,'input/semantic-plan-compiled.json');atomic(output,plan);
 console.log(JSON.stringify({plan:output,layers:layers.length,methods:[...used],construction_archive:path.join(archive,fingerprint+'.json')}));
}catch(error){console.error(JSON.stringify({error:error.message}));process.exitCode=1;}
finally{if(unlock)unlock();}
