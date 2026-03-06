from setuptools import setup, find_packages

setup(
    name='anonex',
    version='1.0.0',
    description='Official Python connector for the AnonEx cryptocurrency exchange API',
    author='AnonEx',
    url='https://anonex.io',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'requests>=2.25.0',
        'websocket-client>=1.0.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
