from setuptools import setup, find_packages

setup(
    name="minipil",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "typer[all]",
        "Pillow"
    ],
    entry_points={
        "console_scripts": [
            "minipil = minipil.cli:app"
        ]
    },
)
