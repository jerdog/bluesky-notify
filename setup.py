"""Setup configuration for bluesky-notify package."""

from setuptools import setup, find_namespace_packages

setup(
    name="bluesky-notify",
    version="0.5.1",
    description="Bluesky Notification Manager - Track and receive notifications from Bluesky accounts",
    author="Jeremy Meiss",
    author_email="jeremy.meiss@gmail.com",
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
        "flask>=3.1.0",
        "flask-cors>=5.0.0",
        "flask-migrate>=4.0.0",
        "flask-sqlalchemy>=3.0.0",
        "atproto>=0.0.28",
        "desktop-notifier>=3.4.0",
        "rich>=13.0.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.1",
        "requests>=2.31.0",
        "urllib3>=2.0.7",
        "certifi>=2023.7.22",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "bluesky-notify=bluesky_notify.cli.commands:main",
        ],
    },
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jerdog/bluesky-notify",
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
