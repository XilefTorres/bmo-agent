#!/bin/bash
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/charts
pip install -r requirements.txt
