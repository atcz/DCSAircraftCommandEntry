'''
*
* logger.py: DCS Aircraft Command Entry - Program Logs Module               *
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

import logging
from sys import stdout


def log_settings(version):
    with open("log.txt", "w+") as f:
        f.write("----settings.ini----\n\n")
        with open("settings.ini", "r") as f2:
            f.writelines(f2.readlines())

        f.write("\n\n--------------------\n\n")
        f.write(f"Program version: {version}\n\n")


def get_logger(name):
    logger = logging.getLogger(name)
    logger.propagate = False
    if logger.hasHandlers(): 
        logger.handlers = []
    formatter = logging.Formatter('%(asctime)s:%(name)s: %(levelname)s - %(message)s')
    s_handler = logging.StreamHandler(stdout)
    s_handler.setFormatter(formatter)
    f_handler = logging.FileHandler("log.txt", encoding="utf-8")
    f_handler.setFormatter(formatter)
    logger.addHandler(f_handler)
    logger.addHandler(s_handler)
    logger.setLevel(logging.DEBUG)

    return logger
