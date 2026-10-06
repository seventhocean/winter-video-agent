// Reframe the real source on a stage before adding semantic layers.
// The crop is normalized to the original source, preserving its aspect ratio.
export function sourceFilter(plan,format,duration) {
 const {width,height,fps}=format,v=plan.source_layout;
 const timing=`setsar=1,fps=${fps},setpts=PTS-STARTPTS`;
 if(!v)return `[0:v]scale=${width}:${height}:force_original_aspect_ratio=decrease,pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2,${timing}[base]`;
 const c=v.crop||{x:0,y:0,width:1,height:1};
 const crop=`crop=trunc(iw*${c.width}/2)*2:trunc(ih*${c.height}/2)*2:trunc(iw*${c.x}/2)*2:trunc(ih*${c.y}/2)*2`;
 return `[0:v]${crop},scale=${v.width}:${v.height}:force_original_aspect_ratio=decrease,${timing}[host];color=c=${v.background.replace('#','0x')}:s=${width}x${height}:r=${fps}:d=${duration+1}[stage];[stage][host]overlay=${v.x}:${v.y}:shortest=1[base]`;
}
