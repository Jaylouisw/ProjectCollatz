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
    
    # Python version requirement - FUTURE-PROOFED for wide compatibility
    python_requires='>=3.8,<4.0',  # Support current and future 3.x, prepare for 4.x
    
    # Core dependencies (FUTURE-PROOFED with version ranges)
    install_requires=[
        # IPFS: Allow patch updates while avoiding breaking changes
        'ipfshttpclient>=0.8.0,<0.10.0',  # Moved from alpha to stable range
        
        # Cryptography: Wide range for security updates, quantum-safe future
        'cryptography>=41.0.0,<50.0.0',  # Allow major security updates
        
        # System monitoring: Stable API, wide compatibility
        'psutil>=5.9.0,<7.0.0',  # psutil has stable API
        
        # NumPy: Conservative range to avoid breaking changes
        'numpy>=1.24.0,<2.1.0',  # Support NumPy 2.x but test first
    ],
    
    # Optional dependencies - FUTURE-PROOFED with flexible GPU support
    extras_require={
        # GPU support with multiple backend options
        'gpu': [
            'cupy-cuda12x>=12.0.0,<15.0.0',  # CUDA 12.x with future versions
        ],
        'gpu-cuda11': [
            'cupy-cuda11x>=11.0.0,<13.0.0',  # CUDA 11.x legacy support
        ],
        'gpu-rocm': [
            'cupy-rocm-5-0>=12.0.0,<15.0.0',  # AMD ROCm support
        ],
        'gpu-intel': [
            # Future: Intel GPU support when available
            # 'intel-extension-for-pytorch>=2.0.0',
        ],
        
        # Development tools with version ranges
        'dev': [
            'pytest>=7.0.0,<9.0.0',
            'black>=23.0.0,<25.0.0',
            'flake8>=6.0.0,<8.0.0',
            'mypy>=1.0.0,<2.0.0',  # Type checking
        ],
        
        # Alternative networking backends (future-proofing)
        'networking-alt': [
            'libp2p>=0.1.0,<1.0.0',  # Alternative P2P protocol
            # 'bittorrent-protocol>=1.0.0',  # Future alternative
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
