"""Setup configuration for GOD CLI."""
from setuptools import setup, find_packages
from pathlib import Path

readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="god-cli",
    version="1.0.0",
    description="Professional-grade global help indexer with BLUX integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OuterVoid Team",
    author_email="outervoid.blux@gmail.com",
    url="https://github.com/outervoid/god-cli",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "typer[all]>=0.12.0",
        "rich>=13.7.0",
        "click>=8.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-timeout>=2.2.0",
            "ruff>=0.1.0",
            "mypy>=1.8.0",
            "black>=24.0.0",
            "isort>=5.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "god=god.cli:main_cli",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
