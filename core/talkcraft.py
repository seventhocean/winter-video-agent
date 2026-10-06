"""External TalkCraft instances. Native TSX execution, no semantic-layer conversion."""
import math
import errno
import os
import re
import shutil
import subprocess
from pathlib import Path

from .project import REPO, digest, external, load, now, probe, project_lock, read_json, save, write_json
from .lifecycle import executable

TEMPLATE = REPO / 'workflows/talking-head/native'
LIBRARY = REPO / 'library/talkcraft-native'
CARDS = {'doc-park-left-pill-deal', 'grid-to-hero', 'media-pop-in'}


def link_media(source, destination):
    # Remotion's static server rejects leaf symlinks. Hard links share bytes and
    # are read-only inputs to this renderer. Across volumes, make an explicit copy.
    try:
        os.link(source, destination)
        return 'hard-link'
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        shutil.copyfile(source, destination)
        return 'cross-volume-copy'


def prepare(args):
    project = external(args.project)
    if not args.runtime_root:
        raise ValueError('Pass an external pinned runtime with --runtime-root')
    root = external(args.runtime_root).resolve(strict=True)
    node = executable(args.node or shutil.which('node'), 'Node')
    browser = executable(args.browser, 'Browser')
    expected = read_json(TEMPLATE / 'runtime/package.json')['dependencies']
    versions = {}
    for package in ('remotion', '@remotion/renderer', '@remotion/bundler', 'react', 'react-dom'):
        actual = read_json(root / 'node_modules' / package / 'package.json')['version']
        if actual != expected[package]:
            raise ValueError(f'{package}: expected pinned {expected[package]}, found {actual}')
        versions[package] = actual
    # Verify module resolution without downloading or installing anything.
    subprocess.run([node, '-e', "require('@remotion/bundler');require('@remotion/renderer')"],
                   cwd=root, check=True, capture_output=True, text=True)
    with project_lock(project):
        value = load(project)
        if value['primary_workflow'] != 'talking-head':
            raise ValueError('TalkCraft is a talking-head workflow')
        value['talkcraft_runtime'] = {'root': str(root), 'node': node, 'browser': browser,
                                     'versions': versions, 'checked_at': now()}
        save(project, value)
    return {'talkcraft_runtime': value['talkcraft_runtime']}


def validate(book, metadata):
    if book.get('engine') != 'talkcraft-native' or book.get('schema_version') != 1:
        raise ValueError('Expected a TalkCraft native shotbook v1')
    if book.get('fps') != 30 or metadata['format']['fps'] != 30:
        raise ValueError('These native cards currently use 30 fps')
    if (book['width'], book['height']) != (metadata['format']['width'], metadata['format']['height']):
        raise ValueError('Native canvas must match the external project format')
    source = next(s for s in metadata['source']['metadata']['streams'] if s['codec_type'] == 'video')
    if abs(book['width'] / book['height'] - source['width'] / source['height']) > .001:
        raise ValueError('Native preview must preserve the original aspect ratio')
    for key in ('sourceFrame', 'durationInFrames'):
        if not isinstance(book[key], int) or book[key] < (1 if key == 'durationInFrames' else 0):
            raise ValueError(f'{key} must be a valid nonnegative frame count')
    start = book['sourceFrame'] / 30
    end = start + book['durationInFrames'] / 30
    if start < metadata['clip']['start'] or end > metadata['clip']['start'] + metadata['clip']['duration'] + .001:
        raise ValueError('Native selection extends outside the registered clip')
    if not isinstance(book.get('shots'), list) or not book['shots']:
        raise ValueError('Native shotbook requires at least one shot')
    ids, used = set(), set()
    for shot in book['shots']:
        if shot['id'] in ids or shot['card'] not in CARDS:
            raise ValueError('Shot IDs must be unique and cards must be connected native components')
        ids.add(shot['id'])
        if any(not isinstance(shot[k], int) for k in ('from', 'duration')) or not 0 <= shot['from'] < shot['from'] + shot['duration'] <= book['durationInFrames']:
            raise ValueError('Native shot frames are outside the selection')
        placement = shot['placement']
        x, y, scale = (placement[k] for k in ('x', 'y', 'scale'))
        height = placement.get('height', 540)
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y, scale, height)):
            raise ValueError('Placement geometry must be finite numbers')
        if scale <= 0 or height <= 0 or x < 0 or y < 0 or x + 960 * scale > book['width'] or y + height * scale > book['height']:
            raise ValueError('Native component placement must fit the source canvas')
        for region in book.get('protected_regions', []):
            r0 = region.get('from', 0)
            r1 = r0 + region.get('duration', book['durationInFrames'])
            if shot['from'] >= r1 or shot['from'] + shot['duration'] <= r0:
                continue
            if x < region['x'] + region['width'] and x + 960 * scale > region['x'] and y < region['y'] + region['height'] and y + height * scale > region['y']:
                raise ValueError(f"Native placement overlaps a source protection region: {shot['id']}")
        props = shot.get('props', {})
        if props.get('hostSrc') or props.get('showHost') is True:
            raise ValueError('Native overlays cannot create a second presenter or crop the original')
        if props.get('background') != 'transparent':
            raise ValueError('Overlay cards must have a transparent root')
        if shot['card'] == 'doc-park-left-pill-deal' and not props.get('docSrc'):
            raise ValueError('Native document scene needs genuine registered evidence')
        if shot['card'] in ('grid-to-hero', 'media-pop-in'):
            count = 4 if shot['card'] == 'grid-to-hero' else 3
            if len(props.get('srcs', [])) != count:
                raise ValueError(f"{shot['card']} needs {count} registered real images")
        if shot['card'] == 'media-pop-in' and props.get('showHost') is not False:
            raise ValueError('Disable the native demo presenter with showHost=false')
        used.update(props.get('srcs', []))
        if props.get('docSrc'):
            used.add(props['docSrc'])
    if used - metadata['assets'].keys():
        raise ValueError('All native image assets must be registered with core.cli asset')
    return used


def render(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        runtime = metadata.get('talkcraft_runtime') or {}
        if not runtime:
            raise ValueError('Run prepare --engine talkcraft-native --runtime-root ... first')
        node = executable(runtime['node'], 'Node')
        browser = executable(runtime['browser'], 'Browser')
        modules = external(runtime['root']) / 'node_modules'
        expected = read_json(TEMPLATE / 'runtime/package.json')['dependencies']
        for package in ('remotion', '@remotion/renderer', '@remotion/bundler', 'react', 'react-dom'):
            if read_json(modules / package / 'package.json')['version'] != expected[package]:
                raise ValueError('Pinned native runtime has changed; run prepare again')
        if getattr(args, 'shot', None):
            raise ValueError('Use a native shotbook selection rather than semantic --shot')
        if getattr(args, 'output', None):
            raise ValueError('Use --version for native artifact filenames')
        plan = Path(args.native_plan).expanduser().resolve() if args.native_plan else project / 'input/talkcraft-shotbook.json'
        book = read_json(plan)
        used = validate(book, metadata)
        if not book.get('construction'):
            raise ValueError('A native shotbook needs its reference analysis and construction sheet')
        construction = (project / book['construction']).resolve(strict=True)
        if project / 'decisions' not in construction.parents or not construction.is_file():
            raise ValueError('Keep native construction records in this project decisions/')
        version = args.version or ('native-render-v1' if args.command == 'render' else 'native-preview-v1')
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}', version):
            raise ValueError('Use a simple native version name')
        at = getattr(args, 'at', None)
        if at is not None and (not math.isfinite(at) or not 0 <= at * 30 < book['durationInFrames']):
            raise ValueError('--at is selection-local seconds inside the native shotbook')
        kind = 'still' if at is not None else ('render' if args.command == 'render' else 'preview')
        output = project / ('render' if kind == 'render' else 'preview') / (version + ('.png' if kind == 'still' else '.mp4'))
        instance = project / 'work/talkcraft-native' / version
        if output.exists() or instance.exists():
            raise ValueError('Native version already exists; choose a new version, never overwrite inputs')
        # Verify actual source/assets before serving them via links in public/.
        if digest(metadata['source']['path']) != metadata['source']['sha256']:
            raise ValueError('Original talking-head file changed since registration')
        for key in used:
            if digest(metadata['assets'][key]['path']) != metadata['assets'][key]['sha256']:
                raise ValueError(f'Native asset changed since registration: {key}')
        (instance / 'src/cards').mkdir(parents=True)
        (instance / 'public').mkdir()
        output.parent.mkdir(exist_ok=True)
        (instance / 'node_modules').symlink_to(modules, target_is_directory=True)
        templates = [TEMPLATE / 'Root.tsx', TEMPLATE / 'render.cjs', LIBRARY / 'provenance.json', LIBRARY / 'LICENSE.upstream']
        shutil.copy2(TEMPLATE / 'Root.tsx', instance / 'src/Root.tsx')
        shutil.copy2(TEMPLATE / 'render.cjs', instance / 'render.cjs')
        shutil.copy2(LIBRARY / 'provenance.json', instance / 'provenance.json')
        shutil.copy2(LIBRARY / 'LICENSE.upstream', instance / 'LICENSE.upstream')
        shutil.copy2(construction, instance / 'construction.md')
        for card in CARDS:
            source = LIBRARY / 'cards' / (card + '.tsx')
            shutil.copy2(source, instance / 'src/cards' / source.name)
            templates.append(source)
        write_json(instance / 'shotbook-original.json', book)
        # Per-card public props refer to asset IDs. Persist the resolved native props separately.
        resolved = read_json(plan)
        for shot in resolved['shots']:
            props = shot['props']
            if props.get('docSrc'):
                props['docSrc'] = 'assets/' + props['docSrc'] + Path(metadata['assets'][props['docSrc']]['path']).suffix
            if props.get('srcs'):
                props['srcs'] = ['assets/' + key + Path(metadata['assets'][key]['path']).suffix for key in props['srcs']]
        write_json(instance / 'src/shotbook.json', resolved)
        media_links = {'source': link_media(Path(metadata['source']['path']).resolve(), instance / 'public/source.mov')}
        (instance / 'public/assets').mkdir()
        for key in used:
            source = Path(metadata['assets'][key]['path']).resolve()
            if not re.fullmatch(r'[a-zA-Z0-9_-]+', key):
                raise ValueError('Native asset IDs must be safe filenames')
            media_links[key] = link_media(source, instance / 'public/assets' / (key + source.suffix))
        snapshot = {'engine': 'talkcraft-native', 'plan_hash': digest(plan), 'clip': metadata['clip'],
                    'format': metadata['format'], 'source_hash': metadata['source']['sha256'],
                    'asset_hashes': {key: metadata['assets'][key]['sha256'] for key in used},
                    'render_range': {'start': book['sourceFrame'] / 30 - metadata['clip']['start'],
                                     'end': (book['sourceFrame'] + book['durationInFrames']) / 30 - metadata['clip']['start']},
                    'template_hashes': {str(p.relative_to(REPO)): digest(p) for p in templates},
                    'construction_hash': digest(construction), 'construction_snapshot': str(instance / 'construction.md'),
                    'native_runtime': runtime, 'media_links': media_links, 'created_at': now()}
        snapshot_path = instance / 'snapshot.json'
        write_json(snapshot_path, snapshot)
        command = [node, str(instance / 'render.cjs'), browser, str(output)]
        if at is not None:
            command.append(str(round(at * 30)))
        write_json(instance / 'command.json', command)
        subprocess.run(command, cwd=instance, check=True)
        artifact = {'engine': 'talkcraft-native', 'path': str(output), 'kind': kind,
                    'sha256': digest(output), 'bytes': output.stat().st_size, 'metadata': probe(output),
                    'plan_hash': snapshot['plan_hash'], 'snapshot': str(snapshot_path),
                    'review': 'awaiting-user', 'created_at': now()}
        metadata['artifacts'].append(artifact)
        metadata['native_plan'] = {'path': str(plan), 'hash': snapshot['plan_hash'], 'instance': str(instance)}
        # An alternate trial does not revoke the previously approved delivery.
        metadata['native_trial'] = {'status': 'awaiting-user', 'artifact': str(output)}
        save(project, metadata)
    return {'artifact': str(output), 'instance': str(instance), 'engine': 'talkcraft-native', 'visual_review': 'awaiting-user'}
