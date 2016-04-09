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


def make_tarball(conf, compress, suffix):
    manifest_files = ' '.join(
        conf['manifest'] | set(['install.sh', '.beeper-data'])
    )

    archive_cmd = 'tar -c{z}f $DIST_DIR/{app}-{ver}.{suffix} {files}'.format(
        z='z' if compress else '',
        app=conf['application'],
        ver=conf['version'],
        suffix=suffix,
        files=manifest_files,
    )

    run('cd $BUILD_DIR; ' + archive_cmd)

def make_zip(conf):
    manifest_files = ' '.join(
        conf['manifest'] | set(['install.sh', '.beeper-data'])
    )
    archive_cmd = 'zip -r $DIST_DIR/{app}-{ver}.zip {files}'.format(
        app=conf['application'],
        ver=conf['version'],
        files=manifest_files,
    )
    run('cd $BUILD_DIR; ' + archive_cmd)

def make_target(conf):
    if conf['format'] == 'tar':
        make_tarball(conf, compress=False, suffix='tar')
    elif conf['format'] == 'tgz':
        make_tarball(conf, compress=True, suffix='tgz')
    elif conf['format'] == 'tar.gz':
        make_tarball(conf, compress=True, suffix='tar.gz')
    elif conf['format'] == 'zip':
        make_zip(conf)
    else:
        raise Exception('Unknown target format: %s' % conf['format'])

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
