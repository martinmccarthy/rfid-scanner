from mfrc522 import MFRC522
import utime

reader = MFRC522(spi_id=0, sck=18, miso=16, mosi=19, cs=17, rst=9)

print("Ready. Tap a 13.56MHz card/tag...")

while True:
    reader.init()
    (stat, tag_type) = reader.request(reader.REQIDL)
    if stat == reader.OK:
        (stat, uid) = reader.SelectTagSN()
        if stat == reader.OK:
            print("UID:", reader.tohexstring(uid))
            utime.sleep_ms(500)

    utime.sleep_ms(50)
