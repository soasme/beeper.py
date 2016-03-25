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

def test_compress():
    run('python beeper/cmd.py build --version 1 --conf tests/beeper.yml')
    assert os.path.exists('dist/test-1.tgz')

def test_no_compress():
    run('python beeper/cmd.py build --version 1 --no-compress --conf tests/beeper.yml')
    assert os.path.exists('dist/test-1.tar')

def test_version_default_is_none():
    run('python beeper/cmd.py build --no-compress --conf tests/beeper.yml')
    assert os.path.exists('dist/test-none.tar')

def test_file_included_in_manifest():
    run('python beeper/cmd.py build --version 1 --conf tests/beeper.yml')
    run('cd dist; tar xvzf test-1.tgz')
    run('ls dist')
    for filename in (
            'dist/.beeper-data/virtualenv.py',
            'dist/.beeper-data/requirements.txt',
            'dist/tests/hello.py',
            'dist/install.sh',
        ):
        assert os.path.exists(filename)

def test_install_venv():
    run('python beeper/cmd.py build --version 1 --conf tests/beeper.yml')
    run('cd dist; tar xvzf test-1.tgz')
    run('cd dist; ./install.sh')
    assert os.path.exists('dist/venv/bin/python')
    assert os.path.exists('dist/venv/bin/pip')
    assert os.path.exists('dist/venv/bin/py.test')
    with open('.beeper-data/MESSAGE') as f:
        assert f.read() == 'BEEPER\n'
