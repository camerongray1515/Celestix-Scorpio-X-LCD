# Celestix Scorpio-X LCD Menu
I own a Celestix Scorpio-X CLB4000 which was originally sold as a load balancer
running a custom Linux-based operating system.  The machine has a very nice
40x2 LCD on the front along with a knob that is used to operate a menu system
on the screen when it is running its factory OS.

On my machine I run VyOS which is based on Debian 6.0 (Squeeze).  This is a
simple Python script that provides a simple menu system on the screen to display
throughputs on each network interface, general system health information as
well as options to shut down and reboot the system.

I imagine this will work with most Linux based operating systems, it won't work
properly on BSD (including PFSense) however the logic for interfacing with the
screen and knob is possibly helpful for implementing a custom driver.

## Compatibility
This is fully compatible with Python 2.6 (the default on VyOS 1.1.7) and does
not require any separate libraries to be installed.

This has been tested under VyOS 1.1.7 which is based on Debian 6.0 (Squeeze).
It may work with other Linux-based operating systems however there is some
custom logic for VyOS (such as displaying the VyOS version on the screen) that
would need to be removed.  It also assumes that the "w83627ehf" kernel module
has been loaded in order to get the fan speed.

## Init Script
An init script is provided in init.d/lcd for running the LCD script as a
system service.

## Disclaimer
This was thrown together fairly quickly in an afternoon - I make no claims that
this is reliable or efficient but it does the job.  There are also possibly some
strange multithreading related bugs that I haven't noticed yet.
