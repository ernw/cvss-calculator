import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except:
        return None

def tooltips(target):
    root = os.path.join(os.path.dirname(__file__), 'tooltips')
    all_files = []
    for sub in ('base', 'temp', 'env'):
        files = os.listdir(os.path.join(root, sub))
        all_files.append((
                    os.path.join(target, sub),
                    [os.path.join('tooltips', sub, f) for f in files if f.endswith('.txt')]))
    return all_files

requires = [
        'wxpython',
        ]

setup(
    name="cvss_calculator",
    version="0.0.5",
    author="Timo Schmid",
    author_email="tschmid@ernw.de",
    description=("A CVSS 2 Calculator and Editor"),
    license="BSD",
    keywords="cvss calculator editor",
    url="",
    install_requires=requires,
    packages=[
        'cvsscalc',
        #'tests'
        ],
    package_data={
        'cvsscalc': ['tooltips/*/*.txt', '*.xrc', '*.png', '*.ico']
    },
    include_package_data=True,
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    data_files=[
        ('share/applications', ('freedesktop/cvsscalc.desktop',)),
        ('share/mime/application', ('freedesktop/x-extension-cvss-mime.xml',)),
    ],# + tooltips('share/cvsscalc'),
    entry_points={
        'gui_scripts': [
            'cvss-calculator = cvsscalc.wxgui:main'
        ]
    }
)
