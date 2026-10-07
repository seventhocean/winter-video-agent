import React from 'react';
import {AbsoluteFill, Composition, Img, OffthreadVideo, Sequence, registerRoot, staticFile, useCurrentFrame} from 'remotion';
import Doc from './cards/doc-park-left-pill-deal';
import Grid from './cards/grid-to-hero';
import Media from './cards/media-pop-in';
import {IdentityStack, MetricComparison, MetricProcess, EvidenceImage, VerdictStamp, DevelopmentTime, DatabaseRelations, TemperatureAlert} from './Scenes';
import data from './shotbook.json';

type Shot = {id: string; card: string; from: number; duration: number; heading?: string;
  placement: {x: number; y: number; scale: number; width?: number; height?: number}; props: Record<string, any>};
type Book = {width: number; height: number; fps: number; sourceFrame: number;
  durationInFrames: number; shots: Shot[]; referenceSrc?: string};
const book = data as Book;

// TalkCraft keeps its own frame-based shotbook and native TSX components.
// These cards are templates; generated instances are controlled by the shotbook.
const cards: Record<string, React.ComponentType<any>> = {
  'doc-park-left-pill-deal': Doc, 'grid-to-hero': Grid, 'media-pop-in': Media,
  'identity-stack': IdentityStack, 'metric-comparison': MetricComparison,
  'evidence-image': EvidenceImage, 'verdict-stamp': VerdictStamp,
  'development-time': DevelopmentTime,
  'database-relations': DatabaseRelations,
  'temperature-alert': TemperatureAlert,
  'metric-process': MetricProcess,
};
const assetProps = (props: Record<string, any>) => ({
  ...props,
  ...(props.docSrc ? {docSrc: staticFile(props.docSrc)} : {}),
  ...(props.srcs ? {srcs: props.srcs.map((src: string) => staticFile(src))} : {}),
});

const Overlay = ({shot}: {shot: Shot}) => {
  const frame = useCurrentFrame();
  const Card = cards[shot.card as keyof typeof cards] as React.ComponentType<any>;
  const {x, y, scale, width = 960, height = 540} = shot.placement;
  const originalCard = ['doc-park-left-pill-deal', 'grid-to-hero', 'media-pop-in'].includes(shot.card);
  const opacity = Math.min(1, Math.max(0, (shot.duration - 1 - frame) / 8));
  return <>
    {shot.heading && <div style={{position: 'absolute', left: x + 40 * scale, top: y - 90,
      fontFamily: '"PingFang SC", sans-serif', fontSize: 44, fontWeight: 650,
      color: '#142c48', opacity, letterSpacing: -1, whiteSpace: 'pre-line'}}>{shot.heading}</div>}
    <div style={{position: 'absolute', left: x, top: y, width: width * scale,
      height: height * scale, overflow: originalCard ? 'hidden' : 'visible', opacity}}>
      <div style={{position: 'absolute', width, height,
        transform: `scale(${scale})`, transformOrigin: '0 0'}}>
        <Card {...assetProps(shot.props)} canvasWidth={width} />
      </div>
    </div>
  </>;
};

const Foreground = () => <>{book.shots.map((shot) =>
  <Sequence key={shot.id} name={shot.id} from={shot.from} durationInFrames={shot.duration}>
    <Overlay shot={shot} />
  </Sequence>)}</>;

const NativeVideo = () => (
  <AbsoluteFill style={{background: '#000'}}>
    <OffthreadVideo src={staticFile('source.mov')} trimBefore={book.sourceFrame}
      style={{width: '100%', height: '100%', objectFit: 'contain'}} />
    <Foreground />
  </AbsoluteFill>
);

// Calibration views belong to the same instance, with no extra renderer or
// style package. Their matte is never part of the production composition.
const OverlayOnly = () => <AbsoluteFill style={{background: '#1b2321'}}><Foreground /></AbsoluteFill>;
const ReferenceFrame = () => <AbsoluteFill><Img src={staticFile(book.referenceSrc!)}
  style={{width: '100%', height: '100%', objectFit: 'contain'}} /></AbsoluteFill>;
const ReferenceComparison = () => {
  const time = (book.sourceFrame + useCurrentFrame()) / book.fps;
  const panelWidth = book.width / 2, panelHeight = book.height / 2;
  const top = book.height / 4;
  return <AbsoluteFill style={{background: '#111716', color: '#fff', fontFamily: '"PingFang SC", sans-serif'}}>
    {['原片 · 含原有动效', '复建 · 独立透明前景'].map((label, i) =>
      <div key={label} style={{position: 'absolute', left: i * panelWidth + 35, top: top - 70,
        fontSize: 32, fontWeight: 650}}>{label}</div>)}
    <div style={{position: 'absolute', left: 0, top, width: panelWidth, height: panelHeight, overflow: 'hidden'}}>
      <div style={{width: book.width, height: book.height, transform: 'scale(.5)', transformOrigin: '0 0'}}>
        <OffthreadVideo src={staticFile('source.mov')} trimBefore={book.sourceFrame}
          style={{width: book.width, height: book.height, objectFit: 'contain'}} />
      </div>
    </div>
    <div style={{position: 'absolute', left: panelWidth, top, width: panelWidth, height: panelHeight,
      overflow: 'hidden', background: '#1b2321'}}>
      <div style={{position: 'relative', width: book.width, height: book.height,
        transform: 'scale(.5)', transformOrigin: '0 0'}}><Foreground /></div>
    </div>
    <div style={{position: 'absolute', left: 35, top: top + panelHeight + 35, fontSize: 27, color: '#b0b5b5'}}>
      原片时间 {Math.floor(time / 60)}:{(time % 60).toFixed(2).padStart(5, '0')} · 两侧同步，原声只播放一次
    </div>
  </AbsoluteFill>;
};
const Root = () => <>
  <Composition id="TalkCraftNative" component={NativeVideo}
    width={book.width} height={book.height} fps={book.fps} durationInFrames={book.durationInFrames} />
  <Composition id="OverlayOnly" component={OverlayOnly}
    width={book.width} height={book.height} fps={book.fps} durationInFrames={book.durationInFrames} />
  <Composition id="ReferenceComparison" component={ReferenceComparison}
    width={book.width} height={book.height} fps={book.fps} durationInFrames={book.durationInFrames} />
  {book.referenceSrc && <Composition id="ReferenceFrame" component={ReferenceFrame}
    width={book.width} height={book.height} fps={book.fps} durationInFrames={book.durationInFrames} />}
</>;
registerRoot(Root);
