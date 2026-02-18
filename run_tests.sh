#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest app/tests/
