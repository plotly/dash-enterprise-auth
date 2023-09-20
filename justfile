
build:
    python setup.py bdist_wheel sdist --formats=gztar
    rm -rf build

test:
    pytest tests
