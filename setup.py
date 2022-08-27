import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("LICENSE", "r", encoding="utf-8") as fh:
    license = fh.read()

setuptools.setup(
    name="python-glinet",
    version="0.7.0",
    author="Tomtana",
    author_email="python@tomtana.net",
    description="Python3 client for Gl.Inet LUCI API firmware 4.0 onwards.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomtana/python-glinet",
    project_urls={
        "Bug Tracker": "https://github.com/tomtana/python-glinet/issues",
        "Documentation": "https://tomtana.github.io/python-glinet"
    },
        classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)"
    ],
    python_requires=">=3.6",
    install_requires=["ipython", "tabulate", "requests", "passlib"],
    packages=setuptools.find_packages()
)
