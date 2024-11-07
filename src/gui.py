'''
*
* gui.py: DCS Aircraft Command Entry - Main GUI Module                      *
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

from src.objects import Profile, Command, load_cmd_file, get_command_data
from src.first_setup import first_time_setup
from src.logger import get_logger
from peewee import DoesNotExist
from decimal import Decimal
import keyboard
import urllib.request
import urllib.error
import webbrowser
import json
import base64
from packaging import version
import pyperclip
import PySimpleGUI as sg
import re
import winsound
import zlib

UX_SND_ERROR = "data/ux_error.wav"
UX_SND_SUCCESS = "data/ux_success.wav"


def str_zip(s):
    return base64.encodebytes(zlib.compress(s.encode('utf-8'))).decode('ascii')


def str_unzip(s):
    return zlib.decompress(base64.b64decode(s)).decode('utf-8')


def strike(text):
    return '\u0336'.join(text) + '\u0336'


def unstrike(text):
    return text.replace('\u0336', '')


def exception_gui(exc_info):
    return sg.PopupOK(f"An exception occurred and the program terminated execution:\n\n{exc_info}")


def data_error_gui(name, err_info):
    return sg.PopupOK(f"An error occurred processing {name}.\n{err_info}")


def progress_gui(count, location):
    progress_layout = [
        [sg.Text('Processing:')],
        [sg.ProgressBar(count, orientation='h', size=(20, 20), key='progress')],
        [sg.Cancel()]
    ]
    return sg.Window('Progress Indicator', progress_layout, location=location, modal=True, finalize=True)

def check_version(current_version):
    version_url = "https://raw.githubusercontent.com/atcz/DCSAircraftCommandEntry/main/release_version.txt"
    releases_url = "https://github.com/atcz/DCSAircraftCommandEntry/releases"

    try:
        with urllib.request.urlopen(version_url) as response:
            if response.code == 200:
                html = response.read()
            else:
                return False
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False

    git_version = html.decode("utf-8")
    if version.parse(current_version) < version.parse(git_version):
        popup_answer = sg.PopupYesNo(f"New version available: {git_version}\nDo you wish to update?")

        if popup_answer == "Yes":
            webbrowser.open(releases_url)
            return True
        else:
            return False


def try_get_setting(settings, setting_name, setting_fallback, section="PREFERENCES"):
    if settings.has_option(section, setting_name):
        return settings.get(section, setting_name)
    else:
        settings[section][setting_name] = setting_fallback
        with open("settings.ini", "w") as configfile:
            settings.write(configfile)
        return setting_fallback


class GUI:
    def __init__(self, editor, software_version):
        self.logger = get_logger("gui")
        self.editor = editor
        self.profile = Profile('')
        self.values = None
        self.command_key = dict()
        self.command_detail = dict()
        self.enter_aircraft_hotkey = try_get_setting(self.editor.settings, "enter_aircraft_hotkey", "")
        self.pysimplegui_theme = try_get_setting(self.editor.settings, "pysimplegui_theme", sg.theme())
        self.default_aircraft = try_get_setting(self.editor.settings, "default_aircraft", "")
        self.software_version = software_version
        self.profile.aircraft = self.default_aircraft
        self.editor.set_driver("dcsbios")

        self.window = self.create_gui()
        if self.enter_aircraft_hotkey != '':
            self.hotkey_ispressed = False
            keyboard.add_hotkey(self.enter_aircraft_hotkey, self.set_enter_aircraft_flag)

    @staticmethod
    def get_profile_names():
        return [profile.name for profile in Profile.list_all()]

    def calculate_popup_position(self, popup_window_size):
        main_x, main_y = self.window.CurrentLocation()
        main_width, main_height = self.window.Size
        popup_width, popup_height = popup_window_size

        popup_x = main_x + (main_width - popup_width) // 2
        popup_y = main_y + (main_height - popup_height) // 2

        return popup_x, popup_y

    def create_gui(self):
        self.logger.debug("Creating GUI")
        
        sg.theme(self.pysimplegui_theme)

        command_col1 = [
            [sg.Text("Device:", pad=((9,5),3)), 
             sg.InputText(size=(5, 1), key="device", pad=((5,5),3), readonly=True),
             sg.Text("Code:", pad=((9,5),3)), 
             sg.InputText(size=(5, 1), key="code", pad=((5,5),3), readonly=True),
             sg.Text("Type:", pad=((9,5),3)), 
             sg.InputText(size=(20, 1), key="type", pad=((5,5),3), readonly=True),
             sg.Text("Name:", pad=((9,5),3)), 
             sg.InputText(size=(20, 1), key="name", pad=((5,5),3), readonly=True)],
        ]

        values_col1 = [
            [sg.Text("Min:", pad=((9,9),3)), 
             sg.InputText(size=(8, 1), key="min", pad=((9,5),3), readonly=True),
             sg.Text("Max:", pad=((9,5),3)), 
             sg.InputText(size=(8, 1), key="max", pad=((9,5),3), readonly=True),
             sg.Text("Step:", pad=((9,5),3)), 
             sg.InputText(size=(8, 1), key="step", pad=((9,5),3), readonly=True)]
        ]

        values_col2 = [
            [sg.Text("Setting:", pad=((5,5),3)), 
             sg.InputText(size=(5, 1), key="setValue", pad=((9,5),3), readonly=False),
             sg.Text("Range:", pad=((5,5),3)),
             sg.Combo(values=list(), readonly=True, enable_events=True, key='rangeSelector',
                      size=(5,1), pad=((9,5),3))]
        ]

        framedatalayout = [
            [sg.Listbox(values=list(), size=(48, 14),
                           enable_events=True, key='commandSelector')]
        ]

        framegrouplayout = [
            [sg.Text("Select group:")],
            [sg.Combo(values=[""] + sorted(self.editor.default_cmds), readonly=False,
                        enable_events=True, key='groupSelector', size=(28,1)),
             sg.Button(button_text="F", key="groupFilter")]
        ]

        frameaircraftlayout = [
            [sg.Text("Select aircraft:")],
            [sg.Combo(sorted(self.editor.cmd_files), readonly=True,
                         enable_events=True, key='aircraftSelector', size=(10,1), pad=(6, 6))]
        ]

        buttonslist = [
            sg.Button('Up', size=(4, 1), key='Up', pad=((12,6),3)),
            sg.Button('Down', size=(4, 1), key='Down'),
            sg.Button('Insert', size=(7,1), key='Insert'),
            sg.Button('Remove', size=(7, 1)),
            sg.Button('Pause', size=(8, 1), pad=((28,6),3)),
            sg.Button('Update', size=(8, 1)),
            sg.Button('Add', size=(8, 1)),
            sg.Button('Send To Aircraft', size=(14, 1), key='Send'),
        ]

        framelimit = sg.Frame("Limit Values", [
            [sg.Column(values_col1),
            ]
        ])

        framevalue = sg.Frame("Command Value", [
            [sg.Column(values_col2),
            ]
        ])

        framedcsbios = sg.Frame("DCS-BIOS Details", [
            [sg.Column(command_col1),
            ]
        ])

        framecommandlayout = [
            [framedcsbios],
            [framelimit, framevalue],
        ]

        framecommand = sg.Frame("Command Details", framecommandlayout)
        framegroup = sg.Frame("Groups", framegrouplayout)
        frameaircraft = sg.Frame("Aircraft", frameaircraftlayout)
        framedata = sg.Frame("Commands", framedatalayout)

        col0 = [
            [sg.Text("Select profile:")],
            [sg.Combo(values=[""] + sorted(self.get_profile_names()), readonly=False,
                         enable_events=True, key='profileSelector', size=(29, 1)),
             sg.Button(button_text="F", key="profileFilter")],
            [sg.Listbox(values=list(), size=(33, 17),
                           enable_events=True, key='activesList')],
        ]

        col1 = [
            [frameaircraft, framegroup],
            [framedata],
        ]

        menudef = [['&File',
                    ['&Settings', '---', 'E&xit']],
                   ['&Profile',
                    ['&Save Profile', '&Delete Profile', 'Save Profile &As...', '---',
                        '&Import', ['Paste as &String from clipboard', 'Load from &Encoded file'],
                        '&Export', ['Copy as &String to clipboard', 'Copy plain &Text to clipboard',
                                    'Save as &Encoded file', 'Save &All as Encoded file']]],
                   ['&?',
                    ['&About']]
                  ]

        colmain1 = [
            [sg.MenuBar(menudef)],
            [sg.Column(col1)],
        ]

        layout = [
            [sg.Column(col0), sg.Column(colmain1)],
            [buttonslist],
            [framecommand],
            [sg.Text(f"Version: {self.software_version}")]
        ]

        return sg.Window('DCS Aircraft Command Entry', layout, finalize=True)

    def update_command_data(self, item=None, value=None):
        val_list = list()
        if item is not None:
            #set device
            device = item['device_id']

            #set code
            if 'command' in item:
                code = item['command']
            else:
                for val in item.values():
                    if val.isdigit() and len(val) == 4:
                        code = val
                        continue

            dev_type = item['type']
            name = item['msg']

            #set val_min, val_max
            if dev_type in ("EjectionSeatHandle", "ToggleSwitch", "ToggleSwitchToggleOnly", "ToggleSwitchToggleOnly2",
                            "ElectricallyHeldSwitch", "CMSPSwitch", "PushButton", "LedPushButton", "DoubleCommandButton",
                            "Springloaded_2PosTumb"):
                (val_min, val_max) = (0, 1)
            elif dev_type in ("3PosTumb", "3PosTumb1", "3Pos2CommandSwitchA10", "Springloaded_3PosTumb", "3PosMossi",
                            "EmergencyParkingBrake", "MissionComputerSwitch", "RockerSwitch", "MomentaryRockerSwitch",
                            "3Pos2CommandSwitchF5"):
                (val_min, val_max) = (0, 2)
            elif dev_type == 'MultipositionSwitch':
                val_max = item['num_positions']
                val_min = 1
            elif dev_type in ("FixedStepInput", "FixedStepTumb"):
                #get rel_args
                self.logger.info(f"Getting rel_args {item['rel_args']}")
                match = re.match(r'{\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\s*}', item['rel_args'])
                val_min = match.group(1)
                val_max = match.group(2)
            else:
                #look for limits
                try:
                    match = re.match(r'{\s*(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\s*}', item['limits'])
                    val_min = match.group(1)
                    val_max = match.group(2)
                except:
                    val_min, val_max = ("", "")

            #set step
            if 'step' in item:
                step = item['step']
            elif 'increment' in item:
                step = item['increment']
            else:
                step = ""
        else:
            device = ""
            code = ""
            dev_type = ""
            name = ""
            val_min = ""
            val_max = ""
            step = ""

        #adjust specific values and create pulldown list
        if re.search(r'\d', str(val_min)) and re.search(r'\d', str(val_max)):
            if dev_type in ("Potentiometer", "Pause"):
                step = (Decimal(val_max) - Decimal(val_min)) / 5
            elif dev_type == "MultipositionSwitch":
                step = 1
            elif dev_type in ("FixedStepInput", "FixedStepTumb"):
                step = val_max
            else:
                step = step or 1
            current_step = Decimal(val_min)
            while current_step <= Decimal(val_max):
                val_list.append(current_step)
                current_step += Decimal(step)

        #update window
        self.window.Element("device").Update(device)
        self.window.Element("code").Update(code)
        self.window.Element("type").Update(dev_type)
        self.window.Element("name").Update(name)
        self.window.Element("min").Update(val_min)
        self.window.Element("max").Update(val_max)
        self.window.Element("step").Update(step)
        self.window.Element("setValue").Update(value)
        self.window.Element("rangeSelector").Update(values=[""] + val_list, set_to_index=0)

    def update_command_list(self, category=None, refresh=True):
        cmd = list()
        if category != [''] and category is not None:
            for i in category:
                for key,val in self.editor.default_cmds[i].items():
                    try:
                        cmd.append(val['description'])
                        self.command_key[val['description']] = key
                        self.command_detail[val['msg']] = val
                    except:
                        self.logger.info(f'Error {self.editor.default_cmds[i]}')
        if refresh:
            self.window.Element("commandSelector").Update(sorted(cmd))
            self.update_command_data(None)

    def update_profile_commands(self, set_to_first=False):
        values = list()
        self.profile.update_command_numbers()

        for wp in sorted(self.profile.commands,
                         key=lambda command: command.wp_type if command.wp_type != "MSN" else str(command.station)):
            namestr = str(wp)

            if not wp.msg in self.command_detail:
                namestr = strike(namestr)

            values.append(namestr)

        if set_to_first:
            self.window.Element('activesList').Update(values=values, set_to_index=0)
        else:
            self.window.Element('activesList').Update(values=values)

    def filter_groups_dropdown(self):
        text = self.values["groupSelector"]
        self.window.Element("groupSelector").Update\
            (values=[""] + sorted(filter(lambda group: text.lower() in group.lower(), self.editor.default_cmds)),
             set_to_index=0)

    def filter_profile_dropdown(self):
        text = self.values["profileSelector"]
        self.window.Element("profileSelector").Update\
            (values=[""] + sorted([profile.name for profile in Profile.list_all()
             if text.lower() in profile.name.lower()]), set_to_index=0)

    def move_command_up(self):
        reorder = list()
        wp = self.find_selected_command()
        wp_number = wp.as_dict['number']
        if wp_number > 1:
            for w in self.profile.commands:
                if w.number < wp_number - 1 or w.number > wp_number:
                    reorder.append(w)
                elif w.number == wp_number - 1:
                    movedown = w
                elif w.number == wp_number:
                    reorder.append(w)
                    reorder.append(movedown)
            self.profile.commands = reorder
            self.update_profile_commands()

    def move_command_down(self):
        reorder = list()
        wp = self.find_selected_command()
        wp_number = wp.as_dict['number']
        if wp_number < len(self.profile.commands):
            for w in self.profile.commands:
                if w.number < wp_number or w.number > wp_number + 1:
                    reorder.append(w)
                elif w.number == wp_number:
                    movedown = w
                elif w.number == wp_number + 1:
                    reorder.append(w)
                    reorder.append(movedown)
            self.profile.commands = reorder
            self.update_profile_commands()

    def add_command(self, name, value=None):
        try:
            wp = Command(device_type=self.values.get('type'),
                         msg=self.values.get('name'),
                         step=self.values.get('step'),
                         limitLow=self.values.get('min'),
                         limitHigh=self.values.get('max'),
                         description=self.command_detail[name].get('description'),
                         value=self.values.get('setValue'),
                         number=len(self.profile.commands_of_type())+1)
            self.profile.commands.append(wp)
            self.update_profile_commands()
        except (KeyError, ValueError):
            self.winpos = self.window.CurrentLocation()
            psize = (273, 101)
            pposition = self.calculate_popup_position(psize)
            sg.Popup("Error: missing data or invalid data format.", location=pposition)

        return True

    def insert_command(self, name, value=None):
        reorder = list()
        try:
            wp = self.find_selected_command()
            wp_number = wp.as_dict['number']
            wp = Command(device_type=self.values.get('type'),
                         msg=self.values.get('name'),
                         step=self.values.get('step'),
                         limitLow=self.values.get('min'),
                         limitHigh=self.values.get('max'),
                         description=self.command_detail[name].get('description'),
                         value=self.values.get('setValue'),
                         number=len(self.profile.commands_of_type())+1)
            for w in self.profile.commands:
                if w.number == wp_number:
                    reorder.append(wp)
                reorder.append(w)
            self.profile.commands = reorder
            self.update_profile_commands()
        except (KeyError, ValueError):
            self.winpos = self.window.CurrentLocation()
            psize = (273, 101)
            pposition = self.calculate_popup_position(psize)
            sg.Popup("Error: missing data or invalid data format.", location=pposition)

        return True

    def export_to_string(self):
        dump = str(self.profile)
        encoded = str_zip(dump)
        pyperclip.copy(encoded)
        self.winpos = self.window.CurrentLocation()
        psize = (313, 101)
        pposition = self.calculate_popup_position(psize)
        sg.Popup('Encoded string copied to clipboard, paste away!', location=pposition)

    def import_from_string(self):
        # Load the encoded string from the clipboard
        encoded = pyperclip.paste()
        self.winpos = self.window.CurrentLocation()
        psize = (313, 101)
        pposition = self.calculate_popup_position(psize)
        try:
            decoded = str_unzip(encoded)
            self.profile = Profile.from_string(decoded)
            self.logger.debug(self.profile.to_dict())
            self.set_aircraft(self.profile.aircraft)
            self.update_profile_commands(set_to_first=True)
            self.update_profiles_list(self.profile.profilename)
            sg.Popup('Loaded command data from encoded string successfully.', location=pposition)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            sg.Popup('Failed to parse profile from string.', location=pposition)

    def export_to_file(self, obj):
        self.winpos = self.window.CurrentLocation()
        psize = (431, 133)
        pposition = self.calculate_popup_position(psize)
        filename = sg.PopupGetFile("Enter file name", "Exporting profile", default_extension=".json",
                                    save_as=True, location=pposition, file_types=(("JSON File", "*.json"),))
        if filename is None:
            return

        psize = (365, 101)
        pposition = self.calculate_popup_position(psize)
        try:
            with open(filename, "w+") as f:
                f.write(str(obj))
        except IOError:
            sg.Popup(f"Error writing file {filename}", location=pposition)
        else:
            sg.Popup(f"JSON encoded file saved: {filename}", location=pposition)

    def export_db_to_file(self):
        dbdump = list()
        profiles = self.get_profile_names()
        for name in profiles:
            profile = Profile.load(name)
            dbdump.append(json.loads(str(profile)))
        json_string = json.dumps([profile for profile in dbdump], indent=4)
        self.export_to_file(json_string)

    def load_from_file(self):
        self.winpos = self.window.CurrentLocation()
        psize = (431, 133)
        pposition = self.calculate_popup_position(psize)
        filename = sg.PopupGetFile("Enter file name:", "Importing profile", location=pposition)
        if filename is None:
            return
        try:
            with open(filename, "r") as f:
                filedata = json.loads(f.read())
                if type(filedata) == list:
                    proceed = sg.PopupOKCancel(f"File {filename} contains {len(filedata)} profiles.\n"\
                                                "Existing profiles with the same name will be overwritten!\nProceed?",
                                                location=pposition)
                    if proceed == "OK":
                        for to_load in filedata:
                            self.profile = Profile.from_string(json.dumps(to_load))
                else:
                    self.profile = Profile.from_string(json.dumps(filedata))
                self.set_aircraft(self.profile.aircraft)
                self.update_profile_commands()
        except IOError:
            sg.Popup(f"Error reading file {filename}", location=pposition)
        except json.JSONDecodeError:
            sg.Popup(f"Error in JSON data.", location=pposition)
        if self.profile.profilename:
            self.update_profiles_list(self.profile.profilename)

    def load_new_profile(self):
        self.profile = Profile('', aircraft=self.profile.aircraft)

    def write_profile(self):
        self.winpos = self.window.CurrentLocation()
        psize = (351, 133)
        pposition = self.calculate_popup_position(psize)
        profiles = self.get_profile_names()
        overwrite = "OK"
        name = sg.PopupGetText("Enter profile name:", "Saving profile", location=pposition)
        if name in profiles:
            overwrite = sg.PopupOKCancel(f"Profile {name} already exists, overwrite?", location=pposition)
        if name and overwrite == "OK":
            self.profile.save(name)
            self.update_profiles_list(name)

    def update_profiles_list(self, name):
        profiles = sorted(self.get_profile_names())
        self.window.Element("profileSelector").Update(values=[""] + profiles,
                                                      set_to_index=profiles.index(name) + 1)

    def find_selected_command(self):
        valuestr = unstrike(self.values['activesList'][0])
        for wp in self.profile.commands:
            if str(wp) == valuestr:
                return wp

    def remove_selected_command(self):
        valuestr = unstrike(self.values['activesList'][0])
        for wp in self.profile.commands:
            if str(wp) == valuestr:
                self.profile.commands.remove(wp)

    def set_aircraft(self, aircraft=None):
        if aircraft in self.editor.cmd_files:
            load_cmd_file(self.editor.cmd_files[aircraft], self.editor.default_cmds)
        self.command_detail = dict()
        sorted_group = sorted(self.editor.default_cmds)
        self.update_command_list(sorted_group, refresh=False)

        self.window.Element("groupSelector").\
            Update(values=[""] + sorted_group, set_to_index=0)
        self.update_command_list(None)
        self.profile.aircraft = aircraft
        self.window.Element("aircraftSelector").Update(value=aircraft)
        self.update_profile_commands()

    def enter_commands_to_aircraft(self):
        psize = (250, 194)
        self.editor.driver.pposition = self.calculate_popup_position(psize)
        self.editor.driver.command_detail = self.command_detail
        self.window.Element('Send').Update(disabled=True)
        try:
            self.editor.enter_all(self.profile)
            winsound.PlaySound(UX_SND_SUCCESS, flags=winsound.SND_FILENAME)
        except Exception as e:
            winsound.PlaySound(UX_SND_ERROR, flags=winsound.SND_FILENAME)
            psize = (351, 301)
            pposition = self.calculate_popup_position(psize)
            sg.Popup(f"Error: {e}", location=pposition)
        self.window.Element('Send').Update(disabled=False)

    def set_enter_aircraft_flag(self):
        self.hotkey_ispressed = True
        winsound.PlaySound(UX_SND_SUCCESS, flags=winsound.SND_FILENAME)

    def run(self):
        self.window.Element("aircraftSelector").Update(value=self.default_aircraft)
        self.set_aircraft(self.default_aircraft)
        while True:
            event, self.values = self.window.Read(timeout=750)

            if self.hotkey_ispressed:
                self.hotkey_ispressed = False
                self.enter_commands_to_aircraft()

            if event != "__TIMEOUT__":
                self.logger.debug(f"Event: {event}")
                self.logger.debug(f"Values: {self.values}")

                if event is None or event == 'Exit':
                    self.logger.info("Exiting...")
                    break

                elif event == "Settings":
                    first_time_setup(self.editor.settings)
                    self.default_aircraft = try_get_setting(self.editor.settings, "default_aircraft", "")

                elif event == "Copy as String to clipboard":
                    self.export_to_string()

                elif event == "Paste as String from clipboard":
                    self.import_from_string()

                elif event == "Copy plain Text to clipboard":
                    profile_string = self.profile.to_readable_string()
                    pyperclip.copy(profile_string)
                    self.winpos = self.window.CurrentLocation()
                    psize = (264, 133)
                    pposition = self.calculate_popup_position(psize)
                    sg.Popup("Profile copied as plain text to clipboard.", location=pposition)

                elif event == "Up":
                    if self.values['activesList']: 
                        self.move_command_up()

                elif event == "Down":
                    if self.values['activesList']:
                        self.move_command_down()

                elif event == "Add":
                    name = self.values.get('name')
                    try:
                        value = self.values.get('setValue') and float(self.values.get('setValue'))
                    except ValueError:
                        self.winpos = self.window.CurrentLocation()
                        psize = (264, 133)
                        pposition = self.calculate_popup_position(psize)
                        sg.Popup("Error: missing data or invalid data format.", location=pposition)
                    else:
                        self.add_command(name, value)

                elif event == "Update":
                    if self.values['activesList']:
                        command = self.find_selected_command()
                        try:
                            value = self.values.get('setValue') and float(self.values.get('setValue'))
                        except ValueError:
                            self.winpos = self.window.CurrentLocation()
                            psize = (264, 133)
                            pposition = self.calculate_popup_position(psize)
                            sg.Popup("Error: missing data or invalid data format.", location=pposition)
                        else:
                            command.value = self.values.get('setValue')
                            command.step=self.values.get('step')
                            command.limitLow=self.values.get('min')
                            command.limitHigh=self.values.get('max')

                elif event == "Insert":
                    if self.values['activesList']:
                        name = self.values.get('name')
                        try:
                            value = self.values.get('setValue') and float(self.values.get('setValue'))
                        except ValueError:
                            self.winpos = self.window.CurrentLocation()
                            psize = (264, 133)
                            pposition = self.calculate_popup_position(psize)
                            sg.Popup("Error: missing data or invalid data format.", location=pposition)
                        else:
                            self.insert_command(name, value)

                elif event == "Remove":
                    if self.values['activesList']:
                        self.remove_selected_command()
                        self.update_profile_commands()

                elif event == "Pause":
                    name = 'PROGRAM_PAUSE_10'
                    self.update_command_data(self.command_detail[name])

                elif event == "Send":
                    self.enter_commands_to_aircraft()

                elif event == "activesList":
                    if self.values['activesList']:
                        command = self.find_selected_command()
                        if command.msg in self.command_detail:
                            self.update_command_data(self.command_detail[command.msg], command.value)
                        else:
                            self.update_command_data(None)

                elif event == "Save Profile":
                    if self.profile.commands:
                        name = self.profile.profilename
                        if name:
                            self.profile.save(name)
                            self.update_profiles_list(name)
                        else:
                            self.write_profile()

                elif event == "Save Profile As...":
                    if self.profile.commands:
                        self.write_profile()

                elif event == "Delete Profile":
                    if not self.profile.profilename:
                        continue
                    self.winpos = self.window.CurrentLocation()
                    psize = (264, 133)
                    pposition = self.calculate_popup_position(psize)
                    confirm_delete = sg.PopupOKCancel(f"Confirm delete {self.profile.profilename}?", location=pposition)
                    if confirm_delete == "OK":
                        Profile.delete(self.profile.profilename)
                        profiles = sorted(self.get_profile_names())
                        self.window.Element("profileSelector").Update(
                            values=[""] + profiles)
                        self.load_new_profile()
                        self.update_profile_commands()
                        self.update_command_data(None)

                elif event == "profileSelector":
                    try:
                        save_aircraft = self.profile.aircraft
                        profile_name = self.values['profileSelector']
                        if profile_name != '':
                            self.profile = Profile.load(profile_name)
                            if save_aircraft != self.profile.aircraft:
                                self.set_aircraft(self.profile.aircraft)
                        else:
                            self.profile = Profile('', aircraft=self.profile.aircraft)
                        self.update_profile_commands()
                    except DoesNotExist:
                        self.winpos = self.window.CurrentLocation()
                        psize = (264, 133)
                        pposition = self.calculate_popup_position(psize)
                        sg.Popup("Profile not found.", location=pposition)

                elif event == "Save as Encoded file":
                    self.export_to_file(self.profile)

                elif event == "Save All as Encoded file":
                    self.export_db_to_file()

                elif event == "Load from Encoded file":
                    self.load_from_file()

                elif event == "groupSelector":
                    group_name = self.values['groupSelector']
                    self.update_command_list([group_name])

                elif event == "commandSelector":
                    if self.values.get('commandSelector'):
                        command_desc = self.values.get('commandSelector')[0]
                        dcsbios_name = self.command_key[command_desc]
                        self.update_command_data(self.command_detail[dcsbios_name])

                elif event == "rangeSelector":
                    self.window.Element('setValue').Update(self.values['rangeSelector'])

                elif event == "aircraftSelector":
                    self.set_aircraft(self.values.get('aircraftSelector'))

#                elif event == "_setValue":
#                    if self.values['setValue'] < self.values['min']:
#                        self.window.Element('setValue').Update(self.values['min'])
#                        self.values['setValue'] = self.values['min']
#                    elif self.values['setValue'] > self.values['max']:
#                        self.window.Element('setValue').Update(self.values['max'])
#                        self.values['setValue'] = self.values['max']

                elif event == "groupFilter":
                    self.filter_groups_dropdown()

                elif event == "profileFilter":
                    self.filter_profile_dropdown()

                elif event == 'About':
                    # Define the layout for the information popup window
                    text = f"    DCS Aircraft Command Entry {self.software_version}"
                    gpltext = "This program is free software; you can redistribute it and/or \n"\
                              "modify it under the terms of the GNU General Public License as \n"\
                              "published by the Free Software Foundation; either version 3 of \n"\
                              "the License, or at your option any later version. \n\n"\
                              "This program is distributed in the hope that it will be useful, but \n"\
                              "WITHOUT ANY WARRANTY; without even the implied warranty \n"\
                              "of MERCHANTABILITY or FITNESS FOR A PARTICULAR \n"\
                              "PURPOSE. See the GNU General Public License for more details. \n\n"\
                              "You should have received a copy of the GNU General Public License\n"\
                              "along with this program. If not, see <https://www.gnu.org/licenses/>."
                    url = 'https://github.com/atcz/DCSAircraftCommandEntry'
                    layout = [
                        [sg.Column([
                            [sg.Text(f"      {text}", justification='center')],
                            [sg.Text(url, enable_events=True, text_color='blue', key='-LINK-')]
                        ], vertical_alignment='center', justification='center')],
                    [sg.Frame("GNU General Public License", [
                        [sg.Text(gpltext, pad=(40,(10,20)))],
                        ])
                    ],
                        [sg.Column([
                            [sg.Button('OK', size=(10, 1), pad=(10, 20), bind_return_key=True)]
                        ], vertical_alignment='center', justification='center')]
                    ]

                    # Create the window
                    psize = (513, 392)
                    pposition = self.calculate_popup_position(psize)
                    pwindow = sg.Window('Information', layout, location=pposition, finalize=True, modal=True)

                    # Event loop
                    while True:
                        event, _ = pwindow.read()
                        if event == sg.WINDOW_CLOSED or event == 'OK':
                            break
                        elif event == '-LINK-':
                            webbrowser.open(url)
                            break
                    # Close the window
                    pwindow.close()

        self.close()

    def close(self):
        try:
            keyboard.remove_hotkey(self.enter_aircraft_hotkey)
        except KeyError:
            pass

        self.window.close()
        self.editor.stop()
