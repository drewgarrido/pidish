# pidish
Python script to run a DLP/SLA 3D printer from a Raspberry Pi 2. This
script will read a directory filled with the slice images of an object
to be 3D printed. Then it will control the lift and projector to create
the object.

Currently, the script supports connecting a Big Easy Driver directly to the
PIO on the Raspberry Pi 2, skipping a microcontroller such as an Arduino. The
Raspberry Pi 2 needs to have Python, pygame, and RPi.GPIO installed, which are
native to a Raspbian installation. The script and support Python scripts for
controlling the stepper motor and projector must be in the same directory.

The script runs by the SSH command:
sudo python pidish.py path/to/images

Getting the slice images of the object to the Raspberry Pi 2 must be done
separately. I'm using Samba at the moment to transfer slice images created by
Creation Workshop from my Windows machine to the Raspberry Pi 2.

## Slicers
If you cannot get a copy of Creation Workshop or don't like closed software, I
wrote a [slicer](https://github.com/drewgarrido/pidish_slicer). On the
upside, this slicer finds the best position on the lift. The downside is that
Creation Workshop also offers scaling, rotation, multiple object printing, and
easy support placement in a visual GUI.
