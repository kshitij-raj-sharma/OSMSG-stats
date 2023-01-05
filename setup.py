from setuptools import setup

setup(
    name="osmsg",
    version="0.0.1",
    description="Simple python script processes OSM files and produces stats from changefiles on the fly",
    url="https://github.com/kshitijrajsharma/OSMSG",
    author="Kshitij Raj Sharma",
    author_email="skshitizraj@gmail.com",
    license="MIT",
    packages=["osmsg"],
    entry_points={"console_scripts": ["osmsg = app:main"]},
    install_requires=["osmium", "pandas", "requests"],
)
