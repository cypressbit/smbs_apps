"""
Section patterns: curated, ready-made sections (hero, features, FAQ, contact…)
stored as JSON in smbs_pages/patterns/. The editor's "Add section" palette
offers them, and the AI builds pages only from them, so generated layouts stay
consistent and responsive.

Each file is {"key", "name", "category", "description", "ai_hint",
"capability", "section"}, where "section" is a page-document section without
node ids. `instantiate()` returns a copy with fresh ids, ready to insert.
"""
import copy
import functools
import json
from pathlib import Path

from smbs_apps.smbs_pages import documents


PATTERNS_DIR = Path(__file__).parent / 'patterns'
METADATA_KEYS = ('key', 'name', 'category', 'description', 'ai_hint', 'capability')


class UnknownPattern(KeyError):
    pass


@functools.cache
def _load():
    patterns = {}
    for path in sorted(PATTERNS_DIR.glob('*.json')):
        with open(path) as f:
            data = json.load(f)
        if data.get('key') != path.stem:
            raise ValueError(f'{path.name}: key {data.get("key")!r} must match the file name')
        patterns[data['key']] = data
    return patterns


def _enabled(pattern, capabilities):
    return capabilities is None or not pattern.get('capability') or pattern['capability'] in capabilities


def list_patterns(capabilities=None):
    """Pattern metadata (without the section), filtered by the site's capabilities."""
    return [{key: pattern.get(key) for key in METADATA_KEYS}
            for pattern in _load().values() if _enabled(pattern, capabilities)]


def get_pattern(key):
    try:
        return copy.deepcopy(_load()[key])
    except KeyError:
        raise UnknownPattern(key)


def instantiate(key):
    """A deep copy of the pattern's section with fresh node ids, tagged with its pattern key."""
    section = get_pattern(key)['section']
    section['pattern'] = key
    return documents.reassign_ids(section, 'section')


def catalog(capabilities=None):
    """Patterns including their sections, for the AI's system prompt."""
    return [get_pattern(pattern['key']) for pattern in list_patterns(capabilities)]
