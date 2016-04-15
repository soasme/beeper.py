# -*- coding: utf-8 -*-

import os

import pytest
import click
from beeper.cmd import build, main, run

from click.testing import CliRunner

import pytest

def setup_function(f):
    if os.path.exists('dist/'):
        run('rm -rf dist/')

def teardown_function(f):
    if os.path.exists('dist/'):
        run('rm -rf dist/')

def run_beeper(command='build', options='', **kwargs):
    return run('beeper %s %s --conf %s' % (
        command, options, os.path.join(os.getcwd(), 'tests/beeper.yml')), **kwargs)

def test_make_tgz():
    run_beeper('build', '--version 1')
    assert os.path.exists('dist/test-1.tgz')

def test_stat():
    run_beeper('build', '--version 1')
    output = run_beeper('stat', '--version 1', capture=True)
    assert output.splitlines()[-1] == 'test-1.tgz'

def test_make_tar():
    run_beeper('build', '--version 1 --format tar')
    assert os.path.exists('dist/test-1.tar')

def test_make_zip():
    run_beeper('build', '--version 1 --format zip')
    assert os.path.exists('dist/test-1.zip')

def test_version_default_is_none():
    run_beeper()
    assert os.path.exists('dist/test-none.tgz')

def test_file_included_in_manifest():
    run_beeper('build', '--version 1')
    run('cd dist; tar xvzf test-1.tgz')
    run('ls dist')
    for filename in (
            'dist/.beeper-data/virtualenv.py',
            'dist/.beeper-data/requirements.txt',
            'dist/main.py',
            'dist/install.sh',
        ):
        assert os.path.exists(filename)

def test_install_venv():
    run_beeper('build', '--version 1')
    run('cd dist; tar xvzf test-1.tgz')
    run('cd dist; ./install.sh')
    assert os.path.exists('dist/venv/bin/python')
    assert os.path.exists('dist/venv/bin/pip')
    assert os.path.exists('dist/venv/bin/py.test')
    with open('dist/MESSAGE') as f:
        assert f.read() == 'BEEPER\n'
