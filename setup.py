import io

from setuptools import setup

# Read the content of the README file
with io.open("README.md", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="osmsg",
    version="0.1.33",
    description="OpenStreetMap Stats Generator : Commandline",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/kshitijrajsharma/OSMSG",
    author="Kshitij Raj Sharma",
    author_email="skshitizraj@gmail.com",
    license="MIT",
    packages=["osmsg"],
    entry_points={"console_scripts": ["osmsg = osmsg.app:main"]},
    install_requires=[
        "osmium",
        "pandas==1.5.2",
        "requests",
        "Shapely",
        "geopandas==0.10.2",
        "tqdm",
        "seaborn",
        "matplotlib",
        "humanize",
    ],
)
