#!/usr/bin/env python3
"""
Setup script for Collatz Distributed Network
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_file(filename):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='collatz-distributed',
    version='1.0.0',
    description='Distributed verification network for the Collatz Conjecture',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Jaylouisw',
    author_email='wenden.jason@gmail.com',
    url='https://github.com/Jaylouisw/ProjectCollatz',
    
    # Package discovery
    packages=find_packages(exclude=['tests', 'benchmarks']),
    py_modules=[
        'distributed_collatz',
        'ipfs_coordinator',
        'user_account',
        'counterexample_handler',
        'leaderboard_generator',
        'production_init',
        'network_launcher',
        'trust_system',
        'contribution_tracker',
        'proof_verification',
        'error_handler',
    ],
    
    # Python version requirement
    python_requires='>=3.8',
    
    # Core dependencies (always needed)
    install_requires=[
        'ipfshttpclient>=0.8.0a2',
        'cryptography>=41.0.0',
        'psutil>=5.9.0',
        'numpy>=1.24.0',
    ],
    
    # Optional dependencies
    extras_require={
        'gpu': [
            'cupy-cuda12x>=12.0.0',  # CUDA 12.x
        ],
        'gpu-cuda11': [
            'cupy-cuda11x>=11.0.0',  # CUDA 11.x
        ],
        'dev': [
            'pytest>=7.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
        ],
    },
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'collatz-network=network_launcher:main',
            'collatz-worker=distributed_collatz:main',
            'collatz-account=user_account:main',
        ],
    },
    
    # Classifiers for PyPI
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Mathematics',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
    ],
    
    # Include additional files
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.json'],
    },
    
    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/Jaylouisw/ProjectCollatz/issues',
        'Source': 'https://github.com/Jaylouisw/ProjectCollatz',
        'Documentation': 'https://github.com/Jaylouisw/ProjectCollatz#readme',
    },
)
