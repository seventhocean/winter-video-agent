"""External talking-head project lifecycle; creative decisions remain with Codex."""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from .project import digest, external, load, probe, read_json, save, write_json, project_lock
from . import lifecycle, planning, talkcraft
from .reference_catalog import catalog, search


def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Motion values must be finite')
    return value


def track(keys, field):
    """Piecewise cosine ease, clamped at both ends; times are clip-local seconds."""
    times = [number(k['t']) for k in keys]
    values = [number(k[field]) for k in keys]
    if not times or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Keyframes must have strictly increasing times')
    expression = str(values[-1])
    for i in range(len(times) - 2, -1, -1):
        a, b = times[i:i+2]
        va, vb = values[i:i+2]
        segment = f'{va}+({vb-va})*(1-cos(PI*(t-{a})/{b-a}))/2'
        expression = f'if(lt(t,{b}),{segment},{expression})'
    return f'if(lt(t,{times[0]}),{values[0]},{expression})'


def create(args):
    project = external(args.project)
    if (project / 'project.json').exists():
        raise ValueError('Project already exists')
    source = Path(args.source).expanduser().resolve(strict=True)
    metadata = probe(source)
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    if not all(math.isfinite(v) for v in (args.start, args.duration, args.fps)) or args.start < 0 or args.duration <= 0 or args.start + args.duration > float(metadata['format']['duration']) + .001:
        raise ValueError('Requested excerpt lies outside source duration')
    if args.width < 320 or args.width > 4096 or args.width % 2 or not 0 < args.fps <= 60:
        raise ValueError('Width must be even, 320–4096; fps must be 0–60')
    height = round(args.width * video['height'] / video['width'] / 2) * 2
    if height < 320 or height > 4096:
        raise ValueError('Source aspect ratio produces an unsupported output height')
    for name in ('input', 'decisions', 'work', 'preview', 'delivery'):
        (project / name).mkdir(parents=True, exist_ok=True)
    save(project, {
        'schema_version': 1, 'project_id': project.name,
        'primary_workflow': 'talking-head', 'status': 'draft',
        'source': {'path': str(source), 'bytes': source.stat().st_size,
                   'sha256': digest(source), 'metadata': metadata},
        'clip': {'start': args.start, 'duration': args.duration},
        'format': {'width': args.width, 'height': height, 'fps': args.fps},
        'assets': {}, 'artifacts': [],
        'notes': ['Keep original speech, edits and burned-in subtitles.']
    })
    return {'project': str(project), 'status': 'draft'}


def asset(args):
    project = external(args.project)
    value = load(project)
    path = Path(args.path).expanduser().resolve(strict=True)
    value['assets'][args.id] = {'path': str(path), 'sha256': digest(path),
                               'bytes': path.stat().st_size, 'origin': args.origin}
    save(project, value)
    return value['assets'][args.id]


def inspect(args):
    project = external(args.project)
    value = load(project)
    files = [p for p in project.rglob('*') if p.is_file() and not p.is_symlink()]
    inventory = {name: {'files': sum(name in p.relative_to(project).parts[:1] for p in files),
                        'bytes': sum(p.stat().st_size for p in files if name in p.relative_to(project).parts[:1])}
                 for name in ('input', 'decisions', 'work', 'preview', 'render', 'delivery')}
    return {'project': value, 'local_bytes': sum(p.stat().st_size for p in files), 'storage': inventory,
            'files': [str(p.relative_to(project)) for p in files],
            'missing_assets': [k for k, a in value['assets'].items() if not Path(a['path']).exists()]}


def legacy_preview(args):
    project = external(args.project)
    value = load(project)
    plan = read_json(project / 'input' / 'motion.json')
    duration = value['clip']['duration']
    width, height, fps = (value['format'][k] for k in ('width', 'height', 'fps'))
    args.output = args.output or 'preview-v1.mp4'
    output = project / 'preview' / args.output
    if Path(args.output).name != args.output or not args.output.endswith('.mp4'):
        raise ValueError('Output must be a simple .mp4 filename')
    if output.exists():
        raise ValueError('Output already exists; choose a new version filename')
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-n',
               '-ss', str(value['clip']['start']), '-i', value['source']['path']]
    filters = [f'[0:v]scale={width}:{height},setsar=1,fps={fps},setpts=PTS-STARTPTS[base0]']
    layers = plan['layers']
    for i, layer in enumerate(layers, 1):
        path = Path(value['assets'][layer['asset']]['path'])
        if not path.is_file():
            raise ValueError(f'Missing asset: {path}')
        if not 0 <= layer['start'] < layer['end'] <= duration:
            raise ValueError('Layer timing is outside clip')
        command += ['-loop', '1', '-framerate', str(fps), '-i', str(path)]
        keys = layer['keys']
        if any(number(k['width']) < 2 for k in keys):
            raise ValueError('Image width must be >= 2')
        w, x, y = (track(keys, field) for field in ('width', 'x', 'y'))
        filters.append(f"[{i}:v]format=rgba,scale=w='{w}':h=-1:eval=frame[img{i}]")
        filters.append(f"[base{i-1}][img{i}]overlay=x='{x}-overlay_w/2':y='{y}-overlay_h/2':eval=frame:enable='between(t,{layer['start']},{layer['end']})'[base{i}]")
    graph = project / 'work' / (output.stem + '.ffgraph')
    graph.write_text(';\n'.join(filters) + '\n', encoding='utf-8')
    command += ['-filter_complex_threads', '1', '-filter_complex_script', str(graph),
                '-map', f'[base{len(layers)}]', '-map', '0:a:0?', '-t', str(duration),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(output)]
    write_json(project / 'work' / (output.stem + '.command.json'), command)
    subprocess.run(command, check=True)
    metadata = probe(output)
    value['status'] = 'previewed'
    value['artifacts'].append({'path': str(output), 'kind': 'preview', 'sha256': digest(output),
                               'bytes': output.stat().st_size, 'metadata': metadata,
                               'plan': plan, 'review': 'awaiting-user'})
    save(project, value)
    return {'preview': str(output), 'review': 'awaiting-user'}


def preview(args):
    if args.engine == 'talkcraft-native':
        return talkcraft.render(args)
    if (external(args.project) / 'input/semantic-plan.json').is_file():
        if args.output and (Path(args.output).name != args.output or not args.output.endswith('.mp4')):
            raise ValueError('Output must be a simple .mp4 filename; use --version for semantic previews')
        return lifecycle.render(args)
    if args.shot or args.at is not None or args.version:
        raise ValueError('Register a semantic plan before using semantic preview options')
    with project_lock(external(args.project)):
        return legacy_preview(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    doctor = sub.add_parser('doctor')
    doctor.add_argument('project', nargs='?', help='Also verify this project runtime')
    new = sub.add_parser('new')
    new.add_argument('project'); new.add_argument('--source', required=True)
    new.add_argument('--start', type=float, default=0)
    new.add_argument('--duration', type=float, default=10)
    new.add_argument('--width', type=int, default=1280)
    new.add_argument('--fps', type=float, default=30)
    add = sub.add_parser('asset')
    add.add_argument('project'); add.add_argument('id'); add.add_argument('path')
    add.add_argument('--origin', default='user-provided')
    ins = sub.add_parser('inspect'); ins.add_argument('project')
    cards = sub.add_parser('cards', help='Search pinned local cards/cases without treating them as runnable')
    cards.add_argument('--query', default=''); cards.add_argument('--semantic'); cards.add_argument('--limit', type=int, default=8)
    content = sub.add_parser('brief', help='Create an annotation skeleton, or register a completed content brief')
    content.add_argument('project'); content.add_argument('file', nargs='?')
    picks = sub.add_parser('suggest', help='Rank cards by annotated meaning and available materials')
    picks.add_argument('project'); picks.add_argument('--top', type=int, default=5)
    sheet = sub.add_parser('storyboard', help='Validate and link reference analysis, construction sheet and executable motions')
    sheet.add_argument('project'); sheet.add_argument('file', nargs='?'); sheet.add_argument('--construction')
    sheet.add_argument('--init', action='store_true', help='Create an editable construction skeleton from the brief')
    sheet.add_argument('--check', action='store_true')
    prep = sub.add_parser('prepare'); prep.add_argument('project')
    prep.add_argument('--engine', choices=['semantic', 'talkcraft-native'], default='semantic')
    prep.add_argument('--runtime-root', help='External pinned TalkCraft npm runtime directory')
    prep.add_argument('--node'); prep.add_argument('--playwright-package'); prep.add_argument('--browser')
    prep.add_argument('--from-project', help='Reuse runtime settings from another external project')
    planned = sub.add_parser('plan'); planned.add_argument('project'); planned.add_argument('file', nargs='?')
    planned.add_argument('--check', action='store_true'); planned.add_argument('--compile', action='store_true')
    ren = sub.add_parser('preview'); ren.add_argument('project')
    ren.add_argument('--engine', choices=['semantic', 'talkcraft-native'], default='semantic')
    ren.add_argument('--native-plan', help='External native TalkCraft shotbook JSON')
    ren.add_argument('--studio', action='store_true', help='Prepare a native interactive instance without rendering')
    ren.add_argument('--composition', choices=['TalkCraftNative', 'OverlayOnly', 'ReferenceFrame', 'ReferenceComparison'],
                     default='TalkCraftNative', help='Native production or reference calibration composition')
    ren.add_argument('--output', help='Legacy filename or semantic version filename')
    ren.add_argument('--version'); ren.add_argument('--shot'); ren.add_argument('--at', type=float)
    full = sub.add_parser('render'); full.add_argument('project'); full.add_argument('--version')
    full.add_argument('--engine', choices=['semantic', 'talkcraft-native'], default='semantic')
    full.add_argument('--native-plan', help='External native TalkCraft shotbook JSON')
    checked = sub.add_parser('qa'); checked.add_argument('project'); checked.add_argument('artifact')
    reviewed = sub.add_parser('review'); reviewed.add_argument('project'); reviewed.add_argument('artifact')
    reviewed.add_argument('--verdict', required=True, choices=['approved', 'changes-requested'])
    reviewed.add_argument('--feedback', required=True)
    delivery = sub.add_parser('deliver'); delivery.add_argument('project'); delivery.add_argument('artifact')
    delivery.add_argument('--destination', help='External .mp4 destination; default is project delivery/')
    cleaned = sub.add_parser('clean'); cleaned.add_argument('project'); cleaned.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        if getattr(args, 'studio', False) and args.engine != 'talkcraft-native':
            raise ValueError('--studio uses the existing native Remotion execution path')
        if getattr(args, 'composition', 'TalkCraftNative') != 'TalkCraftNative' and args.engine != 'talkcraft-native':
            raise ValueError('--composition uses the existing native Remotion execution path')
        if args.command == 'cards':
            print(json.dumps(search(catalog(), args.query, args.semantic, args.limit), ensure_ascii=False, indent=2)); return 0
        if args.command == 'suggest' and not 1 <= args.top <= 10:
            raise ValueError('top must be 1–10')
        if args.command == 'doctor':
            result = {name: shutil.which(name) for name in ('ffmpeg', 'ffprobe', 'python3')}
            if args.project:
                result['runtime'] = lifecycle.validate_runtime(lifecycle.runtime_for(external(args.project)))
            print(json.dumps(result, indent=2)); return 0 if all(result.values()) else 1
        actions = {'new': create, 'asset': asset, 'inspect': inspect, 'preview': preview,
                   'prepare': talkcraft.prepare if args.command == 'prepare' and args.engine == 'talkcraft-native' else lifecycle.prepare,
                   'plan': lifecycle.plan, 'render': talkcraft.render if args.command == 'render' and args.engine == 'talkcraft-native' else lifecycle.render,
                   'qa': lifecycle.qa, 'review': lifecycle.review, 'deliver': lifecycle.deliver, 'clean': lifecycle.clean,
                   'brief': planning.brief, 'suggest': planning.candidates, 'storyboard': planning.storyboard}
        if args.command == 'asset':
            with project_lock(external(args.project)):
                result = asset(args)
        else:
            result = actions[args.command](args)
        metadata = load(external(args.project))
        result = {'project_path': str(external(args.project)), 'workflow': metadata['primary_workflow'],
                  'status': metadata['status'], **result}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, StopIteration, subprocess.CalledProcessError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
