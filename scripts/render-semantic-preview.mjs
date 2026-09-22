// Frame-driven HTML overlay; uses an explicitly selected external Playwright runtime.
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const [projectArg,runtimeArg,browserPath,version='preview-v2']=process.argv.slice(2);
if(!projectArg||!runtimeArg||!browserPath)throw Error('Usage: node scripts/render-semantic-preview.mjs PROJECT PLAYWRIGHT_PACKAGE_JSON CHROME [VERSION]');
if(!/^[a-z0-9-]+$/.test(version))throw Error('Invalid version');
const project=fs.realpathSync(projectArg),root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
if(project===root||project.startsWith(root+path.sep))throw Error('Project must be outside Agent repository');
const metadata=JSON.parse(fs.readFileSync(path.join(project,'project.json'),'utf8'));
if(metadata.format.width!==1280||metadata.format.height!==960)throw Error('This first semantic profile requires 1280x960');
const output=path.join(project,'preview',version+'.mp4');
if(fs.existsSync(output))throw Error('Preview exists; choose a new version');
const frames=path.join(project,'work',version+'-frames');fs.mkdirSync(frames,{recursive:true});
const template=fs.readFileSync(path.join(root,'workflows/talking-head/semantic-stage.html'),'utf8');
fs.writeFileSync(path.join(project,'work',version+'-stage.html'),template);
const data={};for(const id of ['terminal','assistant','real']){const item=metadata.assets[id];if(!item)throw Error('Missing asset '+id);data[id]='data:image/'+(id==='real'?'jpeg':'png')+';base64,'+fs.readFileSync(item.path).toString('base64');}
const {chromium}=createRequire(path.resolve(runtimeArg))('playwright');
const browser=await chromium.launch({executablePath:browserPath,headless:true});
const fps=metadata.format.fps,total=Math.round(metadata.clip.duration*fps);
try{
 const page=await browser.newPage({viewport:{width:1280,height:960},deviceScaleFactor:1});
 await page.setContent(template);await page.evaluate(data=>window.setup(data),data);
 await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(im=>im.decode()));});
 for(let n=0;n<total;n++){await page.evaluate(t=>window.seek(t),n/fps);await page.screenshot({path:path.join(frames,String(n).padStart(5,'0')+'.png'),omitBackground:true});if(n%60===0)console.log(`overlay ${n}/${total}`);}
}finally{await browser.close();}
const args=['-hide_banner','-loglevel','warning','-n','-ss',String(metadata.clip.start),'-i',metadata.source.path,'-framerate',String(fps),'-i',path.join(frames,'%05d.png'),'-filter_complex','[0:v]scale=1280:960,setsar=1,fps='+fps+',setpts=PTS-STARTPTS[host];[host][1:v]overlay=0:0:shortest=1[out]','-map','[out]','-map','0:a:0?','-t',String(metadata.clip.duration),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',output];
fs.writeFileSync(path.join(project,'work',version+'-command.json'),JSON.stringify(args,null,2));
const result=spawnSync('ffmpeg',args,{stdio:'inherit'});if(result.status!==0)throw Error('FFmpeg failed');
const hash=createHash('sha256').update(fs.readFileSync(output)).digest('hex');
metadata.artifacts.push({path:output,kind:'preview',review:'awaiting-user',sha256:hash,profile:'semantic-stage-v0',template_snapshot:path.join(project,'work',version+'-stage.html')});metadata.status='previewed';
fs.writeFileSync(path.join(project,'project.json'),JSON.stringify(metadata,null,2)+'\n');
console.log(JSON.stringify({preview:output,frames:total,review:'awaiting-user'}));
