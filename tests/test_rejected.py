import io
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from kazllm import data, query, gemini_query as google, failures
from test_gemini import response as google_response
from test_local import response as local_response


class RejectedResponseTests(unittest.TestCase):
    def test_local_failure_is_saved_separately_and_skipped_on_resume(self):
        ps = [{'prompt_id': f'p{i}', 'task': 'mt', 'prompt': 'Translate.'} for i in range(3)]
        spec = {'name': 'test', 'id': 'qwen2.5:1.5b', 'qa_max_tokens': 64, 'mt_max_tokens': 1024,
                'temperature': 0, 'seed': 42, 'num_ctx': 8192}
        identity = {'digest': 'test', 'show_sha256': 'test'}
        bad = dict(local_response(), done_reason='length')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'local.jsonl'
            with patch.object(query, 'request', side_effect=[bad, local_response()]) as call, redirect_stdout(io.StringIO()):
                query.run_model(ps, path, spec, identity, 'TEST', max_new=2, continue_on_invalid=True)
            self.assertEqual(call.call_count, 2)
            self.assertEqual([r['prompt_id'] for r in data.read_jsonl(path)], ['p1'])
            self.assertEqual(set(failures.checked_records(path, ps, spec)), {'p0'})
            with patch.object(query, 'request', return_value=local_response()) as call, redirect_stdout(io.StringIO()):
                query.run_model(ps, path, spec, identity, 'TEST', max_new=1, continue_on_invalid=True)
                self.assertEqual(call.call_args.args[1]['messages'][0]['content'], 'Translate.')
                self.assertEqual(call.call_count, 1)
            self.assertEqual([r['prompt_id'] for r in data.read_jsonl(path)], ['p1', 'p2'])
            with patch.object(query, 'request', return_value=local_response()), redirect_stdout(io.StringIO()):
                query.run_model(ps, path, spec, identity, 'TEST', max_new=1, continue_on_invalid=True, retry_failed=True)
            self.assertEqual([r['prompt_id'] for r in data.read_jsonl(path)], ['p1', 'p2', 'p0'])

    def test_google_invalid_response_does_not_block_next_prompt(self):
        ps = [{'prompt_id': f'p{i}', 'task': 'qa', 'prompt': 'Answer.'} for i in range(2)]
        spec = {'id': google.MODEL, 'backend': 'gemini', 'name': 'test',
                'qa_max_tokens': 512, 'mt_max_tokens': 2048, 'temperature': 0, 'seed': 42}
        bad = google_response()
        bad['candidates'][0]['finishReason'] = 'MAX_TOKENS'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'google.jsonl'
            with patch.dict(os.environ, {'GEMINI_FREE_TIER_CONFIRMED': '1'}), \
                    patch.object(google, 'request', side_effect=[bad, google_response()]), \
                    patch.object(google.time, 'sleep'), redirect_stdout(io.StringIO()):
                query.run_model(ps, path, spec, max_new=2, continue_on_invalid=True)
            self.assertEqual([r['prompt_id'] for r in data.read_jsonl(path)], ['p1'])
            self.assertEqual(set(failures.checked_records(path, ps, spec)), {'p0'})
