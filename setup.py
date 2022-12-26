from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    readme = f.read()

setup(
    name='cli3',
    version='1.0.2',
    license='MIT',
    packages=find_packages(),
    url='https://github.com/imgurbot12/cli',
    author='Andrew Scott',
    author_email='imgurbot12@gmail.com',
    description=(
        'A highly configurable, dynamic, fast, and easy '
        'solution to managing a command-line application.'
    ),
    python_requires='>=3.7',
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=['jinja2'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
