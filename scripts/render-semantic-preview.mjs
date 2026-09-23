// Data-driven talking-head preview. Runtime and media stay outside the repo.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {read,atomic,hash,projectRoot,validatePlan,lockProject} from '../core/semantic-plan.mjs';

const [projectArg,runtimeArg,browserPath,version='preview-v3',stillArg,shotId]=process.argv.slice(2);
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
let unlock;
async function fileHash(file) {
 const digest=createHash('sha256');
 for await(const chunk of fs.createReadStream(file))digest.update(chunk);
 return digest.digest('hex');
}
try {
 if(!projectArg||!runtimeArg||!browserPath)throw Error('Usage: render-semantic-preview.mjs PROJECT PLAYWRIGHT_PACKAGE_JSON CHROME VERSION [STILL_SECONDS]');
 if(!/^[a-z0-9-]+$/.test(version))throw Error('Invalid version');
 const project=projectRoot(projectArg);unlock=lockProject(project);
 const metadata=read(path.join(project,'project.json'));
 const plan=validatePlan(read(path.join(project,'input/semantic-plan.json')),metadata);
 const planHash=hash(JSON.stringify(plan));
 if(metadata.plan?.hash!==planHash)throw Error('Plan changed; register it with semantic-plan.mjs set first');
 const {width,height,fps}=metadata.format;
 const shot=stillArg==='--shot'?plan.shots?.find(s=>s.id===shotId):null;
 if(stillArg==='--shot'&&!shot)throw Error('Unknown shot: '+shotId);
 const range=shot||{start:0,end:metadata.clip.duration};
 const duration=range.end-range.start;
 const still=stillArg!==undefined&&stillArg!=='--shot',second=Number(stillArg);
 if(still&&(!Number.isFinite(second)||second<0||second>=metadata.clip.duration))throw Error('Invalid still time');
 const output=path.join(project,'preview',version+(still?'.png':'.mp4'));
 if(fs.existsSync(output))throw Error('Output exists; choose a new version');
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
 const frames=path.join(project,'work',version+'-frames');fs.mkdirSync(frames,{recursive:true});
 const snapshot=path.join(project,'work',version+'-snapshot.json');
 atomic(snapshot,{plan,plan_hash:planHash,asset_hashes:assetHashes,source_hash:sourceHash,format:metadata.format,clip:metadata.clip,render_range:range,template_hash:hash(template)});
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
 const args=['-hide_banner','-loglevel','warning','-n','-ss',String(metadata.clip.start+(still?second:range.start)),'-i',metadata.source.path,'-framerate',String(fps),'-i',path.join(frames,'%05d.png'),'-filter_complex','[0:v]scale='+width+':'+height+':force_original_aspect_ratio=decrease,pad='+width+':'+height+':(ow-iw)/2:(oh-ih)/2,setsar=1,fps='+fps+',setpts=PTS-STARTPTS[host];[host][1:v]overlay=0:0:shortest=1[out]','-map','[out]'];
 if(still)args.push('-frames:v','1');
 else args.push('-map','0:a:0?','-t',String(duration),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart');
 const pending=path.join(project,'work',version+(still?'.pending.png':'.pending.mp4'));
 if(fs.existsSync(pending))throw Error('Partial render exists; inspect or use another version');
 args.push(pending);atomic(path.join(project,'work',version+'-command.json'),args);
 if(spawnSync('ffmpeg',args,{stdio:'inherit'}).status!==0)throw Error('FFmpeg failed; incomplete output retained in work');
 fs.renameSync(pending,output);
 const current=read(path.join(project,'project.json'));
 current.artifacts.push({path:output,kind:still?'still':'preview',review:'awaiting-user',sha256:hash(fs.readFileSync(output)),plan_hash:planHash,snapshot,profile:plan.recipe});
 current.status='previewed';atomic(path.join(project,'project.json'),current);
 console.log(JSON.stringify({preview:output,frames:total,review:'awaiting-user'}));
} catch(error){console.error(JSON.stringify({error:error.message}));process.exitCode=1;}
finally{if(unlock)unlock();}
