import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class BatchTests(unittest.TestCase):
    def test_gemma_still_runs_after_google_and_qwen_fail(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(root / 'run_batch.sh', target / 'run_batch.sh')
            scripts = {
                'run_gemini.sh': 'echo Gemini >> calls; exit 1',
                'run_local.sh': 'echo "$2" >> calls; [ "$2" != "qwen2.5-7b" ]',
                'refresh_site.sh': 'echo refresh >> calls',
                'demo.sh': 'echo status >> calls',
            }
            for name, body in scripts.items():
                path = target / name
                path.write_text('#!/bin/bash\n' + body + '\n')
                path.chmod(0o755)
            result = subprocess.run(['bash', str(target / 'run_batch.sh'), '5'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual((target / 'calls').read_text().splitlines(),
                             ['Gemini', 'qwen2.5-7b', 'gemma3', 'refresh', 'status'])
