building with micropico:

i use micropico with visual studio code since the extension is pretty intuitive:

To Install MicroPico with visual studio code:
https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go


to run code all you need to do is right click the python file and hit run python file on board or something similar, do this for:
blink.py to print the UIDs of all the scannable items
place these UIDs into main.py in the required uid section


To Flash MicroPython Firmware (should already have this but if for whatever reason the thing is tweaking)
	1.	Hold BOOTSEL button on the Pico
	2.	Plug it into your computer
	3.	It appears as a USB drive
	4.	Drag and drop the MicroPython .uf2 firmware file
