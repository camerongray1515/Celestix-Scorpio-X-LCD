#!/usr/bin/python
import time
import os
import re
from multiprocessing import Process

def interface_rates(interface, interval=1):
    initial = get_bits_transfered(interface)
    time.sleep(interval)
    current = get_bits_transfered(interface)

    rates = ((current[0]-initial[0])/interval, (current[1]-initial[1])/interval)
    return rates

def get_bits_transfered(interface):
    path = "/sys/class/net/{0}/statistics/".format(interface)

    with open(path + "rx_bytes") as rx_f:
        with open(path + "tx_bytes") as tx_f:
            bytes_transfered = (int(rx_f.read())*8, int(tx_f.read())*8)

    return bytes_transfered

def bits_format(n_bits, per_unit=1024):
    units = ["bit", "kbit", "Mbit", "Gbit"]
    for unit in units:
        if n_bits >= per_unit and unit != units[-1]:
            n_bits /= float(per_unit)
        else:
            return (n_bits, unit)

def lcd_display(message, line=1):
    message = str(message)
    line_selection = "\x00" if line == 1 else "\x01"
    preamble = "\x02\x00\x00{0}\x28\x00\x00\x00".format(line_selection)
    endpad = "\x20"*(40-len(message))

    data = preamble + message + endpad
    with open("/dev/hidraw0", "w") as lcd:
        lcd.write(data)

def lcd_clear():
    lcd_display("", line=1)
    lcd_display("", line=2)

def disp_interface_stats(interface):
    lcd_clear()

    while True:
        path = "/sys/class/net/{0}/".format(interface)
        with open(path + "carrier") as f:
            link_state = "UP" if int(f.read()) else "DOWN"
        with open(path + "address") as f:
            address = f.read().strip()

        top_line = "{0} - {1} - {2}".format(interface, address, link_state)
        lcd_display(top_line, line=1)

        rx, tx = interface_rates(interface, interval=1)
        rx_formatted = bits_format(rx)
        tx_formatted = bits_format(tx)

        rx_str = "{0}{1}/s".format(round(rx_formatted[0], 2), rx_formatted[1])
        tx_str = "{0}{1}/s".format(round(tx_formatted[0], 2), tx_formatted[1])

        bottom_line = "RX: {0:<13} TX: {1}".format(rx_str+",", tx_str)

        lcd_display(bottom_line, line=2)

def get_knob_action():
    with open("/dev/hidraw0", "r") as knob:
        char = knob.read(6)[2]
        if ord(char) == 58: # Pressed
            return "pressed"
        elif ord(char) == 59: # Turned right
            return "right"
        elif ord(char) == 60: # Turned left
            return "left"

def interface_stats():
    interface_index = 0
    interfaces = sorted(os.listdir("/sys/class/net/"))

    while True:
        p = Process(target=disp_interface_stats,
            args=(interfaces[interface_index],))
        p.start()
        action = get_knob_action()
        p.terminate()

        if action == "pressed":
            return
        elif action == "right":
            interface_index = (interface_index + 1) % len(interfaces)
        elif action == "left":
            interface_index = (interface_index - 1) % len(interfaces)

def disp_system_health():
    while True:
        lcd_clear()
        la = os.getloadavg()
        top_line = "CPU Load: {0} {1} {2}".format(la[0], la[1], la[2])

        with open("/sys/class/thermal/thermal_zone0/temp") as temp_f:
            temp = round(int(temp_f.read()) / 1000.0, 1)

        with open("/sys/devices/platform/w83627ehf.656/hwmon/hwmon2/device"
            "/pwm2") as pwm_f:
            fan = round(((float(pwm_f.read()) - 70.0) / 255.0) * 100, 1)

        bottom_line = "Temp: {0}c, Fan: {1}%".format(temp, fan)

        lcd_display(top_line, line=1)
        lcd_display(bottom_line, line=2)
        time.sleep(5)

def system_health():
    p = Process(target=disp_system_health)
    p.start()
    while True:
        action = get_knob_action()
        if action == "pressed":
            p.terminate()
            return

confirm_row_no =  "[No]  Yes "
confirm_row_yes = " No  [Yes]"

def shutdown():
    lcd_display(" System will shut down. Confirm? ".center(40, "-"), line=1)
    confirm = 0
    while True:
        lcd_display((confirm_row_yes if confirm else confirm_row_no).center(40),
            line=2)
        action = get_knob_action()
        if action == "pressed":
            if confirm:
                lcd_clear()
                lcd_display(" SHUTTING DOWN ".center(40, "-"), line=1)
                os.system("/sbin/shutdown -h now")
                # Go back to the menu after some time in case shut down fails
                time.sleep(120)
                return
            else:
                return
        elif action == "right":
            confirm = (confirm + 1) % 2
        elif action == "left":
            confirm = (confirm - 1) % 2

def reboot():
    lcd_display(" System will reboot. Confirm? ".center(40, "-"), line=1)
    confirm = 0
    while True:
        lcd_display((confirm_row_yes if confirm else confirm_row_no).center(40),
            line=2)
        action = get_knob_action()
        if action == "pressed":
            if confirm:
                lcd_clear()
                lcd_display(" REBOOTING ".center(40, "-"), line=1)
                os.system("/sbin/shutdown -r now")
                # Go back to the menu after some time in case reboot fails
                time.sleep(120)
                return
            else:
                return
        elif action == "right":
            confirm = (confirm + 1) % 2
        elif action == "left":
            confirm = (confirm - 1) % 2


def get_vyos_version():
    full = os.popen("/opt/vyatta/bin/vyatta-show-version").read()
    version = re.match(r"Version:\w*([^\n]*)\n", full).group(1).strip()
    return version

def menu():
    menu_items = [
        {"text": "Interface Statistics", "action": interface_stats},
        {"text": "System Health", "action": system_health},
        {"text": "Reboot System", "action": reboot},
        {"text": "Shut down System", "action": shutdown}
    ]
    current_item = 0
    while True:
        lcd_display(" {0} ".format(get_vyos_version()).center(40, "-"), line=1)
        lcd_display("\x0B {0}".format(menu_items[current_item]["text"]), line=2)

        action = get_knob_action()
        if action == "pressed":
            menu_items[current_item]["action"]()
        elif action == "right":
            current_item = (current_item + 1) % len(menu_items)
        elif action == "left":
            current_item = (current_item - 1) % len(menu_items)

if __name__ == "__main__":
    menu()
