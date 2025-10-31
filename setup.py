"""Setup script for LexTimeCheck."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lextimecheck",
    version="0.1.0",
    author="LexTimeCheck Team",
    description="Intertemporal Norm-Conflict Auditing for Changing Laws",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bridge-ai-law/lextimecheck",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "python-dateutil>=2.8.2",
        "openai>=1.0.0",
        "anthropic>=0.8.0",
        "jinja2>=3.1.0",
        "click>=8.1.0",
        "pyyaml>=6.0.0",
        "plotly>=5.18.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "requests>=2.31.0",
        "markdown>=3.5.0",
    ],
    extras_require={
        "solver": ["z3-solver>=4.12.0"],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lextimecheck=cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "lextimecheck": ["prompts/*.txt"],
    },
)

