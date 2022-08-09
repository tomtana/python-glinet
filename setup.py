import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("LICENSE", "r", encoding="utf-8") as fh:
    license = fh.read()

setuptools.setup(
    name="python-glinet",
    version="0.1.6",
    author="Thomas Fontana",
    author_email="python@fontana.onl",
    description="This package gives client access to the Gl-Inet json-rpc for firmware >=4.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomtana/python-glinet",
    project_urls={
        "Bug Tracker": "https://github.com/tomtana/python-glinet/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)"
    ],
    python_requires=">=3.6",
    install_requires=["ipython", "tabulate", "requests"],
    packages=setuptools.find_packages()
)
