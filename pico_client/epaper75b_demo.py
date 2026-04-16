from machine import Pin, SPI
import framebuf
import utime


# Waveshare Pico-ePaper-7.5-B (wiki pin mapping for Pico)
EPD_WIDTH = 800
EPD_HEIGHT = 480

PIN_RST = 12
PIN_DC = 8
PIN_CS = 9
PIN_BUSY = 13
PIN_SCK = 10
PIN_MOSI = 11


class EPD75B:
    def __init__(self):
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.rst = Pin(PIN_RST, Pin.OUT)
        self.dc = Pin(PIN_DC, Pin.OUT)
        self.cs = Pin(PIN_CS, Pin.OUT)
        self.busy = Pin(PIN_BUSY, Pin.IN, Pin.PULL_UP)

        # Pico SPI1: SCK=GP10, MOSI=GP11
        self.spi = SPI(
            1,
            baudrate=4_000_000,
            polarity=0,
            phase=0,
            sck=Pin(PIN_SCK),
            mosi=Pin(PIN_MOSI),
            miso=None,
        )

        buf_len = (self.width * self.height) // 8
        self.buffer_black = bytearray(buf_len)
        self.buffer_red = bytearray(buf_len)

        self.black = framebuf.FrameBuffer(
            self.buffer_black,
            self.width,
            self.height,
            framebuf.MONO_HLSB,
        )
        self.red = framebuf.FrameBuffer(
            self.buffer_red,
            self.width,
            self.height,
            framebuf.MONO_HLSB,
        )

    def _delay_ms(self, ms):
        utime.sleep_ms(ms)

    def _reset(self):
        self.rst.value(1)
        self._delay_ms(200)
        self.rst.value(0)
        self._delay_ms(2)
        self.rst.value(1)
        self._delay_ms(200)

    def _cmd(self, value):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([value]))
        self.cs.value(1)

    def _data(self, value):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(bytearray([value]))
        self.cs.value(1)

    def _data_block(self, buf):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(buf)
        self.cs.value(1)

    def _wait_idle(self):
        print("EPD busy...")
        while self.busy.value() == 0:
            self._delay_ms(20)
        self._delay_ms(20)
        print("EPD ready")

    def init(self):
        self._reset()

        self._cmd(0x06)  # Booster Soft Start
        self._data(0x17)
        self._data(0x17)
        self._data(0x28)
        self._data(0x17)

        self._cmd(0x04)  # Power ON
        self._delay_ms(100)
        self._wait_idle()

        self._cmd(0x00)  # Panel setting
        self._data(0x0F)

        self._cmd(0x61)  # Resolution setting
        self._data(0x03)  # 800 high byte
        self._data(0x20)  # 800 low byte
        self._data(0x01)  # 480 high byte
        self._data(0xE0)  # 480 low byte

        self._cmd(0x15)
        self._data(0x00)

        self._cmd(0x50)  # VCOM and data interval setting
        self._data(0x11)
        self._data(0x07)

        self._cmd(0x60)  # TCON setting
        self._data(0x22)

        self._cmd(0x65)  # Resolution setting extension
        self._data(0x00)
        self._data(0x00)
        self._data(0x00)
        self._data(0x00)

    def _refresh(self):
        self._cmd(0x12)  # Display refresh
        self._delay_ms(100)
        self._wait_idle()

    def clear_white(self):
        # White background: black plane = 0xFF, red plane = 0x00
        self._cmd(0x10)
        self._data_block(b"\xFF" * len(self.buffer_black))
        self._cmd(0x13)
        self._data_block(b"\x00" * len(self.buffer_red))
        self._refresh()

    def display(self):
        # Uses the same transfer order as Waveshare's reference MicroPython code.
        high = self.height
        wide = self.width // 8

        self._cmd(0x10)
        for i in range(wide):
            start = i * high
            self._data_block(self.buffer_black[start : start + high])

        self._cmd(0x13)
        for i in range(wide):
            start = i * high
            self._data_block(self.buffer_red[start : start + high])

        self._refresh()

    def sleep(self):
        self._cmd(0x02)  # Power off
        self._wait_idle()
        self._cmd(0x07)  # Deep sleep
        self._data(0xA5)


def draw_demo(epd):
    # Base state: white background
    epd.black.fill(0xFF)
    epd.red.fill(0x00)

    epd.black.text("Pico ePaper 7.5-B", 16, 16, 0x00)
    epd.black.text("MicroPython demo", 16, 36, 0x00)
    epd.red.text("BLACK/WHITE/RED", 16, 56, 0xFF)

    epd.black.rect(12, 90, 320, 120, 0x00)
    epd.red.line(12, 90, 332, 210, 0xFF)
    epd.red.line(332, 90, 12, 210, 0xFF)

    for i in range(8):
        x = 380 + i * 45
        epd.black.fill_rect(x, 90, 30, 120, 0x00 if i % 2 == 0 else 0xFF)
        epd.red.fill_rect(x, 230, 30, 80, 0xFF if i % 2 == 0 else 0x00)

    epd.black.text("If you see this, SPI + init is OK.", 16, 440, 0x00)


def main():
    epd = EPD75B()
    epd.init()
    epd.clear_white()

    draw_demo(epd)
    epd.display()

    # Keep final frame visible, then enter sleep for panel health.
    utime.sleep_ms(3000)
    epd.sleep()
    print("Demo done.")


if __name__ == "__main__":
    main()