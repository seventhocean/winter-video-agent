// Structured data graphic: shared baseline, numeric hierarchy and one ratio scale.
// Returns ordinary plan layers; no runtime dependencies or topic-specific assets.
export function metricCard({id,beat,x,y,width,start,end,headline,unit,context,rows,scale,show_values=true,theme={}}) {
 if(!Number.isFinite(scale)||scale<=0||width<340||!rows.length)throw Error('Metric card needs a positive shared scale and width >=340');
 const layers=[];
 const common={beat,start,end,motion:{kind:'none',duration:.4}};
 const {color='#ffffff',accent='#73e6ce',muted='#cde0e4',shadow=true}=theme;
 const text=(suffix,value,dx,dy,w,size,fill=color)=>({id:id+'-'+suffix,...common,type:'text',text:value,x:x+dx,y:y+dy,width:w,height:size*1.5,style:{fontSize:size,fontWeight:600,color:fill,shadow}});
 const digits=Math.max(...headline.map(k=>k.value.toFixed(0).length)),numberWidth=Math.min(width*.52,digits*62+6),unitX=numberWidth+16;
 layers.push({id:id+'-hero',...common,type:'counter',x,y,width:numberWidth,height:144,values:headline,decimals:0,value_easing:'ease-out',style:{fontSize:96,fontWeight:700,color,shadow}});
 layers.push(text('unit',unit,unitX,64,width-unitX,28,accent));
 layers.push(text('context',context,0,146,width,18,muted));
 rows.forEach((row,i)=>{
  const rowStart=row.values[0].t,dy=198+i*50,label=text('label-'+i,row.label,0,dy,112,21);
  label.start=rowStart;label.motion={kind:'reveal',duration:.25};layers.push(label);
  const values=row.values.map(k=>({t:k.t,value:k.value/scale}));
  if(values.some(k=>k.value<0||k.value>1))throw Error('Metric row exceeds shared scale');
  layers.push({id:id+'-bar-'+i,...common,start:rowStart,type:'bar',x:x+120,y:y+dy+9,width:width-(show_values?190:120),height:13,values,value_easing:'ease-out',style:{color:row.color||accent,radius:4}});
  if(show_values)layers.push({id:id+'-value-'+i,...common,start:rowStart,type:'counter',x:x+width-64,y:y+dy,width:64,height:36,values:row.values,decimals:row.decimals||0,value_easing:'ease-out',style:{fontSize:21,fontWeight:600,color:row.color||accent,shadow}});
 });
 return layers;
}
