#!/usr/bin/env python
import os
import shutil
import tempfile
import subprocess
import sys
from distutils.command.install import INSTALL_SCHEMES
from string import Template

if sys.version_info[0] < 3:
    from urllib2 import urlopen
else:
    from urllib.request import urlopen

def tempdir(func):
    def _tempdir(*args, **kwargs):
        test_dir = tempfile.mkdtemp()
        old_dir = os.getcwd()
        os.chdir(test_dir)
        try:
            return func(*args, **kwargs)
        finally:
            os.chdir(old_dir)
            shutil.rmtree(test_dir)
    return _tempdir

SIMPLE_BUILDOUT = """\
[buildout]

parts = eggs

[eggs]
recipe = zc.recipe.egg

eggs =
    extensions
"""

BOOTSTRAP = 'http://python-distribute.org/bootstrap.py'
PYVER = sys.version.split()[0][:3]


_VARS = {'base': '.',
         'py_version_short': PYVER}

if sys.platform == 'win32':
    PURELIB = INSTALL_SCHEMES['nt']['purelib']
else:
    PURELIB = INSTALL_SCHEMES['unix_prefix']['purelib']


@tempdir
def test_virtualenv():
    """virtualenv with distribute"""
    purelib = os.path.abspath(Template(PURELIB).substitute(**_VARS))
    os.system('virtualenv --no-site-packages . --distribute')
    os.system('bin/easy_install -q distribute==dev')
    # linux specific
    site_pkg = os.listdir(purelib)
    site_pkg.sort()
    assert 'distribute' in site_pkg[0]
    easy_install = os.path.join(purelib, 'easy-install.pth')
    with open(easy_install) as f:
        res = f.read()
    assert 'distribute' in res
    assert 'setuptools' not in res

@tempdir
def test_full():
    """virtualenv + pip + buildout"""
    os.system('virtualenv --no-site-packages .')
    os.system('bin/easy_install -q distribute==dev')
    os.system('bin/easy_install -qU distribute==dev')
    os.system('bin/easy_install -q pip')
    os.system('bin/pip install -q zc.buildout')
    with open('buildout.cfg', 'w') as f:
        f.write(SIMPLE_BUILDOUT)

    with open('bootstrap.py', 'w') as f:
        f.write(urlopen(BOOTSTRAP).read())

    os.system('bin/python bootstrap.py --distribute')
    os.system('bin/buildout -q')
    eggs = os.listdir('eggs')
    eggs.sort()
    assert len(eggs) == 3
    assert eggs[0].startswith('distribute')
    assert eggs[1:] == ['extensions-0.3-py2.6.egg',
                        'zc.recipe.egg-1.2.2-py2.6.egg']


if __name__ == '__main__':
    test_virtualenv()
    test_full()

