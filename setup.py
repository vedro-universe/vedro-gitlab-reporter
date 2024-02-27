from setuptools import find_packages, setup


def find_required():
    with open("requirements.txt") as f:
        return f.read().splitlines()


def find_dev_required():
    with open("requirements-dev.txt") as f:
        return f.read().splitlines()


setup(
    name="vedro-gitlab-reporter",
    version="2.1.4",
    description="GitLab reporter with collapsable sections for Vedro framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nikita Tsvetkov",
    author_email="tsv1@fastmail.com",
    python_requires=">=3.7",
    url="https://github.com/vedro-universe/vedro-gitlab-reporter",
    project_urls={
        "Docs": "https://vedro.io/docs/integrations/gitlab-reporter",
        "GitHub": "https://github.com/vedro-universe/vedro-gitlab-reporter",
    },
    license="Apache-2.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"vedro_gitlab_reporter": ["py.typed"]},
    install_requires=find_required(),
    tests_require=find_dev_required(),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
    ],
)
