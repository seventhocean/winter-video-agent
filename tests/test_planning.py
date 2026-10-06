"""Meaningful planning boundaries: unavailable media, stale inputs, false readiness."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from core import planning
from core.project import REPO, digest, load, save, write_json


class PlanningBoundaries(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='winter-planning-')
        self.project = Path(self.temporary.name)
        (self.project / 'input').mkdir()
        self.metadata = {'primary_workflow': 'talking-head', 'status': 'prepared',
                         'source': {'sha256': 'fixture-source'}, 'clip': {'start': 0, 'duration': 4},
                         'format': {'width': 1280, 'height': 960, 'fps': 30}, 'assets': {}, 'artifacts': []}
        save(self.project, self.metadata)
        self.document = {'schema_version': 1, 'intent': 'Explain a sourced quantity',
                         'timing_basis': 'Synthetic fixture, manual semantic anchors',
                         'project_basis': planning.basis(self.metadata), 'segments': [
                             {'id': 'quantity', 'start': 0, 'end': 4, 'text': 'A measured quantity',
                              'purpose': 'Understand a quantity', 'mode': 'enhance',
                              'host_present': False, 'semantics': ['数据'], 'needs': ['量化'],
                              'entities': ['quantity'], 'materials': [], 'material_requests': []}]}
        write_json(self.project / 'input/content-brief.json', self.document)
        self.suggest()

    def tearDown(self):
        self.temporary.cleanup()

    def suggest(self):
        return planning.candidates(SimpleNamespace(project=str(self.project), top=5))

    def construction(self, method='metric-card'):
        candidates = self.project / 'input/card-candidates.json'
        brief = self.project / 'input/content-brief.json'
        sheet = {'schema_version': 1, 'brief_sha256': digest(brief), 'candidates_sha256': digest(candidates),
                 'references': [{'id': 'metric', 'card_id': 'winter:metric-card', 'task': 'Compare quantities',
                                 'grouping': 'Values share a common scale', 'motion': 'Count then hold',
                                 'adaptation': 'Use only supplied measurements', 'evidence': [
                                     {'kind': 'document', 'path': str(REPO / 'library/recipes/progressive-explanation/RECIPE.md'),
                                      'locator': 'Metric card contract', 'findings': 'Requires a common scale'}]}],
                 'segments': [{'id': 'quantity', 'mode': 'enhance', 'layout': 'Use actual available space',
                               'handoff_in': 'Establish quantity', 'handoff_out': 'Leave result readable',
                               'reference_ids': ['metric'], 'selections': [{'card_id': 'winter:metric-card', 'reason': 'Measured quantity'}],
                               'objects': [{'id': 'value', 'role': 'Measured value', 'basis': 'text'}],
                               'phases': [{'start': 0, 'end': 4, 'kind': 'read', 'objects': ['value'], 'action': 'Read supplied value'}],
                               'render_ids': ['metric']} ]}
        write_json(self.project / 'input/sheet.json', sheet)
        write_json(self.project / 'input/construction.json', {'motions': [{'id': 'metric', 'method': method}]})
        return SimpleNamespace(project=str(self.project), file=str(self.project / 'input/sheet.json'),
                               construction=str(self.project / 'input/construction.json'), check=False, init=False)

    def test_unavailable_evidence_cannot_become_ready(self):
        document = copy.deepcopy(self.document)
        document['segments'][0]['semantics'] = ['例证', '强调']
        write_json(self.project / 'input/content-brief.json', document)
        row = self.suggest()['segments'][0]
        self.assertNotIn('winter:evidence-focus', [c['id'] for c in row['ready_candidates']])
        self.assertEqual(load(self.project)['status'], 'prepared')
        self.assertTrue(all(c['availability'] == 'ready' for c in row['ready_candidates']))

    def test_changed_brief_rejects_old_candidates(self):
        args = self.construction()
        document = copy.deepcopy(self.document)
        document['intent'] = 'Different task'
        write_json(self.project / 'input/content-brief.json', document)
        with self.assertRaisesRegex(ValueError, 'Planning dependency changed'):
            planning.storyboard(args)

    def test_ready_selection_must_have_matching_implementation(self):
        args = self.construction('group-sequence')
        with self.assertRaisesRegex(ValueError, 'no corresponding construction method'):
            planning.storyboard(args)

    def test_required_material_gap_blocks_construction(self):
        document = copy.deepcopy(self.document)
        document['segments'][0]['material_requests'] = [{'description': 'Actual evidence', 'required': True}]
        write_json(self.project / 'input/content-brief.json', document)
        self.suggest()
        with self.assertRaisesRegex(ValueError, 'Resolve required material'):
            planning.storyboard(self.construction())

    def test_linked_construction_preserves_review_state(self):
        result = planning.storyboard(self.construction())
        self.assertEqual(result['visual_review'], 'awaiting-user')
        self.assertTrue(Path(result['construction']).is_file())
        self.assertEqual(load(self.project)['planning']['status'], 'constructed')
        self.assertEqual(load(self.project)['status'], 'prepared')


if __name__ == '__main__':
    unittest.main()
