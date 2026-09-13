import os
import sys

from setuptools import setup, find_packages

setup(
    name="wave-music",
    version="1.0.0",
    packages=find_packages(),
    py_modules=["run_app"],
    entry_points={
        "console_scripts": [
            "gunicorn=run_app:main",
        ],
    },
)
