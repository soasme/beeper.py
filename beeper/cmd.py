# -*- coding: utf-8 -*-

__version__ = '0.8.3'

import tempfile
import subprocess
import os
import sys
import click

from .builders.core import build as build_for_language
from .utils import parse_yaml, run

@click.group()
def main():
    pass

@main.command()
def version():
    click.secho(__version__, fg='green')

@main.command()
@click.option('--version', default='none')
@click.option('--compress/--no-compress', default=True)
@click.option('--conf', default='./beeper.yml')
def build(version, compress, conf):
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
    conf['version'] = version
    conf['manifest'] = set(conf['manifest'])

    os.environ['WORK_DIR'] = os.getcwd()
    os.environ['BUILD_DIR'] = tempfile.mkdtemp()
    os.environ['DATA_DIR'] = os.path.join(os.environ['BUILD_DIR'], '.beeper-data')
    os.environ['DIST_DIR'] = os.path.join(os.environ['WORK_DIR'], 'dist')

    run('rm -rf $DIST_DIR')
    run('mkdir -p $DIST_DIR')


    build_for_language(conf['language'], conf)

    for script in conf['scripts']:
        run(script)

    for file in conf['manifest']:
        run('cd $WORK_DIR; cp -r %s $BUILD_DIR/' % file)

    manifest_files = ' '.join(
        conf['manifest'] | set(['install.sh', '.beeper-data'])
    )

    archive_cmd = 'tar -c{z}f $DIST_DIR/{app}-{ver}.{suffix} {files}'.format(
        z='z' if compress else '',
        app=conf['application'],
        ver=conf['version'],
        suffix='tgz' if compress else 'tar',
        files=manifest_files,
    )
    run('cd $BUILD_DIR;' + archive_cmd)
    run('rm -rf $BUILD_DIR')
    run('ls $DIST_DIR')

if __name__ == '__main__':
    main()
