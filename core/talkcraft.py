"""External TalkCraft instances. Native TSX execution, no semantic-layer conversion."""
import math
import errno
import os
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

from .project import REPO, digest, external, load, now, probe, project_lock, read_json, save, write_json
from .lifecycle import executable

TEMPLATE = REPO / 'workflows/talking-head/native'
LIBRARY = REPO / 'library/talkcraft-native'
CARDS = {'doc-park-left-pill-deal', 'grid-to-hero', 'media-pop-in'}
SCENES = {'identity-stack', 'metric-comparison', 'metric-process', 'evidence-image', 'verdict-stamp', 'development-time', 'database-relations', 'temperature-alert'}


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
    if book.get('referenceSrc'):
        used.add(book['referenceSrc'])
    for shot in book['shots']:
        if shot['id'] in ids or shot['card'] not in CARDS | SCENES:
            raise ValueError('Shot IDs must be unique and cards must be connected native components')
        ids.add(shot['id'])
        if any(not isinstance(shot[k], int) for k in ('from', 'duration')) or not 0 <= shot['from'] < shot['from'] + shot['duration'] <= book['durationInFrames']:
            raise ValueError('Native shot frames are outside the selection')
        placement = shot['placement']
        x, y, scale = (placement[k] for k in ('x', 'y', 'scale'))
        height = placement.get('height', 540)
        width = placement.get('width', 960)
        if shot['card'] in CARDS and width != 960:
            raise ValueError('Original TalkCraft cards retain their native 960px width')
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y, scale, height, width)):
            raise ValueError('Placement geometry must be finite numbers')
        if scale <= 0 or height <= 0 or width <= 0 or x < 0 or y < 0 or x + width * scale > book['width'] or y + height * scale > book['height']:
            raise ValueError('Native component placement must fit the source canvas')
        for region in book.get('protected_regions', []):
            r0 = region.get('from', 0)
            r1 = r0 + region.get('duration', book['durationInFrames'])
            if shot['from'] >= r1 or shot['from'] + shot['duration'] <= r0:
                continue
            if x < region['x'] + region['width'] and x + width * scale > region['x'] and y < region['y'] + region['height'] and y + height * scale > region['y']:
                raise ValueError(f"Native placement overlaps a source protection region: {shot['id']}")
        props = shot.get('props', {})
        if props.get('hostSrc') or props.get('showHost') is True:
            raise ValueError('Native overlays cannot create a second presenter or crop the original')
        if props.get('background') != 'transparent':
            raise ValueError('Overlay cards must have a transparent root')
        if shot['card'] in SCENES:
            validate_scene(shot, width, height)
        if shot['card'] in ('doc-park-left-pill-deal', 'evidence-image') and not props.get('docSrc'):
            raise ValueError('Native document scene needs genuine registered evidence')
        if shot['card'] in ('grid-to-hero', 'media-pop-in'):
            count = 4 if shot['card'] == 'grid-to-hero' else 3
            if len(props.get('srcs', [])) != count:
                raise ValueError(f"{shot['card']} needs {count} registered real images")
        if shot['card'] == 'media-pop-in' and props.get('showHost') is not False:
            raise ValueError('Disable the native demo presenter with showHost=false')
        if shot['card'] == 'grid-to-hero' and 'focusIndices' in props:
            indices = props['focusIndices']
            if not isinstance(indices, list) or not indices or any(not isinstance(i, int) or not 0 <= i < 4 for i in indices):
                raise ValueError('Sequential grid focus requires nonempty registered item indices 0–3')
            timing = {'lead': .3, 'enterDur': .55, 'stagger': .12, 'holdGrid': 1.2,
                      'reflow': .8, 'holdHero': 2., 'holdBack': .8, 'exit': .4, 'exitStagger': .04}
            config = props.get('config', {})
            timing.update({key: config[key] for key in timing if key in config})
            if any(not isinstance(t, (int, float)) or not math.isfinite(t) or t < 0 for t in timing.values()) or any(timing[k] <= 0 for k in ('enterDur', 'reflow', 'exit')):
                raise ValueError('Sequential focus requires finite nonnegative timing and positive motion durations')
            end = (timing['lead'] + timing['enterDur'] + 3 * timing['stagger'] + timing['holdGrid']
                   + len(indices) * (2 * timing['reflow'] + timing['holdHero'])
                   + timing['holdBack'] + timing['exit'] + 3 * timing['exitStagger'])
            if end > shot['duration'] / book['fps']:
                raise ValueError('Native shot must include every focused item and the complete grid exit')
        used.update(props.get('srcs', []))
        if props.get('docSrc'):
            used.add(props['docSrc'])
    if used - metadata['assets'].keys():
        raise ValueError('All native image assets must be registered with core.cli asset')
    return used


def validate_scene(shot, width, height):
    """Validate the direct scene inputs before bundling, not visual approval."""
    props, card = shot['props'], shot['card']
    if shot.get('heading'):
        raise ValueError('Reference scenes own their typography; do not add an external heading')
    if props.get('appearance') not in ('light', 'dark'):
        raise ValueError('Set appearance from the actual background: light or dark')
    required = {
        'identity-stack': ('chapter', 'name', 'latin', 'facts'),
        'metric-comparison': ('chapter', 'metric', 'rows', 'scaleMax', 'result', 'source'),
        'metric-process': ('chapter', 'metric', 'docSrc', 'evidence', 'steps', 'result', 'clearAt'),
        'evidence-image': ('docSrc', 'imageHeight', 'caption'),
        'verdict-stamp': ('chapter', 'question', 'statement', 'stamp', 'statementAt', 'stampAt'),
        'development-time': ('chapter', 'headline', 'nodes', 'srcs', 'timeline', 'clearAt'),
        'database-relations': ('chapter', 'chapterAt', 'hub', 'left', 'right', 'srcs', 'activateAt', 'result', 'clearAt'),
        'temperature-alert': ('chapter', 'sectionNumber', 'condition', 'reading', 'range', 'risk', 'before', 'after', 'srcs', 'clearAt'),
    }
    if any(key not in props for key in required[card]):
        raise ValueError(f'Missing required direct scene properties: {card}')
    if card != 'evidence-image' and any(not props['chapter'].get(k) for k in ('kicker', 'label')):
        raise ValueError('Reference chapter requires a kicker and label')
    if card == 'metric-comparison':
        maximum = props['scaleMax']
        values = [props['metric']['value'], *(row['value'] for row in props['rows'])]
        if not isinstance(maximum, (int, float)) or not math.isfinite(maximum) or maximum <= 0:
            raise ValueError('Comparison requires one positive finite scaleMax')
        if not props['rows'] or any(not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
            raise ValueError('Metric and comparison values must be finite and nonnegative')
        if any(row['value'] > maximum for row in props['rows']):
            raise ValueError('Comparison rows cannot exceed the common scaleMax')
        if len({row['unit'] for row in props['rows']}) != 1:
            raise ValueError('Comparison rows must share the same unit')
        decimals = props['metric'].get('decimals', 0)
        if not isinstance(decimals, int) or not 0 <= decimals <= 4:
            raise ValueError('Metric decimals must be 0–4')
        times = [props['metric']['at'], *(row['at'] for row in props['rows']), props['result']['at']]
        if props['result']['at'] < max(row['at'] + .6 for row in props['rows']):
            raise ValueError('Comparison result must follow the completed bars')
        extent = 500 + len(props['rows']) * 57 + (85 if props.get('tags') else 0)
    elif card == 'metric-process':
        steps, metric = props['steps'], props['metric']
        value = metric['value']
        if not isinstance(value, int) or value <= 0 or len(steps) != 3:
            raise ValueError('Count/process scene requires a positive count and three steps')
        if not props['docSrc'] or not all(metric.get(k) for k in ('unit', 'context')) or not props['evidence']['caption']:
            raise ValueError('Count/process needs genuine count evidence and its interpretation')
        if not all(step.get('text') and step.get('detail') for step in steps) or not props['result']['text']:
            raise ValueError('Count/process needs labelled steps, detail and an outcome')
        times = [metric['at'], props['evidence']['at'], *(step['at'] for step in steps), props['result']['at'], props['clearAt']]
        if not all(isinstance(t, (int, float)) and math.isfinite(t) for t in times):
            raise ValueError('Count/process timing must be finite seconds')
        if steps[0]['at'] < max(metric['at'] + .75, props['evidence']['at'] + .16):
            raise ValueError('Establish the count and source before the explanatory steps')
        if any(b['at'] < a['at'] + .4 for a, b in zip(steps, steps[1:])):
            raise ValueError('Count/process steps must accumulate in reading order')
        if props['result']['at'] < steps[-1]['at'] + .35 or props['clearAt'] < props['result']['at'] + .3:
            raise ValueError('Hold the completed steps and outcome before clearing')
        if props['clearAt'] + .25 > shot['duration'] / 30 or height < 820 * width / 520:
            raise ValueError('Count/process placement and shot must include the outcome and clear')
        extent = None
    elif card == 'identity-stack':
        if len(props['facts']) > 4:
            raise ValueError('Identity scene supports at most four accumulated facts')
        times = [props.get('nameAt', .65), *(fact['at'] for fact in props['facts'])]
        if props.get('action'):
            times.append(props['action']['at'])
        extent = 395 + len(props['facts']) * 72 + (155 if props.get('action') else 0)
    elif card == 'evidence-image':
        image_height = props['imageHeight']
        if not isinstance(image_height, (int, float)) or not math.isfinite(image_height) or image_height <= 0:
            raise ValueError('Evidence imageHeight must be positive and finite')
        times = [props.get('at', .65)]
        caption_size = props.get('captionSize', 24)
        if not isinstance(caption_size, (int, float)) or not math.isfinite(caption_size) or not 16 <= caption_size <= 72:
            raise ValueError('Evidence captionSize must be a readable finite size from 16 to 72')
        if props.get('chapter') and any(not props['chapter'].get(k) for k in ('kicker', 'label')):
            raise ValueError('Evidence chapter requires both labels')
        extent = image_height + max(65, caption_size * 1.18 + 32) + (108 if props.get('chapter') else 0)
    elif card == 'database-relations':
        left, right = props['left'], props['right']
        if not 1 <= len(left) <= 5 or not 1 <= len(right) <= 5:
            raise ValueError('Database relation scene supports one to five nodes on each side')
        nodes = [*left, *right]
        indices = [props['hub']['imageIndex'], props['result']['imageIndex'],
                   *(node['imageIndex'] for node in nodes), *(node['activeImageIndex'] for node in nodes)]
        if not all(isinstance(i, int) and 0 <= i < len(props['srcs']) for i in indices):
            raise ValueError('Database nodes need registered standby and active icon indices')
        if not all(node.get('text') for node in nodes) or not all(props['hub'].get(k) for k in ('text', 'system', 'hint')):
            raise ValueError('Database scene needs labelled nodes and a hub explanation')
        if not all(props['result'].get(k) for k in ('text', 'detail')):
            raise ValueError('Database scene needs its final conclusion and detail')
        times = [props['chapterAt'], props['hub']['at'], *(node['at'] for node in nodes),
                 props['activateAt'], props['result']['at'], props['clearAt']]
        if not all(isinstance(t, (int, float)) and math.isfinite(t) for t in times):
            raise ValueError('Database scene timing must be finite seconds')
        if props['hub']['at'] < props['chapterAt'] + .4 or min(node['at'] for node in nodes) < props['hub']['at'] + .4:
            raise ValueError('Establish chapter and hub before connected categories')
        if any(b['at'] < a['at'] + .4 for group in (left, right) for a, b in zip(group, group[1:])):
            raise ValueError('Categories on each side must build in reading order')
        if props['activateAt'] < max(node['at'] + .4 for node in nodes):
            raise ValueError('Activate relationships only after all categories have entered')
        if props['result']['at'] < props['activateAt'] + .12 or props['clearAt'] < props['result']['at'] + .4:
            raise ValueError('Show the result after activation, then hold before clearing')
        if props['clearAt'] + .3 > shot['duration'] / 30:
            raise ValueError('Include the complete database scene clear in the shot')
        if height < 850 * width / 1500:
            raise ValueError('Database placement must include categories and final conclusion')
        extent = None
    elif card == 'temperature-alert':
        samples, limits, nodes = props['reading']['samples'], props['range'], props['before']['nodes']
        if len(samples) < 2 or len(nodes) != 3:
            raise ValueError('Temperature scene needs a sampled rise and three manual response nodes')
        values = [sample['value'] for sample in samples]
        range_values = [limits['comfortable']['min'], limits['comfortable']['max'], limits['threshold']['value']]
        if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in [*values, *range_values]):
            raise ValueError('Temperature readings and limits must be finite')
        if not values[0] < limits['threshold']['value'] < values[-1] or any(b < a for a, b in zip(values, values[1:])):
            raise ValueError('Temperature rise must move from below the limit to above it')
        if not range_values[0] < range_values[1] < range_values[2]:
            raise ValueError('Comfortable range must precede the upper limit')
        positions = [limits['comfortable']['position'], limits['threshold']['position']]
        if any(not isinstance(p, (int, float)) or not math.isfinite(p) or not .11 <= p <= .89 for p in positions) or positions[0] >= positions[1]:
            raise ValueError('Schematic range labels must fit and retain comfortable-to-limit order')
        indices = [props['condition']['imageIndex'], props['risk']['imageIndex'], *(node['imageIndex'] for node in nodes)]
        if not all(isinstance(i, int) and 0 <= i < len(props['srcs']) for i in indices):
            raise ValueError('Temperature and response icons must reference registered assets')
        if not props['sectionNumber'] or not props['reading']['unit'] or not props['condition']['text'] or not all(node.get('text') for node in nodes):
            raise ValueError('Temperature scene needs a chapter number, reading unit and labelled nodes')
        if any(not props[group].get(key) for group, keys in [('risk', ('text', 'source')), ('before', ('label', 'scaleText')), ('after', ('kicker', 'label'))] for key in keys):
            raise ValueError('Temperature scene needs risk, manual response and automated response explanations')
        times = [props['condition']['at'], *(sample['at'] for sample in samples), props['risk']['at'],
                 props['before']['at'], *(node['at'] for node in nodes), props['after']['at'], props['clearAt']]
        if not all(isinstance(t, (int, float)) and math.isfinite(t) for t in times):
            raise ValueError('Temperature scene timing must be finite seconds')
        if samples[0]['at'] < props['condition']['at'] or any(b['at'] <= a['at'] for a, b in zip(samples, samples[1:])):
            raise ValueError('Establish the range before its strictly ordered reading samples')
        if props['risk']['at'] < samples[-1]['at'] or props['before']['at'] < props['risk']['at'] + .4:
            raise ValueError('Show the completed temperature rise before the risk and response explanation')
        if nodes[0]['at'] < props['before']['at'] or any(b['at'] < a['at'] + .2 for a, b in zip(nodes, nodes[1:])):
            raise ValueError('Manual response nodes must follow their heading in reading order')
        if props['after']['at'] < nodes[-1]['at'] + .4 or props['clearAt'] < props['after']['at'] + .16:
            raise ValueError('Establish the manual response before automation, then complete its entry before clearing')
        if props['clearAt'] + .45 > shot['duration'] / 30 or height < 730 * width / 900:
            raise ValueError('Temperature placement and shot must include the response and complete clear')
        extent = None
    elif card == 'development-time':
        nodes, timeline = props['nodes'], props['timeline']
        events = timeline['events']
        if len(nodes) != 3 or len(events) != 2:
            raise ValueError('Development scene needs three process nodes and two dated events')
        if not all(node.get('text') and node.get('detail') and isinstance(node.get('imageIndex'), int)
                   and 0 <= node['imageIndex'] < len(props['srcs']) for node in nodes):
            raise ValueError('Each process node needs text, detail and a registered icon index')
        dates = [date.fromisoformat(event['date']) for event in events]
        if dates[1] <= dates[0] or not all(event.get('label') and event.get('caption') for event in events):
            raise ValueError('Dated events must be labelled and in chronological order')
        times = [props['headline']['at'], *(node['at'] for node in nodes), timeline['at'],
                 *(event['at'] for event in events), timeline['resultAt'], props['clearAt']]
        if not all(isinstance(t, (int, float)) and math.isfinite(t) for t in times):
            raise ValueError('Development scene timing must be finite seconds')
        if any(later < earlier + .4 for earlier, later in zip(times, times[1:])):
            raise ValueError('Build headline, process, dates, result and clear in that order')
        if not all(props['headline'].get(k) for k in ('value', 'unit', 'caption')) or not timeline.get('caption'):
            raise ValueError('Development scene needs headline and interval captions')
        if height < 780 * width / 1300:
            raise ValueError('Development placement must include both date captions')
        extent = None
    else:
        times = [.45, props['statementAt'], props['stampAt']]
        if props['stampAt'] < props['statementAt'] + .4:
            raise ValueError('Verdict stamp must follow statement entry')
        extent = 560
    if any(not isinstance(t, (int, float)) or not math.isfinite(t) or t < 0 or t >= shot['duration'] / 30 for t in times):
        raise ValueError('Scene timing must be finite seconds inside the shot')
    if extent is not None and height < (extent if card == 'evidence-image' else extent * width / 800):
        raise ValueError('Scene placement must include its text and caption; increase height')


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
        composition = getattr(args, 'composition', 'TalkCraftNative')
        if composition not in ('TalkCraftNative', 'OverlayOnly', 'ReferenceFrame', 'ReferenceComparison'):
            raise ValueError('Unknown native composition')
        if args.command == 'render' and composition != 'TalkCraftNative':
            raise ValueError('Calibration compositions are previews, not production renders')
        if composition == 'ReferenceFrame' and not book.get('referenceSrc'):
            raise ValueError('ReferenceFrame requires a registered referenceSrc')
        if not book.get('construction'):
            raise ValueError('A native shotbook needs its reference analysis and construction sheet')
        construction = (project / book['construction']).resolve(strict=True)
        if project / 'decisions' not in construction.parents or not construction.is_file():
            raise ValueError('Keep native construction records in this project decisions/')
        studio = getattr(args, 'studio', False)
        version = args.version or ('native-studio-v1' if studio else 'native-render-v1' if args.command == 'render' else 'native-preview-v1')
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}', version):
            raise ValueError('Use a simple native version name')
        at = getattr(args, 'at', None)
        if studio and at is not None:
            raise ValueError('--studio prepares an interactive instance; do not combine it with --at')
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
        templates = [TEMPLATE / 'Root.tsx', TEMPLATE / 'Scenes.tsx', TEMPLATE / 'scene-provenance.json',
                     TEMPLATE / 'render.cjs', TEMPLATE / 'runtime/package.json',
                     LIBRARY / 'provenance.json', LIBRARY / 'LICENSE.upstream']
        # Studio reads this manifest for dependency discovery, even though
        # actual modules live in the linked external shared runtime.
        shutil.copy2(TEMPLATE / 'runtime/package.json', instance / 'package.json')
        shutil.copy2(TEMPLATE / 'Root.tsx', instance / 'src/Root.tsx')
        shutil.copy2(TEMPLATE / 'Scenes.tsx', instance / 'src/Scenes.tsx')
        shutil.copy2(TEMPLATE / 'scene-provenance.json', instance / 'scene-provenance.json')
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
        if resolved.get('referenceSrc'):
            key = resolved['referenceSrc']
            resolved['referenceSrc'] = 'assets/' + key + Path(metadata['assets'][key]['path']).suffix
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
        snapshot = {'engine': 'talkcraft-native', 'composition': composition, 'plan_hash': digest(plan), 'clip': metadata['clip'],
                    'format': metadata['format'], 'source_hash': metadata['source']['sha256'],
                    'asset_hashes': {key: metadata['assets'][key]['sha256'] for key in used},
                    'render_range': {'start': book['sourceFrame'] / 30 - metadata['clip']['start'],
                                     'end': (book['sourceFrame'] + book['durationInFrames']) / 30 - metadata['clip']['start']},
                    'template_hashes': {str(p.relative_to(REPO)): digest(p) for p in templates},
                    'construction_hash': digest(construction), 'construction_snapshot': str(instance / 'construction.md'),
                    'native_runtime': runtime, 'media_links': media_links, 'created_at': now()}
        snapshot_path = instance / 'snapshot.json'
        write_json(snapshot_path, snapshot)
        if studio:
            # Build the existing external instance without rendering a movie,
            # creating a trial artifact, or changing any prior delivery status.
            return {'instance': str(instance), 'engine': 'talkcraft-native',
                    'snapshot': str(snapshot_path), 'kind': 'studio-instance',
                    'studio_entry': str(instance / 'src/Root.tsx'), 'visual_review': 'not-reviewed'}
        command = [node, str(instance / 'render.cjs'), browser, str(output)]
        if at is not None:
            command.append(str(round(at * 30)))
        command.append('--composition=' + composition)
        write_json(instance / 'command.json', command)
        subprocess.run(command, cwd=instance, check=True)
        artifact = {'engine': 'talkcraft-native', 'composition': composition, 'path': str(output), 'kind': kind,
                    'sha256': digest(output), 'bytes': output.stat().st_size, 'metadata': probe(output),
                    'plan_hash': snapshot['plan_hash'], 'snapshot': str(snapshot_path),
                    'review': 'awaiting-user', 'created_at': now()}
        metadata['artifacts'].append(artifact)
        metadata['native_plan'] = {'path': str(plan), 'hash': snapshot['plan_hash'], 'instance': str(instance)}
        # An alternate trial does not revoke the previously approved delivery.
        metadata['native_trial'] = {'status': 'awaiting-user', 'artifact': str(output)}
        save(project, metadata)
    return {'artifact': str(output), 'instance': str(instance), 'engine': 'talkcraft-native', 'visual_review': 'awaiting-user'}
