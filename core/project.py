"""Small shared helpers for external video projects."""
import hashlib
import json
import os
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(f'{path.name}.{os.getpid()}.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def external(path):
    result = Path(path).expanduser().resolve()
    if result == REPO or REPO in result.parents:
        raise ValueError('Video projects and outputs must live outside the Agent repository')
    return result


def load(project):
    return read_json(Path(project) / 'project.json')


def save(project, value):
    write_json(Path(project) / 'project.json', value)


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)
    ], text=True))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def project_lock(project):
    target = Path(project) / '.semantic.lock'
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError('Project is busy: .semantic.lock exists') from error
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump({'pid': os.getpid(), 'started': now()}, stream)
        yield
    finally:
        target.unlink(missing_ok=True)
