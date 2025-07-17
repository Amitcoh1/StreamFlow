#!/usr/bin/env python
"""
StreamFlow - real-time analytics pipeline
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="streamflow",
    version="0.1.0",
    author="Amit Cohen",
    author_email="amit.cohen@streamflow.dev",
    description="real-time analytics pipeline using Python, FastAPI, and RabbitMQ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amitcohen/streamflow",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
        "Framework :: AsyncIO",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
            "bandit>=1.7.0",
        ],
        "monitoring": [
            "prometheus-client>=0.15.0",
            "opentelemetry-api>=1.15.0",
            "opentelemetry-sdk>=1.15.0",
            "opentelemetry-instrumentation-fastapi>=0.36b0",
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=8.5.0",
            "mkdocs-mermaid2-plugin>=0.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "streamflow=streamflow.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
