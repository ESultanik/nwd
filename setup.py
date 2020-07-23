import os
from setuptools import setup, find_packages

setup(
    name='nwd',
    description='Notify When Done (NWD). A tool for posting a desktop notification, E-mail, or other alert when a process finishes.',
    url='https://github.com/ESultanik/nwd',
    author='Evan Sultanik',
    version='2.0.0',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'pyobjc;platform_system=="Darwin"',
        'win10toast;platform_system=="Windows"',
        'keyring',
        'psutil'
    ],
    extras_require={
        "dev": ["flake8"]
    },
    entry_points={
        'console_scripts': [
            'nwd = nwd.__main__:main'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities'
    ]
)
