"""Setup file"""

from setuptools import setup, find_packages
import quartus_cadence_netlist_merger

setup(
    name='quartus_cadence_netlist_merger',
    version=quartus_cadence_netlist_merger.__version__,
    description='Quartus pin and Cadence Allegro Net-List merger (cnl - Cadence Net-List)',
    url='',
    author='Yuriy VG',
    author_email='yuravg@gmail.com',
    license='MIT',
    install_requires=[],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    entry_points={
        'console_scripts': [
            'qp_cnl_merger = quartus_cadence_netlist_merger.main:main'
        ]
    },
    long_description=open('README.md').read(),
    include_package_data=True,
    packages=find_packages(exclude=['tests']),
    test_suite='tests'
)
