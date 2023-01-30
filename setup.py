import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="schoolchoice_da",
    version="1.1.3",
    install_requires=[
        'pandas>=1.2.5',
        'numpy>=1.20.2'
    ],
    author="TetherEducation",
    author_email="benjamin@tether.education",
    description='Implementation of the Deferred Acceptance algorithm (Galey-Shapley) for school choice.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://https://github.com/TetherEducation/SchoolChoice_da",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
