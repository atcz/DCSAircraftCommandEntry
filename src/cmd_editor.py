'''
*
* cmd_editor.py: DCS Aircraft Command Entry - Main DB/Object Module          *
*                                                                           *
* Copyright (C) 2023 Atcz                                                   *
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

from time import sleep
from src.objects import cmd_files, default_cmds
from src.db import DatabaseInterface
from src.logger import get_logger
from src.drivers import DCSBIOSDriver


class CommandEditor:

    def __init__(self, settings):
        self.logger = get_logger("driver")
        self.settings = settings
        self.db = DatabaseInterface(settings['PREFERENCES'].get("DB_Name", "profiles.db"))
        self.default_cmds = default_cmds
        self.cmd_files = cmd_files
        self.drivers = dict(dcsbios=DCSBIOSDriver(self.logger, settings))
        self.driver = self.drivers["dcsbios"]

    def set_driver(self, driver_name):
        try:
            self.driver = self.drivers[driver_name]
        except KeyError:
            raise DriverException(f"Undefined driver: {driver_name}")

    def enter_all(self, profile):
        self.logger.info(f"Sending commands to aircraft: {profile.aircraft}")
        sleep(int(self.settings['PREFERENCES'].get('Grace_Period', 2)))
        self.driver.enter_all(profile)

    def stop(self):
        self.db.close()
        if self.driver is not None:
            self.driver.stop()
