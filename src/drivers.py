'''
*
* drivers.py: DCS Aircraft Command Entry - DCS-BIOS Interface Module        *
*                                                                           *
* Copyright (C) 2024 Atcz                                                   *
*                                                                           *
* This program is free software: you can redistribute it and/or modify it   *
* under the terms of the GNU General Public License as published by the     *
* Free Software Foundation, either version 3 of the License, or (at your    *
* option) any later version.                                                *
*                                                                           *
* This program is distributed in the hope that it will be useful, but       *
* WITHOUT ANY WARRANTY; without even the implied warranty of                *
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General  *
* Public License for more details.                                          *
*                                                                           *
* You should have received a copy of the GNU General Public License along   *
* with this program. If not, see <https://www.gnu.org/licenses/>.           *
'''

import socket
from time import sleep
from configparser import NoOptionError
from src.gui import data_error_gui, progress_gui

class DriverException(Exception):
    pass

class Driver:
    def __init__(self, logger, config, host="127.0.0.1", port=7778):
        self.logger = logger
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host, self.port = host, port
        self.config = config

        try:
            self.short_delay = float(self.config.get("PREFERENCES", "button_release_short_delay"))
            self.medium_delay = float(self.config.get("PREFERENCES", "button_release_medium_delay"))
        except NoOptionError:
            self.short_delay, self.medium_delay = 0.3, 0.5

    def press_with_delay(self, key, delay_after=None, delay_release=None, raw=False):
        if not key:
            return False

        if delay_after is None:
            delay_after = self.short_delay

        if delay_release is None:
            delay_release = self.short_delay

        encoded_str = key.encode("utf-8")                                                              
        if raw:
            sent = self.s.sendto(f"{key}\n".encode("utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 1
        else:
            sent = self.s.sendto(f"{key} 1\n".encode("utf-8"), (self.host, self.port))
            sleep(delay_release)

            self.s.sendto(f"{key} 0\n".encode("utf-8"), (self.host, self.port))
            strlen = len(encoded_str) + 3

        sleep(delay_after)
        return sent == strlen

    def validate_command(self, command):
        try:
            return command.msg in self.command_detail
        except KeyError:
            return False

    def validate_commands(self, commands):
        for command in commands[:]:
            if not self.validate_command(command):
                self.logger.info(f"Remove {command}")
                commands.remove(command)
        return sorted(commands, key=lambda wp: wp.wp_type)

    def stop(self):
        self.s.close()


class DCSBIOSDriver(Driver):
    def __init__(self, logger, config):
        super().__init__(logger, config)

    def _3PosTumb(self, wp):
        val = int(float(wp.value)) if wp.value not in (None, '') else int(float(wp.limitHigh))
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)

    def FixedStepTumb(self, wp):
        val = float(wp.value) if wp.value not in (None, '') else float(wp.limitHigh)
        val = "DEC" if val < 0 else "INC"
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)

    def Springloaded_3PosTumb(self, wp):
        val = int(float(wp.value)) if wp.value not in (None, '') else int(float(wp.limitHigh))
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)
        key=f"{wp.msg} 1"
        self.press_with_delay(key, raw=True)

    def Tumb(self, wp):
        val = float(wp.value) if wp.value not in (None, '') else float(wp.step)
        val = round(float(val) / float(wp.step))
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)

    def _3Pos2CommandSwitchA10(self, wp):
        val = int(wp.value) if wp.value not in (None, '')  else int(float(wp.limitHigh))
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        if val == 0:
            self.press_with_delay(key, raw=True)
            sleep(7)
            key = key[:-1] + '1'
            self.press_with_delay(key.replace('0', '1'), raw=True)
        else:
            self.press_with_delay(key, raw=True)

    def EmergencyParkingBrake(self, wp):
        val = int(wp.value) if wp.value not in (None, '') else int(float(wp.limitHigh))
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        if wp.value == 2:
            self.press_with_delay(key, raw=True)
            self.press_with_delay(f"{wp.msg} 0", raw=True)
        else:
            self.press_with_delay(key, raw=True)

    def MultipositionSwitch(self, wp):
        val = int(float(wp.value)) if wp.value not in (None, '') else int(wp.limitLow)
        val = val - 1
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)

    def Potentiometer(self, wp):
        val = float(wp.value) if wp.value not in (None, '') else float(wp.limitHigh)
        interval = float(wp.limitHigh) - float(wp.limitLow)
        val = (val - float(wp.limitLow)) / interval * 65535
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)

    def Rotary(self, wp):
        val = int(float(wp.value)) if wp.value not in (None, '') else 65535
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)

    def PushButton(self, wp, delay_after=None, delay_release=None):
        if wp.value not in (None, '')  and int(float(wp.value)) == 1:
            key=f"{wp.msg} 1"
            self.logger.info(f"Sending {key}")
            self.press_with_delay(key, delay_after=delay_after, delay_release=delay_release, raw=True)
        else:
            self.logger.info(f"Sending {wp.msg}")
            self.press_with_delay(wp.msg, delay_after=delay_after, delay_release=delay_release)

    def ToggleSwitch(self, wp):
        val = int(float(wp.value)) if wp.value not in (None, '') else 1
        key=f"{wp.msg} {val}"
        self.logger.info(f"Sending {key}")
        self.press_with_delay(key, raw=True)

    def Pause(self, wp):
        val = float(wp.value) if wp.value not in (None, '') else float(wp.limitHigh)
        self.logger.info(f"Sending Pause {val}")
        sleep(val)

    def enter_commands(self, wps):

    # TODO list

        Devices = {
                    '3PosMossi': self._3PosTumb,
                    '3PosTumb': self._3PosTumb,
                    '3PosTumb1': self._3PosTumb,
                    '3PosTumbA10': self._3PosTumb,
                    '3PosTumb0To1': self.MultipositionSwitch,
                    '3Pos2CommandSwitchA10': self._3Pos2CommandSwitchA10,
                    '3Pos2CommandSwitchF5': self._3PosTumb,
                    'CMSPSwitch': self.ToggleSwitch,
                    'DoubleCommandButton': self.FixedStepTumb,
                    'EjectionHandleSwitch': self.ToggleSwitch,
                    'ElectricallyHeldSwitch': self.ToggleSwitch,
                    'EmergencyParkingBrake': self.EmergencyParkingBrake,
                    'FixedStepInput': self.FixedStepTumb,
                    'FixedStepTumb': self.FixedStepTumb,
                    'LedPushButton': self.PushButton,
                    'InputOnlyPushButton': self.PushButton,
                    'MissionComputerSwitch': self._3PosTumb,
                    'MomentaryRockerSwitch': self.Springloaded_3PosTumb,
                    'MultipositionSwitch': self.MultipositionSwitch,
                    'MultipositionSwitch0To1': self.MultipositionSwitch,
                    'MultipositionRollerLimited': self.Tumb,
                    'Potentiometer': self.Potentiometer,
                    'Potentiometer2': self.Potentiometer,
                    'PushButton': self.PushButton,
                    'RadioWheel': self.FixedStepTumb,
                    'RockerSwitch': self.Springloaded_3PosTumb,
                    'RockerSwitchMossi': self.Springloaded_3PosTumb,
                    'Rotary': self.Rotary,
                    'RotaryPlus': self.Rotary,
                    'SetCommandTumb': self.Tumb,
                    'Springloaded_2PosTumb': self.Springloaded_3PosTumb,
                    'Springloaded_3PosTumb': self.Springloaded_3PosTumb,
                    'Springloaded_3PosTumbWithRange': self.Springloaded_3PosTumb,
                    'Springloaded3PosTumb': self.Springloaded_3PosTumb,
                    'ToggleSwitch': self.ToggleSwitch,
                    'ToggleSwitchToggleOnly': self.ToggleSwitch,
                    'ToggleSwitchToggleOnly2': self.ToggleSwitch,
                    'Tumb': self.Tumb,
                    'VariableStepTumb': self.Rotary,
                    # User defined
                    'Pause': self.Pause,
                  }

        pwindow = progress_gui(len(wps), self.pposition)

        i = 1
        for wp in wps:
            event, values = pwindow.Read(timeout=20)
            if event is None or event == 'Cancel':
                pwindow.close()
                return
            self.logger.info(f"Entering command: {wp}")
            try:
                Devices[wp.device_type](wp)
            except KeyError:
                self.logger.info(f"Unsupported device: {wp.device_type}")
            except Exception as e:
                self.logger.error(e, exc_info=True)
                data_error_gui(wp, e)
            pwindow['progress'].update(i)
            i += 1

        pwindow.close()

    def enter_all(self, profile):
        self.enter_commands(self.validate_commands(profile.commands_as_list))
