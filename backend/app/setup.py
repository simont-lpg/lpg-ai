from setuptools import setup, find_packages

setup(
    name="haystack-rag-service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "farm-haystack==1.26.4",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
        "pydantic<2.0.0",
    ],
) 