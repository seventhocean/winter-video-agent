"""Talking-head execution, delivery and narrowly scoped cache cleanup."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .project import REPO, digest, external, load, now, probe, project_lock, read_json, save


def executable(value, label):
    resolved = shutil.which(str(value)) if value else None
    if not resolved or not os.access(resolved, os.X_OK):
        raise ValueError(f'{label} executable is unavailable: {value}')
    return str(Path(resolved).resolve())


def validate_runtime(runtime):
    if runtime.get('kind') != 'playwright-chromium':
        raise ValueError('Run prepare with --playwright-package and --browser first')
    node = executable(runtime.get('node'), 'Node')
    if not runtime.get('playwright_package') or not runtime.get('browser'):
        raise ValueError('Run prepare with --playwright-package and --browser, or --from-project')
    package = Path(runtime['playwright_package']).expanduser().resolve(strict=True)
    if REPO in package.parents or read_json(package).get('name') != 'playwright':
        raise ValueError('Use an external Playwright package.json, outside the Agent repository')
    browser = executable(runtime.get('browser'), 'Browser')
    version = subprocess.check_output([node, '--version'], text=True).strip()
    # Resolve the actual package, without installing or making network requests.
    code = "const {createRequire}=require('node:module');const r=createRequire(process.argv[1]);if(!r('playwright').chromium)process.exit(1)"
    subprocess.run([node, '-e', code, str(package)], check=True, capture_output=True, text=True)
    return {'kind': 'playwright-chromium', 'node': node, 'playwright_package': str(package),
            'browser': browser, 'node_version': version,
            'playwright_version': read_json(package)['version']}


def runtime_for(project):
    runtime = load(project).get('runtime') or {}
    if not all(runtime.get(k) for k in ('node', 'playwright_package', 'browser')):
        raise ValueError('Runtime is not configured; run prepare PROJECT with external runtime paths')
    return runtime


def prepare(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        runtime = metadata.get('runtime') or {}
        if args.from_project:
            runtime = load(external(args.from_project)).get('runtime') or {}
        runtime = dict(runtime)
        for field, value in (('node', args.node), ('playwright_package', args.playwright_package), ('browser', args.browser)):
            if value:
                runtime[field] = value
        runtime.setdefault('node', shutil.which('node'))
        runtime['kind'] = 'playwright-chromium'
        runtime = validate_runtime(runtime)
        if not Path(metadata['source']['path']).is_file():
            raise ValueError('Source media is missing')
        missing = [key for key, asset in metadata['assets'].items() if not Path(asset['path']).is_file()]
        if missing:
            raise ValueError('Missing registered assets: ' + ', '.join(missing))
        metadata['runtime'] = {**runtime, 'checked_at': now()}
        if metadata['status'] in ('draft', 'inspected'):
            metadata['status'] = 'prepared'
        save(project, metadata)
    return {'project': str(project), 'runtime': runtime, 'status': metadata['status']}


def run_node(project, script, arguments):
    node = executable(runtime_for(project)['node'], 'Node')
    command = [node, str(REPO / 'scripts' / script), *map(str, arguments)]
    result = None
    # Progress goes to stderr; stdout remains one machine-readable result.
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as process:
        for line in process.stdout:
            try:
                result = json.loads(line)
            except json.JSONDecodeError:
                print(line.rstrip(), file=sys.stderr, flush=True)
        code = process.wait()
    if code:
        raise ValueError(f'{script} failed (exit {code}); see the diagnostic above')
    if not isinstance(result, dict):
        raise ValueError(f'{script} returned no result')
    return result


def plan(args):
    project = external(args.project)
    source = Path(args.file).expanduser().resolve() if args.file else project / 'input/semantic-plan.json'
    if args.compile:
        if args.check:
            raise ValueError('--compile registers a compiled plan; use --check on the resulting plan')
        compiled = run_node(project, 'compile-motion-plan.mjs', [project, source])
        source = Path(compiled['plan'])
    return run_node(project, 'semantic-plan.mjs', ['check' if args.check else 'set', project, source])


def render(args):
    project = external(args.project)
    runtime = runtime_for(project)
    version = args.version or (Path(args.output).stem if getattr(args, 'output', None) else
                               ('render-v1' if args.command == 'render' else 'preview-v1'))
    options = []
    if getattr(args, 'shot', None):
        options += ['--shot', args.shot]
    if getattr(args, 'at', None) is not None:
        options += [str(args.at)]
    if args.command == 'render':
        options += ['--kind', 'render']
    return run_node(project, 'render-semantic-preview.mjs', [project, runtime['playwright_package'],
                    runtime['browser'], version, *options])


def find_artifact(metadata, identifier):
    matches = [a for a in metadata['artifacts'] if a['path'] == identifier]
    if not matches:
        matches = [a for a in metadata['artifacts'] if Path(a['path']).name == identifier]
    if len(matches) != 1:
        raise ValueError('Choose an unambiguous registered artifact filename or absolute path')
    return matches[0]


def media_check(metadata, artifact):
    path = Path(artifact['path'])
    if digest(path) != artifact['sha256']:
        raise ValueError('Artifact changed since registration')
    snapshot = read_json(artifact['snapshot']) if artifact.get('snapshot') else None
    if not snapshot or snapshot['plan_hash'] != artifact.get('plan_hash'):
        raise ValueError('Artifact has no matching semantic render snapshot')
    if snapshot['clip'] != metadata['clip'] or snapshot['format'] != metadata['format'] or snapshot['source_hash'] != metadata['source']['sha256']:
        raise ValueError('Artifact was rendered with different project inputs or format')
    if any(metadata['assets'].get(key, {}).get('sha256') != value for key, value in snapshot['asset_hashes'].items()):
        raise ValueError('Artifact uses a previous registered asset version')
    media = artifact.get('metadata') or probe(path)
    video = next(s for s in media['streams'] if s['codec_type'] == 'video')
    format_ = snapshot['format']
    if (video['width'], video['height']) != (format_['width'], format_['height']):
        raise ValueError('Unexpected output dimensions')
    range_ = snapshot['render_range']
    if artifact['kind'] == 'still':
        return {'status': 'checked', 'scope': 'single-frame', 'width': video['width'], 'height': video['height']}
    duration = range_['end'] - range_['start']
    expected_frames = round(duration * format_['fps'])
    actual_frames = int(video.get('nb_frames', 0))
    numerator, denominator = map(int, video['r_frame_rate'].split('/'))
    if abs(numerator / denominator - format_['fps']) > 1e-6 or actual_frames != expected_frames:
        raise ValueError('Unexpected frame rate or frame coverage')
    if abs(float(video['duration']) - duration) > 1 / format_['fps'] + .001:
        raise ValueError('Unexpected video duration')
    audio = next((s for s in media['streams'] if s['codec_type'] == 'audio'), None)
    source_has_audio = any(s['codec_type'] == 'audio' for s in metadata['source']['metadata']['streams'])
    if source_has_audio and (not audio or abs(float(audio['duration']) - duration) > .12):
        raise ValueError('Expected source audio coverage is missing')
    full = abs(range_['start']) < 1e-8 and abs(range_['end'] - snapshot['clip']['duration']) < 1e-8
    return {'status': 'checked', 'scope': 'full-clip' if full else 'partial-clip',
            'duration': duration, 'frames': actual_frames, 'width': video['width'],
            'height': video['height'], 'fps': format_['fps'], 'audio': bool(audio)}


def qa(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        artifact = find_artifact(metadata, args.artifact)
        report = media_check(metadata, artifact)
        artifact['technical_check'] = {**report, 'checked_at': now()}
        save(project, metadata)
    return {'artifact': artifact['path'], 'technical': report, 'visual_review': artifact['review']}


def review(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        artifact = find_artifact(metadata, args.artifact)
        if artifact.get('engine') == 'talkcraft-native':
            artifact['review'] = args.verdict
            artifact.setdefault('feedback', []).append({'at': now(), 'verdict': args.verdict, 'text': args.feedback})
            metadata['native_trial'] = {'status': args.verdict, 'artifact': artifact['path']}
            save(project, metadata)
            return {'artifact': artifact['path'], 'visual_review': args.verdict, 'feedback': args.feedback}
    return run_node(project, 'semantic-plan.mjs', ['review', project, args.artifact, args.verdict, args.feedback])


def deliver(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        artifact = find_artifact(metadata, args.artifact)
        plan_key = 'native_plan' if artifact.get('engine') == 'talkcraft-native' else 'plan'
        if artifact.get('plan_hash') != metadata.get(plan_key, {}).get('hash'):
            raise ValueError('Choose an artifact of the current registered plan')
        report = media_check(metadata, artifact)
        if report['scope'] != 'full-clip':
            raise ValueError('Delivery requires a video covering the full project clip')
        source = Path(artifact['path'])
        destination = external(args.destination) if args.destination else project / 'delivery' / source.name
        # Keep generated media separate from registered source and input assets.
        protected = {Path(metadata['source']['path']).resolve(),
                     *(Path(a['path']).resolve() for a in metadata['assets'].values())}
        if destination in protected or project / 'input' in destination.parents or project / 'work' in destination.parents:
            raise ValueError('Delivery cannot overwrite inputs or use the work directory')
        if destination.suffix.lower() != '.mp4':
            raise ValueError('Delivery destination must end in .mp4')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if not destination.is_file() or digest(destination) != artifact['sha256']:
                raise ValueError('Destination already contains a different file; choose a new version')
        else:
            # Exclusive creation prevents accidentally replacing another version.
            created = False
            try:
                with destination.open('xb') as output:
                    created = True
                    with source.open('rb') as input_:
                        shutil.copyfileobj(input_, output, 1024 * 1024)
                if digest(destination) != artifact['sha256']:
                    raise ValueError('Delivery copy hash mismatch')
            except Exception:
                if created:
                    destination.unlink(missing_ok=True)
                raise
        record = {**artifact, 'path': str(destination), 'kind': 'delivery',
                  'render_origin': artifact.get('render_origin', str(source)), 'technical_check': report,
                  'bytes': destination.stat().st_size}
        existing = next((a for a in metadata['artifacts'] if a['path'] == str(destination)), None)
        if existing:
            existing.update(record)
        else:
            metadata['artifacts'].append(record)
        metadata['delivery'] = {'path': str(destination), 'sha256': record['sha256'],
                                'plan_hash': record['plan_hash'], 'visual_review': record['review'],
                                'bytes': record['bytes'], **report}
        metadata['status'] = 'delivered'
        save(project, metadata)
    return {'delivery': str(destination), 'technical': report, 'visual_review': record['review']}


def clean(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        keep = {Path(metadata['source']['path']).resolve(),
                *(Path(a['path']).resolve() for a in metadata['assets'].values()),
                *(Path(a['path']).resolve() for a in metadata['artifacts'])}
        candidates, skipped = {}, []
        work = project / 'work'
        for artifact in metadata['artifacts']:
            snapshot_path = Path(artifact.get('snapshot', ''))
            if snapshot_path.parent != work or snapshot_path.is_symlink() or not snapshot_path.is_file():
                continue
            if not Path(artifact['path']).is_file() or not snapshot_path.name.endswith('-snapshot.json'):
                continue
            snapshot = read_json(snapshot_path)
            prefix = snapshot_path.name[:-len('-snapshot.json')]
            cache = work / (prefix + '-frames')
            if not cache.exists():
                continue
            files = list(cache.iterdir()) if cache.is_dir() and not cache.is_symlink() else []
            range_ = snapshot.get('render_range', {})
            expected = 1 if artifact['kind'] == 'still' else round(
                (range_.get('end', 0) - range_.get('start', 0)) * snapshot.get('format', {}).get('fps', 0))
            safe = expected > 0 and len(files) == expected and {p.name for p in files} == {
                f'{index:05d}.png' for index in range(expected)} and all(
                p.is_file() and not p.is_symlink() and p.resolve() not in keep for p in files)
            if snapshot.get('plan_hash') != artifact.get('plan_hash') or not safe:
                skipped.append(str(cache))
                continue
            candidates[str(cache)] = (files, sum(p.stat().st_size for p in files))
        reclaimed = sum(size for _, size in candidates.values())
        if args.apply:
            for directory, (files, _) in candidates.items():
                for file in files:
                    file.unlink()
                Path(directory).rmdir()
            metadata.setdefault('cache_cleanups', []).append({'at': now(), 'directories': list(candidates), 'bytes': reclaimed})
            save(project, metadata)
    return {'project': str(project), 'applied': args.apply, 'directories': list(candidates),
            'bytes': reclaimed, 'skipped': skipped, 'retained': 'inputs, plans, snapshots, previews, renders, deliveries, runtime'}
