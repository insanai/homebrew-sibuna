#!/usr/bin/env python3
"""Import the formula attached to an upstream Sibuna release, after checking it.

The formula installs the release archives that the upstream release workflow built and
verified. Every archive URL and checksum in the formula must match the release's
SHA256SUMS and GitHub's own asset digests before the formula is written.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

REPOSITORY = 'insanai/sibuna'
TAG = re.compile(r'v\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?')
ARCHIVES = ('sibuna-macos-arm64.tar.gz', 'sibuna-macos-amd64.tar.gz',
            'sibuna-linux-arm64.tar.gz', 'sibuna-linux-amd64.tar.gz')


def release_for(tag):
    """Returns the release named `tag`, or the newest published release (prereleases too)."""
    if tag is None:
        releases = json.loads(subprocess.check_output(
            ['gh', 'api', f'repos/{REPOSITORY}/releases?per_page=20'], text=True))
        published = [r for r in releases if not r['draft']]
        if not published:
            raise ValueError('no published release')
        return published[0]
    if not TAG.fullmatch(tag):
        raise ValueError('a vMAJOR.MINOR.PATCH tag, optionally with a pre-release suffix, is required')
    return json.loads(subprocess.check_output(
        ['gh', 'api', f'repos/{REPOSITORY}/releases/tags/{tag}'], text=True))


def checksums_of(text):
    """Parses SHA256SUMS: one `<sha256>  <name>` line per file, no duplicates."""
    sums = {}
    for line in text.splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([^/\\]+)', line)
        if not match or match[2] in sums:
            raise ValueError('invalid or duplicate release checksum entry')
        sums[match[2]] = match[1]
    return sums


def check_formula(text, tag, sums):
    """Raises unless the formula names this release's archives with their checksums."""
    version = tag[1:]
    if not text.startswith('# Generated from') or 'class Sibuna < Formula\n' not in text:
        raise ValueError('not an upstream Sibuna formula')
    if f'  version "{version}"' not in text or '  license "LGPL-3.0-or-later"' not in text:
        raise ValueError('formula version or license mismatch')
    for name in ARCHIVES:
        url = f'https://github.com/{REPOSITORY}/releases/download/{tag}/{name}'
        if f'url "{url}"\n      sha256 "{sums[name]}"' not in text:
            raise ValueError(f'formula URL or checksum mismatch: {name}')


def synchronize(tag=None, destination=Path('Formula/sibuna.rb')):
    release = release_for(tag)
    tag = release['tag_name']
    if release['draft'] or not TAG.fullmatch(tag):
        raise ValueError('only published application releases may update the tap')
    assets = {a['name']: a for a in release['assets']}
    for name in ('sibuna.rb', 'SHA256SUMS') + ARCHIVES:
        if name not in assets:
            raise ValueError(f'missing release asset: {name}')
    with tempfile.TemporaryDirectory() as scratch:
        subprocess.run(['gh', 'release', 'download', tag, '--repo', REPOSITORY,
                        '--pattern', 'sibuna.rb', '--pattern', 'SHA256SUMS',
                        '--dir', scratch], check=True)
        sums = checksums_of((Path(scratch) / 'SHA256SUMS').read_text())
        for name in ('sibuna.rb',) + ARCHIVES:
            digest = sums.get(name)
            if digest is None or assets[name].get('digest') != 'sha256:' + digest:
                raise ValueError(f'GitHub asset digest/checksum mismatch: {name}')
        formula = (Path(scratch) / 'sibuna.rb').read_bytes()
        if hashlib.sha256(formula).hexdigest() != sums['sibuna.rb']:
            raise ValueError('formula checksum mismatch')
        text = formula.decode('utf-8')
        check_formula(text, tag, sums)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(formula)
        print(f'Imported the verified formula for {tag}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', help='published upstream tag; default: the newest release')
    args = parser.parse_args()
    synchronize(args.tag)
