from setuptools import setup
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="tsmpy",
    version="1.0.0",
    author="uknfire",
    author_email="uknfire@gmail.com",
    description="An orthogonal layout algorithm, using TSM approach",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/uknfire/tsmpy",
    license="LICENSE.txt",
    packages=["tsmpy"],
    keywords=[
        "Graph Drawing",
        "orthogonal",
        "layout",
        "graph",
    ],
    install_requires=["networkx", "pulp"],
    python_requires=">=3.6",
)
