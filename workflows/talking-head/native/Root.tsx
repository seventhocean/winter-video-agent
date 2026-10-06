import React from 'react';
import {AbsoluteFill, Composition, OffthreadVideo, Sequence, registerRoot, staticFile, useCurrentFrame} from 'remotion';
import Doc from './cards/doc-park-left-pill-deal';
import Grid from './cards/grid-to-hero';
import Media from './cards/media-pop-in';
import book from './shotbook.json';

// TalkCraft keeps its own frame-based shotbook and native TSX components.
// These cards are templates; generated instances are controlled by the shotbook.
const cards = {'doc-park-left-pill-deal': Doc, 'grid-to-hero': Grid, 'media-pop-in': Media};
const assetProps = (props: Record<string, any>) => ({
  ...props,
  ...(props.docSrc ? {docSrc: staticFile(props.docSrc)} : {}),
  ...(props.srcs ? {srcs: props.srcs.map((src: string) => staticFile(src))} : {}),
});

const Overlay = ({shot}: {shot: typeof book.shots[number]}) => {
  const frame = useCurrentFrame();
  const Card = cards[shot.card as keyof typeof cards] as React.ComponentType<any>;
  const {x, y, scale, height = 540} = shot.placement;
  const opacity = Math.min(1, Math.max(0, (shot.duration - 1 - frame) / 8));
  return <>
    {shot.heading && <div style={{position: 'absolute', left: x + 40 * scale, top: y - 90,
      fontFamily: '"PingFang SC", sans-serif', fontSize: 44, fontWeight: 650,
      color: '#142c48', opacity, letterSpacing: -1, whiteSpace: 'pre-line'}}>{shot.heading}</div>}
    <div style={{position: 'absolute', left: x, top: y, width: 960 * scale,
      height: height * scale, overflow: 'hidden', opacity}}>
      <div style={{position: 'absolute', width: 960, height,
        transform: `scale(${scale})`, transformOrigin: '0 0'}}>
        <Card {...assetProps(shot.props)} />
      </div>
    </div>
  </>;
};

const NativeVideo = () => (
  <AbsoluteFill style={{background: '#000'}}>
    <OffthreadVideo src={staticFile('source.mov')} trimBefore={book.sourceFrame}
      style={{width: '100%', height: '100%', objectFit: 'contain'}} />
    {book.shots.map((shot) => {
      return <Sequence key={shot.id} name={shot.id} from={shot.from} durationInFrames={shot.duration}>
        <Overlay shot={shot} />
      </Sequence>;
    })}
  </AbsoluteFill>
);

const Root = () => <Composition id="TalkCraftNative" component={NativeVideo}
  width={book.width} height={book.height} fps={30} durationInFrames={book.durationInFrames} />;
registerRoot(Root);
