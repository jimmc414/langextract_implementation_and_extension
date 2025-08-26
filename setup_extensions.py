"""
Setup script for LangExtract Extensions
"""

from setuptools import setup, find_packages

setup(
    name="langextract-extensions",
    version="0.1.0",
    description="Additional features for Google's LangExtract library",
    author="LangExtract Extensions Contributors",
    packages=find_packages(),
    install_requires=[
        "langextract",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "PyPDF2>=3.0.0",
        "pandas>=1.3.0",
        "Pillow>=8.0.0",
        "imgkit>=1.2.0",
        "click>=8.0.0",
        "pyyaml>=5.4.0",
        "matplotlib>=3.3.0",
        "google-generativeai>=0.3.0",
    ],
    entry_points={
        'console_scripts': [
            'langextract=langextract_extensions.cli:cli',
        ],
        'langextract.providers': [
            'gemini=langextract_extensions.providers.gemini:GeminiProvider',
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)