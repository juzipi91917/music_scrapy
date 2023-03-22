from setuptools import setup, find_packages

setup(
    name='toyosaki_music',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'jsonpath',
        'lxml'
    ],
    entry_points={
        'console_scripts': [
            'toyosaki_music=toyosaki_music:main'
        ]
    }
)
