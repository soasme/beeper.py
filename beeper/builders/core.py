# -*- coding: utf-8 -*-

import os
from contextlib import contextmanager
import tempfile

from ..utils import run

def build_for_language(conf):
    language = conf['language']
    if language == 'python':
        from .python import build as pybuild
        pybuild(conf)
    else:
        raise NotImplementedError('Not Supported Language ;(')


def prepare_dist(conf):
    run('rm -rf $DIST_DIR')
    run('mkdir -p $DIST_DIR')


def run_postbuild(conf):
    for script in conf['scripts']:
        run(script)


def dist_manifest(conf):
    for file in conf['manifest']:
        run('cd $WORK_DIR; cp -r %s $BUILD_DIR/' % file)


def make_tarball(conf):
    manifest_files = ' '.join(
        conf['manifest'] | set(['install.sh', '.beeper-data'])
    )

    archive_cmd = 'tar -c{z}f $DIST_DIR/{app}-{ver}.{suffix} {files}'.format(
        z='z' if conf['compress']else '',
        app=conf['application'],
        ver=conf['version'],
        suffix='tgz' if conf['compress'] else 'tar',
        files=manifest_files,
    )

    run('cd $BUILD_DIR;' + archive_cmd)

@contextmanager
def within_build_dir():
    try:
        os.environ['BUILD_DIR'] = tempfile.mkdtemp()
        yield
    except Exception as exc:
        run('rm -rf $BUILD_DIR')
        raise exc

def set_env(conf):
    os.environ['WORK_DIR'] = os.getcwd()
    os.environ['DATA_DIR'] = os.path.join(os.environ['BUILD_DIR'], '.beeper-data')
    os.environ['DIST_DIR'] = os.path.join(os.environ['WORK_DIR'], 'dist')
