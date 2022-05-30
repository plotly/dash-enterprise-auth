
build:
    python setup.py bdist_wheel --universal sdist --formats=gztar
    rm -rf build

test:
    pytest tests
