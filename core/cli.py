"""Small, dependency-free project and image-motion preview CLI."""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def external(path):
    result = Path(path).expanduser().resolve()
    if result == REPO or REPO in result.parents:
        raise ValueError('Video projects and outputs must live outside the Agent repository')
    return result


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)
    ], text=True))


def save(project, value):
    write_json(project / 'project.json', value)


def load(project):
    return read_json(project / 'project.json')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


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
    if args.start < 0 or args.duration <= 0 or args.start + args.duration > float(metadata['format']['duration']):
        raise ValueError('Requested excerpt lies outside source duration')
    for name in ('input', 'decisions', 'work', 'preview', 'delivery'):
        (project / name).mkdir(parents=True, exist_ok=True)
    save(project, {
        'schema_version': 1, 'project_id': project.name,
        'primary_workflow': 'talking-head', 'status': 'prepared',
        'source': {'path': str(source), 'bytes': source.stat().st_size,
                   'sha256': digest(source), 'metadata': metadata},
        'clip': {'start': args.start, 'duration': args.duration},
        'format': {'width': 1280, 'height': round(1280 * video['height'] / video['width'] / 2) * 2, 'fps': 30},
        'assets': {}, 'artifacts': [],
        'notes': ['Keep original speech, edits and burned-in subtitles.']
    })
    return {'project': str(project), 'status': 'prepared'}


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
    return {'project': value, 'local_bytes': sum(p.stat().st_size for p in files),
            'files': [str(p.relative_to(project)) for p in files],
            'missing_assets': [k for k, a in value['assets'].items() if not Path(a['path']).exists()]}


def render(args):
    project = external(args.project)
    value = load(project)
    plan = read_json(project / 'input' / 'motion.json')
    duration = value['clip']['duration']
    width, height, fps = (value['format'][k] for k in ('width', 'height', 'fps'))
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    new = sub.add_parser('new')
    new.add_argument('project'); new.add_argument('--source', required=True)
    new.add_argument('--start', type=float, default=0)
    new.add_argument('--duration', type=float, default=10)
    add = sub.add_parser('asset')
    add.add_argument('project'); add.add_argument('id'); add.add_argument('path')
    add.add_argument('--origin', default='user-provided')
    ins = sub.add_parser('inspect'); ins.add_argument('project')
    ren = sub.add_parser('preview'); ren.add_argument('project')
    ren.add_argument('--output', default='preview-v1.mp4')
    args = parser.parse_args()
    try:
        if args.command == 'doctor':
            result = {name: shutil.which(name) for name in ('ffmpeg', 'ffprobe', 'python3')}
            print(json.dumps(result, indent=2)); return 0 if all(result.values()) else 1
        result = {'new': create, 'asset': asset, 'inspect': inspect, 'preview': render}[args.command](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError, StopIteration, subprocess.CalledProcessError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
