#!/bin/bash

# Update system
sudo apt update

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/ticketing.service > /dev/null <<EOF
[Unit]
Description=Ticketing System
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ticketing
sudo systemctl start ticketing

echo "Ticketing system installed and running on port 8006"
echo "Access at: http://$(hostname -I | awk '{print $1}'):8006"
echo "Default login: admin/123"