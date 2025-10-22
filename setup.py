from setuptools import setup, find_packages

setup(
    name="minipil",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "typer[all]",
        "PIL"
    ],
    entry_points={
        "console_scripts": [
            "Photoshop = Photoshop.main:main"
        ]
    },
)
