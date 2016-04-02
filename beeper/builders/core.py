# -*- coding: utf-8 -*-

def build(language, conf):
    if language == 'python':
        from .python import build as pybuild
        pybuild(conf)
    else:
        raise NotImplementedError('Not Supported Language ;(')
