#!/usr/bin/env python3
"""Run core tests and tests for each active plugin."""

import subprocess
from pathlib import Path
import generate_site


def main():
    # run core tests
    subprocess.check_call(['pytest', '-v', 'tests'])
    # run tests for each active plugin
    for name in generate_site.PLUGINS:
        plugin_tests = Path('plugins') / name / 'tests'
        if plugin_tests.is_dir():
            subprocess.check_call(['pytest', '-v', str(plugin_tests)])


if __name__ == '__main__':
    main()
