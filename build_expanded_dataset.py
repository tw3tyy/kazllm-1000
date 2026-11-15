"""Build an isolated 1000 MT / 1000 QA / 1000 templated-probe study."""
import hashlib
import json
from pathlib import Path
import random
import tarfile
from zipfile import ZipFile

from kazllm import data, prompts, query
from pipeline import ROOT, save_json


SUBJECTS = [('student', 'студент'), ('teacher', 'мұғалім'), ('doctor', 'дәрігер'),
            ('child', 'бала'), ('scientist', 'ғалым'), ('engineer', 'инженер'),
            ('artist', 'суретші'), ('writer', 'жазушы'), ('driver', 'жүргізуші'),
            ('athlete', 'спортшы')]
PLACES = [('at school', 'мектепте'), ('at home', 'үйде'), ('in the city', 'қалада'),
          ('at the hospital', 'ауруханада'), ('at the university', 'университетте'),
          ('in the office', 'кеңседе'), ('in the library', 'кітапханада'),
          ('in the museum', 'мұражайда'), ('in the park', 'саябақта'),
          ('in the shop', 'дүкенде')]
PATTERNS = [
    ('location', 'The {s} is {p}.', '{k} {l}.'),
    ('past', 'The {s} was {p} yesterday.', 'Кеше {k} {l} болды.'),
    ('future', 'The {s} will be {p} tomorrow.', 'Ертең {k} {l} болады.'),
    ('negation', 'The {s} is not {p}.', '{k} {l} емес.'),
    ('past_negation', 'The {s} was not {p} yesterday.', 'Кеше {k} {l} болған жоқ.'),
    ('future_negation', 'The {s} will not be {p} tomorrow.', 'Ертең {k} {l} болмайды.'),
    ('work', 'The {s} works {p}.', '{k} {l} жұмыс істейді.'),
    ('reading', 'The {s} reads a book {p}.', '{k} {l} кітап оқиды.'),
    ('today', 'The {s} is {p} today.', 'Бүгін {k} {l}.'),
    ('question', 'Is the {s} {p}?', '{k} {l} {q}?'),
]


def build(source_dir):
    if (ROOT / 'data/benchmark.jsonl').exists():
        raise ValueError('Benchmark already frozen; create a separate study to rebuild it')
    rng = random.Random(42)
    mt = []
    with tarfile.open(source_dir / 'flores.tar.gz') as archive:
        for split in ('dev', 'devtest'):
            languages = []
            for lang in ('eng_Latn', 'kaz_Cyrl'):
                member = archive.getmember(f'./flores200_dataset/{split}/{lang}.{split}')
                languages.append(archive.extractfile(member).read().decode().splitlines())
            if len(languages[0]) != len(languages[1]):
                raise ValueError('FLORES source files are not aligned')
            for index, (en, kk) in enumerate(zip(*languages)):
                mt.append({'item_id': f'expanded_mt_{split}_{index:05d}', 'task': 'mt',
                           'source': 'FLORES-200', 'domain': split, 'en': en, 'kk': kk})
    unique = {}
    for item in mt:
        unique.setdefault((item['en'], item['kk']), item)
    mt = list(unique.values())[:1000]
    with ZipFile(source_dir / 'belebele.zip') as archive:
        languages = []
        for lang in ('eng_Latn', 'kaz_Cyrl'):
            records = [json.loads(line) for line in archive.read('Belebele/' + lang + '.jsonl').decode().splitlines() if line.strip()]
            keyed = {(r['link'], int(r['question_number'])): r for r in records}
            assert len(keyed) == len(records) == 900
            languages.append(keyed)
    assert set(languages[0]) == set(languages[1])
    qa = []
    for index, key in enumerate(sorted(languages[0])):
        item = {'item_id': f'expanded_belebele_{index:04d}', 'task': 'qa', 'source': 'Belebele', 'domain': 'belebele'}
        for lang, records in zip(('en', 'kk'), languages):
            row = records[key]
            item[lang] = {'passage': row['flores_passage'], 'question': row['question'],
                          'options': [row[f'mc_answer{i}'] for i in range(1, 5)],
                          'gold': 'ABCD'[int(row['correct_answer_num']) - 1]}
        qa.append(item)
    names = [('Aigerim', 'Айгерім'), ('Dana', 'Дана'), ('Aruzhan', 'Аружан'),
             ('Amina', 'Әмина'), ('Madina', 'Мәдина'), ('Asel', 'Әсел'),
             ('Aliya', 'Әлия'), ('Dinara', 'Динара'), ('Ainur', 'Айнұр'), ('Sara', 'Сара')]
    for name_en, name_kk in names:
        for count in range(3, 13):
            index = len(qa) - 900
            options = [str(count - 1), str(count), str(count + 1), str(count + 2)]
            correct = options.pop(0)
            position = index % 4
            rng.shuffle(options)
            options.insert(position, correct)
            qa.append({'item_id': f'expanded_custom_qa_{index:03d}', 'task': 'qa',
                       'source': 'team_constructed', 'domain': 'constructed_reading_arithmetic',
                       'review_status': 'pending_human_review',
                       'en': {'passage': f'{name_en} has {count} books. She gives one book to a friend. She keeps the remaining books at home.',
                              'question': f'How many books does {name_en} have after giving one away?',
                              'options': options, 'gold': 'ABCD'[position]},
                       'kk': {'passage': f'{name_kk} есімді оқушыда {count} кітап бар. Ол досына бір кітап береді. Қалған кітаптарын үйде сақтайды.',
                              'question': 'Бір кітап бергеннен кейін оқушыда неше кітап қалады?',
                              'options': options, 'gold': 'ABCD'[position]}})
    probes = []
    for family, en_template, kk_template in PATTERNS:
        for en_subject, kk_subject in SUBJECTS:
            for en_place, kk_place in PLACES:
                probes.append({'item_id': f'expanded_probe_{len(probes):04d}', 'task': 'probe',
                               'source': 'team_templates', 'domain': family,
                               'review_status': 'pending_human_review',
                               'en': en_template.format(s=en_subject, p=en_place),
                               'kk': kk_template.format(k=kk_subject, l=kk_place, q="ма" if kk_place[-1] in "аыоұ" else "ме").capitalize()})
    assert len(mt) == len(qa) == len(probes) == 1000
    items = [item for triple in zip(mt, qa, probes) for item in triple]
    assert len({r['item_id'] for r in items}) == 3000
    data.write_jsonl(ROOT / 'data/benchmark.jsonl', items)
    # This new study has no pilot. Historical study remains a separate archive.
    data.write_jsonl(ROOT / 'pilot/benchmark.jsonl', [])
    generated = prompts.build_prompts(items)
    assert len(generated) == 5000
    save_json(ROOT / 'data/input_manifest.json', {
        'sha256': {name: query.file_hash(ROOT / name) for name in ('data/benchmark.jsonl', 'pilot/benchmark.jsonl')},
        'generated_prompts_sha256': query.digest(generated),
        'provenance_note': '900 published Belebele questions plus 100 constructed reading/arithmetic questions; 1000 templated probes require human review.'})
    save_json(ROOT / 'data/expanded_sources.json', {
        'source_sha256': {name: hashlib.sha256((source_dir / name).read_bytes()).hexdigest()
                          for name in ('belebele.zip', 'flores.tar.gz')},
        'mt_source': 'https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz',
        'qa_source': 'https://dl.fbaipublicfiles.com/belebele/Belebele.zip',
        'custom_qa_note': '100 templated reading/arithmetic items. Report separately from Belebele.',
        'probe_note': '10 templates times 10 subjects times 10 places. Template variants are correlated.',
        'review_status': '1100 constructed items require independent language and answer review.'})
    save_json(ROOT / 'results/status.json', {'llm_runs_complete': False,
        'saved_benchmark_responses': {s['name']: 0 for s in json.loads((ROOT / 'config.json').read_text())['models']},
        'prompts_per_model': 5000, 'nllb': 'pending', 'annotation': 'pending'})
    print('Frozen 1000 MT + 1000 QA + 1000 probes; 5000 prompts per model.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source_dir', type=Path, help='Folder containing the two official source archives')
    build(parser.parse_args().source_dir)
