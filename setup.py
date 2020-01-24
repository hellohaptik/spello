import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    require_packages = [line[:-1] if line[-1] == '\n' else line for line in f]

setuptools.setup(
    name="spello",
    version="1.1.0",
    author="Aman Srivastava",
    author_email="amans.rlx@gmail.com",
    description="Spello: Fast and Smart Spell Correction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hellohaptik/spello",
    packages=setuptools.find_packages(),
    install_requires=require_packages,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords='nlp  machine learning spell correction',
)
