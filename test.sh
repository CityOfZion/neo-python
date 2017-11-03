#!/bin/bash
coverage run -m unittest discover neo
pycodestyle prompt.py
pycodestyle neo/