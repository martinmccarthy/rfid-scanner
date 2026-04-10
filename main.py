from mfrc522 import MFRC522
from machine import Pin
from rfidscannerthing import RFIDReader, PresenceSwitch, AudioSystem, LightSystem, VaultController
import utime

SPI_ID = 0
SCK    = 18
MISO   = 16
MOSI   = 19
CS     = 17
RST    = 9

EXPECTED_UID = "[0x32, 0xA1, 0x27, 0x5B]"

BUZZER_PIN  = 22
GREEN_PIN   = 20
RED_PIN     = 21


class HardwareRFIDReader(RFIDReader):
    def __init__(self, slot_id):
        super().__init__(slot_id)
        self._reader = MFRC522(spi_id=SPI_ID, sck=SCK, miso=MISO, mosi=MOSI, cs=CS, rst=RST)
        self._last_uid = None

    def poll(self):
        self._reader.init()
        stat, _ = self._reader.request(self._reader.REQIDL)
        if stat == self._reader.OK:
            stat, uid = self._reader.SelectTagSN()
            if stat == self._reader.OK:
                self._last_uid = self._reader.tohexstring(uid)
                return self._last_uid
        self._last_uid = None
        return None

    def read_uid(self):
        return self._last_uid


class HardwarePresenceSwitch(PresenceSwitch):
    def __init__(self, slot_id, reader: HardwareRFIDReader):
        super().__init__(slot_id)
        self._reader = reader
        self._present = False

    def update(self):
        self._present = self._reader.poll() is not None

    def is_pressed(self):
        return self._present


class HardwareAudioSystem(AudioSystem):
    def __init__(self):
        self._buzzer = Pin(BUZZER_PIN, Pin.OUT)

    def play_success(self):
        for _ in range(2):
            self._buzzer.value(1)
            utime.sleep_ms(100)
            self._buzzer.value(0)
            utime.sleep_ms(100)

    def play_error(self):
        self._buzzer.value(1)
        utime.sleep_ms(500)
        self._buzzer.value(0)


class HardwareLightSystem(LightSystem):
    def __init__(self):
        self._green = Pin(GREEN_PIN, Pin.OUT)
        self._red   = Pin(RED_PIN,   Pin.OUT)

    def set_idle(self):
        self._green.value(0)
        self._red.value(0)

    def set_green(self):
        self._green.value(1)
        self._red.value(0)

    def flash_red(self, flashes=4, interval=0.2):
        self._green.value(0)
        interval_ms = int(interval * 1000)
        for _ in range(flashes):
            self._red.value(1)
            utime.sleep_ms(interval_ms)
            self._red.value(0)
            utime.sleep_ms(interval_ms)


reader  = HardwareRFIDReader(1)
switch  = HardwarePresenceSwitch(1, reader)
audio   = HardwareAudioSystem()
lights  = HardwareLightSystem()

controller = VaultController(
    expected_uid_by_slot={1: EXPECTED_UID},
    required_order=[1],
    readers={1: reader},
    switches={1: switch},
    audio=audio,
    lights=lights,
    reset_delay=2.0,
    poll_interval=0.05,
)

print("Ready. Tap a card...")

while True:
    switch.update()
    controller.tick()
    utime.sleep_ms(50)
