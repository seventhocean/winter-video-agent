import React, {CSSProperties} from 'react';
import {Img, interpolate, interpolateColors, useCurrentFrame, useVideoConfig} from 'remotion';

// Direct reconstruction of the reference's foreground. No panel, host crop,
// generated intermediate timeline, CSS transitions, or continuous idle motion.
type Appearance = 'light' | 'dark';
type Chapter = {kicker: string; label: string};
type Base = {canvasWidth?: number; appearance: Appearance; chapter: Chapter};
type Fact = {text: string; detail?: string; at: number; negative?: boolean};
export type IdentityProps = Base & {name: string; latin: string; facts: Fact[];
  action?: {kicker: string; text: string; at: number}; nameAt?: number};
export type MetricProps = Base & {
  metric: {value: number; unit: string; label: string; context: string; at: number; decimals?: number};
  rows: {label: string; value: number; unit: string; at: number; primary?: boolean}[];
  scaleMax: number; result: {text: string; at: number}; source: string;
  tags?: string[];
};
export type EvidenceProps = {canvasWidth?: number; appearance: Appearance; docSrc: string;
  imageHeight: number; caption: string; at?: number; chapter?: Chapter; captionSize?: number};
export type VerdictProps = Base & {question: string; statement: string; stamp: string;
  statementAt: number; stampAt: number};

const font = '"PingFang SC", "Hiragino Sans GB", sans-serif';
const palette = (appearance: Appearance) => appearance === 'light'
  ? {ink: '#152223', secondary: '#415456', green: '#007642', red: '#c82e3d', gold: '#955c00', bar: '#667578'}
  : {ink: '#ffffff', secondary: '#b0b5b5', green: '#36d566', red: '#ed4256', gold: '#efb948', bar: '#a5a9af'};
// Power4-out growth is also used by TalkCraft's bar-chart-growth; provenance
// records its exact source. The counter below instead uses observed samples.
const progress = (time: number, at: number, duration = .4) =>
  1 - Math.pow(1 - Math.max(0, Math.min(1, (time - at) / duration)), 4);
const entry = (time: number, at: number, distance = 76): CSSProperties => ({
  opacity: Math.max(0, Math.min(1, (time - at) / .16)),
  translate: `${distance * (1 - progress(time, at))}px 0`,
});
// Reuse the confirmed reference counter in both the wide comparison and the
// narrow count/process layout. Input data, never a second hand-tuned curve.
const countedMetric = (time: number, at: number, value: number, decimals = 0) => {
  const p = interpolate(time - at, [0, .125, .25, .375, .5, .625, .75],
    [0, .40, .76, .89, .96, .99, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return Number((value * p).toFixed(decimals));
};
const inkStyle = (appearance: Appearance): CSSProperties => ({
  fontFamily: font, color: palette(appearance).ink, fontWeight: 700,
  // Soft dark shadow on the reference's dark footage, never a white stroke.
  textShadow: appearance === 'dark' ? '0 3px 6px rgba(0,0,0,.55)' : 'none',
  lineHeight: 1.18, WebkitTextStroke: '0px',
});
const Canvas = ({width = 800, logicalWidth = 800, appearance, children}: {width?: number;
  logicalWidth?: number; appearance: Appearance; children: React.ReactNode}) =>
  <div style={{...inkStyle(appearance), position: 'relative', width: logicalWidth,
    scale: width / logicalWidth, transformOrigin: '0 0'}}>{children}</div>;

const ChapterMark = ({chapter, appearance, time, accent, at = 0, labelSize = 25, kickerSize = 27,
  tracking = 6}: {chapter: Chapter; appearance: Appearance; time: number; accent?: string;
  at?: number; labelSize?: number; kickerSize?: number; tracking?: number}) => {
  const colors = palette(appearance);
  const color = accent ?? colors.green;
  return <div style={{...entry(time, at, 28), borderLeft: `5px solid ${color}`, paddingLeft: 20}}>
    <div style={{fontFamily: 'Arial, sans-serif', fontSize: kickerSize, letterSpacing: tracking,
      fontWeight: 800, color}}>{chapter.kicker}</div>
    <div style={{fontSize: labelSize, marginTop: 9}}>{chapter.label}</div>
  </div>;
};

export const IdentityStack = (props: IdentityProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const colors = palette(props.appearance);
  return <Canvas width={props.canvasWidth} appearance={props.appearance}>
    <ChapterMark chapter={props.chapter} appearance={props.appearance} time={time} />
    <div style={{...entry(time, props.nameAt ?? .65), marginTop: 70}}>
      <div style={{fontFamily: 'Arial, sans-serif', fontSize: 56}}>{props.latin}</div>
      <div style={{fontSize: 112, fontWeight: 900, letterSpacing: 2, marginTop: 14}}>{props.name}</div>
    </div>
    <div style={{marginTop: 72, display: 'flex', flexDirection: 'column', gap: 30}}>
      {props.facts.map((fact, i) => <div key={i} style={{...entry(time, fact.at, 45), display: 'flex', alignItems: 'baseline', gap: 18}}>
        {fact.negative && <span style={{color: colors.red, fontSize: 40, fontWeight: 500}}>×</span>}
        <span style={{fontSize: 35, whiteSpace: 'nowrap'}}>{fact.text}</span>
        {fact.detail && <span style={{fontFamily: 'Arial, sans-serif', fontSize: 17,
          letterSpacing: 3, color: colors.secondary}}>{fact.detail}</span>}
      </div>)}
    </div>
    {props.action && <div style={{...entry(time, props.action.at, 35), marginTop: 74,
      borderLeft: `5px solid ${colors.green}`, paddingLeft: 20}}>
      <div style={{fontSize: 18, letterSpacing: 4, color: colors.green}}>{props.action.kicker}</div>
      <div style={{fontSize: 36, marginTop: 14}}>{props.action.text}</div>
    </div>}
  </Canvas>;
};

export const MetricComparison = (props: MetricProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const colors = palette(props.appearance);
  const m = props.metric;
  // 44.125..44.875s: 0,40,76,89,96,99,100 in the reference.
  // This reproduces sampled states, not a claim about the author's easing.
  const value = countedMetric(time, m.at, m.value, m.decimals);
  return <Canvas width={props.canvasWidth} appearance={props.appearance}>
    <ChapterMark chapter={props.chapter} appearance={props.appearance} time={time} />
    <div style={{...entry(time, m.at), marginTop: 26}}>
      <div style={{display: 'flex', alignItems: 'baseline', gap: 18, whiteSpace: 'nowrap'}}>
        <span style={{fontFamily: 'Arial, sans-serif', fontSize: 152, fontWeight: 900,
          letterSpacing: -5, fontVariantNumeric: 'tabular-nums'}}>{value}</span>
        <span style={{fontFamily: 'Arial, sans-serif', fontSize: 64, color: colors.green}}>{m.unit}</span>
        <span style={{fontSize: 38}}>{m.label}</span>
      </div>
      <div style={{fontSize: 27, color: colors.secondary}}>{m.context}</div>
    </div>
    <div style={{marginTop: 38, display: 'flex', flexDirection: 'column', gap: 18}}>
      {props.rows.map((row, i) => {
        const grow = progress(time, row.at, .6);
        const length = 320 * row.value / props.scaleMax;
        const color = row.primary ? colors.green : colors.bar;
        return <div key={i} style={{...entry(time, row.at, 26), display: 'flex', alignItems: 'center', gap: 16}}>
          <div style={{width: 148, flexShrink: 0, fontSize: 24, whiteSpace: 'nowrap',
            color: row.primary ? colors.ink : colors.secondary}}>{row.label}</div>
          <div style={{position: 'relative', width: 510, height: 32}}>
            <div style={{position: 'absolute', left: 0, top: 4, width: length, height: 25,
              borderRadius: 6, background: color, scale: `${grow} 1`, transformOrigin: '0 50%'}} />
            <div style={{position: 'absolute', left: length * grow + 12, top: 0,
              fontFamily: 'Arial, sans-serif', fontSize: 28, whiteSpace: 'nowrap', color}}>
              {row.value} {row.unit}
            </div>
            {i === props.rows.length - 1 && <div style={{...entry(time, props.result.at, 30),
              position: 'absolute', left: length + 96, top: -10, fontSize: 32,
              color: colors.gold, border: `2px solid ${colors.gold}`, borderRadius: 9,
              padding: '4px 14px', whiteSpace: 'nowrap'}}>{props.result.text}</div>}
          </div>
        </div>;
      })}
    </div>
    <div style={{...entry(time, props.result.at, 30), fontSize: 18,
      color: colors.secondary, marginTop: 26}}>{props.source}</div>
    {props.tags && <div style={{...entry(time, props.result.at + .3, 20), marginTop: 35,
      display: 'flex', gap: 28, fontSize: 28}}>{props.tags.map((tag, i) =>
      <span key={tag} style={{color: i === 0 ? colors.green : colors.ink}}>{tag}</span>)}</div>}
  </Canvas>;
};

export const EvidenceImage = (props: EvidenceProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const width = props.canvasWidth ?? 800;
  return <div style={{...inkStyle(props.appearance), ...entry(time, props.at ?? .65, 100)}}>
    {props.chapter && <div style={{marginBottom: 28}}>
      <ChapterMark chapter={props.chapter} appearance={props.appearance} time={time}
        at={props.at ?? .65} accent={props.appearance === 'light' ? '#1765a4' : '#52a9ff'}
        labelSize={35} kickerSize={24} tracking={3} />
    </div>}
    <Img src={props.docSrc} style={{display: 'block', width, height: props.imageHeight,
      objectFit: 'contain', borderRadius: 18}} />
    <div style={{fontSize: props.captionSize ?? 24, marginTop: 16, paddingLeft: 16, display: 'flex', alignItems: 'center', gap: 12}}>
      <span style={{width: 8, height: 8, borderRadius: '50%', background: palette(props.appearance).green}} />
      {props.caption}
    </div>
  </div>;
};

export type MetricProcessProps = Base & {
  metric: {value: number; unit: string; context: string; at: number};
  docSrc: string; evidence: {at: number; caption: string};
  steps: {text: string; detail: string; at: number}[];
  result: {text: string; at: number}; clearAt: number;
};

// Narrow, vertically reflowed count + source + process. The 4:3 presenter is
// never moved; only this foreground group is arranged for the actual space.
export const MetricProcess = (props: MetricProcessProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const colors = palette(props.appearance);
  const blue = props.appearance === 'light' ? '#1765a4' : '#52a9ff';
  const clear = interpolate(time, [props.clearAt, props.clearAt + .25], [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const value = countedMetric(time, props.metric.at, props.metric.value);
  return <Canvas width={props.canvasWidth ?? 520} logicalWidth={520} appearance={props.appearance}>
    <div style={{position: 'relative', height: 820, opacity: clear}}>
      <ChapterMark chapter={props.chapter} appearance={props.appearance} time={time}
        labelSize={36} kickerSize={23} tracking={3} />
      <div style={{...entry(time, props.metric.at, 28), position: 'absolute', left: 0, top: 90}}>
        <div style={{display: 'flex', alignItems: 'baseline', gap: 15, color: colors.green}}>
          <span style={{fontSize: 156, lineHeight: 1.1, fontFamily: 'Arial, sans-serif',
            fontWeight: 900, fontVariantNumeric: 'tabular-nums', letterSpacing: -5}}>{value}</span>
          <span style={{fontSize: 60}}>{props.metric.unit}</span>
        </div>
        <div style={{fontSize: 33, marginTop: 0}}>{props.metric.context}</div>
      </div>
      <div style={{...entry(time, props.evidence.at, 28), position: 'absolute', left: 0, top: 305}}>
        <Img src={props.docSrc} style={{display: 'block', width: 520, height: 112, objectFit: 'contain', borderRadius: 8}} />
        <div style={{fontSize: 22, color: colors.secondary, marginTop: 11}}>{props.evidence.caption}</div>
      </div>
      {props.steps.map((step, i) => {
        const active = progress(time, step.at + .22, .3);
        const color = interpolateColors(active, [0, 1], [blue, colors.green]);
        return <React.Fragment key={i}>
          {i > 0 && <div style={{position: 'absolute', left: 33, top: 482 + i * 110 - 25,
            width: 2, height: 22, background: blue, opacity: progress(time, step.at, .18),
            scale: `1 ${progress(time, step.at, .3)}`, transformOrigin: 'center top'}} />}
          <div style={{...entry(time, step.at, 28), position: 'absolute', left: 0,
            top: 482 + i * 110, width: 520, height: 88, display: 'flex', alignItems: 'center',
            gap: 18, border: `1px solid ${color}`, borderRadius: 12, boxSizing: 'border-box', padding: '0 18px'}}>
            <span style={{fontFamily: 'Arial, sans-serif', fontSize: 43, color, fontWeight: 800}}>{i + 1}</span>
            <div style={{whiteSpace: 'nowrap'}}>
              <div style={{fontSize: 36, fontWeight: 800}}>{step.text}</div>
              <div style={{fontSize: 22, color: i === props.steps.length - 1 && time >= props.result.at
                ? colors.green : colors.secondary, marginTop: 5}}>
                {i === props.steps.length - 1 && time >= props.result.at ? props.result.text : step.detail}
              </div>
            </div>
          </div>
        </React.Fragment>;
      })}
    </div>
  </Canvas>;
};

export const VerdictStamp = (props: VerdictProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const colors = palette(props.appearance);
  return <Canvas width={props.canvasWidth} appearance={props.appearance}>
    <ChapterMark chapter={props.chapter} appearance={props.appearance} time={time} />
    <div style={{...entry(time, .45), marginTop: 65, fontSize: 110,
      fontFamily: 'Arial, sans-serif', fontWeight: 900}}>{props.question}</div>
    <div style={{...entry(time, props.statementAt, 100), marginTop: 48, fontSize: 54}}>{props.statement}</div>
    <div style={{opacity: Math.max(0, Math.min(1, (time - props.stampAt) / .1)),
      scale: interpolate(time, [props.stampAt, props.stampAt + .25], [1.8, 1],
        {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
      rotate: '-8deg', transformOrigin: '50% 50%', display: 'inline-block',
      marginTop: 55, padding: '14px 24px', border: `6px solid ${colors.red}`,
      color: colors.red, fontSize: 58, fontWeight: 900}}>{props.stamp}</div>
  </Canvas>;
};

type ProcessNode = {text: string; detail: string; at: number; imageIndex: number};
type DateEvent = {date: string; label: string; caption: string; at: number};
export type DevelopmentProps = Base & {
  headline: {value: string; unit: string; caption: string; at: number};
  nodes: ProcessNode[]; srcs: string[];
  timeline: {at: number; events: DateEvent[]; resultAt: number; caption: string};
  clearAt: number;
};

// The chain and timeline are direct React pieces of one accumulated scene.
// Connectors carry a process/date relationship; there is no decorative linework.
const ProcessChain = ({nodes, srcs, time, appearance}: {nodes: ProcessNode[]; srcs: string[];
  time: number; appearance: Appearance}) => {
  const blue = appearance === 'dark' ? '#52a9ff' : '#1765a4';
  const positions = [0, 349, 677], widths = [277, 260, 277];
  return <div style={{position: 'absolute', top: 415, left: 0}}>
    {nodes.map((node, i) => <React.Fragment key={i}>
      {i > 0 && <svg width={48} height={22} viewBox="0 0 48 22"
        style={{position: 'absolute', left: positions[i] - 57, top: 29,
          opacity: progress(time, node.at, .18), overflow: 'visible'}}>
        <g style={{transform: `scaleX(${progress(time, node.at, .3)})`, transformOrigin: '0 11px'}}>
          <path d="M1 11H43M35 3L43 11L35 19" fill="none" stroke={blue} strokeWidth={3}
            strokeLinecap="round" strokeLinejoin="round" />
        </g>
      </svg>}
      <div style={{...entry(time, node.at, 35), position: 'absolute', left: positions[i],
        width: widths[i], height: 80, boxSizing: 'border-box', border: `1px solid ${blue}`,
        borderRadius: 12, display: 'flex', alignItems: 'center', gap: 12, padding: '0 18px'}}>
        <Img src={srcs[node.imageIndex]} style={{width: 27, height: 27, flexShrink: 0}} />
        <div style={{whiteSpace: 'nowrap'}}>
          <div style={{fontSize: i === 2 ? 24 : 26}}>{node.text}</div>
          <div style={{fontFamily: 'Arial, sans-serif', fontSize: 16, letterSpacing: 2,
            color: palette(appearance).secondary, marginTop: 6}}>{node.detail}</div>
        </div>
      </div>
    </React.Fragment>)}
  </div>;
};

const EventTimeline = ({timeline, time, appearance}: {timeline: DevelopmentProps['timeline'];
  time: number; appearance: Appearance}) => {
  const colors = palette(appearance);
  const blue = appearance === 'dark' ? '#52a9ff' : '#1765a4';
  const positions = [305, 1005], baseline = 650;
  const days = (Date.parse(timeline.events[1].date) - Date.parse(timeline.events[0].date)) / 86400000;
  return <>
    <div style={{position: 'absolute', left: 75, top: baseline - 1, height: 2, width: 1205,
      background: colors.secondary, opacity: .55 * progress(time, timeline.at, .3),
      scale: `${progress(time, timeline.at, .4)} 1`, transformOrigin: 'left center'}} />
    {timeline.events.map((event, i) => {
      const color = i === 0 ? blue : colors.green;
      return <React.Fragment key={event.date}>
        <div style={{position: 'absolute', left: positions[i] - 10, top: baseline - 10,
          width: 20, height: 20, borderRadius: '50%', background: color,
          boxSizing: 'border-box', border: `2px solid ${colors.ink}`,
          opacity: progress(time, event.at, .15), scale: .4 + .6 * progress(time, event.at, .25)}} />
        <div style={{...entry(time, event.at, 24), position: 'absolute', left: positions[i] - 230,
          top: baseline + 37, width: 460, textAlign: 'center'}}>
          <div style={{fontSize: 30, color}}>{event.label}</div>
          <div style={{fontSize: 24, marginTop: 10}}>{event.caption}</div>
        </div>
      </React.Fragment>;
    })}
    <div style={{position: 'absolute', left: positions[0], top: baseline - 2,
      width: positions[1] - positions[0], height: 4, background: colors.gold,
      scale: `${progress(time, timeline.resultAt, .55)} 1`, transformOrigin: 'left center'}} />
    <div style={{...entry(time, timeline.resultAt, 30), position: 'absolute', left: 480,
      top: baseline - 87, width: 350, textAlign: 'center'}}>
      <div style={{fontSize: 50, color: colors.gold, fontFamily: 'Arial, sans-serif', fontWeight: 900}}>
        {days} DAYS
      </div>
      <div style={{fontSize: 24, marginTop: 7}}>{timeline.caption}</div>
    </div>
  </>;
};

export const DevelopmentTime = (props: DevelopmentProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const colors = palette(props.appearance);
  const clear = interpolate(time, [props.clearAt, props.clearAt + .18], [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return <Canvas width={props.canvasWidth ?? 1300} logicalWidth={1300} appearance={props.appearance}>
    <div style={{position: 'relative', height: 780, opacity: clear}}>
      <div style={{...entry(time, 0, 28), borderLeft: `5px solid ${colors.gold}`, paddingLeft: 20}}>
        <div style={{fontFamily: 'Arial, sans-serif', fontSize: 27, letterSpacing: 6,
          color: colors.gold, fontWeight: 800}}>{props.chapter.kicker}</div>
        <div style={{fontSize: 25, marginTop: 9}}>{props.chapter.label}</div>
      </div>
      <div style={{...entry(time, props.headline.at), position: 'absolute', left: 0, top: 105,
        display: 'flex', alignItems: 'baseline', gap: 18, whiteSpace: 'nowrap'}}>
        <span style={{fontFamily: 'Arial, sans-serif', fontSize: 200, fontWeight: 900,
          color: colors.gold, lineHeight: 1.1}}>{props.headline.value}</span>
        <span style={{fontFamily: 'Arial, sans-serif', fontSize: 100, fontWeight: 900,
          color: colors.gold}}>{props.headline.unit}</span>
        <span style={{fontSize: 44, marginLeft: 15}}>{props.headline.caption}</span>
      </div>
      <ProcessChain nodes={props.nodes} srcs={props.srcs} time={time} appearance={props.appearance} />
      <EventTimeline timeline={props.timeline} time={time} appearance={props.appearance} />
    </div>
  </Canvas>;
};

type RelationNode = {text: string; at: number; imageIndex: number; activeImageIndex: number};
export type DatabaseProps = Base & {
  chapterAt: number; srcs: string[];
  hub: {text: string; system: string; hint: string; at: number; imageIndex: number};
  left: RelationNode[]; right: RelationNode[];
  activateAt: number; result: {text: string; detail: string; at: number; imageIndex: number};
  clearAt: number;
};

// Adapted from TalkCraft source-converge's cubic paths and draw-on strokes.
// SVG pathLength normalizes each actual curve; no runtime DOM measurement.
// Nodes remain where they are, with no swallowing, packets or idle pulses.
const relationPath = (left: boolean, y: number) => left
  ? `M 210,${y} C 260,${y} 300,465 340,465`
  : `M 605,${y} C 550,${y} 530,465 490,465`;
const relationY = (i: number, count: number) => count === 1 ? 430 : 190 + i * 480 / (count - 1);

export const DatabaseRelations = (props: DatabaseProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const colors = palette(props.appearance);
  const blue = props.appearance === 'dark' ? '#52a9ff' : '#1765a4';
  // A single state time drives the lines, borders and icons together.
  const active = interpolate(time, [props.activateAt, props.activateAt + .12], [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const clear = interpolate(time, [props.clearAt, props.clearAt + .3], [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const nodeColor = interpolateColors(active, [0, 1], [colors.secondary, colors.green]);
  const count = props.left.length + props.right.length;
  const groups = [{nodes: props.left, left: true}, {nodes: props.right, left: false}];
  return <Canvas width={props.canvasWidth ?? 1500} logicalWidth={1500} appearance={props.appearance}>
    <div style={{position: 'relative', height: 850, opacity: clear}}>
      <div style={{position: 'absolute', left: 15, top: 0}}>
        <ChapterMark chapter={props.chapter} appearance={props.appearance} time={time}
          accent={blue} at={props.chapterAt} />
      </div>
      <svg width={815} height={760} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
        {groups.flatMap(group => group.nodes.map((node, i) => {
          const draw = progress(time, node.at + .1, .4);
          const path = relationPath(group.left, relationY(i, group.nodes.length) + 35);
          return <React.Fragment key={`${group.left}-${i}`}>
            <path d={path} pathLength={1} fill="none" stroke={colors.secondary}
              strokeWidth={1.6} opacity={.7} strokeDasharray={1} strokeDashoffset={1 - draw} />
            <path d={path} pathLength={1} fill="none" stroke={colors.green}
              strokeWidth={3.2} opacity={active} strokeDasharray={1} strokeDashoffset={1 - draw} />
          </React.Fragment>;
        }))}
      </svg>
      <div style={{...entry(time, props.hub.at, 40), position: 'absolute', left: 265,
        top: 370, width: 300, textAlign: 'center'}}>
        <div style={{width: 150, height: 150, margin: '0 auto', border: `2px solid ${blue}`,
          borderRadius: 34, boxSizing: 'border-box', display: 'flex', alignItems: 'center',
          justifyContent: 'center', scale: .85 + .15 * progress(time, props.hub.at, .4)}}>
          <Img src={props.srcs[props.hub.imageIndex]} style={{width: 74, height: 74}} />
        </div>
        <div style={{fontSize: 30, fontWeight: 900, marginTop: 15}}>{props.hub.text}</div>
        <div style={{fontSize: 17, fontFamily: 'Arial, sans-serif', letterSpacing: 2.5,
          color: colors.secondary, marginTop: 14}}>{props.hub.system} · {count} 类表全关联</div>
        <div style={{fontSize: 18, marginTop: 14, whiteSpace: 'nowrap',
          position: 'relative', left: -40, width: 380}}>{props.hub.hint}</div>
      </div>
      {groups.flatMap(group => group.nodes.map((node, i) =>
        <div key={`${group.left}-${i}`} style={{...entry(time, node.at, 35), position: 'absolute',
          left: group.left ? 0 : 605, top: relationY(i, group.nodes.length), width: 210, height: 58,
          border: `1px solid ${nodeColor}`, borderRadius: 12, boxSizing: 'border-box',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12}}>
          <div style={{position: 'relative', width: 25, height: 25, flexShrink: 0}}>
            <Img src={props.srcs[node.imageIndex]} style={{position: 'absolute', width: 25, height: 25, opacity: 1 - active}} />
            <Img src={props.srcs[node.activeImageIndex]} style={{position: 'absolute', width: 25, height: 25, opacity: active}} />
          </div>
          <div style={{fontSize: 28, fontWeight: 800, whiteSpace: 'nowrap'}}>{node.text}</div>
        </div>
      ))}
      <div style={{...entry(time, props.result.at, 60), position: 'absolute', left: 1080,
        top: 750, display: 'flex', alignItems: 'center', gap: 16}}>
        <Img src={props.srcs[props.result.imageIndex]} style={{width: 34, height: 34}} />
        <div>
          <div style={{fontSize: 50, fontWeight: 900, whiteSpace: 'nowrap'}}>{props.result.text}</div>
          <div style={{fontSize: 18, letterSpacing: 5, fontFamily: 'Arial, sans-serif',
            marginTop: 10, color: colors.gold}}>{props.result.detail}</div>
        </div>
      </div>
    </div>
  </Canvas>;
};

type TemperatureSample = {at: number; value: number};
export type TemperatureProps = Base & {
  sectionNumber: string; srcs: string[];
  condition: {text: string; at: number; imageIndex: number};
  reading: {unit: string; samples: TemperatureSample[]};
  range: {comfortable: {min: number; max: number; position: number};
    threshold: {value: number; position: number}};
  risk: {text: string; source: string; at: number; imageIndex: number};
  before: {label: string; scaleText: string; at: number;
    nodes: {text: string; at: number; imageIndex: number}[]};
  after: {kicker: string; label: string; at: number}; clearAt: number;
};

export const TemperatureAlert = (props: TemperatureProps) => {
  const time = useCurrentFrame() / useVideoConfig().fps;
  const colors = palette(props.appearance);
  const blue = props.appearance === 'dark' ? '#2693ff' : '#1765a4';
  const samples = props.reading.samples;
  const reading = interpolate(time, samples.map(s => s.at), samples.map(s => s.value),
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  // The source reveals the full gradient as 18→40 rises. This is an animated
  // heat-range illustration, not an axis whose pixels measure temperature.
  // Marker positions are explicit; the same sampled reading drives the reveal.
  const grow = (reading - samples[0].value) / (samples[samples.length - 1].value - samples[0].value);
  const hot = reading > props.range.threshold.value;
  const readingColor = hot ? colors.red : colors.ink;
  const clear = interpolate(time, [props.clearAt, props.clearAt + .3], [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const chapterClear = interpolate(time, [props.clearAt + .2, props.clearAt + .45], [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const icon = (index: number, size: number) => <Img src={props.srcs[index]}
    style={{width: size, height: size, flexShrink: 0}} />;
  return <Canvas width={props.canvasWidth ?? 900} logicalWidth={900} appearance={props.appearance}>
    <div style={{position: 'relative', height: 730}}>
      {/* The chapter is established by the preceding evidence shot and stays
          through this range/alert sequence, rather than restarting every beat. */}
      <div style={{opacity: chapterClear}}>
        <div style={{position: 'absolute', left: 0, top: 0, color: blue,
          fontFamily: 'Arial, sans-serif', fontSize: 144, fontWeight: 900,
          letterSpacing: -8, lineHeight: 1}}>{props.sectionNumber}</div>
        <div style={{position: 'absolute', left: 185, top: 0, width: 3, height: 125, background: blue}} />
        <div style={{position: 'absolute', left: 210, top: 20, fontFamily: 'Arial, sans-serif',
          color: blue, fontSize: 25, fontWeight: 800, letterSpacing: 5}}>{props.chapter.kicker}</div>
        <div style={{position: 'absolute', left: 210, top: 64, fontSize: 34,
          fontWeight: 900}}>{props.chapter.label}</div>
      </div>
      <div style={{opacity: clear}}>
        <div style={{...entry(time, props.condition.at, 24), position: 'absolute', left: 3,
          top: 260, display: 'flex', alignItems: 'center', gap: 18, fontSize: 28}}>
          {icon(props.condition.imageIndex, 26)}{props.condition.text}
        </div>
        <div style={{...entry(time, props.condition.at, 24), position: 'absolute', left: 570,
          top: 240, width: 213, textAlign: 'right', color: readingColor,
          fontFamily: 'Arial, sans-serif', fontSize: 74, fontWeight: 900,
          fontVariantNumeric: 'tabular-nums', letterSpacing: -2}}>
          {Math.round(reading)}{props.reading.unit}
        </div>
        <div style={{...entry(time, props.condition.at, 24), position: 'absolute', left: 3, top: 338}}>
          <div style={{position: 'relative', width: 780, height: 17, borderRadius: 9,
            overflow: 'hidden', background: props.appearance === 'dark' ? '#555b57' : '#b5bfba'}}>
            <div style={{position: 'absolute', inset: 0,
              background: `linear-gradient(90deg, ${colors.green} 0%, ${colors.green} 15%, ${colors.red} 85%, ${colors.red} 100%)`,
              clipPath: `inset(0 ${100 * (1 - grow)}% 0 0 round 9px)`}} />
          </div>
          <div style={{position: 'absolute', left: props.range.threshold.position * 780 - 1.5,
            top: -3, width: 3, height: 26, background: colors.red}} />
          <div style={{position: 'absolute', left: props.range.comfortable.position * 780 - 85,
            top: 27, width: 170, textAlign: 'center', color: colors.green, fontSize: 18}}>
            {props.range.comfortable.min}-{props.range.comfortable.max}{props.reading.unit} 适温
          </div>
          <div style={{position: 'absolute', left: props.range.threshold.position * 780 - 85,
            top: 27, width: 170, textAlign: 'center', color: colors.red, fontSize: 18}}>
            {props.range.threshold.value}{props.reading.unit} 上限
          </div>
        </div>
        <div style={{...entry(time, props.risk.at, 30), position: 'absolute', left: 3, top: 399,
          display: 'flex', alignItems: 'center', gap: 18, color: colors.red, whiteSpace: 'nowrap'}}>
          {icon(props.risk.imageIndex, 25)}
          <span style={{fontSize: 38, fontWeight: 900}}>{props.risk.text}</span>
          <span style={{fontSize: 18, color: colors.secondary, marginLeft: -3}}>{props.risk.source}</span>
        </div>
        <div style={{...entry(time, props.before.at, 24), position: 'absolute', left: 3, top: 485,
          display: 'flex', alignItems: 'center', gap: 12, color: colors.secondary}}>
          <span style={{fontFamily: 'Arial, sans-serif', fontSize: 22, letterSpacing: 5}}>BEFORE</span>
          <span style={{fontSize: 22}}>{props.before.label}</span>
          <span style={{fontSize: 20, color: colors.red, border: `1px solid ${colors.red}`,
            borderRadius: 18, padding: '5px 13px'}}>{props.before.scaleText}</span>
        </div>
        {props.before.nodes.map((node, i) => <React.Fragment key={i}>
          {i > 0 && <div style={{position: 'absolute', left: 3 + i * 219 - 45, top: 558,
            width: 30, height: 2, background: colors.secondary,
            opacity: .65 * progress(time, node.at, .15),
            scale: `${progress(time, node.at, .3)} 1`, transformOrigin: 'left center'}} />}
          <div style={{...entry(time, node.at, 25), position: 'absolute', left: 3 + i * 219,
            top: 530, width: 165, height: 58, border: `1px solid ${colors.secondary}88`,
            borderRadius: 9, boxSizing: 'border-box', display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: 10, fontSize: 26, color: colors.secondary, whiteSpace: 'nowrap'}}>
            {icon(node.imageIndex, 25)}{node.text}
          </div>
        </React.Fragment>)}
        <div style={{...entry(time, props.after.at, 25), position: 'absolute', left: 3, top: 638,
          display: 'flex', alignItems: 'baseline', gap: 14}}>
          <span style={{fontFamily: 'Arial, sans-serif', fontSize: 21, letterSpacing: 4,
            color: blue}}>{props.after.kicker}</span>
          <span style={{fontSize: 23}}>{props.after.label}</span>
        </div>
      </div>
    </div>
  </Canvas>;
};
