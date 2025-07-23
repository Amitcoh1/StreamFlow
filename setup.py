"""
StreamFlow Analytics Platform Setup
"""
from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "StreamFlow - Enterprise-Grade Real-Time Analytics Platform"

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.23.0",
            "pydantic>=2.0.0",
            "sqlalchemy>=2.0.0",
            "asyncpg>=0.28.0",
            "aioredis>=2.0.0",
            "aio-pika>=9.0.0",
            "prometheus-client>=0.17.0",
            "python-multipart>=0.0.6",
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "httpx>=0.24.0",
            "click>=8.0.0",
            "rich>=13.0.0",
            "pyyaml>=6.0.0",
        ]

# Version management
__version__ = "0.1.0"

setup(
    name="streamflow-analytics",
    version=__version__,
    author="Amit Cohen",
    author_email="amit@streamflow.io",
    description="Enterprise-Grade Real-Time Analytics Platform",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Amitcoh1/StreamFlow",
    project_urls={
        "Homepage": "https://streamflow.io",
        "Documentation": "https://docs.streamflow.io",
        "Source Code": "https://github.com/Amitcoh1/StreamFlow",
        "Bug Tracker": "https://github.com/Amitcoh1/StreamFlow/issues",
        "Changelog": "https://github.com/Amitcoh1/StreamFlow/blob/main/CHANGELOG.md",
        "Discussion": "https://github.com/Amitcoh1/StreamFlow/discussions",
    },
    packages=find_packages(exclude=["tests*", "docs*", "examples*", "web-ui*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: System :: Monitoring",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Database :: Database Engines/Servers",
        "Framework :: AsyncIO",
        "Framework :: FastAPI",
        "Environment :: Web Environment",
        "Natural Language :: English",
    ],
    keywords=[
        "analytics", "real-time", "streaming", "dashboard", "monitoring",
        "fastapi", "react", "postgresql", "redis", "rabbitmq", "kubernetes",
        "docker", "prometheus", "grafana", "alerting", "event-processing",
        "time-series", "observability", "microservices", "cloud-native"
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "locust>=2.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocs-mermaid2-plugin>=1.0.0",
        ],
        "cloud": [
            "boto3>=1.28.0",
            "google-cloud-storage>=2.10.0",
            "azure-storage-blob>=12.17.0",
            "kubernetes>=27.0.0",
        ],
        "monitoring": [
            "sentry-sdk[fastapi]>=1.30.0",
            "structlog>=23.0.0",
            "elasticsearch>=8.0.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "streamflow=streamflow.cli:main",
            "streamflow-server=streamflow.server:main",
            "streamflow-worker=streamflow.worker:main",
            "streamflow-migrate=streamflow.migrate:main",
        ],
    },
    include_package_data=True,
    package_data={
        "streamflow": [
            "templates/*.html",
            "templates/*.json",
            "static/*",
            "migrations/*.sql",
            "config/*.yaml",
            "config/*.json",
        ],
    },
    zip_safe=False,
    platforms=["any"],
    license="MIT",
    license_files=["LICENSE"],
    
    # Additional metadata for PyPI
    maintainer="StreamFlow Team",
    maintainer_email="team@streamflow.io",
    
    # Advanced configuration
    cmdclass={},
    
    # Security and quality badges
    download_url=f"https://github.com/Amitcoh1/StreamFlow/archive/v{__version__}.tar.gz",
    
    # Supported platforms
    options={
        "bdist_wheel": {
            "universal": False,
        }
    },
)
