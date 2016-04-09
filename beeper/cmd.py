# -*- coding: utf-8 -*-

__version__ = '0.8.4'

import tempfile
import subprocess
import os
import sys
import click

from .builders.core import (
        within_build_dir,
        build_for_language,
        set_env,
        prepare_dist,
        build_for_language,
        run_postbuild,
        dist_manifest,
        make_target,
)
from .utils import parse_yaml, run

@click.group()
def main():
    pass

@main.command()
def version():
    click.secho(__version__, fg='green')

@main.command()
@click.option('--version', default='none')
@click.option('--format', default='tgz', type=click.Choice(['tar', 'tgz', 'tar.gz', 'zip']))
@click.option('--conf', default='./beeper.yml')
def build(version, format, conf):
    try:
        conf = parse_yaml(conf)
    except:
        click.secho(
            'Missing configuration. Did you put a `beeper.yml` file?',
            blink=True,
            fg='red'
        )
        sys.exit(1)

    conf.setdefault('language', 'python')
    conf.setdefault('python', 'python')
    conf.setdefault('postinstall', [])
    conf.setdefault('postinstall_commands', '\n'.join(conf.get('postinstall')))
    conf.setdefault('manifest', set())
    conf.setdefault('current_dir', run('pwd'))
    conf.setdefault('scripts', [])
    conf['postbuild'] = conf['scripts']
    conf['version'] = version
    conf['manifest'] = set(conf['manifest'])
    conf['format'] = format

    with within_build_dir():
        set_env(conf)
        prepare_dist(conf)
        build_for_language(conf)
        run_postbuild(conf)
        dist_manifest(conf)
        make_target(conf)

if __name__ == '__main__':
    main()
