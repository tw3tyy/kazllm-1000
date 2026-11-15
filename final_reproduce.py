"""Reproduce available evidence from validated logs without inference."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from kazllm import baselines, data, query, score
from pipeline import ROOT, load_inputs, overlap_audit, save_json


def coverage(config, prompts):
    return {spec['name']: len(query.read_validated(
        ROOT / 'outputs' / (spec['name'] + '.jsonl'), prompts, spec))
        for spec in config['models']}


def export_tables(result, qa, destination):
    import pandas as pd
    mt = [{'condition': name, **values} for name, values in result['main'].items()]
    tables = {
        'translation': mt,
        'paired_tests': [{'comparison': k, **v} for k, v in result['tests'].items()],
        'domain': [{'domain': k, **v} for k, v in result['domain'].items()],
        'qa_baselines': [{'baseline': k, **v} for k, v in qa.items()],
        'efficiency': [{'direction': k, **result['efficiency'][k]}
                       for k in ('en2kk', 'kk2en')],
        'pilot_sensitivity': [
            {'sample': 'all_complete_pairs', 'pairs': result['n_items_complete_pairs'], **result['gap_all']},
            {'sample': 'without_pilot', 'pairs': result['n_no_pilot'], **result['gap_no_pilot']}],
    }
    for name, rows in tables.items():
        frame = pd.DataFrame(rows)
        frame.to_csv(destination / (name + '.csv'), index=False)
        (destination / (name + '.md')).write_text(frame.to_markdown(index=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Validate logs and print remaining work')
    parser.add_argument('--output', type=Path, default=Path('final_results'), help='New output folder')
    args = parser.parse_args()
    with (ROOT / '.pipeline.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        config, items, prompts = load_inputs()
        counts = coverage(config, prompts)
        status = {'saved_benchmark_responses': counts, 'prompts_per_model': len(prompts),
                  'complete_model_comparison': all(n == len(prompts) for n in counts.values()),
                  'human_annotation': 'Requires independent human completion',
                  'independent_reproduction': 'Requires a person outside the team'}
        print(json.dumps(status, indent=2), flush=True)
        if args.check_only:
            return
        gemini = next(s for s in config['models'] if s['backend'] == 'gemini')
        rows = query.read_validated(ROOT / 'outputs' / (gemini['name'] + '.jsonl'), prompts, gemini)
        pairs = {}
        for row in rows:
            iid, condition = row['prompt_id'].split('|')
            pairs.setdefault(iid, set()).add(condition)
        if not any({'en2kk', 'kk2en'} <= conditions for conditions in pairs.values()):
            raise ValueError('No complete translation pairs available')
        target = args.output.resolve()
        if target.exists():
            raise ValueError('Output folder already exists. Select a new folder with --output.')
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.kazllm-reproduce-', dir=target.parent) as tmp:
            stage = Path(tmp)
            save_json(stage / 'data_audit.json', overlap_audit(items))
            environment = dict(os.environ, MPLCONFIGDIR=str(stage / '.matplotlib'))
            print('Recomputing translation scores, paired intervals, tests and four figures...', flush=True)
            subprocess.run([sys.executable, str(ROOT / 'assignment4/analyze_partial.py'),
                            str(ROOT), str(stage)], env=environment, check=True)
            fixed = stage / 'qa_fixed_dictionary.jsonl'
            random = stage / 'qa_random.jsonl'
            baselines.run_simple_baseline(prompts, fixed, majority_class='A')
            baselines.run_random_baseline(prompts, random, seed=config['seed'])
            qa = {}
            for name, path in [('Always A', fixed), ('Seeded random', random)]:
                outputs = {r['prompt_id']: r['output'] for r in data.read_jsonl(path)}
                qa[name] = score.score_qa(prompts, outputs)
            save_json(stage / 'qa_baselines.json', qa)
            result = json.loads((stage / 'results.json').read_text())
            export_tables(result, qa, stage)
            versions = {name: importlib.metadata.version(name)
                        for name in ('numpy', 'pandas', 'scipy', 'sacrebleu', 'matplotlib', 'tabulate', 'certifi')}
            (stage / 'requirements-used.txt').write_text(''.join(
                name + '==' + version + '\n' for name, version in versions.items()))
            inputs = [ROOT / 'config.json', ROOT / 'data/benchmark.jsonl', ROOT / 'pilot/benchmark.jsonl']
            inputs += sorted((ROOT / 'outputs').glob('*.jsonl'))
            status.update(python=platform.python_version(), versions=versions,
                          complete_translation_pairs=result['n_items_complete_pairs'],
                          files_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                        for p in inputs})
            save_json(stage / 'reproduction.json', status)
            # Only publish a directory once every calculation has completed.
            import shutil
            shutil.rmtree(stage / '.matplotlib', ignore_errors=True)
            stage.rename(target)
        print('Saved ' + str(target), flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit('STOP: ' + str(exc))
