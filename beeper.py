# -*- coding: utf-8 -*-

__version__ = '0.5.0'

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

VIRTUALENV_TOOLS = '''
#!/usr/bin/env python
"""
    move-virtualenv
    ~~~~~~~~~~~~~~~
    A helper script that moves virtualenvs to a new location.
    It only supports POSIX based virtualenvs and Python 2 at the moment.
    :copyright: (c) 2012 by Fireteam Ltd.
    :license: BSD, see LICENSE for more details.
"""
import os
import re
import sys
import marshal
import optparse
import subprocess
from types import CodeType


ACTIVATION_SCRIPTS = [
    'activate',
    'activate.csh',
    'activate.fish'
]
_pybin_match = re.compile(r'^python\d+\.\d+$')
_activation_path_re = re.compile(r'^(?:set -gx |setenv |)VIRTUAL_ENV[ =]"(.*?)"\s*$')


def update_activation_script(script_filename, new_path):
    """Updates the paths for the activate shell scripts."""
    with open(script_filename) as f:
        lines = list(f)

    def _handle_sub(match):
        text = match.group()
        start, end = match.span()
        g_start, g_end = match.span(1)
        return text[:(g_start - start)] + new_path + text[(g_end - end):]

    changed = False
    for idx, line in enumerate(lines):
        new_line = _activation_path_re.sub(_handle_sub, line)
        if line != new_line:
            lines[idx] = new_line
            changed = True

    if changed:
        print 'A %s' % script_filename
        with open(script_filename, 'w') as f:
            f.writelines(lines)


def update_script(script_filename, new_path):
    """Updates shebang lines for actual scripts."""
    with open(script_filename) as f:
        lines = list(f)
    if not lines:
        return

    if not lines[0].startswith('#!'):
        return
    args = lines[0][2:].strip().split()
    if not args:
        return

    if not args[0].endswith('/bin/python') or \\
       '/usr/bin/env python' in args[0]:
        return

    new_bin = os.path.join(new_path, 'bin', 'python')
    if new_bin == args[0]:
        return

    args[0] = new_bin
    lines[0] = '#!%s\\n' % ' '.join(args)
    print 'S %s' % script_filename
    with open(script_filename, 'w') as f:
        f.writelines(lines)


def update_scripts(bin_dir, new_path):
    """Updates all scripts in the bin folder."""
    for fn in os.listdir(bin_dir):
        if fn in ACTIVATION_SCRIPTS:
            update_activation_script(os.path.join(bin_dir, fn), new_path)
        else:
            update_script(os.path.join(bin_dir, fn), new_path)


def update_pyc(filename, new_path):
    """Updates the filenames stored in pyc files."""
    with open(filename, 'rb') as f:
        magic = f.read(8)
        code = marshal.load(f)

    def _make_code(code, filename, consts):
        return CodeType(code.co_argcount, code.co_nlocals, code.co_stacksize,
                        code.co_flags, code.co_code, tuple(consts),
                        code.co_names, code.co_varnames, filename,
                        code.co_name, code.co_firstlineno, code.co_lnotab,
                        code.co_freevars, code.co_cellvars)

    def _process(code):
        new_filename = new_path
        consts = []
        for const in code.co_consts:
            if type(const) is CodeType:
                const = _process(const)
            consts.append(const)
        if new_path != code.co_filename or consts != list(code.co_consts):
            code = _make_code(code, new_path, consts)
        return code

    new_code = _process(code)

    if new_code is not code:
        print 'B %s' % filename
        with open(filename, 'wb') as f:
            f.write(magic)
            marshal.dump(new_code, f)


def update_pycs(lib_dir, new_path, lib_name):
    """Walks over all pyc files and updates their paths."""
    files = []

    def get_new_path(filename):
        filename = os.path.normpath(filename)
        if filename.startswith(lib_dir.rstrip('/') + '/'):
            return os.path.join(new_path, filename[len(lib_dir) + 1:])

    for dirname, dirnames, filenames in os.walk(lib_dir):
        for filename in filenames:
            if filename.endswith(('.pyc', '.pyo')):
                filename = os.path.join(dirname, filename)
                local_path = get_new_path(filename)
                if local_path is not None:
                    update_pyc(filename, local_path)


def update_local(base, new_path):
    """On some systems virtualenv seems to have something like a local
    directory with symlinks.  It appears to happen on debian systems and
    it causes havok if not updated.  So do that.
    """
    local_dir = os.path.join(base, 'local')
    if not os.path.isdir(local_dir):
        return

    for folder in 'bin', 'lib', 'include':
        filename = os.path.join(local_dir, folder)
        target = '../%s' % folder
        if os.path.islink(filename) and os.readlink(filename) != target:
            os.remove(filename)
            os.symlink('../%s' % folder, filename)
            print 'L %s' % filename


def update_paths(base, new_path):
    """Updates all paths in a virtualenv to a new one."""
    if new_path == 'auto':
        new_path = os.path.abspath(base)
    if not os.path.isabs(new_path):
        print 'error: %s is not an absolute path' % new_path
        return False

    bin_dir = os.path.join(base, 'bin')
    base_lib_dir = os.path.join(base, 'lib')
    lib_dir = None
    lib_name = None

    if os.path.isdir(base_lib_dir):
        for folder in os.listdir(base_lib_dir):
            if _pybin_match.match(folder):
                lib_name = folder
                lib_dir = os.path.join(base_lib_dir, folder)
                break

    if lib_dir is None or not os.path.isdir(bin_dir) \\
       or not os.path.isfile(os.path.join(bin_dir, 'python')):
        print 'error: %s does not refer to a python installation' % base
        return False

    update_scripts(bin_dir, new_path)
    update_pycs(lib_dir, new_path, lib_name)
    update_local(base, new_path)

    return True


def reinitialize_virtualenv(path):
    """Re-initializes a virtualenv."""
    lib_dir = os.path.join(path, 'lib')
    if not os.path.isdir(lib_dir):
        print 'error: %s is not a virtualenv bin folder' % path
        return False

    py_ver = None
    for filename in os.listdir(lib_dir):
        if _pybin_match.match(filename):
            py_ver = filename
            break

    if py_ver is None:
        print 'error: could not detect python version of virtualenv %s' % path
        return False

    sys_py_executable = subprocess.Popen(['which', py_ver],
        stdout=subprocess.PIPE).communicate()[0].strip()

    if not sys_py_executable:
        print 'error: could not find system version for expected python ' \\
            'version %s' % py_ver
        return False

    lib_dir = os.path.join(path, 'lib', py_ver)

    args = ['virtualenv', '-p', sys_py_executable]
    if not os.path.isfile(os.path.join(lib_dir,
            'no-global-site-packages.txt')):
        args.append('--system-site-packages')

    for filename in os.listdir(lib_dir):
        if filename.startswith('distribute-') and \\
           filename.endswith('.egg'):
            args.append('--distribute')

    new_env = {}
    for key, value in os.environ.items():
        if not key.startswith('VIRTUALENV_'):
            new_env[key] = value
    args.append(path)
    subprocess.Popen(args, env=new_env).wait()


def main():
    parser = optparse.OptionParser()
    parser.add_option('--reinitialize', action='store_true',
                      help='Updates the python installation '
                      'and reinitializes the virtualenv.')
    parser.add_option('--update-path', help='Update the path for all '
                      'required executables and helper files that are '
                      'supported to the new python prefix.  You can also set '
                      'this to "auto" for autodetection.')
    options, paths = parser.parse_args()
    if not paths:
        paths = ['.']

    rv = 0

    if options.reinitialize:
        for path in paths:
            reinitialize_virtualenv(path)
    if options.update_path:
        for path in paths:
            if not update_paths(path, options.update_path):
                rv = 1
    sys.exit(rv)


if __name__ == '__main__':
    main()
'''


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
    with open('venv/bin/virtualenv-tools', 'wb') as f:
        f.write(VIRTUALENV_TOOLS)

    for script in conf['scripts']:
        run(script)

    run('chmod +x install.sh venv/bin/virtualenv-tools')

    conf['manifest'].add('venv')
    conf['manifest'].add('install.sh')
    conf['manifest_files'] = ' '.join(conf['manifest'])
    run('tar -cf dist/%(application)s-%(version)s.tar %(manifest_files)s' % conf)
    run('rm -rf venv')
    run('ls dist/')

if __name__ == '__main__':
    cli()
