from setuptools import setup, find_packages

setup(
    name="lpg-ai-service",
    version="1.2.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "sentence-transformers>=2.2.0",
        "numpy>=1.21.0",
        "python-dotenv>=0.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
        ]
    },
) 