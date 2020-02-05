import io
from setuptools import setup

main_ns = {}
exec(open("dash_enterprise_auth/version.py").read(), main_ns)  # pylint: disable=exec-used

setup(
    name="dash-enterprise-auth",
    version=main_ns["__version__"],
    description="Authentication integrations for dash apps using dash-deployment-server",
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="dash dash-enterprise dash-auth plotly",
    author="Antoine Roy-Gobeil",
    author_email="antoine@plot.ly",
    packages=[
        "dash_enterprise_auth"
    ],
    install_requires=[
        "dash",
        "requests[security]",
        "retrying"
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ]
)
