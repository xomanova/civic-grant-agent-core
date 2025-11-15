from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="firehouse-ai",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI agent system for finding and drafting grant applications for volunteer fire departments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xomanova/civic-grant-agent-core",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Other Audience",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "google-generativeai>=0.3.0",
        "google-adk>=0.1.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "PyPDF2>=3.0.0",
        "pdfplumber>=0.10.0",
        "python-dateutil>=2.8.0",
        "structlog>=23.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ],
        "deploy": [
            "gunicorn>=21.2.0",
            "flask>=3.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "firehouse-ai=main:main",
        ],
    },
)
