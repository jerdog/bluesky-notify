from setuptools import setup, find_namespace_packages

setup(
    name="bluesky-notify",
    version="0.1.0",
    packages=find_namespace_packages(where="src", include=["bluesky_notify*"]),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "bluesky_notify": [
            "data/*",
            "templates/*",
            "static/*",
        ],
    },
    install_requires=[
        "flask>=2.0.0",
        "flask-cors>=4.0.0",
        "flask-migrate>=4.0.0",
        "flask-sqlalchemy>=3.0.0",
        "atproto>=0.0.28",
        "desktop-notifier>=3.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "bluesky-notify=bluesky_notify.cli.commands:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A cross-platform desktop notification system for Bluesky",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bluesky-notify",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
