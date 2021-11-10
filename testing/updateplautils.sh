#!/bin/sh
# This is a comment!

git clone https://github.com/AI-Planning/planutils.git
cd planutils
git checkout manifest-new-version
pip uninstall planutils
python3 setup.py install --old-and-unmanageable

# Then add the planutils packages
planutils install lama-first