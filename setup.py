from setuptools import setup, find_packages
from setuptools.extension import Extension

USE_CYTHON = True

try:
    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
except ImportError:
    USE_CYTHON = False

def cython_or_c(ext):
    if USE_CYTHON:
        return cythonize(ext)
    else:
        for e in ext:        
            for i, j in enumerate(e.sources):
                e.sources[i] = j.replace('.pyx', '.c')
                
            # Enable creating Sphinx documentation
            ext.cython_directives = {
                'embedsignature': True,
                'binding': True,
                'linetrace': True
            }
        return ext
    
extensions = cython_or_c([
    Extension(
        "pgreaper.core.table",
        sources=["pgreaper/core/table.pyx"],
    ),
    Extension(
        "pgreaper.io.json_tools",
        sources=["pgreaper/io/json_tools.pyx"],
        language="c++",
    )
])

setup(
    name='pgreaper',
    cmdclass={'build_ext': build_ext},
    version='1.0.0a2',
    description='A simple, flexible, and robust wrapper around the Postgres COPY command. Supports loading CSV/JSON files and Python objects with automatic schema inference.',
    long_description='A simple, flexible, and robust wrapper around the Postgres COPY command. Supports loading CSV/JSON files and Python objects with automatic schema inference.',
    url='https://github.com/vincentlaucsb/pgreaper',
    author='Vincent La',
    author_email='vincela9@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: SQL',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ],
    keywords='sql convert txt csv text delimited',
    packages=find_packages(exclude=['benchmarks', 'dev', 'docs', 'scratch',
        'setup', 'tests*', 'tools']),
    install_requires=[
        'psycopg2',
        'Click',
        'csvmorph>=1.0.1a8',
    ],
    entry_points='''
        [console_scripts]
        pgreaper=pgreaper.cli:cli_copy
    ''',
    ext_modules = cythonize(extensions),
    include_package_data=True
)