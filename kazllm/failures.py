"""Durable records for rejected service responses, separate from successful outputs."""
import json
import os
from pathlib import Path


def path_for(output_path):
    path = Path(output_path)
    return path.parent / 'failures' / path.name


def checked_records(output_path, prompts, spec):
    """Offline validation of failure evidence for progress displays."""
    from .query import make_payload
    path = path_for(output_path)
    if not path.exists() or not path.stat().st_size:
        return {}
    first = json.loads(path.read_text(encoding='utf-8').splitlines()[0])
    return read(output_path, prompts, spec, make_payload, first['fingerprint'])


def read(output_path, prompts, spec, payload, fingerprint):
    from .query import digest
    path = path_for(output_path)
    if not path.exists():
        return {}
    expected = {row['prompt_id']: row for row in prompts}
    records = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        pid = record['prompt_id']
        if pid not in expected or record.get('status') != 'failed':
            raise ValueError('Invalid failure record ID or status')
        if record.get('requested_model') != spec['id'] or record.get('fingerprint') != fingerprint:
            raise ValueError('Failure record model/runtime changed')
        if record.get('prompt_sha256') != digest(expected[pid]['prompt']) or record.get('request_sha256') != digest(payload(expected[pid], spec)):
            raise ValueError('Failure record prompt or settings changed')
        if record.get('response_sha256') != digest(record['response']):
            raise ValueError('Failure response checksum changed')
        records[pid] = record
    return records


def append(output_path, row, spec, payload, response, reason, fingerprint):
    from .query import digest, now
    path = path_for(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {'status': 'failed', 'prompt_id': row['prompt_id'], 'requested_model': spec['id'],
              'prompt_sha256': digest(row['prompt']), 'request_sha256': digest(payload),
              'fingerprint': fingerprint, 'time': now(), 'reason': reason,
              'response': response, 'response_sha256': digest(response)}
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
