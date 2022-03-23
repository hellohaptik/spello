import os
import setuptools

THIS_DIR = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))

with open(os.path.join(THIS_DIR, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(os.path.join(THIS_DIR, "requirements.txt")) as f:
    require_packages = [line[:-1] if line[-1] == "\n" else line for line in f]

setuptools.setup(
    name="spello",
    version="1.3.0",
    author="Machine Learning Team @ Jio Haptik Technologies Limited",
    author_email="machinelearning@haptik.ai",
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
    python_requires=">=3.6",
    keywords="nlp machine learning spell correction",
)
