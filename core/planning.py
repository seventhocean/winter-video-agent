"""Codex authors content and construction; deterministic tools retrieve and validate it."""
import importlib.util
import math
from pathlib import Path

from .project import REPO, digest, external, load, now, project_lock, read_json, save, write_json
from .reference_catalog import catalog, search

spec = importlib.util.spec_from_file_location('talking_head_card_match', REPO / 'workflows/talking-head/card_match.py')
matcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matcher)
KINDS = {'image': '图', 'screenshot': '截图', 'video': 'V'}
NEEDS = {'证据', '身份', '量化', '对比', '结构', '强调', '无'}


def require(test, message):
    if not test:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and value.strip(), 'Missing ' + label)


def project_file(project, filename):
    path = (project / filename).resolve()
    require(path.is_relative_to(project) and path.is_file(), 'Expected existing project file: ' + str(path))
    return path


def file_record(path):
    return {'path': str(path), 'sha256': digest(path)}


def basis(metadata):
    return {key: metadata[key] for key in ('clip', 'format')} | {
        'source_sha256': metadata['source']['sha256'],
        'asset_hashes': {key: asset['sha256'] for key, asset in metadata['assets'].items()}}


def same_inputs(document, metadata):
    require(document['project_basis'] == basis(metadata), 'Project inputs changed; refresh the brief and suggestions')


def validate_brief(document, metadata, data):
    require(metadata['primary_workflow'] == 'talking-head', 'Planning currently supports talking-head only')
    require(document.get('schema_version') == 1, 'Unsupported brief version')
    same_inputs(document, metadata)
    text(document.get('timing_basis'), 'honest timing basis')
    text(document.get('intent'), 'video intent')
    rows = document.get('segments')
    require(isinstance(rows, list) and rows, 'Brief needs semantic segments')
    vocabulary = {v[0] if isinstance(v, list) else v for v in data['vocab']}
    previous = 0
    ids = set()
    for row in rows:
        sid = row.get('id')
        text(sid, 'segment ID')
        require(sid not in ids, 'Duplicate segment ID: ' + sid)
        ids.add(sid)
        start, end = row.get('start'), row.get('end')
        require(all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in (start, end)), 'Invalid segment timing')
        require(abs(start - previous) < 1e-6 and start < end <= metadata['clip']['duration'], 'Segments must cover clip without gaps/overlaps: ' + sid)
        previous = end
        text(row.get('text'), sid + ' speech/content')
        text(row.get('purpose'), sid + ' audience task')
        require(row.get('mode') in ('enhance', 'source'), 'Choose enhance/source: ' + sid)
        require(isinstance(row.get('host_present'), bool), 'Declare actual host presence: ' + sid)
        require(isinstance(row.get('semantics'), list) and set(row['semantics']) <= vocabulary, 'Unknown semantic labels: ' + sid)
        require(row['mode'] == 'source' or row['semantics'], 'Annotate semantics before suggesting: ' + sid)
        require(isinstance(row.get('needs'), list) and row['needs'] and set(row['needs']) <= NEEDS, 'Invalid visual needs: ' + sid)
        require(isinstance(row.get('entities'), list), 'Declare entities: ' + sid)
        for material in row.get('materials', []):
            require(material.get('kind') in KINDS, 'Invalid material kind: ' + sid)
            require(material.get('asset') in metadata['assets'], 'Register material asset first: ' + str(material.get('asset')))
            require(Path(metadata['assets'][material['asset']]['path']).is_file(), 'Material file missing')
        for request in row.get('material_requests', []):
            text(request.get('description'), sid + ' material request')
            if request.get('asset'):
                require(request['asset'] in metadata['assets'], 'Register requested material first')
            require(isinstance(request.get('required', False), bool), 'Material required must be boolean')
        require(row.get('position', '任意') in ('开场', '中段', '收尾', '任意'), 'Invalid segment position')
    require(abs(previous - metadata['clip']['duration']) < 1e-6, 'Brief must cover entire clip')


def brief(args):
    project = external(args.project)
    target = project / 'input/content-brief.json'
    with project_lock(project):
        metadata = load(project)
        require(metadata['primary_workflow'] == 'talking-head', 'Brief supports talking-head only')
        if args.file:
            incoming = read_json(external(args.file))
            validate_brief(incoming, metadata, catalog())
            write_json(target, incoming)
            metadata['planning'] = {'status': 'annotated', 'brief': file_record(target), 'updated_at': now()}
            save(project, metadata)
            return {'brief': str(target), 'planning_status': 'annotated'}
        require(not target.exists(), 'Brief already exists; edit it or register an annotated file')
        old = read_json(project / 'input/semantic-plan.json') if (project / 'input/semantic-plan.json').exists() else None
        segments = []
        for row in old['beats'] if old else [{'id': 'segment-1', 'start': 0, 'end': metadata['clip']['duration'], 'purpose': ''}]:
            captions = [l['text'] for l in old['layers'] if l['type'] == 'text' and l['id'].startswith('caption-') and l['start'] < row['end'] and l['end'] > row['start']] if old else []
            segments.append({'id': row['id'], 'start': row['start'], 'end': row['end'],
                             'text': ' / '.join(captions), 'purpose': row['purpose'], 'mode': 'enhance',
                             'semantics': [], 'needs': [], 'entities': [], 'materials': [],
                             'material_requests': [], 'host_present': None, 'reference_query': ''})
        draft = {'schema_version': 1, 'intent': old['intent'] if old else '', 'project_basis': basis(metadata),
                 'timing_basis': '', 'segments': segments}
        write_json(target, draft)
        return {'brief': str(target), 'planning_status': 'needs-agent-annotation',
                'note': 'Skeleton only; inspect speech/footage and annotate before suggest. No transcription performed.'}


def candidates(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        brief_path = project_file(project, 'input/content-brief.json')
        document, data = read_json(brief_path), catalog()
        validate_brief(document, metadata, data)
        results, history = [], []
        for row in document['segments']:
            kinds = {'文'} | ({'人'} if row['host_present'] else set()) | {KINDS[m['kind']] for m in row.get('materials', [])}
            recent = set().union(*history[-2:]) if history else set()
            ranked, rejected = [], []
            if row['mode'] == 'enhance':
                for card in data['cards']:
                    matches = set(card['semantics']) & set(row['semantics'])
                    if not matches:
                        continue
                    allowed, reason = matcher.feasible(card, kinds)
                    if not allowed:
                        rejected.append({'id': card['id'], 'reason': reason})
                        continue
                    value, why = matcher.score(card, kinds, row.get('position', '中段'), recent,
                                               len({m['asset'] for m in row.get('materials', [])}))
                    value += len(matches) * 2
                    ranked.append({**card, 'score': value, 'matched_semantics': sorted(matches),
                                   'reasons': ['语义匹配：' + '、'.join(sorted(matches)), *why]})
                ranked.sort(key=lambda c: (-c['score'], c['id']))
            history.append(set(row.get('previously_selected', [])))
            results.append({'id': row['id'], 'mode': row['mode'], 'candidates': ranked[:args.top],
                            'ready_candidates': [c for c in ranked if c['availability'] == 'ready'][:args.top],
                            'rejected': rejected[:5],
                            'related_references': search(data, row.get('reference_query', ''), limit=4)['results'] if row.get('reference_query') else [],
                            'material_requests': row.get('material_requests', []),
                            'note': '候选排序不代表已选择、已观看或已获审美确认。'})
        output = {'schema_version': 1, 'project_basis': basis(metadata), 'brief': file_record(brief_path),
                  'catalog_files': data['files'], 'source_commits': data['sources'], 'segments': results,
                  'visual_review': 'not-performed-by-search'}
        target = project / 'input/card-candidates.json'
        write_json(target, output)
        fingerprint = digest(target)
        archive = project / 'decisions/candidates'
        archive.mkdir(parents=True, exist_ok=True)
        write_json(archive / (fingerprint + '.json'), output)
        lines = ['# 内容驱动的参考候选', '', '检索结果需要 Codex 查看成品和准确实现，再形成施工单。', '']
        for row in results:
            lines += ['## ' + row['id'], '']
            if row['mode'] == 'source':
                lines += ['本段保留原片；施工单写明理由。', '']
            for card in row['candidates']:
                lines += [f"- {card['id']} · {card['score']} · {card['availability']}：{'；'.join(card['reasons'])}",
                          f"  参考：{card.get('reference')}；预览：{card.get('preview')}；可调用方法：{', '.join(card['methods']) or '待适配'}"]
            for request in row['material_requests']:
                lines += ['- 素材缺口：' + request['description']]
            lines += ['']
        (archive / (fingerprint + '.md')).write_text('\n'.join(lines), encoding='utf-8')
        metadata['planning'] = {'status': 'candidates', 'brief': output['brief'],
                                'candidates': file_record(target), 'updated_at': now()}
        save(project, metadata)
        return {'candidates': str(target), 'report': str(archive / (fingerprint + '.md')),
                'planning_status': 'candidates', 'segments': results}


def verify_records(records):
    for item in records:
        require(Path(item['path']).is_file() and digest(item['path']) == item['sha256'],
                'Planning dependency changed: ' + item['path'])


def storyboard(args):
    project = external(args.project)
    with project_lock(project):
        metadata = load(project)
        data = catalog()
        brief_path, candidate_path = project_file(project, 'input/content-brief.json'), project_file(project, 'input/card-candidates.json')
        document, suggestions = read_json(brief_path), read_json(candidate_path)
        validate_brief(document, metadata, data)
        same_inputs(suggestions, metadata)
        verify_records([suggestions['brief'], *suggestions['catalog_files']])
        if args.init:
            require(not args.file and not args.construction and not args.check, '--init does not accept a finished file/construction/check')
            target = project / 'input/storyboard.json'
            require(not target.exists(), 'Storyboard skeleton already exists; edit or use a versioned file')
            write_json(target, {'schema_version': 1, 'brief_sha256': digest(brief_path),
                       'candidates_sha256': digest(candidate_path), 'references': [],
                       'segments': [{'id': row['id'], 'mode': row['mode'], 'layout': '',
                                     'handoff_in': '', 'handoff_out': '', 'objects': [], 'phases': [],
                                     'reference_ids': [], 'selections': [], 'render_ids': [],
                                     **({'reason': ''} if row['mode'] == 'source' else {})} for row in document['segments']]})
            return {'storyboard': str(target), 'planning_status': 'needs-agent-construction'}
        require(args.file and args.construction, 'Pass a finished storyboard and --construction, or use --init')
        sheet_path, construction_path = external(args.file), external(args.construction)
        require(construction_path != project / 'input/motion-plan-planned.json', 'Use a versioned construction input, not the linked output')
        sheet, construction = read_json(sheet_path), read_json(construction_path)
        require(sheet.get('schema_version') == 1, 'Unsupported storyboard version')
        require(sheet.get('brief_sha256') == digest(brief_path) and sheet.get('candidates_sha256') == digest(candidate_path), 'Storyboard must name the current brief and candidate hashes')
        cards = {c['id']: c for c in data['cards'] + data['cases']}
        references, reference_records = {}, []
        for ref in sheet.get('references', []):
            rid = ref.get('id')
            text(rid, 'reference ID')
            require(rid not in references, 'Duplicate reference ID')
            if ref.get('card_id'):
                require(ref['card_id'] in cards, 'Unknown reference card')
            for field in ('task', 'grouping', 'motion', 'adaptation'):
                text(ref.get(field), rid + ' ' + field)
            require(ref.get('evidence'), 'Reference needs an actual viewed/read evidence record')
            for evidence in ref['evidence']:
                require(evidence.get('kind') in ('image', 'video', 'code', 'document'), 'Invalid evidence kind')
                path = Path(evidence.get('path', '')).expanduser().resolve(strict=True)
                text(evidence.get('locator'), rid + ' evidence locator')
                text(evidence.get('findings'), rid + ' evidence findings')
                reference_records.append(file_record(path))
            references[rid] = ref
        rows = sheet.get('segments', [])
        require([r.get('id') for r in rows] == [r['id'] for r in document['segments']], 'Storyboard must cover each semantic segment in order')
        construction_ids = {l['id'] for l in construction.get('layers', [])} | {m['id'] for m in construction.get('motions', [])}
        used_ids = set()
        for row, semantic, suggestion in zip(rows, document['segments'], suggestions['segments']):
            sid = row['id']
            require(row.get('mode') == semantic['mode'], 'Storyboard mode differs from brief: ' + sid)
            for field in ('layout', 'handoff_in', 'handoff_out'):
                text(row.get(field), sid + ' ' + field)
            if row['mode'] == 'source':
                text(row.get('reason'), sid + ' retained-source reason')
            else:
                require(not any(r.get('required') and not r.get('asset') for r in semantic.get('material_requests', [])), 'Resolve required material requests before construction: ' + sid)
                require(row.get('reference_ids') and set(row['reference_ids']) <= references.keys(), 'Enhanced segment needs analyzed references: ' + sid)
                selections = row.get('selections', [])
                require(selections, 'Choose an expression method: ' + sid)
                offered = {c['id'] for c in suggestion['candidates'] + suggestion['ready_candidates'] + suggestion['related_references']}
                for pick in selections:
                    require(pick.get('card_id') in cards, 'Unknown selected card: ' + sid)
                    text(pick.get('reason'), sid + ' selection reason')
                    if pick['card_id'] not in offered:
                        text(pick.get('deviation_reason'), sid + ' reason to select outside candidates')
                    require(any(references[r].get('card_id') == pick['card_id'] for r in row['reference_ids']), 'Selected card needs its own analyzed reference: ' + sid)
                    chosen = cards[pick['card_id']]
                    if chosen['availability'] != 'ready':
                        text(pick.get('implementation_note'), sid + ' adaptation for reference-only selection')
            objects = row.get('objects', [])
            object_ids = {o.get('id') for o in objects}
            require(len(object_ids) == len(objects) and all(isinstance(i, str) and i.strip() for i in object_ids), 'Invalid object IDs: ' + sid)
            for obj in objects:
                text(obj.get('role'), sid + ' object role')
                require(obj.get('basis') in ('source', 'schematic', 'evidence', 'text'), 'Declare object basis: ' + sid)
                if obj.get('asset'):
                    require(obj['asset'] in metadata['assets'], 'Object asset is not registered')
                require(obj.get('basis') != 'evidence' or obj.get('asset'), 'Evidence object needs a registered asset')
            phases = row.get('phases', [])
            require(phases, 'Describe full action sequence: ' + sid)
            previous = semantic['start']
            for phase in phases:
                start, end = phase.get('start'), phase.get('end')
                require(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (start, end)), 'Invalid action timing: ' + sid)
                require(abs(start - previous) < 1e-6 and start < end <= semantic['end'], 'Phases must cover segment in order: ' + sid)
                require(phase.get('kind') in ('establish', 'change', 'read', 'handoff', 'hold'), 'Invalid phase kind')
                require(set(phase.get('objects', [])) <= object_ids, 'Unknown action object')
                text(phase.get('action'), sid + ' phase action')
                previous = end
            require(abs(previous - semantic['end']) < 1e-6, 'Action sequence must include reading and handoff time: ' + sid)
            if row['mode'] == 'enhance':
                require(any(p['kind'] in ('read', 'hold') for p in phases), 'Reserve reading time: ' + sid)
            render_ids = set(row.get('render_ids', []))
            require(render_ids <= construction_ids, 'Unknown construction element: ' + sid)
            require(row['mode'] == 'source' or render_ids, 'Enhanced segment needs executable construction elements: ' + sid)
            selected_methods = {m['method'] for m in construction.get('motions', []) if m['id'] in render_ids}
            for pick in row.get('selections', []):
                chosen = cards[pick['card_id']]
                if chosen['availability'] == 'ready':
                    require(set(chosen['methods']) & selected_methods, 'Selected ready card has no corresponding construction method: ' + pick['card_id'])
            used_ids |= render_ids
        # Global subtitles/navigation may stay outside segment construction mappings.
        require({m['id'] for m in construction.get('motions', [])} <= used_ids, 'Every motion must belong to a storyboard segment')
        records = [file_record(brief_path), file_record(candidate_path), file_record(sheet_path), file_record(construction_path), *suggestions['catalog_files'], *reference_records]
        fingerprint = digest(sheet_path)
        archive = project / 'decisions/storyboards'
        if args.check:
            return {'planning_status': 'checked', 'segments': len(rows), 'storyboard_sha256': fingerprint}
        archive.mkdir(parents=True, exist_ok=True)
        archived = archive / (fingerprint + '.json')
        write_json(archived, sheet)
        records = [r for r in records if r['path'] != str(sheet_path)] + [file_record(archived)]
        lines = ['# 逐镜施工单', '', '时序依据：' + document['timing_basis'], '', '审美状态：awaiting-user', '']
        for row, semantic in zip(rows, document['segments']):
            lines += [f"## {row['id']} · {semantic['start']}–{semantic['end']} 秒", '',
                      '口播：' + semantic['text'], '', '观众任务：' + semantic['purpose'], '',
                      '布局：' + row['layout'], '', '接入：' + row['handoff_in'], '']
            if row['mode'] == 'source':
                lines += ['保留原片：' + row['reason'], '']
            for pick in row.get('selections', []):
                lines += [f"选择：{pick['card_id']} — {pick['reason']}", '']
            for rid in row.get('reference_ids', []):
                ref = references[rid]
                lines += ['参考分析：' + rid, '', '信息分组：' + ref['grouping'], '', '动作：' + ref['motion'], '', '本期适配：' + ref['adaptation'], '']
            for phase in row['phases']:
                lines += [f"- {phase['start']}–{phase['end']} · {phase['kind']}：{phase['action']}"]
            lines += ['', '交出：' + row['handoff_out'], '', '实现：' + ', '.join(row.get('render_ids', [])), '']
        report = archive / (fingerprint + '.md')
        report.write_text('\n'.join(lines), encoding='utf-8')
        linked = project / 'input/motion-plan-planned.json'
        write_json(linked, {**construction, 'planning': {'storyboard_sha256': fingerprint,
                   'brief_sha256': digest(brief_path), 'candidates_sha256': digest(candidate_path),
                   'project_basis': basis(metadata), 'files': records, 'visual_review': 'awaiting-user'}})
        metadata['planning'] = {**metadata.get('planning', {}), 'status': 'constructed',
                                'storyboard': file_record(archived), 'report': str(report),
                                'construction': file_record(linked), 'updated_at': now()}
        save(project, metadata)
        return {'planning_status': 'constructed', 'storyboard': str(archived), 'report': str(report),
                'construction': str(linked), 'segments': len(rows), 'visual_review': 'awaiting-user'}
