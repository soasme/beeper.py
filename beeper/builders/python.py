# -*- coding: utf-8 -*-

import os

from ..utils import run

installer_tmpl_path = os.path.join(os.path.dirname(__file__), 'python_installer.sh')
with open(installer_tmpl_path) as f:
    INSTALLER = f.read()
del installer_tmpl_path

def build(conf):
    install_sh_file = os.path.join(os.environ['BUILD_DIR'], 'install.sh')
    with open(install_sh_file, 'wb') as f:
        f.write(INSTALLER % conf)
    run('chmod +x $BUILD_DIR/install.sh')
    run('rm -rf $DATA_DIR && mkdir -p $DATA_DIR')
    run('pip download -d $DATA_DIR virtualenv')
    run('cd $DATA_DIR && unzip `ls | grep virtualenv`')
    run('pip wheel --wheel-dir $DATA_DIR -r requirements.txt')
    run('cp $WORK_DIR/requirements.txt $DATA_DIR')
