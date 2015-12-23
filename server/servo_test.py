# Copyright (C) 2015  Drew Garrido
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

###############################################################################
#
#   A mock class that simulates servo controls. This enables testing of
#   the webserver without actually running on the RPi
#
###############################################################################
class BED_servo:
    def __init__(self,a): pass
    def nop(*args, **kw): pass
    def __getattr__(self, name):
        print("Servo.{0}".format(name))
        return self.nop
