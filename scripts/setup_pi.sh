#!/bin/bash
# ============================================================
# AgriTwin Pi Setup / Update Script
# Run this ON the Raspberry Pi:  bash ~/setup_pi.sh
# ============================================================

NEW_IP="192.168.1.5"    # <-- your laptop's LAN IP

echo "=== 1. Updating fog_server.py CLOUD_URL to http://$NEW_IP:8000 ==="
sed -i "s|CLOUD_URL = .*|CLOUD_URL = 'http://$NEW_IP:8000'|g" /home/pi/agritwin-fog/fog_server.py
grep "CLOUD_URL" /home/pi/agritwin-fog/fog_server.py

echo ""
echo "=== 2. Also updating camera_service.py CLOUD_URL ==="
sed -i "s|CLOUD_URL = .*|CLOUD_URL = 'http://$NEW_IP:8000'|g" /home/pi/camera_service.py
grep "CLOUD_URL" /home/pi/camera_service.py

echo ""
echo "=== 3. Enabling camera.service for autostart on boot ==="
sudo systemctl enable camera.service
sudo systemctl enable agritwin-fog.service

echo ""
echo "=== 4. Restarting services ==="
sudo systemctl restart agritwin-fog.service
sudo systemctl restart camera.service

echo ""
echo "=== 5. Service status ==="
sudo systemctl status agritwin-fog.service --no-pager -l
echo "---"
sudo systemctl status camera.service --no-pager -l

echo ""
echo "=== Done! Pi updated to point to laptop at $NEW_IP ==="
