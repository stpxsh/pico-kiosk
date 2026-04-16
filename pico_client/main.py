import network
import time
from machine import Pin, SPI
import requests
import secrets


EPD_WIDTH = 800
EPD_HEIGHT = 480
PAYLOAD_SIZE = (EPD_WIDTH * EPD_HEIGHT) // 8  # 48000 B

PIN_RST = 12
PIN_DC = 8
PIN_CS = 9
PIN_BUSY = 13
PIN_SCK = 10
PIN_MOSI = 11

# E-paper full refresh je pomaly a panel by se nemel obnovovat moc casto.
REFRESH_INTERVAL_S = 180


class EPD75BMono:
    def __init__(self):
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.rst = Pin(PIN_RST, Pin.OUT)
        self.dc = Pin(PIN_DC, Pin.OUT)
        self.cs = Pin(PIN_CS, Pin.OUT)
        self.busy = Pin(PIN_BUSY, Pin.IN, Pin.PULL_UP)

        self.spi = SPI(
            1,
            baudrate=4_000_000,
            polarity=0,
            phase=0,
            sck=Pin(PIN_SCK),
            mosi=Pin(PIN_MOSI),
            miso=None,
        )

    def _delay_ms(self, ms):
        time.sleep_ms(ms)

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

    def _reset(self):
        self.rst.value(1)
        self._delay_ms(200)
        self.rst.value(0)
        self._delay_ms(2)
        self.rst.value(1)
        self._delay_ms(200)

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

        self._cmd(0x61)  # Resolution setting (800x480)
        self._data(0x03)
        self._data(0x20)
        self._data(0x01)
        self._data(0xE0)

        self._cmd(0x15)
        self._data(0x00)

        self._cmd(0x50)  # VCOM and data interval
        self._data(0x11)
        self._data(0x07)

        self._cmd(0x60)  # TCON setting
        self._data(0x22)

        self._cmd(0x65)
        self._data(0x00)
        self._data(0x00)
        self._data(0x00)
        self._data(0x00)

    def _refresh(self):
        self._cmd(0x12)  # Display refresh
        self._delay_ms(100)
        self._wait_idle()

    def display_bw_payload(self, payload):
        if len(payload) != PAYLOAD_SIZE:
            raise ValueError("Neocekavana delka payloadu: {} (cekam {})".format(len(payload), PAYLOAD_SIZE))

        # Stejny prenosovy format jako referencni Waveshare driver pro 7.5-B.
        high = self.height
        wide = self.width // 8

        self._cmd(0x10)  # black/white RAM
        for i in range(wide):
            start = i * high
            self._data_block(payload[start : start + high])

        # Red RAM nechame prazdnou (ciste cernobily provoz).
        self._cmd(0x13)
        zeros = b"\x00" * 1200
        remaining = PAYLOAD_SIZE
        while remaining > 0:
            chunk = 1200 if remaining >= 1200 else remaining
            self._data_block(zeros[:chunk])
            remaining -= chunk

        self._refresh()

    def sleep(self):
        self._cmd(0x02)
        self._wait_idle()
        self._cmd(0x07)
        self._data(0xA5)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # Nastavení power managementu pro lepší stabilitu (Pico W specifikum)
    wlan.config(pm=0xa11140) 
    
    wlan.connect(secrets.SSID, secrets.PASSWORD)
    
    print("Pripojovani k WiFi...")
    max_wait = 15
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print("Cekam...")
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('Pripojeni k WiFi selhalo!')
    else:
        status = wlan.ifconfig()
        print('Pripojeno k WiFi! IP adresa:', status[0])

def fetch_payload():
    print("\nStahuji data z {} ...".format(secrets.SERVER_URL))

    try:
        response = requests.get(secrets.SERVER_URL)

        if response.status_code == 200:
            data = response.content
            print("Uspesne stazeno {} bytu".format(len(data)))
            return data

        else:
            print("Chyba serveru: Status {}".format(response.status_code))
            return None

    except Exception as e:
        print("Chyba pri stahovani: {}".format(e))
        return None
    finally:
        if 'response' in locals():
            response.close()

# --- HLAVNÍ SMYČKA ---
try:
    connect_wifi()

    epd = EPD75BMono()
    epd.init()

    while True:
        payload = fetch_payload()
        if payload is not None:
            try:
                epd.display_bw_payload(payload)
                print("Obraz vykreslen na displej.")
            except Exception as e:
                print("Chyba pri vykresleni: {}".format(e))

        print("Cekam {} s do dalsiho refresh...".format(REFRESH_INTERVAL_S))
        time.sleep(REFRESH_INTERVAL_S)

except KeyboardInterrupt:
    print("\nProgram ukoncen uzivatelem.")
    try:
        epd.sleep()
    except Exception:
        pass
except Exception as e:
    print("\nKriticka chyba: {}".format(e))