#!/bin/bash

echo "=== Service Status ==="
sudo systemctl status ticketing

echo -e "\n=== Recent Logs ==="
sudo journalctl -u ticketing --no-pager -n 20

echo -e "\n=== Port Check ==="
sudo netstat -tlnp | grep 8006

echo -e "\n=== File Permissions ==="
ls -la run.py

echo -e "\n=== Python Path ==="
which python3

echo -e "\n=== Virtual Environment ==="
ls -la venv/bin/python