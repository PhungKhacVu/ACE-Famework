#!/bin/sh
# bootstrap.sh — One-shot setup for ACE Framework in a-Shell / a-Shell mini
#
# Copy-paste the following block into a-Shell to set up the project:
#
#   cd ~
#   git clone https://github.com/PhungKhacVu/ACE-Famework.git
#   cd ACE-Famework
#   sh bootstrap.sh
#
# After the script completes you can run:
#   python -m app.cli run-task --input data/sample_tasks.json
#   python -m pytest tests/ -v

set -e

echo "=== ACE Framework bootstrap ==="

# 1. Upgrade pip quietly
python -m pip install --upgrade pip --quiet

# 2. Install pytest (the only dev dependency)
python -m pip install pytest --quiet

echo ""
echo "=== Running tests to verify the installation ==="
python -m pytest tests/ -v

echo ""
echo "=== Running sample tasks ==="
python -m app.cli run-task --input data/sample_tasks.json

echo ""
echo "=== Current playbook ==="
python -m app.cli show-playbook

echo ""
echo "=== Bootstrap complete! ==="
echo ""
echo "Useful commands:"
echo "  python -m app.cli run-task --input data/sample_tasks.json"
echo "  python -m app.cli show-playbook"
echo "  python -m app.cli clear-playbook"
echo "  python -m pytest tests/ -v"
