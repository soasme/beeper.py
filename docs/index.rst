.. beeper documentation master file, created by
   sphinx-quickstart on Sat Apr  2 06:53:15 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to beeper's documentation!
==================================

Beeper is a tool for Python that simplified distribution on Unix servers. 
It defines a compact and self-contained way for offline installation.
The aim of beeper is to pre-download all dependencies and pre-compile all assets before deployment.

The principles of Beeper are:

* No build infrastructure on production server;
* No network call on production server;
* No vague version of dependencies;

Beeper need you to have

* `wheel`, `virtualenv`, `pip` installed;
* normally seen Unix command: `unzip`, `tar`, `grep`;
* `requirements.txt` in root of your project.

You can get the tool directly from PyPI::

    $ pip install beeper

To create a beeper distribution you need to define build information and run build command.

Beeper parse a YAML file, default `beeper.yml`, to read build information. For example, a Flask example might be like this::

    application: example
    manifest:
      - app.py

Running build command is simple::

    $ beeper build --version 1

If you use build project from a git repo, you can always get version from a git log command::

    $ beeper build --version `git log -1 --format=%h`

Once this finishes, it will have created a tar file generated in `dist` folder with all dependencies and an installation script. You can then distribute this file to remote servers and install it::

    $ scp dist/example-1.tgz deploy@server:/var/www/example/example-1.tgz
    $ ssh deploy@server
    deploy $ cd /var/www/example/
    deploy $ tar -xzf example-1.tgz
    deploy $ ./install.sh




.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

