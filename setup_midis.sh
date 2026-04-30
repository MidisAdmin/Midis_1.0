#!/bin/bash
echo "=== Midis Setup Script ==="

# Update
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git python3-pip python3-pil cython3 python3-setuptools python3-dev libpython3-dev

# Install Python packages
sudo pip3 install FlightRadarAPI beautifulsoup4 MLB-StatsAPI pytz --break-system-packages

# Clone RGB matrix library
cd ~ && git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd ~/rpi-rgb-led-matrix && make

# Patch core.pyx to remove Pillow dependency
cat > ~/rpi-rgb-led-matrix/bindings/python/rgbmatrix/core.pyx << 'PATCHEOF'
# distutils: language = c++

from libcpp cimport bool
from libc.stdint cimport uint8_t, uint32_t, uintptr_t
import cython

cdef class Canvas:
    cdef cppinc.Canvas* _getCanvas(self) except *:
        raise Exception("Not implemented")

    def SetImage(self, image, int offset_x = 0, int offset_y = 0, unsafe=True):
        if (image.mode != "RGB"):
            raise Exception("Currently, only RGB mode is supported for SetImage(). Please create images with mode 'RGB' or convert first with image = image.convert('RGB').")
        img_width, img_height = image.size
        pixels = image.load()
        for x in range(max(0, -offset_x), min(img_width, self.width - offset_x)):
            for y in range(max(0, -offset_y), min(img_height, self.height - offset_y)):
                (r, g, b) = pixels[x, y]
                self.SetPixel(x + offset_x, y + offset_y, r, g, b)

cdef class FrameCanvas(Canvas):
    def __dealloc__(self):
        if <void*>self.__canvas != NULL:
            self.__canvas = NULL

    cdef cppinc.Canvas* _getCanvas(self) except *:
        if <void*>self.__canvas != NULL:
            return self.__canvas
        raise Exception("Canvas was destroyed or not initialized")

    def Fill(self, uint8_t red, uint8_t green, uint8_t blue):
        (<cppinc.FrameCanvas*>self._getCanvas()).Fill(red, green, blue)

    def Clear(self):
        (<cppinc.FrameCanvas*>self._getCanvas()).Clear()

    def SetPixel(self, int x, int y, uint8_t red, uint8_t green, uint8_t blue):
        (<cppinc.FrameCanvas*>self._getCanvas()).SetPixel(x, y, red, green, blue)

    property width:
        def __get__(self): return (<cppinc.FrameCanvas*>self._getCanvas()).width()

    property height:
        def __get__(self): return (<cppinc.FrameCanvas*>self._getCanvas()).height()

    property pwmBits:
        def __get__(self): return (<cppinc.FrameCanvas*>self._getCanvas()).pwmbits()
        def __set__(self, pwmBits): (<cppinc.FrameCanvas*>self._getCanvas()).SetPWMBits(pwmBits)

    property brightness:
        def __get__(self): return (<cppinc.FrameCanvas*>self._getCanvas()).brightness()
        def __set__(self, val): (<cppinc.FrameCanvas*>self._getCanvas()).SetBrightness(val)

cdef class RGBMatrixOptions:
    def __cinit__(self):
        self.__options = cppinc.Options()
        self.__runtime_options = cppinc.RuntimeOptions()

    property hardware_mapping:
        def __get__(self): return self.__options.hardware_mapping
        def __set__(self, value):
            self.__py_encoded_hardware_mapping = value.encode('utf-8')
            self.__options.hardware_mapping = self.__py_encoded_hardware_mapping

    property rows:
        def __get__(self): return self.__options.rows
        def __set__(self, uint8_t value): self.__options.rows = value

    property cols:
        def __get__(self): return self.__options.cols
        def __set__(self, uint32_t value): self.__options.cols = value

    property chain_length:
        def __get__(self): return self.__options.chain_length
        def __set__(self, uint8_t value): self.__options.chain_length = value

    property parallel:
        def __get__(self): return self.__options.parallel
        def __set__(self, uint8_t value): self.__options.parallel = value

    property pwm_bits:
        def __get__(self): return self.__options.pwm_bits
        def __set__(self, uint8_t value): self.__options.pwm_bits = value

    property pwm_lsb_nanoseconds:
        def __get__(self): return self.__options.pwm_lsb_nanoseconds
        def __set__(self, uint32_t value): self.__options.pwm_lsb_nanoseconds = value

    property brightness:
        def __get__(self): return self.__options.brightness
        def __set__(self, uint8_t value): self.__options.brightness = value

    property scan_mode:
        def __get__(self): return self.__options.scan_mode
        def __set__(self, uint8_t value): self.__options.scan_mode = value

    property multiplexing:
        def __get__(self): return self.__options.multiplexing
        def __set__(self, uint8_t value): self.__options.multiplexing = value

    property row_address_type:
        def __get__(self): return self.__options.row_address_type
        def __set__(self, uint8_t value): self.__options.row_address_type = value

    property disable_hardware_pulsing:
        def __get__(self): return self.__options.disable_hardware_pulsing
        def __set__(self, value): self.__options.disable_hardware_pulsing = value

    property show_refresh_rate:
        def __get__(self): return self.__options.show_refresh_rate
        def __set__(self, value): self.__options.show_refresh_rate = value

    property inverse_colors:
        def __get__(self): return self.__options.inverse_colors
        def __set__(self, value): self.__options.inverse_colors = value

    property led_rgb_sequence:
        def __get__(self): return self.__options.led_rgb_sequence
        def __set__(self, value):
            self.__py_encoded_led_rgb_sequence = value.encode('utf-8')
            self.__options.led_rgb_sequence = self.__py_encoded_led_rgb_sequence

    property pixel_mapper_config:
        def __get__(self): return self.__options.pixel_mapper_config
        def __set__(self, value):
            self.__py_encoded_pixel_mapper_config = value.encode('utf-8')
            self.__options.pixel_mapper_config = self.__py_encoded_pixel_mapper_config

    property panel_type:
        def __get__(self): return self.__options.panel_type
        def __set__(self, value):
            self.__py_encoded_panel_type = value.encode('utf-8')
            self.__options.panel_type = self.__py_encoded_panel_type

    property pwm_dither_bits:
        def __get__(self): return self.__options.pwm_dither_bits
        def __set__(self, uint8_t value): self.__options.pwm_dither_bits = value

    property limit_refresh_rate_hz:
        def __get__(self): return self.__options.limit_refresh_rate_hz
        def __set__(self, value): self.__options.limit_refresh_rate_hz = value

    property gpio_slowdown:
        def __get__(self): return self.__runtime_options.gpio_slowdown
        def __set__(self, uint8_t value): self.__runtime_options.gpio_slowdown = value

    property daemon:
        def __get__(self): return self.__runtime_options.daemon
        def __set__(self, uint8_t value): self.__runtime_options.daemon = value

    property drop_privileges:
        def __get__(self): return self.__runtime_options.drop_privileges
        def __set__(self, uint8_t value): self.__runtime_options.drop_privileges = value

    property drop_priv_user:
        def __get__(self): return self.__runtime_options.drop_priv_user
        def __set__(self, value):
            self.__py_encoded_drop_priv_user = value.encode('utf-8')
            self.__runtime_options.drop_priv_user = self.__py_encoded_drop_priv_user

    property drop_priv_group:
        def __get__(self): return self.__runtime_options.drop_priv_group
        def __set__(self, value):
            self.__py_encoded_drop_priv_group = value.encode('utf-8')
            self.__runtime_options.drop_priv_group = self.__py_encoded_drop_priv_group

cdef class RGBMatrix(Canvas):
    def __cinit__(self, int rows = 0, int chains = 0, int parallel = 0,
        RGBMatrixOptions options = None):
        if options == None:
            options = RGBMatrixOptions()
        if rows > 0:
            options.rows = rows
        if chains > 0:
            options.chain_length = chains
        if parallel > 0:
            options.parallel = parallel
        self.__matrix = cppinc.CreateMatrixFromOptions(options.__options, options.__runtime_options)

    def __dealloc__(self):
        self.__matrix.Clear()
        del self.__matrix

    cdef cppinc.Canvas* _getCanvas(self) except *:
        if <void*>self.__matrix != NULL:
            return self.__matrix
        raise Exception("Canvas was destroyed or not initialized")

    def Fill(self, uint8_t red, uint8_t green, uint8_t blue):
        self.__matrix.Fill(red, green, blue)

    def SetPixel(self, int x, int y, uint8_t red, uint8_t green, uint8_t blue):
        self.__matrix.SetPixel(x, y, red, green, blue)

    def Clear(self):
        self.__matrix.Clear()

    def CreateFrameCanvas(self):
        return __createFrameCanvas(self.__matrix.CreateFrameCanvas())

    def SwapOnVSync(self, FrameCanvas newFrame, uint8_t framerate_fraction = 1):
        return __createFrameCanvas(self.__matrix.SwapOnVSync(newFrame.__canvas, framerate_fraction))

    property luminanceCorrect:
        def __get__(self): return self.__matrix.luminance_correct()
        def __set__(self, luminanceCorrect): self.__matrix.set_luminance_correct(luminanceCorrect)

    property pwmBits:
        def __get__(self): return self.__matrix.pwmbits()
        def __set__(self, pwmBits): self.__matrix.SetPWMBits(pwmBits)

    property brightness:
        def __get__(self): return self.__matrix.brightness()
        def __set__(self, brightness): self.__matrix.SetBrightness(brightness)

    property height:
        def __get__(self): return self.__matrix.height()

    property width:
        def __get__(self): return self.__matrix.width()

cdef __createFrameCanvas(cppinc.FrameCanvas* newCanvas):
    canvas = FrameCanvas()
    canvas.__canvas = newCanvas
    return canvas
PATCHEOF

# Build Python bindings
cd ~/rpi-rgb-led-matrix/bindings/python
cython3 --cplus rgbmatrix/core.pyx rgbmatrix/graphics.pyx
g++ -shared -fPIC -O3 -o rgbmatrix/core.cpython-313-aarch64-linux-gnu.so rgbmatrix/core.cpp -I../../include -I/usr/include/python3.13 -Irgbmatrix/shims -L../../lib -lrgbmatrix -lpthread -lrt -lm $(python3-config --includes --ldflags)
g++ -shared -fPIC -O3 -o rgbmatrix/graphics.cpython-313-aarch64-linux-gnu.so rgbmatrix/graphics.cpp -I../../include -I/usr/include/python3.13 -Irgbmatrix/shims -L../../lib -lrgbmatrix -lpthread -lrt -lm $(python3-config --includes --ldflags)
sudo mkdir -p /usr/local/lib/python3.13/dist-packages/rgbmatrix
sudo cp rgbmatrix/*.so /usr/local/lib/python3.13/dist-packages/rgbmatrix/
sudo cp rgbmatrix/__init__.py /usr/local/lib/python3.13/dist-packages/rgbmatrix/

# Copy fonts
sudo mkdir -p /usr/local/share/midis-fonts
sudo cp ~/rpi-rgb-led-matrix/fonts/*.bdf /usr/local/share/midis-fonts/

# Clone Midis code
cd ~ && git clone https://github.com/MidisAdmin/Midis_1.0.git
cp ~/Midis_1.0/*.py ~/
sudo mkdir -p /usr/local/share/midis-icons
sudo cp ~/Midis_1.0/icons/midis-icons/*.png /usr/local/share/midis-icons/

# WiFi power management fix
sudo bash -c 'cat > /etc/NetworkManager/conf.d/wifi-powersave-off.conf << EOF
[connection]
wifi.powersave = 2
EOF'
sudo systemctl restart NetworkManager

# Add isolcpus=3 to cmdline
sudo sed -i 's/$/ isolcpus=3/' /boot/firmware/cmdline.txt

# WiFi watchdog
cat > ~/wifi_watchdog.sh << 'EOF'
#!/bin/bash
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    sudo nmcli device disconnect wlan0
    sudo nmcli device connect wlan0
fi
EOF
chmod +x ~/wifi_watchdog.sh

# Auto-update script
cat > ~/update_midis.sh << 'EOF'
#!/bin/bash
cd ~/Midis_1.0
git pull
cp *.py ~/
sudo systemctl restart midis
EOF
chmod +x ~/update_midis.sh

# Crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/pi/wifi_watchdog.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * /home/pi/update_midis.sh") | crontab -

# Systemd service
sudo bash -c 'cat > /etc/systemd/system/midis.service << EOF
[Unit]
Description=Midis Display
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/midis_main.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF'
sudo systemctl daemon-reload
sudo systemctl enable midis

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

echo ""
echo "=== Setup Complete! ==="
echo "Next steps:"
echo "1. Create ~/midis_config.py with customer location data"
echo "2. Run: sudo tailscale up"
echo "3. Reboot: sudo reboot"