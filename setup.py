from setuptools import setup, find_packages

setup(
    name='entityagent',
    version='0.1.0',
    description='Entity Agent: An AI assistant with platform interaction capabilities',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'psutil',
        # Add other dependencies here, e.g. 'ollama' if available on PyPI
    ],
    python_requires='>=3.8',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'entity-agent=entityAgent.agent:runtime',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
