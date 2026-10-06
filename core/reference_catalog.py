"""Read pinned local references. Search results never imply a watched or runnable video."""
import subprocess
from collections import Counter
from pathlib import Path

from .project import REPO, digest, read_json


def sources():
    records = read_json(REPO / 'library/sources.json')['sources']
    for item in records:
        actual = subprocess.check_output(['git', '-C', str(REPO / item['path']), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != item['commit']:
            raise ValueError(f"Source {item['id']} changed; perform an explicit upstream sync first")
    return {item['id']: item for item in records}


def local(source, relative):
    path = (REPO / source['path'] / relative).resolve()
    if not path.is_relative_to((REPO / source['path']).resolve()):
        raise ValueError('Reference path escapes source')
    return str(path) if path.is_file() else None


def catalog():
    upstreams = sources()
    talk = upstreams['video-talkcraft']
    talk_index = read_json(REPO / talk['path'] / 'references/cards-index.json')
    native = read_json(REPO / 'library/talkcraft-native/provenance.json')
    native_cards = {Path(item['original_path']).stem: item for item in native['adaptations']} if native['commit'] == talk['commit'] else {}
    cards = []
    for original in talk_index['cards']:
        slug = original['slug']
        card = {**original, 'id': 'video-talkcraft:' + slug, 'source': talk['id'], 'commit': talk['commit'],
                'summary': original['oneliner'], 'reference': local(talk, f'references/cards/{slug}.md'),
                'code': local(talk, original['code']), 'preview': local(talk, f'gallery/thumbs/{slug}.png'),
                'methods': ['title-demote-to-label'] if slug == 'title-demote-to-label' else [],
                'availability': 'ready' if slug == 'title-demote-to-label' else 'reference-only'}
        if slug in native_cards:
            card.update({'availability': 'native-ready', 'engine': 'talkcraft-native',
                         'native_code': str(REPO / native_cards[slug]['adaptation'])})
        cards.append(card)
    shot = upstreams['video-shotcraft']
    for original in read_json(REPO / shot['path'] / 'gallery/api/library.json')['cards']:
        slug = original['name']
        # ShotCraft does not publish TalkCraft's semantic taxonomy. Do not invent annotations.
        card = {'id': 'video-shotcraft:' + slug, 'source': shot['id'], 'commit': shot['commit'],
                'title': slug, 'summary': original['summary'], 'use': original['use'],
                'semantics': [], 'inputs': [], 'methods': [], 'availability': 'reference-only',
                'reference': local(shot, original['source']),
                'preview': local(shot, f'gallery/media/poster/{slug}.jpg'),
                'keywords': original.get('tags', [])}
        cards.append(card)
    for original in read_json(REPO / 'library/planning/references.json')['items']:
        card = {**original, 'availability': 'ready' if original.get('methods') else 'reference-only',
                'methods': original.get('methods', []), 'priority': 'P0', 'position': '任意', 'hardcoded': False}
        source = upstreams.get(card['source'])
        if source:
            card['commit'] = source['commit']
            for field in ('reference', 'code', 'preview'):
                if field in card:
                    card[field] = local(source, card[field])
        else:
            card['reference'] = str(REPO / card['reference'])
        cards.append(card)
    case_source = upstreams['awesome-opus5-5-videos']
    cases = []
    for item in read_json(REPO / case_source['path'] / 'data/videos.json'):
        cases.append({'id': 'awesome-opus5-5-videos:' + item['slug'], 'source': case_source['id'],
                      'commit': case_source['commit'], 'title': item['slug'], 'summary': item['prompt'][:500],
                      'keywords': [item['category'], *item['tech_tags']], 'availability': 'remote-reference',
                      'semantics': [], 'inputs': [], 'methods': [],
                      'reference': local(case_source, 'prompts/' + item['slug'] + '.md'),
                      'post_url': item['post_url'], 'poster_url': item['poster_url']})
    files = ['library/planning/references.json', 'library/planning/provenance.json', 'library/talkcraft-native/provenance.json',
             'library/motion/catalog.json', 'library/sources.json',
             talk['path'] + '/references/cards-index.json', shot['path'] + '/gallery/api/library.json',
             case_source['path'] + '/data/videos.json']
    return {'cards': cards, 'cases': cases, 'vocab': [item['word'] for item in talk_index['vocab']],
            'sources': {key: item['commit'] for key, item in upstreams.items()},
            'files': [{'path': str(REPO / f), 'sha256': digest(REPO / f)} for f in files]}


ALIASES = {'连接': ['连接', '机制', 'connecting', 'connection'], '传输': ['传输', '迁移', 'transfer', 'process'],
           '步骤': ['步骤', 'step', '流程'], '证据': ['证据', '例证', 'evidence', 'screenshot'],
           '数字': ['数字', '数据', 'number', 'chart'], '标题': ['标题', 'title', 'typography']}


def search(data, query='', semantic=None, limit=8):
    if not 1 <= limit <= 30:
        raise ValueError('limit must be 1–30')
    if semantic and semantic not in [v[0] if isinstance(v, list) else v for v in data['vocab']]:
        raise ValueError('Unknown semantic label: ' + semantic)
    terms = [term for word in query.lower().split() for term in ALIASES.get(word, [word])]
    hits = []
    for item in data['cards'] + data['cases']:
        if semantic and semantic not in item['semantics']:
            continue
        haystack = ' '.join(str(item.get(k, '')) for k in ('id', 'title', 'summary', 'use', 'semantics', 'keywords')).lower()
        value = sum(term in haystack for term in terms)
        if terms and not value:
            continue
        hits.append((value, item))
    hits.sort(key=lambda entry: (-entry[0], entry[1]['id']))
    return {'counts': dict(Counter(c['source'] for c in data['cards'] + data['cases'])),
            'total_matches': len(hits), 'visual_review': 'not-performed-by-search',
            'results': [item for _, item in hits[:limit]]}
