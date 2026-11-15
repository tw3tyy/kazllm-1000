import io
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from kazllm import data, query, gemini_query
from pipeline import load_inputs
from test_gemini import response as google_response
from test_local import response as local_response


class ExpandedTests(unittest.TestCase):
    def test_counts_sources_and_prompt_blocks(self):
        _, items, prompts = load_inputs()
        self.assertEqual(len(prompts), 5000)
        for task in ('mt', 'qa', 'probe'):
            rows = [r for r in items if r['task'] == task]
            self.assertEqual(len(rows), 1000)
        self.assertEqual(sum(r.get('source') == 'Belebele' for r in items), 900)
        for start in range(0, len(prompts), 5):
            self.assertEqual([r['task'] for r in prompts[start:start + 5]], ['mt', 'mt', 'qa', 'qa', 'probe'])

    def test_local_bounded_batch_resumes_next_prompt(self):
        ps = [{'prompt_id': f'p{i}', 'task': 'mt', 'prompt': 'Translate.'} for i in range(3)]
        spec = {'name': 'Qwen test', 'id': 'qwen2.5:1.5b', 'qa_max_tokens': 64, 'mt_max_tokens': 1024,
                'temperature': 0, 'seed': 42, 'num_ctx': 8192}
        identity = {'digest': 'test', 'show_sha256': 'test'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'local.jsonl'
            with patch.object(query, 'request', return_value=local_response()) as call, redirect_stdout(io.StringIO()):
                query.run_model(ps, path, spec, identity, 'TEST', max_new=1)
                query.run_model(ps, path, spec, identity, 'TEST', max_new=1)
            self.assertEqual(call.call_count, 2)
            self.assertEqual([r['prompt_id'] for r in data.read_jsonl(path)], ['p0', 'p1'])

    def test_google_bounded_batch_resumes_next_prompt(self):
        ps = [{'prompt_id': f'p{i}', 'task': 'qa', 'prompt': 'Answer.'} for i in range(3)]
        spec = {'id': gemini_query.MODEL, 'backend': 'gemini', 'name': 'Gemini',
                'qa_max_tokens': 512, 'mt_max_tokens': 2048, 'temperature': 0, 'seed': 42}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'google.jsonl'
            with patch.dict(os.environ, {'GEMINI_FREE_TIER_CONFIRMED': '1'}), \
                    patch.object(gemini_query, 'request', return_value=google_response()) as call, \
                    patch.object(gemini_query.time, 'sleep'), redirect_stdout(io.StringIO()):
                query.run_model(ps, path, spec, max_new=1)
                query.run_model(ps, path, spec, max_new=1)
            self.assertEqual(call.call_count, 2)
            self.assertEqual([r['prompt_id'] for r in data.read_jsonl(path)], ['p0', 'p1'])
