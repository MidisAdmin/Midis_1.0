# Midis Setup Notes

## WiFi Power Management Fix
Create /etc/NetworkManager/conf.d/wifi-powersave-off.conf with:
[connection]
wifi.powersave = 2

Then: sudo systemctl restart NetworkManager
