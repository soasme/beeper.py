# -*- coding: utf-8 -*-

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
