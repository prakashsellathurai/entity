from setuptools import setup, find_packages

setup(
    name='entityagent',
    version='0.1.3',
    description='Entity Agent: An AI assistant with platform interaction capabilities',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Prakash Sellathurai',
    author_email='prakashsellathurai@gmail.com',
    url='https://github.com/prakashsellathurai/entity',
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines(),
    python_requires='>=3.8',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'entity-agent=entityAgent.runtime:main',
            'uninstall_entityagent = entityAgent.ollama_utils:uninstall_ollama_cli',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    project_urls={
        'Source': 'https://github.com/prakashsellathurai/entity',
        'Tracker': 'https://github.com/prakashsellathurai/entity/issues',
    },
)
