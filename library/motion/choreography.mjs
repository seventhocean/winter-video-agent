// Compile content-specific choreography into existing deterministic plan layers.
// No fixed palette, assets, canvas or topic; no dependency on upstream runtimes.
import {metricCard} from '../recipes/progressive-explanation/metric-card.mjs';
import {titleDemote} from './title-demote-to-label.mjs';

const geometry=p=>Object.fromEntries(['x','y','width','height'].map(k=>[k,p[k]]));

export function objectMotion({poses,method,...layer}) {
 if(!Array.isArray(poses)||!poses.length)throw Error('object-motion needs timed poses');
 const start=layer.start??poses[0].t;
 if(start!==poses[0].t)throw Error('First pose must match layer start');
 return [{...layer,start,...geometry(poses[0]),
  ...(poses.length>1?{keyframes:poses.map(p=>({t:p.t,...geometry(p)})),keyframe_easing:layer.keyframe_easing||'in-out'}:{}),
  motion:layer.motion||{kind:'none',duration:Math.min(.3,layer.end-start)}}];
}

export function groupSequence({id,beat,items,phases,end,stagger=0,motion}) {
 if(!items?.length||!phases?.length||!Number.isFinite(stagger)||stagger<0)throw Error('group-sequence needs items, phases and a nonnegative stagger');
 if(phases.some(p=>!Array.isArray(p.poses)||p.poses.length!==items.length))throw Error('Each group phase needs one pose per item');
 return items.flatMap((item,i)=>{
  const start=phases[0].t+i*stagger;
  const poses=phases.map((phase,j)=>({t:j===0?start:phase.t,...geometry(phase.poses[i])}));
  if(poses.some((p,j)=>!Number.isFinite(p.t)||p.t>end||j&&p.t<=poses[j-1].t))throw Error('Group phases must remain ordered after stagger');
  return objectMotion({...item,id:id+'-'+item.id,beat,end,poses,motion:item.motion||motion});
 });
}

export function evidenceFocus({views,method,...layer}) {
 if(!Array.isArray(views)||views.length<2||views.some(v=>!v.crop))throw Error('evidence-focus needs at least two timed views with crops');
 return objectMotion({...layer,type:'image',poses:views,
  crop_keyframes:views.map(v=>({t:v.t,...v.crop}))});
}

export const builders={'object-motion':objectMotion,'group-sequence':groupSequence,
 'evidence-focus':evidenceFocus,'metric-card':metricCard,'title-demote-to-label':titleDemote};
