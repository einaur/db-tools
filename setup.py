from setuptools import setup, find_packages

setup(
    name="db_tools",
    version="1.0.0",
    description="Tool for managing output files in a SQLite database",
    author="Your Name",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "db_tools": ["dbtools.inputs.json"],
    },
    entry_points={
        "console_scripts": [
            "dbtools=db_tools.main:main",
        ],
    },
    install_requires=[
        "numpy",
    ],
    python_requires=">=3.7",
)
