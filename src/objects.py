'''
*
* objects.py: DCS Aircraft Command Entry - Datacmd Objects Module          *
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

from dataclasses import dataclass, asdict
from typing import Any
import json
from os import walk
from src.logger import get_logger
from src.models import ProfileModel, CommandModel, SequenceModel, IntegrityError, db


default_cmds = dict()
cmd_files = dict()

logger = get_logger(__name__)


def get_command_data(group, name):
    logger.info(type(default_cmds))
    command = default_cmds.get(group).get(name)
    logger.info(command)
    


def load_cmd_file(filename, cmddict):
    cmddict.clear()

    with open("./cmd/" + "default.json", "r") as f:
        try:
            load_command_data('default.json', json.load(f), cmddict)
            logger.info(
                f"Command data built succesfully from file: default.json")
        except AttributeError:
            logger.warning(
                f"Failed to get command data from file: {filename}", exc_info=True)
    with open("./cmd/" + filename, "r") as f:
        try:
            load_command_data(filename, json.load(f), cmddict)
            logger.info(
                f"Command data built succesfully from file: {filename}")
        except AttributeError:
            logger.warning(
                f"Failed to get command data from file: {filename}", exc_info=True)

def load_command_data(filename, cmddata, cmddict):
    commands_list = cmddata.get("commands")
    ident = cmddata.get("id")
    if ident:
        logger.info(f"{filename}: {ident['aircraft']}")

    if type(commands_list) == list:
        cmddata = {i: cmd for i, cmd in enumerate(commands_list)}

    for key, _ in commands_list.items():
        cmddict[key] = commands_list[key]

def generate_default_cmds():
    for _, _, files in walk("./cmd"):
        for filename in files:
            if filename.endswith(".json") and filename != 'default.json':
                with open("./cmd/" + filename, "r") as f:
                    try:
                        filedata = json.load(f)
                        commands_list = filedata.get("commands")
                        ident = filedata.get("id")
                        if ident and commands_list:
                            logger.info(f"Command data found in {filename}: {ident['aircraft']}")
                            cmd_files[ident['aircraft']] = filename
                    except AttributeError:
                        logger.warning(
                            f"Failed to get command data from file: {filename}", exc_info=True)


@dataclass
class Command:
    device_type: str = ""
    msg: str = ""
    step: float = None
    limitLow: float = None
    limitHigh: float = None
    description: str = ""
    value: float = None
    number: int = 0
    sequence: int = 0
    wp_type: str = "CMD"

    def __str__(self):
        strrep = f"{self.wp_type}{self.number}"
#        strrep += f" | {self.category}"
        strrep += f" | {self.description}"
        return strrep

    @property
    def as_dict(self):
        d = asdict(self)
        return d

    @staticmethod
    def to_object(command):
        return Command(
            device_type = command.get('device_type'),
            msg = command.get('msg'),
            step = command.get('step'),
            limitLow = command.get('limitLow'),
            limitHigh = command.get('limitHigh'),
            description = command.get('description'),
            value = command.get('value'),
            number = command.get('number'),
            wp_type=command.get('wp_type'),
        )


@dataclass
class MSN(Command):
    station: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.wp_type = "MSN"
        if not self.station:
            raise ValueError("MSN station not defined")

    def __str__(self):
        strrep = f"MSN{self.number} | STA{self.station}"
        if self.name:
            strrep += f" | {self.name}"
        return strrep

    @staticmethod
    def to_object(command):
        return MSN(
            LatLon(
                Latitude(command.get('latitude')),
                Longitude(command.get('longitude'))
            ),
            elevation=command.get('elevation'),
            name=command.get('name'),
            sequence=command.get('sequence'),
            wp_type=command.get('wp_type'),
            station=command.get('station')
        )


class Profile:
    def __init__(self, profilename, commands=None, aircraft=None):
        self.profilename = profilename
        self.aircraft = aircraft

        if commands is None:
            self.commands = list()
        else:
            self.commands = commands
            self.update_command_numbers()

    def __str__(self):
        return json.dumps(self.to_dict())

    def update_sequences(self):
        sequences = set()
        for command in self.commands:
            if type(command) == Command and command.sequence:
                sequences.add(command.sequence)
        sequences = list(sequences)
        sequences.sort()
        return sequences

    @property
    def has_commands(self):
        return len(self.commands) > 0

    @property
    def sequences(self):
        return self.update_sequences()

    @property
    def commands_as_list(self):
        return [wp for wp in self.commands if type(wp) == Command]

    @property
    def all_commands_as_list(self):
        return [wp for wp in self.commands if not isinstance(wp, MSN)]

    @property
    def msns_as_list(self):
        return [wp for wp in self.commands if isinstance(wp, MSN)]

    @property
    def stations_dict(self):
        stations = dict()
        for mission in self.msns_as_list:
            station_msn_list = stations.get(mission.station, list())
            station_msn_list.append(mission)
            stations[mission.station] = station_msn_list
        return stations

    @property
    def commands_dict(self):
        wps_dict = dict()
        for wp in self.commands_as_list:
            wps_list = wps_dict.get(wp.wp_type, list())
            wps_list.append(wp)
            wps_dict[wp.wp_type] = wps_list
        return wps_dict

    @property
    def sequences_dict(self):
        d = dict()
        for sequence_identifier in self.sequences:
            for i, wp in enumerate(self.commands_as_list):
                if wp.sequence == sequence_identifier:
                    wp_list = d.get(sequence_identifier, list())
                    wp_list.append(i+1)
                    d[sequence_identifier] = wp_list

        return d

    def commands_of_type(self):
        return [wp for wp in self.commands]

    def get_sequence(self, identifier):
        return self.sequences_dict.get(identifier, list())

    def to_dict(self):
        return dict(
            commands=[command.as_dict for command in self.commands],
            name=self.profilename,
            aircraft=self.aircraft
        )

    def update_command_numbers(self):
        for _, station_msn_list in self.stations_dict.items():
            for i, mission in enumerate(station_msn_list, 1):
                mission.number = i

        for _, command_list in self.commands_dict.items():
            for i, command in enumerate(command_list, 1):
                command.number = i

    def to_readable_string(self):
        readable_string = "Commands:\n\n"
        for wp in self.commands:
            if wp.wp_type != "MSN":
                readable_string += f"{wp.number} | {wp.msg}"
                readable_string += f" | {wp.description} | {wp.value}\n"

        return readable_string

    @staticmethod
    def from_string(profile_string):
        profile_data = json.loads(profile_string)
        try:
            profile_name = profile_data["name"]
            commands = profile_data["commands"]
            wps = [Command.to_object(w) for w in commands if w['wp_type'] != 'MSN']
            msns = [MSN.to_object(w) for w in commands if w['wp_type'] == 'MSN']
            aircraft = profile_data["aircraft"]
            profile = Profile(profile_name, commands=wps+msns, aircraft=aircraft)
            if profile.profilename:
                profile.save()
            return profile

        except Exception as e:
            logger.error(e)
            raise ValueError("Failed to load profile from data")

    def save(self, profilename=None):
        delete_list = list()
        if profilename is not None:
            self.profilename = profilename

        try:
            with db.atomic():
                profile = ProfileModel.create(
                    name=self.profilename, aircraft=self.aircraft)
        except IntegrityError:
            profile = ProfileModel.get(
                ProfileModel.name == self.profilename)
        profile.aircraft = self.aircraft

        for command in profile.commands:
            delete_list.append(command)

        for sequence in profile.sequences:
            delete_list.append(sequence)

        sequences_db_instances = dict()
        for sequencenumber in self.sequences:
            sequence_db_instance = SequenceModel.create(
                identifier=sequencenumber,
                profile=profile
            )
            sequences_db_instances[sequencenumber] = sequence_db_instance

        for command in self.commands:
            if not isinstance(command, MSN):
                sequence = sequences_db_instances.get(command.sequence)
                CommandModel.create(
                    device_type=command.device_type,
                    msg=command.msg,
                    step=command.step,
                    limitLow=command.limitLow,
                    limitHigh=command.limitHigh,
                    description=command.description,
                    value=command.value,
                    wp_type=command.wp_type,
                    profile=profile
                )
            else:
                CommandModel.create(
                    name=command.name,
                    latitude=command.position.lat.decimal_degree,
                    longitude=command.position.lon.decimal_degree,
                    elevation=command.elevation,
                    profile=profile,
                    wp_type=command.wp_type,
                    station=command.station
                )

        for instance in delete_list:
            instance.delete_instance()
        profile.save()

    @staticmethod
    def load(profile_name):
        profile = ProfileModel.get(ProfileModel.name == profile_name)
        aircraft = profile.aircraft

        wps = list()
        for command in profile.commands:
            try:
                sequence = command.sequence.identifier
            except AttributeError:
                sequence = 0

            if command.wp_type != "MSN":
                wp = Command(device_type=command.device_type,
                             msg=command.msg,
                             step=command.step,
                             limitLow=command.limitLow,
                             limitHigh=command.limitHigh,
                             description=command.description,
                             value=command.value,
                             wp_type=command.wp_type)
            else:
                wp = MSN(LatLon(Latitude(command.latitude), Longitude(command.longitude)),
                         elevation=command.elevation, name=command.name, sequence=sequence,
                         wp_type=command.wp_type, station=command.station)
            wps.append(wp)

        profile = Profile(profile_name, commands=wps, aircraft=aircraft)
        profile.update_command_numbers()
        logger.debug(
            f"Fetched {profile_name} from DB, with {len(wps)} commands")
        return profile

    @staticmethod
    def delete(profile_name):
        profile = ProfileModel.get(name=profile_name)

        for command in profile.commands:
            command.delete_instance()

        profile.delete_instance(recursive=True)

    @staticmethod
    def list_all():
        return list(ProfileModel.select())
