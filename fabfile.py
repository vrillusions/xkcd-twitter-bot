# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from fabric.api import env, task, local


env.use_ssh_config = True


@task
def test():
    """runs through all tests"""
    local("flake8")
    local("nosetests")
