# -*- coding: utf-8 -*-

__version__ = '0.4.1'

import subprocess, os, sys
import os
import click


class cd(object):
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def parse_yaml(file):
    import yaml
    with open(file, 'rb') as f:
        return yaml.load(f.read())


VENV_TOOLS_URL = 'https://raw.githubusercontent.com/fireteam/virtualenv-tools/master/virtualenv_tools.py'
INSTALLER = """
#!/bin/bash
# This script installs the bundled wheel distribution of %(application)s into
# a provided path where it will end up in a new virtualenv.

set -e

HERE="$(cd "$(dirname .)"; pwd)"
VIRTUAL_ENV=$HERE/venv
PY="python"

# Ensure Python exists
command -v "$PY" &> /dev/null || error "Given python interpreter not found ($PY)"

# Relocate env
rm -rf $HERE/venv/bin/python*
$PY $HERE/venv/bin/virtualenv-tools --reinitialize $HERE/venv
$PY $HERE/venv/bin/virtualenv-tools --update-path $HERE/venv venv

# Potential post installation
cd "$HERE"
. "$VIRTUAL_ENV/bin/activate"

%(postinstall_commands)s

echo "Done."
"""


class _AttributeString(str):
    """
    Simple string subclass to allow arbitrary attribute access.
    """
    @property
    def stdout(self):
        return str(self)


class _AttributeList(list):
    """
    Like _AttributeString, but for lists.
    """
    pass

def run(command, capture=False, shell=None):
    given_command = command
    # Apply cd(), path() etc
    ## with_env = _prefix_env_vars(command, local=True)
    #wrapped_command = _prefix_commands(with_env, 'local')
    wrapped_command = given_command
    print("[command]: %s" % (wrapped_command))
    #print("[localhost] local: " + given_command)
    # Tie in to global output controls as best we can; our capture argument
    # takes precedence over the output settings.
    dev_null = None
    if capture:
        out_stream = subprocess.PIPE
        err_stream = subprocess.PIPE
    else:
        out_stream = sys.stdout
        err_stream = sys.stderr
    try:
        cmd_arg = [wrapped_command]
        p = subprocess.Popen(cmd_arg, shell=True, stdout=out_stream,
                             stderr=err_stream, executable=shell)
        (stdout, stderr) = p.communicate()
    finally:
        if dev_null is not None:
            dev_null.close()
    # Handle error condition (deal with stdout being None, too)
    out = _AttributeString(stdout.strip() if stdout else "")
    err = _AttributeString(stderr.strip() if stderr else "")
    out.command = given_command
    out.real_command = wrapped_command
    out.failed = False
    out.return_code = p.returncode
    out.stderr = err
    if p.returncode != 0:
        out.failed = True
        msg = "local() encountered an error (return code %s) while executing '%s'" % (p.returncode, command)
        msg += '\n'
        msg += out
        msg += '\n'
        msg += err
        raise Exception(msg)
    out.succeeded = not out.failed
    # If we were capturing, this will be a string; otherwise it will be None.
    return out


@click.group()
def cli():
    pass

@cli.command()
def version():
    print(__version__)

@cli.command()
@click.option('--version')
@click.option('--conf', default='./beeper.yml')
def build(version, conf):
    try:
        conf = parse_yaml(conf)
    except:
        print('Missing configuration. Did you put a `beeper.yml` file?')
        conf = {}

    conf.setdefault('python', 'python')
    conf.setdefault('postinstall', [])
    conf.setdefault('postinstall_commands', '\n'.join(conf.get('postinstall')))
    conf.setdefault('manifest', set())
    conf.setdefault('current_dir', run('pwd'))
    conf.setdefault('scripts', [])
    conf['version'] = version
    conf['manifest'] = set(conf['manifest'])

    run('rm -rf venv/ dist/')
    run('mkdir -p dist/')

    run('mkdir -p ./venv')
    run('virtualenv --distribute ./venv')
    run('./venv/bin/pip install -U pip virtualenv-tools')
    run('./venv/bin/pip install -r requirements.txt')

    with open('install.sh', 'wb') as f:
        f.write(INSTALLER % conf)

    for script in conf['scripts']:
        run(script)

    conf['manifest'].add('venv')
    conf['manifest'].add('install.sh')
    conf['manifest_files'] = ' '.join(conf['manifest'])
    run('tar -cf dist/%(application)s-%(version)s.tar %(manifest_files)s' % conf)
    run('rm -rf venv')
    run('ls dist/')

if __name__ == '__main__':
    cli()
