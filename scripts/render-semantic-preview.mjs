// Data-driven talking-head preview/render. Runtime and media stay outside the repo.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {read,atomic,hash,projectRoot,validatePlan,lockProject} from '../core/semantic-plan.mjs';
import {sourceFilter} from '../core/source-layout.mjs';

const [projectArg,runtimeArg,browserPath,version='preview-v3',...options]=process.argv.slice(2);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
let unlock;
async function fileHash(file) {
 const digest=createHash('sha256');
 for await(const chunk of fs.createReadStream(file))digest.update(chunk);
 return digest.digest('hex');
}
try {
 if(!projectArg||!runtimeArg||!browserPath)throw Error('Usage: render-semantic-preview.mjs PROJECT PLAYWRIGHT_PACKAGE_JSON CHROME VERSION [STILL_SECONDS]');
 let kind='preview',shotId,stillArg;
 for(let i=0;i<options.length;i++) {
  if(options[i]==='--kind')kind=options[++i];
  else if(options[i]==='--shot')shotId=options[++i];
  else if(stillArg===undefined&&Number.isFinite(Number(options[i])))stillArg=options[i];
  else throw Error('Unknown render option: '+options[i]);
 }
 if(!['preview','render'].includes(kind)||kind==='render'&&(shotId||stillArg!==undefined))throw Error('render requires the full clip; use preview for a shot or still');
 if(shotId&&stillArg!==undefined)throw Error('Choose a shot or a still time, not both');
 if(!/^[a-z0-9-]+$/.test(version))throw Error('Invalid version');
 const project=projectRoot(projectArg);unlock=lockProject(project);
 const metadata=read(path.join(project,'project.json'));
 const plan=validatePlan(read(path.join(project,'input/semantic-plan.json')),metadata);
 const planHash=hash(JSON.stringify(plan));
 if(metadata.plan?.hash!==planHash)throw Error('Plan changed; register it with semantic-plan.mjs set first');
 const {width,height,fps}=metadata.format;
 const shot=shotId?plan.shots?.find(s=>s.id===shotId):null;
 if(shotId&&!shot)throw Error('Unknown shot: '+shotId);
 const range=shot||{start:0,end:metadata.clip.duration};
 const duration=range.end-range.start;
 const still=stillArg!==undefined,second=Number(stillArg);
 if(still&&(!Number.isFinite(second)||second<0||second>=metadata.clip.duration))throw Error('Invalid still time');
 const directory=path.join(project,kind);fs.mkdirSync(directory,{recursive:true});
 const output=path.join(directory,version+(still?'.png':'.mp4'));
 if(fs.existsSync(output))throw Error('Output exists; choose a new version');
 if(metadata.artifacts.some(a=>path.basename(a.path)===path.basename(output)))throw Error('Artifact version already registered; choose a unique version');
 const template=fs.readFileSync(path.join(root,'library/recipes/progressive-explanation/stage.html'),'utf8');
 const sourceProbe=spawnSync('ffprobe',['-v','error','-show_format','-show_streams','-of','json',metadata.source.path],{encoding:'utf8'});
 if(sourceProbe.status!==0)throw Error('Cannot read source media');
 const media=JSON.parse(sourceProbe.stdout);
 if(metadata.clip.start+metadata.clip.duration>Number(media.format.duration)+.05)throw Error('Clip exceeds source duration');
 const sourceHash=await fileHash(metadata.source.path);
 if(sourceHash!==metadata.source.sha256)throw Error('Source changed since registration');
 const assets={},assetHashes={};
 for(const id of new Set(plan.layers.filter(l=>l.type==='image').map(l=>l.asset))) {
  const item=metadata.assets[id],bytes=fs.readFileSync(item.path),suffix=path.extname(item.path).toLowerCase();
  const mime={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}[suffix];
  if(!mime)throw Error('Unsupported image type: '+suffix);
  assetHashes[id]=hash(bytes);if(assetHashes[id]!==item.sha256)throw Error('Asset changed; register again: '+id);
  assets[id]='data:'+mime+';base64,'+bytes.toString('base64');
 }
 const frames=path.join(project,'work',version+'-frames');
 const snapshot=path.join(project,'work',version+'-snapshot.json');
 const pending=path.join(project,'work',version+(still?'.pending.png':'.pending.mp4'));
 if([frames,snapshot,pending].some(file=>fs.existsSync(file)))throw Error('Version has existing work files; inspect them or choose a new version');
 fs.mkdirSync(frames);
 const runtime={node:process.execPath,playwright_package:path.resolve(runtimeArg),browser:browserPath,node_version:process.version,playwright_version:JSON.parse(fs.readFileSync(runtimeArg,'utf8')).version};
 atomic(snapshot,{plan,plan_hash:planHash,asset_hashes:assetHashes,source_hash:sourceHash,format:metadata.format,clip:metadata.clip,render_range:range,render_kind:still?'still':kind,runtime,frame_cache:frames,template_hash:hash(template),source_layout_code_hash:hash(fs.readFileSync(path.join(root,'core/source-layout.mjs')))});
 fs.writeFileSync(path.join(project,'work',version+'-stage.html'),template);
 const {chromium}=createRequire(path.resolve(runtimeArg))('playwright');
 const browser=await chromium.launch({executablePath:browserPath,headless:true});
 const total=still?1:Math.round(duration*fps);
 try {
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
  await page.route('**/*',route=>route.abort()); // Assets are data URLs; no remote requests.
  await page.setContent(template);await page.evaluate(data=>{window.planDuration=data.duration;window.setup(data);},{plan,assets,duration:metadata.clip.duration});
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(im=>im.decode()));});
  const overflow=await page.evaluate(()=>window.measure());
  if(overflow.length)throw Error('Text overflow: '+overflow.join(', '));
  for(let n=0;n<total;n++) {
   await page.evaluate(t=>window.seek(t),still?second:range.start+n/fps);
   await page.screenshot({path:path.join(frames,String(n).padStart(5,'0')+'.png'),omitBackground:true});
   if(n%60===0)console.log('overlay '+n+'/'+total);
  }
 } finally {await browser.close();}
 const args=['-hide_banner','-loglevel','warning','-n','-ss',String(metadata.clip.start+(still?second:range.start)),'-i',metadata.source.path,'-framerate',String(fps),'-i',path.join(frames,'%05d.png'),'-filter_complex',sourceFilter(plan,metadata.format,still?1:duration)+';[base][1:v]overlay=0:0:shortest=1[out]','-map','[out]'];
 if(still)args.push('-frames:v','1','-update','1');
 else args.push('-map','0:a:0?','-t',String(duration),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart');
 args.push(pending);atomic(path.join(project,'work',version+'-command.json'),args);
 if(spawnSync('ffmpeg',args,{stdio:'inherit'}).status!==0)throw Error('FFmpeg failed; incomplete output retained in work');
 const outputProbe=spawnSync('ffprobe',['-v','error','-show_format','-show_streams','-of','json',pending],{encoding:'utf8'});
 if(outputProbe.status!==0)throw Error('Cannot inspect rendered output');
 const outputMedia=JSON.parse(outputProbe.stdout),video=outputMedia.streams.find(s=>s.codec_type==='video');
 if(!video||video.width!==width||video.height!==height)throw Error('Rendered dimensions differ from project');
 if(!still) {
  const [n,d]=video.r_frame_rate.split('/').map(Number),audio=outputMedia.streams.find(s=>s.codec_type==='audio');
  if(Math.abs(n/d-fps)>1e-6||Number(video.nb_frames)!==total||Math.abs(Number(video.duration)-duration)>1/fps+.001)throw Error('Rendered frame coverage differs from plan');
  if(media.streams.some(s=>s.codec_type==='audio')&&(!audio||Math.abs(Number(audio.duration)-duration)>.12))throw Error('Rendered audio coverage differs from source');
 }
 fs.renameSync(pending,output);
 outputMedia.format.filename=output;
 const current=read(path.join(project,'project.json'));
 current.artifacts.push({path:output,kind:still?'still':kind,review:'awaiting-user',sha256:await fileHash(output),bytes:fs.statSync(output).size,plan_hash:planHash,snapshot,metadata:outputMedia,technical_status:'checked',profile:plan.recipe});
 current.status=kind==='render'?'production':'previewed';atomic(path.join(project,'project.json'),current);
 console.log(JSON.stringify({[kind]:output,frames:total,review:'awaiting-user',technical_status:'checked'}));
} catch(error){console.error(JSON.stringify({error:error.message}));process.exitCode=1;}
finally{if(unlock)unlock();}
