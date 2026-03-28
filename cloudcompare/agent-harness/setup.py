from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-cloudcompare",
    version="1.0.0",
    description="Agent-friendly CLI harness for CloudCompare 3D point cloud software",
    long_description=open("cli_anything/cloudcompare/README.md").read(),
    long_description_content_type="text/markdown",
    author="cli-anything",
    python_requires=">=3.10",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={
        "cli_anything.cloudcompare": ["skills/*.md"],
    },
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-cloudcompare=cli_anything.cloudcompare.cloudcompare_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
)
