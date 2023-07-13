'''
*
* dcs_ace.py: DCS Aircraft Command Entry                                    *
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

from configparser import ConfigParser
from src.logger import get_logger, log_settings
from src.cmd_editor import CommandEditor
from src.gui import GUI, exception_gui, check_version
from src.first_setup import first_time_setup
from src.objects import generate_default_cmds
import traceback
import logging
from pyproj import datadir, _datadir


version = "1.0.0b1"


def main():
    try:
        open("settings.ini", "r").close()
        settings_found = True
    except FileNotFoundError:
        settings_found = False

    update_exit = check_version(version)
    if update_exit:
        return

    setup_completed = settings_found or first_time_setup(None)

    if setup_completed:
        generate_default_cmds()
        log_settings(version)
        settings = ConfigParser()
        settings.read("settings.ini")
        editor = CommandEditor(settings)

        gui = GUI(editor, version)

        try:
            gui.run()
        except Exception:
            gui.close()
            raise


if __name__ == "__main__":
    logger = get_logger("root")
    logger.info("Initializing")

    try:
        main()
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logging.shutdown()
        exception_gui(traceback.format_exc())
        raise

    logger.info("Finished")
