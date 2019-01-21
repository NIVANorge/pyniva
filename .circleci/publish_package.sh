#!/usr/bin/env bash

set +x

VERSION=$(python setup.py --version)
python setup.py sdist
curl -F package=@dist/pyniva-${VERSION}.tar.gz https://${FURY_TOKEN}@push.fury.io/niva/