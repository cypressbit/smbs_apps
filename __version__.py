"""Version and build information for smbs_apps.

The version number comes from pyproject.toml. The commit information comes from git when this
package is a real checkout (development), otherwise from _build_info.py, which deploys generate
because releases ship without .git:

    python3 __version__.py --write-build-info
"""
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _read_version():
    try:
        with open(os.path.join(_HERE, 'pyproject.toml'), encoding='utf-8') as f:
            match = re.search(r'^version\s*=\s*"([^"]+)"', f.read(), re.MULTILINE)
        if match:
            return match.group(1)
    except OSError:
        pass
    return '0.0.0'


def _git_commit_info():
    """(commit, date, message) from git, only if this directory is itself the checkout root.

    The top-level check keeps a server-wide repository (e.g. etckeeper in /etc) from being
    reported as this package's commit.
    """
    try:
        top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=_HERE, capture_output=True,
                             text=True, timeout=5)
        if top.returncode != 0 or os.path.realpath(top.stdout.strip()) != os.path.realpath(_HERE):
            return None
        log = subprocess.run(['git', 'log', '-1', '--format=%H%n%cs%n%s'], cwd=_HERE, capture_output=True,
                             text=True, timeout=5)
        if log.returncode != 0:
            return None
        commit, date, message = (log.stdout.split('\n') + ['', '', ''])[:3]
        return commit, date, message
    except (OSError, subprocess.SubprocessError):
        return None


def _commit_info():
    info = _git_commit_info()
    if info:
        return info
    try:
        from ._build_info import COMMIT as commit, COMMIT_DATE as date, COMMIT_MESSAGE as message
        return commit, date, message
    except ImportError:
        return 'unknown', '', ''


def write_build_info():
    """Write _build_info.py from git. Exits non-zero (and writes nothing) if git info is unavailable."""
    info = _git_commit_info()
    if not info:
        sys.stderr.write('smbs_apps: git commit info unavailable; _build_info.py not written\n')
        return 1
    commit, date, message = info
    with open(os.path.join(_HERE, '_build_info.py'), 'w', encoding='utf-8') as f:
        f.write('# Generated at deploy time by `python3 __version__.py --write-build-info`. Do not edit.\n')
        f.write('COMMIT = %r\nCOMMIT_DATE = %r\nCOMMIT_MESSAGE = %r\n' % (commit, date, message))
    print('smbs_apps: wrote _build_info.py for %s' % commit[:7])
    return 0


__version__ = _read_version()
VERSION = tuple(int(p) if p.isdigit() else p for p in __version__.split('.'))
COMMIT, COMMIT_DATE, COMMIT_MESSAGE = _commit_info()
COMMIT_SHORT = COMMIT[:7] if COMMIT != 'unknown' else COMMIT


if __name__ == '__main__':
    if '--write-build-info' in sys.argv:
        sys.exit(write_build_info())
    print('%s (%s, %s) %s' % (__version__, COMMIT_SHORT, COMMIT_DATE, COMMIT_MESSAGE))
