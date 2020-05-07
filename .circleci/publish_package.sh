#!/usr/bin/env bash

set +x
set -o nounset

VERSION=$(python setup.py --version)
python setup.py sdist
curl -F package=@dist/pyniva-${VERSION}.tar.gz https://${FURY_TOKEN}@push.fury.io/niva/

python setup.py sdist bdist_wheel

pip install --user twine
PATH=/home/circleci/.local/bin:$PATH
twine upload -u ${PYPI_USERNAME} -p ${PYPI_PASSWORD} dist/*