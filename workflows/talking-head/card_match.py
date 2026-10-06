"""Adapted input feasibility and ranking from TalkCraft; no SHOTBOOK dependency.

Required Notice: Copyright (c) 2026 Vincent Wei (https://github.com/Vincentwei1021/video-talkcraft)
Upstream license: https://polyformproject.org/licenses/noncommercial/1.0.0/
Reuse authorization and exact source are recorded in library/planning/provenance.json.
"""

FAMILY = {'V', '图', '截图'}


def feasible(card, kinds):
    for item in card['inputs']:
        if item.get('need') == '必需' and item['type'] not in kinds:
            return False, f"需要「{item['type']}」，本段没有对应素材"
    family = {item['type'] for item in card['inputs']} & FAMILY
    if family and not family & kinds:
        return False, '需要媒体素材：' + ' / '.join(sorted(family))
    return True, ''


def score(card, kinds, position, recent, media_count):
    value, reasons = 0.0, []
    family = {item['type'] for item in card['inputs']} & FAMILY
    if family and family <= kinds:
        value += 2
        reasons.append('素材完全匹配')
    elif family:
        reasons.append('素材部分匹配')
    card_position = card.get('position', '任意')
    if position != '中段' and card_position in (position, '任意'):
        value += 1
        reasons.append(f'位置合（{card_position}）')
    elif position == '中段' and card_position in ('开场', '收尾'):
        value -= 1
        reasons.append(f'{card_position}专用卡用于中段')
    if card.get('priority') == 'P0':
        value += .5
        reasons.append('上游优先级 P0')
    if card['id'] in recent:
        value -= 2
        reasons.append('前两段已选择，提示检查重复')
    if '多图' in card.get('material_shape', []) and media_count < 2:
        value -= 2
        reasons.append('多图编排只有一份素材')
    if card.get('hardcoded') and media_count:
        value -= 1
        reasons.append('上游内容写死，需要源码适配')
    return value, reasons
