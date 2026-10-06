// Resolve packages from this external instance's linked, pinned runtime.
const {bundle} = require('@remotion/bundler');
const {selectComposition, renderMedia, renderStill} = require('@remotion/renderer');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const [browser, output, at] = process.argv.slice(2);
  const serveUrl = await bundle({entryPoint: path.resolve('src/Root.tsx'),
    outDir: path.resolve('bundle'), publicDir: path.resolve('public'),
    symlinkPublicDir: true,
    onProgress: () => {}});
  const composition = await selectComposition({serveUrl, id: 'TalkCraftNative', browserExecutable: browser});
  if (at !== undefined) {
    await renderStill({serveUrl, composition, output, frame: Number(at), browserExecutable: browser});
  } else {
    let last = -1;
    await renderMedia({serveUrl, composition, outputLocation: output, codec: 'h264', crf: 18,
      audioCodec: 'aac', audioBitrate: '192k', pixelFormat: 'yuv420p',
      browserExecutable: browser, concurrency: 3,
      onProgress: ({progress}) => {
        const percent = Math.floor(progress * 10) * 10;
        if (percent !== last) {last = percent; process.stderr.write(`Native render ${percent}%\n`);}
      }});
  }
  fs.writeFileSync(path.resolve('render-result.json'), JSON.stringify({output, composition}));
})().catch(error => {console.error(error); process.exit(1);});
