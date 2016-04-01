# -*- coding: utf-8 -*-

__version__ = '0.8.1'

import tempfile
import subprocess
import os
import sys
import click


def parse_yaml(file):
    try:
        import yaml
    except ImportError:
        click.abort('Have you installed PyYAML?')
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

    install_sh_file = os.path.join(os.environ['BUILD_DIR'], 'install.sh')
    with open(install_sh_file, 'wb') as f:
        f.write(INSTALLER % conf)

    run('chmod +x $BUILD_DIR/install.sh')

    run('rm -rf $DATA_DIR && mkdir -p $DATA_DIR')
    run('pip download -d $DATA_DIR virtualenv')
    run('cd $DATA_DIR && unzip `ls | grep virtualenv`')
    run('pip wheel --wheel-dir $DATA_DIR -r requirements.txt')
    run('cp $WORK_DIR/requirements.txt $DATA_DIR')

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
    run('ls $DIST_DIR')

if __name__ == '__main__':
    main()
