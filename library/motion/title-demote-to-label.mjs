// Adapted from video-talkcraft/template/cards/title-demote-to-label.tsx,
// commit 914103688cdec20ea35699f73b08e357a817c37a. See library/planning/provenance.json.
// Required Notice: Copyright (c) 2026 Vincent Wei (https://github.com/Vincentwei1021/video-talkcraft)
// License: https://polyformproject.org/licenses/noncommercial/1.0.0/

// Copied timing defaults and overlapping schedule; geometry/content are per episode.
const CONFIG={reveal:.40,stand:.70,demote:.67,growDelay:.40,stagger:.55,growDur:.50,rise:28};
const geometry=p=>Object.fromEntries(['x','y','width','height'].map(k=>[k,p[k]]));

export function titleDemote({id,beat,start,end,title_end=end,title,from,to,items=[],timing={},style={}}) {
 const cfg={...CONFIG,...timing};
 for(const k of Object.keys(timing))if(!Object.hasOwn(CONFIG,k))throw Error('Unknown title timing: '+k);
 if(Object.values(cfg).some(v=>!Number.isFinite(v)||v<0)||cfg.reveal<=0||cfg.demote<=0||cfg.growDur<=0)throw Error('Invalid title timing');
 if(!title||!from||!to||!Array.isArray(items)||items.length>4||new Set(items.map(i=>i.id)).size!==items.length)throw Error('Title demotion needs title, from/to geometry and at most four distinct content objects');
 const demoteAt=start+cfg.reveal+cfg.stand;
 const growAt=demoteAt+cfg.growDelay;
 if(!Number.isFinite(title_end)||title_end>end||demoteAt+cfg.demote>=title_end)throw Error('Reserve time to read the demoted title');
 const layers=[{id:id+'-title',beat,type:'text',text:title,start,end:title_end,...geometry(from),style,
  motion:{kind:'reveal',duration:cfg.reveal},keyframe_easing:'in-out',
  keyframes:[{t:start,...geometry(from)},{t:demoteAt,...geometry(from)},{t:demoteAt+cfg.demote,...geometry(to)}]}];
 for(const [i,item] of items.entries()) {
  const at=item.at??growAt+i*cfg.stagger,pose=geometry(item.pose),{id:itemId,pose:unused,at:ignored,...content}=item;
  if(!Number.isFinite(at)||at<growAt||at+cfg.growDur>=end)throw Error('Content must follow the title and leave reading time');
  layers.push({...content,id:id+'-'+itemId,beat,start:at,end,...pose,
   motion:{kind:'reveal',duration:cfg.growDur},keyframe_easing:'ease-out',
   keyframes:[{t:at,...pose,y:pose.y+cfg.rise},{t:at+cfg.growDur,...pose}]});
 }
 return layers;
}
