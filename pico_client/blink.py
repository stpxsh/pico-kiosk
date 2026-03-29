import machine
from utime import sleep

pin = machine.Pin("LED", machine.Pin.OUT)

print("LED starts flashing...")
while True:
    try:
        pin.toggle()
        print(f"LED is {'on' if pin.value() else 'off'}")
        sleep(1) # sleep 1sec
    except KeyboardInterrupt:
        break
pin.off()
print("Finished.")
