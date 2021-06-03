#!/bin/bash

SKIP=pylint,mypy pre-commit run --all-files
pre-commit run mypy --all-files
