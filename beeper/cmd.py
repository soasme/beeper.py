# -*- coding: utf-8 -*-

__version__ = '0.6.1'

import subprocess
import os
import sys
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


installer_tmpl_path = os.path.join(os.path.dirname(__file__), 'installer.sh')
with open(installer_tmpl_path) as f:
    INSTALLER = f.read()


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
    click.secho("[command]: %s" % (wrapped_command), fg='green')
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
def main():
    pass

@main.command()
def version():
    click.secho(__version__, fg='green')

@main.command()
@click.option('--version')
@click.option('--conf', default='./beeper.yml')
def build(version, conf):
    try:
        conf = parse_yaml(conf)
    except:
        click.secho(
            'Missing configuration. Did you put a `beeper.yml` file?',
            blink=True,
            fg='red'
        )
        sys.exit(1)

    conf.setdefault('python', 'python')
    conf.setdefault('postinstall', [])
    conf.setdefault('postinstall_commands', '\n'.join(conf.get('postinstall')))
    conf.setdefault('manifest', set())
    conf.setdefault('current_dir', run('pwd'))
    conf.setdefault('scripts', [])
    conf['version'] = version
    conf['manifest'] = set(conf['manifest'])

    run('rm -rf dist/')
    run('mkdir -p dist/')

    with open('install.sh', 'wb') as f:
        f.write(INSTALLER % conf)


    run('chmod +x install.sh')

    run('rm -rf .beeper-data && mkdir -p .beeper-data')
    run('pip download -d .beeper-data/ virtualenv')
    run('cd .beeper-data && unzip `ls | grep virtualenv`')
    run('pip wheel --wheel-dir .beeper-data/ -r requirements.txt')
    run('cp requirements.txt .beeper-data/')

    for script in conf['scripts']:
        run(script)

    #conf['manifest'].add('venv')
    conf['manifest'].add('install.sh')
    conf['manifest'].add('.beeper-data')
    conf['manifest_files'] = ' '.join(conf['manifest'])
    run('tar -cf dist/%(application)s-%(version)s.tar %(manifest_files)s' % conf)
    run('rm -rf venv')
    run('ls dist/')

if __name__ == '__main__':
    main()
