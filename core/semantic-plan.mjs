import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
export const hash = value => createHash('sha256').update(value).digest('hex');
export const read = file => JSON.parse(fs.readFileSync(file,'utf8'));
export function atomic(file,value) {
 const temp=file+'.'+process.pid+'.tmp';
 fs.writeFileSync(temp,JSON.stringify(value,null,2)+'\n');fs.renameSync(temp,file);
}
export function projectRoot(input) {
 const p=fs.realpathSync(input),repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
 if(p===repo||p.startsWith(repo+path.sep))throw Error('Project must be outside Agent repository');
 return p;
}
export function lockProject(project) {
 const target=path.join(project,'.semantic.lock'),fd=fs.openSync(target,'wx');
 fs.writeFileSync(fd,JSON.stringify({pid:process.pid,started:new Date().toISOString()}));
 return ()=>{fs.closeSync(fd);fs.unlinkSync(target);};
}
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const assert=(test,message)=>{if(!test)throw Error(message);};
export function validatePlan(plan,project) {
 assert(plan.schema_version===1&&plan.recipe==='progressive-explanation','Unsupported plan version/recipe');
 assert(typeof plan.intent==='string'&&plan.intent.trim(),'Missing semantic intent');
 assert(project.primary_workflow==='talking-head','Recipe only supports talking-head');
 const {width,height}=plan.canvas||{};
 assert([width,height].every(v=>Number.isInteger(v)&&v>=320&&v<=4096&&v%2===0),'Invalid canvas');
 assert(width===project.format?.width&&height===project.format?.height,'Canvas must match project format');
 assert(finite(project.format.fps)&&project.format.fps>0&&project.format.fps<=60,'Invalid fps');
 assert(finite(project.clip?.duration)&&project.clip.duration>0&&finite(project.clip.start)&&project.clip.start>=0,'Invalid clip');
 const interval=o=>finite(o.start)&&finite(o.end)&&o.start>=0&&o.end>o.start&&o.end<=project.clip.duration;
 if(plan.no_mask!==undefined)assert(typeof plan.no_mask==='boolean','Invalid no_mask');
 if(plan.shots!==undefined) {
  assert(Array.isArray(plan.shots)&&plan.shots.length>0,'Missing shots');
  let end=0;const shotIds=new Set();
  for(const shot of plan.shots) {
   assert(typeof shot.id==='string'&&/^[a-z0-9-]+$/.test(shot.id)&&!shotIds.has(shot.id),'Invalid shot ID');shotIds.add(shot.id);
   assert(interval(shot)&&Math.abs(shot.start-end)<1e-8,'Shots must cover clip without gaps or overlaps');
   assert([shot.start,shot.end].every(t=>Math.abs(t*project.format.fps-Math.round(t*project.format.fps))<1e-6),'Shot must start/end on frame boundary');
   end=shot.end;
  }
  assert(Math.abs(end-project.clip.duration)<1e-8,'Shots must cover entire clip');
 }
 assert(Array.isArray(plan.beats)&&plan.beats.length>0,'Missing semantic beats');
 const ids=new Set();
 for(const beat of plan.beats) {
  assert(typeof beat.id==='string'&&!ids.has(beat.id),'Invalid/duplicate beat ID');ids.add(beat.id);
  assert(interval(beat),'Invalid beat timing: '+beat.id);
  assert(typeof beat.purpose==='string'&&beat.purpose.trim(),'Missing beat purpose');
 }
 const regions=plan.protected_regions||[];
 for(const r of regions)assert([r.x,r.y,r.width,r.height].every(finite)&&r.width>0&&r.height>0,'Invalid protected region');
 assert(Array.isArray(plan.layers)&&plan.layers.length>0&&plan.layers.length<=100,'Expected 1–100 layers');
 const layerIds=new Set();
 for(const l of plan.layers) {
  assert(typeof l.id==='string'&&!layerIds.has(l.id),'Invalid/duplicate layer ID');layerIds.add(l.id);
  assert(ids.has(l.beat),'Unknown beat: '+l.id);
  assert(['text','image','panel','line'].includes(l.type),'Unknown layer type');
  assert(interval(l),'Invalid layer timing: '+l.id);
  assert(['x','y','width','height'].every(k=>finite(l[k])),'Invalid geometry: '+l.id);
  assert(l.width>0&&l.height>0&&l.x>=0&&l.y>=0&&l.x+l.width<=width&&l.y+l.height<=height,'Layer outside canvas: '+l.id);
  for(const r of regions)assert(!(l.x<r.x+r.width&&l.x+l.width>r.x&&l.y<r.y+r.height&&l.y+l.height>r.y),'Layer intersects protected region: '+l.id);
  if(l.type==='text')assert(typeof l.text==='string'&&l.text.length>0,'Missing text: '+l.id);
  if(l.type==='image')assert(project.assets?.[l.asset]?.path&&fs.existsSync(project.assets[l.asset].path),'Missing asset: '+l.asset);
  const s=l.style||{},nums=['fontSize','fontWeight','radius','borderWidth','padding'],colors=['color','background','borderColor'];
  if(plan.no_mask)assert(l.type!=='panel'&&!s.background,'no_mask forbids panels and background fills: '+l.id);
  for(const k of Object.keys(s))assert([...nums,...colors,'align','fit'].includes(k),'Unknown style: '+k);
  for(const k of nums)if(k in s)assert(finite(s[k])&&s[k]>=0,'Invalid '+k);
  for(const k of colors)if(k in s)assert(/^#(?:[0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(s[k]),'Use hex colors: '+k);
  if(s.align)assert(['left','center','right'].includes(s.align),'Invalid align');
  if(s.fit)assert(['contain','cover'].includes(s.fit),'Invalid fit');
  if(l.motion) {
   assert(['reveal','pop','draw','none'].includes(l.motion.kind),'Invalid motion');
   assert(finite(l.motion.duration)&&l.motion.duration>0&&l.motion.duration<=l.end-l.start,'Invalid motion duration');
  }
 }
 return plan;
}
