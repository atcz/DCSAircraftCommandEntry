# DCS Aircraft Command Entry

Simple configurable script to input a sequence of commands to DCS aircraft. 

Currently supported aircraft:

* A-10C
* F-15E
* F-16C
* F/A-18C
* Ka-50
* UH-1H

## Installation

1. Unzip the contents of DCS-ACE zip to a folder
2. Run `dcs_ace.exe` and perform the first time setup.

## How It Works

DCS Aircraft Command Entry creates a sequence of aircraft commands for DCS-BIOS which can be saved as profiles and sent
to the aircraft.

Supported control types:
- 3PosTumb
- 3PosTumb1
- EjectionHandleSwitch
- LedPushButton
- MultipositionSwitch
- Potentiometer
- PushButton
- Rotary
- SetCommandTumb
- Springloaded_3PosTumb
- ToggleSwitch
- ToggleSwitchToggleOnly
- ToggleSwitchToggleOnly2
- Tumb
- VariableStepTumb

## Usage

After selecting an aircraft type, command group and command, the command details are displayed and a command value can be set.
Click 'Add' to add the command to the profile.  Profiles can be saved or exported/imported using the Profile menu.

#### Command values entry

General guidelines for setting the command values:

- 3PosTumb, 3PosTumb1, Springloaded_3PosTumb:
The three switch positions correspond to values 0, 1 and 2.  Springloaded_3PosTumb returns to position 1 after selecting either
0 or 2.  Value of 2 is sent if not specified.

- EjectionHandleSwitch, ToggleSwitch, ToggleSwitchToggleOnly, ToggleSwitchToggleOnly2:
Accepts values 0 or 1.  Value of 1 is sent if not specified.

- LedPushButton, PushButton:
Push buttons do not need a value set by default.  They will press and release the button automatically.  For buttons that 
should remain pressed, like some power buttons, set to value 1.

- MultipositionSwitch:
Each MultipositionSwitch will list a Min and Max value.  Set the value corresponding to the desired switch position.  Min value
will be sent if not specified.

- Potentiometer:
The allowable setting is specified by Min and Max, corresponding to the range of the potentiometer.  Max value will be sent
if not specified.

- Rotary:
The value used by DCS-BIOS for rotary is the entered value / 65535.  This will take experimentation to find the correct value to
use.  In the F18, with the radar altimeter off, a value of 11,000 turns on the radar altimeter and sets the altitude to 200 feet.
A value of -50,000 changes the altitude from 3,000 to 1,000.

- SetCommandTumb, Tumb:
These controls specify a Min, Max and Step.  The set value corresponds with the step of the desired position.  For example,
Min 0, Max 0.6, and Step 0.1, setting the value to 0.3 corresponds to position 4.

- VariableStepTumb:
Similar to Rotary, this control accepts values up to 65535.

#### Entering the commands into your aircraft

An optional hotkey can be assigned for sending commands to the aircraft.  This is done during initial setup of the 
application.  Example formats for Python hotkeys are Ctrl+T, Ctrl+Alt+S or ctrl+alt+s.  Changing the hotkey requires
a restart of the program.

#### Profile saving

You may save your current list of waypoints as a profile and then load it later. Selecting "Save Profile" with a profile
active will overwrite it with the current list.

#### Exporting to encoded string

Support for exporting the current profile to an encoded string allows for quick sharing of command sequences with other
people.  Once you have created a profile, select `Copy as String to clipboard` from the menu.  This will copy an encoded
string to your clipboard to share.

#### Importing from encoded string

If another user has sent an encoded string to you, copy the string to your clipboard and select 
`Paste as String from clipboard` from the menu.  If successful, their profile data will be imported into
a new profile and a pop-up will appear letting you know import was successful.

#### Export to file

If you wish to share your current profile via JSON file, select `Save as Encoded file` and give it a descriptive name.

#### Import from file

Profiles may be imported from a file that was previously exported by selecting `Load from Encoded file`.

#### Creating new command files

Aircraft command files are read from the ./cmd directory.  Files added here in the correct format will make that aircraft
type selectable.

## About DCS Aircraft Command Entry
DCS ACE is released under the GNU General Public License v3.0.  The executable is built on Python 3.11.

## About DCS-BIOS
DCS-BIOS is released under a slightly modified Simple Public License 2.0 (think "a version of the GPL readable by 
mere mortals"). Please see DCS-BIOS-License.txt.

DCS-BIOS: https://github.com/DCSFlightpanels/dcs-bios
