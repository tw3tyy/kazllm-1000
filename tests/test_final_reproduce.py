import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import demo
import final_reproduce
from kazllm import gemini_query, query
from pipeline import load_inputs


class ReproductionTests(unittest.TestCase):
    def test_check_only_requires_no_model_request(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(final_reproduce, 'ROOT', Path(directory)), \
                    patch('sys.argv', ['final_reproduce.py', '--check-only']), \
                    patch.object(query, 'request') as local, \
                    patch.object(gemini_query, 'request') as remote, \
                    redirect_stdout(io.StringIO()) as output:
                final_reproduce.main()
            local.assert_not_called()
            remote.assert_not_called()
            self.assertIn('"gemini-3.5-flash-lite": 0', output.getvalue())
            self.assertFalse((Path(directory) / 'final_results').exists())

    def test_smoke_records_never_enter_preliminary_scores(self):
        config, _, prompts = load_inputs()
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(demo, 'ROOT', Path(directory)), \
                    redirect_stdout(io.StringIO()) as output:
                demo.preliminary(config, prompts)
            self.assertIn('gemini-3.5-flash-lite: Pending', output.getvalue())
            self.assertNotIn('chrF2 EN', output.getvalue())


if __name__ == '__main__':
    unittest.main()
