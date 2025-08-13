#!/bin/bash
pip install --upgrade pip
pip cache purge
pip install -r requirements.txt --no-cache-dir 
