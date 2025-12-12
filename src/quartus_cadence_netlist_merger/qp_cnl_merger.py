#!/usr/bin/env python

"""
Quartus Pin and Cadence Allegro Netlist Merger (CNL - Cadence Net List)
"""

import sys
import os
try:
    from tkinter import Frame, Button, Label, StringVar, Entry
    from tkinter import LEFT, RIGHT, IntVar, Toplevel, Checkbutton, W
    from tkinter.filedialog import askopenfilename
except ImportError:  # for version < 3.0
    from Tkinter import Frame, Button, Label, StringVar, Entry
    from Tkinter import LEFT, RIGHT, IntVar, Toplevel, Checkbutton, W
    from tkFileDialog import askopenfilename

import time
import datetime

from .configfile import ConfigFile
from .quartuspin import QuartusPin
from .allegronetlist import AllegroNetList

# TODO: make several output files
# FIXME: refdes field is cleared after selecting a file(after the first launch)

# Constants for GUI layout
MAIN_WINDOW_GEOMETRY = "550x400"
SETTINGS_DIALOG_GEOMETRY = "300x470"

# Constants for output formatting
COLUMN_WIDTH = 20  # Width for net name and pin name columns

# Constants for backup management
MAX_BACKUP_COUNT = 100  # Maximum number of backup files (0-99)

# No-connect pin marker in Cadence netlist
NC_PIN_MARKER = 'NC'

# Standard power rail voltage names for pin categorization
POWER_RAIL_NAMES = [
    '5.0V', '3.3V', '3.0V', '2.5V', '1.8V', '1.5V', '1.35V', '1.25V', '1.2V',
    '1.1V', '1.0V', '0.9V', '0.8V', '0.75V', '0.675V', 'GND', 'GNDA'
]


class QuartusCadenceMerger(Frame):
    """Quartus Pin and Cadence Allegro Netlist Merger (CNL - Cadence Net List)
    """

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.read_config_file()
        self.master.title("Quartus Pin and Cadence Allegro Netlist Merger")
        self.master.geometry(MAIN_WINDOW_GEOMETRY)
        self.pack()
        self.make_widgets()

    fname_config = '.qp_cnl_merger.dat'
    fname_rename = '.qp_cnl_merger_rename.dat'
    fname_header = '.qp_cnl_merger_header.dat'

    # Cache for QuartusPin instance
    _cached_qp = None
    _cached_qp_fname = None
    _cached_qp_mtime = None

    def _get_quartus_pin(self):
        """Get cached QuartusPin instance, reload if file changed
        Returns cached instance if file unchanged, otherwise re-reads file
        """
        current_mtime = self.get_file_mtime(self.qp_fname)
        if (self._cached_qp is None or
                self._cached_qp_fname != self.qp_fname or
                self._cached_qp_mtime != current_mtime):
            self._cached_qp = QuartusPin(self.qp_fname)
            self._cached_qp_fname = self.qp_fname
            self._cached_qp_mtime = current_mtime
        return self._cached_qp

    def _invalidate_quartus_pin_cache(self):
        """Invalidate the QuartusPin cache"""
        self._cached_qp = None
        self._cached_qp_fname = None
        self._cached_qp_mtime = None

    def read_config_file(self):
        """Read configuration file and initialize application settings"""
        k = {'Configuration': {'netlist_file'     : '',
                               'quartus_pin_file' : '',
                               'refdes'           : '',
                               'full_merged'      : '0',
                               'signal'           : '1',
                               'nosignal'         : '0',
                               'format_signal'    : '0',
                               'power'            : '1',
                               'noconnect'        : '1',
                               'refdes_pin_name'  : '0',
                               'net_name'         : '1'},
             'Info': {'Description': 'Configuration file for Quartus Pin and Cadence Allegro Netlist Merger'}
             }
        self.cfg             = ConfigFile(self.fname_config, k)
        self.cnl_fname       = self.cfg.get_key('Configuration', 'netlist_file')
        self.qp_fname        = self.cfg.get_key('Configuration', 'quartus_pin_file')
        self.refdes          = self.cfg.get_key('Configuration', 'refdes')
        self.full_merged     = int(self.cfg.get_key('Configuration', 'full_merged'))
        self.signal          = int(self.cfg.get_key('Configuration', 'signal'))
        self.nosignal        = int(self.cfg.get_key('Configuration', 'nosignal'))
        self.format_signal   = int(self.cfg.get_key('Configuration', 'format_signal'))
        self.power           = int(self.cfg.get_key('Configuration', 'power'))
        self.noconnect       = int(self.cfg.get_key('Configuration', 'noconnect'))
        self.refdes_pin_name = int(self.cfg.get_key('Configuration', 'refdes_pin_name'))
        self.net_name        = int(self.cfg.get_key('Configuration', 'net_name'))

    def save_config(self):
        """Save current configuration to config file"""
        self.cfg.edit_key('Configuration', 'netlist_file',     self.cnl_fname)
        self.cfg.edit_key('Configuration', 'quartus_pin_file', self.qp_fname)
        self.cfg.edit_key('Configuration', 'refdes',           self.refdes)
        self.cfg.edit_key('Configuration', 'full_merged',      str(self.full_merged))
        self.cfg.edit_key('Configuration', 'signal',           str(self.signal))
        self.cfg.edit_key('Configuration', 'nosignal',         str(self.nosignal))
        self.cfg.edit_key('Configuration', 'format_signal',    str(self.format_signal))
        self.cfg.edit_key('Configuration', 'power',            str(self.power))
        self.cfg.edit_key('Configuration', 'noconnect',        str(self.noconnect))
        self.cfg.edit_key('Configuration', 'refdes_pin_name',  str(self.refdes_pin_name))
        self.cfg.edit_key('Configuration', 'net_name',         str(self.net_name))
        self.cfg.write2file()

    def make_widgets(self):
        """Create and layout all GUI widgets"""
        Label(self,  text='Cadence Netlist File:').pack()
        fname = self.cnl_fname
        self.gui_cnl_fname = StringVar()
        self.gui_cnl_fname.set(fname)
        Label(self, textvariable=self.gui_cnl_fname).pack()
        Button(self, text='Browse...', command=self.select_netlist, height=1, width=10).pack()

        Label(self, text='').pack()
        Label(self, text='Quartus Pin File:').pack()
        qp_fname = self.qp_fname
        self.gui_qp_fname = StringVar()
        self.gui_qp_fname.set(qp_fname)
        Label(self, textvariable=self.gui_qp_fname).pack()
        Button(self, text='Browse...', command=self.select_qp_file, height=1, width=10).pack()

        Label(self, text='').pack()
        Label(self, text='Capture Refdes:').pack()

        self.gui_refdes = StringVar()
        self.gui_refdes.set(self.refdes)
        ent = Entry(self, textvariable=self.gui_refdes)
        ent.pack()

        Label(self, text='').pack()
        Button(self, text='Generate Merged Report', command=self.build, height=1, width=20).pack()
        self.gui_state = StringVar()
        self.gui_state.set('Ready')
        Label(self, textvariable=self.gui_state).pack()
        Label(self, text='').pack()

        Button(self, text='Settings',
               command=self.run_config_dialog, height=1, width=10).pack(side=LEFT)
        Button(self, text='Exit',
               command=self.save_and_exit, height=1, width=10).pack(side=RIGHT)

    def run_config_dialog(self):
        """Show settings dialog for output file configuration"""
        self.update_and_save_config()
        win = Toplevel()
        win.title('Output file settings')
        win.geometry(SETTINGS_DIALOG_GEOMETRY)
        full_merged     = IntVar()
        signal          = IntVar()
        nosignal        = IntVar()
        format_signal   = IntVar()
        power           = IntVar()
        noconnect       = IntVar()
        refdes_pin_name = IntVar()
        net_name        = IntVar()
        full_merged.set(self.full_merged)
        signal.set(self.signal)
        nosignal.set(self.nosignal)
        format_signal.set(self.format_signal)
        power.set(self.power)
        noconnect.set(self.noconnect)
        refdes_pin_name.set(self.refdes_pin_name)
        net_name.set(self.net_name)
        label_text = 'Output Files: MergedQC.rpt, MergedQC.summary.rpt'
        Label(win, text=label_text).pack()
        Label(win, text='').pack()
        Label(win, text='Columns (All Files):').pack()
        Checkbutton(win, text='Cadence Net Name',        variable=net_name        ).pack(anchor=W)
        Checkbutton(win, text='Cadence Refdes Pin Name', variable=refdes_pin_name ).pack(anchor=W)
        Label(win, text='').pack()
        Label(win, text='Groups in Summary File:').pack()
        Checkbutton(win, text='Full Merged Summary',  variable=full_merged   ).pack(anchor=W)
        Checkbutton(win, text='Signal Pins',          variable=signal        ).pack(anchor=W)
        Checkbutton(win, text='Non-Signal Pins',      variable=nosignal      ).pack(anchor=W)
        Checkbutton(win, text='Formatted Signal Pins', variable=format_signal ).pack(anchor=W)
        Checkbutton(win, text='Power Pins',           variable=power         ).pack(anchor=W)
        Checkbutton(win, text='Unconnected Pins',     variable=noconnect     ).pack(anchor=W)
        Label(win, text='').pack()
        Button(win, text='OK', command=win.destroy, height=1, width=10).pack()
        Label(win, text='').pack()
        s = 'Create Template Files:'
        s = s + '\n%s - header for summary file' % self.fname_header
        s = s + '\n%s - rename mask file' % self.fname_rename
        Label(win, text=s, justify=LEFT).pack()
        Button(win, text='Create Templates', command=self.write_template_file, height=1, width=15).pack()
        win.grab_set()
        win.focus_set()
        win.wait_window()
        self.full_merged     = full_merged.get()
        self.signal          = signal.get()
        self.nosignal        = nosignal.get()
        self.format_signal   = format_signal.get()
        self.power           = power.get()
        self.noconnect       = noconnect.get()
        self.refdes_pin_name = refdes_pin_name.get()
        self.net_name        = net_name.get()

    def write_template_file(self):
        """Create template files for rename mask and header if they don't exist"""
        if not os.path.exists(self.fname_rename):
            self.write2file(self.fname_rename, 'old_name new_name')
        if not os.path.exists(self.fname_header):
            self.write2file(self.fname_header, '')

    def update_gui2self(self):
        """Update internal state from GUI variables"""
        self.cnl_fname = self.gui_cnl_fname.get()
        self.qp_fname = self.gui_qp_fname.get()
        self.refdes = self.gui_refdes.get()

    def update_self2gui(self):
        """Update GUI variables from internal state"""
        self.gui_cnl_fname.set(self.cnl_fname)
        self.gui_qp_fname.set(self.qp_fname)
        self.gui_refdes.set(self.refdes)

    def update_and_save_config(self):
        """Update internal state from GUI and save configuration"""
        self.update_gui2self()
        self.save_config()

    merged_data = ''

    # List of groups:
    # full_merged
    # signal
    # nosignal
    # format_signal
    # power
    # noconnect
    # refdes_pin_name
    # net_name
    def build(self):
        """Build merged report by combining Quartus Pin file with Cadence netlist"""
        self.update_and_save_config()

        # Validate input files before processing
        if not self.cnl_fname or not self.cnl_fname.strip():
            self.gui_state.set('Error! Please select a Cadence netlist file')
            print('+-----------------------------------+')
            print('| Error! No netlist file selected   |')
            print('| Please select a netlist file      |')
            print('+-----------------------------------+')
            return

        if not os.path.exists(self.cnl_fname):
            self.gui_state.set('Error! Netlist file not found: %s' % self.cnl_fname)
            print('+-----------------------------------+')
            print('| Error! Netlist file not found     |')
            print('| File: \'%s\'' % self.cnl_fname)
            print('| Please check the file path        |')
            print('+-----------------------------------+')
            return

        if not self.qp_fname or not self.qp_fname.strip():
            self.gui_state.set('Error! Please select a Quartus pin file')
            print('+-----------------------------------+')
            print('| Error! No pin file selected       |')
            print('| Please select a Quartus pin file  |')
            print('+-----------------------------------+')
            return

        if not os.path.exists(self.qp_fname):
            self.gui_state.set('Error! Pin file not found: %s' % self.qp_fname)
            print('+-----------------------------------+')
            print('| Error! Pin file not found         |')
            print('| File: \'%s\'' % self.qp_fname)
            print('| Please check the file path        |')
            print('+-----------------------------------+')
            return

        if not self.refdes or not self.refdes.strip():
            self.gui_state.set('Error! Please enter a refdes')
            print('+-----------------------------------+')
            print('| Error! No refdes specified        |')
            print('| Please enter a component refdes   |')
            print('| (e.g., DD2, U1, IC5)              |')
            print('+-----------------------------------+')
            return

        self.gui_state.set('Running...')
        fname = 'MergedQC.rpt'
        fname_summary = 'MergedQC.summary.rpt'
        date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        self.build_merged_data(self.refdes_pin_name, self.net_name)
        s = self.header2string(date)
        s = s + self.qp_pin_header2string(self.refdes_pin_name, self.net_name)
        s = s + self.merged_data
        self.write2newfile(fname, s)
        if not self.full_merged:
            s = self.header2string(date)
        s = self.read_header_file(self.fname_header) + s
        if self.signal:
            s = s + self.only_signal2string()
        if self.nosignal:
            s = s + self.nosignal2string()
        if self.format_signal:
            s = s + self.only_formatted_signal2string()
        if self.power:
            s = s + self.power_pins2string()
        if self.noconnect:
            s = s + self.noconnect2string()
        self.write2newfile(fname_summary, s)
        work_dir = os.getcwd()
        done_msg = 'Done: %s\nWritten files: %s, %s\n(Output directory: %s)' % (date, fname, fname_summary, work_dir)
        self.gui_state.set(done_msg)

    def header2string(self, date):
        time_cnl_fname = self.get_file_mtime(self.cnl_fname)
        time_qp_fname = self.get_file_mtime(self.qp_fname)
        lines = [
            '|--------------------------------------------------------------------------------|',
            '| File contains merged Quartus Pin and Cadence PCB Editor (Allegro) Netlist     |',
            '| NOTE: This file was auto-generated                                             |',
            '| Report creation date: %s                                      |' % date,
            '|--------------------------------------------------------------------------------|',
            '| Quartus, Cadence files and Refdes info:                                        |',
            '|  %s - %s ' % (time_cnl_fname, self.cnl_fname),
            '|  %s - %s ' % (time_qp_fname, self.qp_fname),
            '|  Refdes = %s' % self.refdes,
            '|--------------------------------------------------------------------------------|',
            ''
        ]
        return '\n'.join(lines)

    def qp_pin_header2string(self, require_pin_name, req_net_name):
        pin = self._get_quartus_pin()
        parts = ['* MERGED Quartus Pin File', pin.header]
        if require_pin_name:
            parts.append('Pin Name (Capture):  ')
        if req_net_name:
            parts.append('Net Name (Capture):  ')
        parts.append(pin.table_header)
        parts.append('\n' + pin.table_line + '\n')
        return ''.join(parts)

    def build_merged_data(self, require_pin_name, req_net_name):
        """Build merged data combining Quartus pin and Cadence netlist information

        Creates a row for each pin in the Quartus file, adding the corresponding
        net name and pin name from the Cadence netlist.

        Keyword Arguments:
        require_pin_name -- include Cadence pin names in output
        req_net_name     -- include Cadence net names in output
        """
        netlist = AllegroNetList(self.cnl_fname)
        netlist.build_refdes_list(self.refdes)
        quartus_pin = self._get_quartus_pin()
        output_lines = []

        for pin_index in range(len(quartus_pin.data)):
            pin_number = quartus_pin.get_pin(pin_index)

            # Get net name from Cadence netlist (padded to fixed width)
            net_name_column = ''
            if req_net_name:
                cadence_net_name = netlist.get_net_name4refdes_pin(self.refdes, pin_number)
                net_name_column = cadence_net_name.ljust(COLUMN_WIDTH)

            # Get pin name from Cadence netlist (padded to fixed width)
            pin_name_column = ''
            if require_pin_name:
                cadence_pin_name = netlist.get_refdes_pin_name(self.refdes, pin_number)
                pin_name_column = cadence_pin_name.ljust(COLUMN_WIDTH)

            # Combine columns with Quartus pin data
            prefix_columns = '%s%s' % (pin_name_column, net_name_column)
            quartus_pin_text = quartus_pin.data_qpin2string(pin_index).replace(
                'RESERVED_INPUT_WITH_WEAK_PULLUP', 'RESERVED_INPUT_WITH_WEAK_PUL')
            output_lines.append('%s %s' % (prefix_columns, quartus_pin_text))

        self.merged_data = '\n'.join(output_lines) + '\n' if output_lines else ''

    def find_in_merged_data(self, search_term):
        """Find all lines in merged data containing the search term

        Keyword Arguments:
        search_term -- exact word to search for in merged data

        Returns:
        String containing all matching lines, or empty string if none found
        """
        matching_lines = []
        data_lines = self.merged_data.split('\n')
        for line in data_lines:
            words = line.split()
            if search_term in words:
                matching_lines.append(line)
        return '\n'.join(matching_lines) + '\n' if matching_lines else ''

    def table_header2string(self, pin):
        parts = ['\n']
        if self.refdes_pin_name:
            parts.append('Pin Name (Capture):  ')
        if self.net_name:
            parts.append('Net Name (Capture):  ')
        parts.append(pin.table_header)
        parts.append('\n' + pin.table_line + '\n')
        return ''.join(parts)

    def noconnect2string(self):
        """Generate report section for unconnected (NC) pins"""
        quartus_pin = self._get_quartus_pin()
        parts = [
            '\n\n\n',
            '* Unconnected Pins\n',
            '|--------------------------------------------------------------------------------|\n',
            '| No Connect (Repeating part of pin list):                                      |\n',
            '|--------------------------------------------------------------------------------|\n',
            self.table_header2string(quartus_pin),
            self.find_in_merged_data(NC_PIN_MARKER)
        ]
        return ''.join(parts)

    def power_pins2string(self):
        """Generate report section for power pins grouped by voltage rail"""
        quartus_pin = self._get_quartus_pin()
        parts = [
            '\n\n\n',
            '* Power Pins\n',
            '|--------------------------------------------------------------------------------|\n',
            '| POWER Pins Only (Repeating part of pin list):                                 |\n',
            '|--------------------------------------------------------------------------------|\n'
        ]
        for voltage_rail in POWER_RAIL_NAMES:
            matching_pins = self.find_in_merged_data(voltage_rail)
            if matching_pins != '':
                parts.append('\n** Power: %s\n' % voltage_rail)
                parts.append(self.table_header2string(quartus_pin))
                parts.append(matching_pins)
        return ''.join(parts)

    nosignal_strings = ''

    def only_signal2string(self):
        """Generate report section for signal pins only

        Signal pins are those NOT connected to power rails or marked as NC.
        Also populates nosignal_strings for use by nosignal2string().
        """
        quartus_pin = self._get_quartus_pin()
        parts = [
            '\n\n\n',
            '* Signal Pins\n',
            '|--------------------------------------------------------------------------------|\n',
            '| SIGNAL Pins Only (Repeating part of pin list):                                |\n',
            '|--------------------------------------------------------------------------------|\n',
            self.table_header2string(quartus_pin)
        ]
        # Create set of power and NC markers for fast lookup
        excluded_names = set(POWER_RAIL_NAMES + [NC_PIN_MARKER])
        data_lines = self.merged_data.split('\n')
        signal_lines = []
        nosignal_lines = []

        for line in data_lines:
            words = line.split()
            # Check if any word matches power rail or NC marker
            is_power_or_nc = any(word in excluded_names for word in words)
            if not is_power_or_nc:
                signal_lines.append(line)
            else:
                nosignal_lines.append(line)

        parts.append('\n'.join(signal_lines) + '\n' if signal_lines else '')
        self.nosignal_strings = '\n'.join(nosignal_lines) + '\n' if nosignal_lines else ''
        return ''.join(parts)

    def only_formatted_signal2string(self):
        """Generate report section for signal pins with formatting applied

        Similar to only_signal2string() but applies:
        - Uppercase conversion
        - Rename mask substitutions from config file
        - Removal of bracket characters []()
        """
        quartus_pin = self._get_quartus_pin()
        parts = [
            '\n\n\n',
            '* Formatted Signal Pins\n',
            '|--------------------------------------------------------------------------------|\n',
            '| FORMATTED SIGNAL Pins Only (Repeating part of pin list):                      |\n',
            '|--------------------------------------------------------------------------------|\n',
            self.table_header2string(quartus_pin)
        ]
        # Create set of power and NC markers for fast lookup
        excluded_names = set(POWER_RAIL_NAMES + [NC_PIN_MARKER])
        data_lines = self.merged_data.split('\n')
        self.read_rename_mask_file(self.fname_rename)
        formatted_signal_lines = []

        for line in data_lines:
            words = line.split()
            is_power_or_nc = any(word in excluded_names for word in words)
            if not is_power_or_nc:
                # Apply formatting: uppercase and rename substitutions
                formatted_line = line.upper()
                for old_name, new_name in self.rename_mask:
                    formatted_line = formatted_line.replace(old_name, new_name)
                # Remove bracket characters
                for bracket_char in '[]()':
                    formatted_line = formatted_line.replace(bracket_char, '')
                formatted_signal_lines.append(formatted_line)

        parts.append('\n'.join(formatted_signal_lines) + '\n' if formatted_signal_lines else '')
        return ''.join(parts)

    rename_mask = []

    def read_rename_mask_file(self, fname):
        """Read rename mask file for signal formatting
        Keyword Arguments:
        fname -- rename mask file name
        """
        # Validate filename
        if not fname or not isinstance(fname, str):
            print('+-----------------------------------+')
            print('| Error! Invalid rename mask file   |')
            print('| Please provide a valid filename   |')
            print('+-----------------------------------+')
            return

        if not os.path.exists(fname):
            # Silently ignore missing rename mask file (it's optional)
            return

        try:
            with open(fname) as f:
                line_num = 0
                for line in f:
                    line_num += 1
                    parts = line.split()
                    if len(parts) >= 2:
                        a = parts[0]
                        b = parts[1]
                        self.rename_mask.append([a, b])
                    elif len(parts) == 1:
                        # Warn about malformed lines
                        print('Warning! Rename mask line %d has only 1 field (expected 2)' % line_num)
        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot read rename mask    |')
            print('| File: \'%s\'' % fname)
            print('| Check file permissions            |')
            print('+-----------------------------------+')
        except:
            print('+-----------------------------------+')
            print('| Error! Parsing rename mask file   |')
            print('| File: \'%s\'' % fname)
            print('| Expected format: old_name new_name|')
            print('+-----------------------------------+')

    def read_header_file(self, fname):
        """Read custom header file for summary report
        Keyword Arguments:
        fname -- header file name
        Returns:
        Header content as string, or empty string if file doesn't exist
        """
        s = ''

        # Validate filename
        if not fname or not isinstance(fname, str):
            print('+-----------------------------------+')
            print('| Error! Invalid header file name   |')
            print('+-----------------------------------+')
            return s

        if not os.path.exists(fname):
            # Silently ignore missing header file (it's optional)
            return s

        try:
            with open(fname) as f:
                s = f.read()
        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot read header file    |')
            print('| File: \'%s\'' % fname)
            print('| Check file permissions            |')
            print('+-----------------------------------+')
        except:
            print('+-----------------------------------+')
            print('| Error! Reading header file        |')
            print('| File: \'%s\'' % fname)
            print('+-----------------------------------+')
        return s

    def nosignal2string(self):
        """Generate report section for non-signal pins (power and NC)

        Uses cached nosignal_strings from only_signal2string() if available.
        """
        if self.nosignal_strings == '':
            self.only_signal2string()
        quartus_pin = self._get_quartus_pin()
        parts = [
            '\n\n\n',
            '* Non-Signal Pins\n',
            '|--------------------------------------------------------------------------------|\n',
            '| Non-Signal Pins (Repeating part of pin list):                                 |\n',
            '|--------------------------------------------------------------------------------|\n',
            self.table_header2string(quartus_pin),
            self.nosignal_strings
        ]
        return ''.join(parts)

    def write2newfile(self, fname, data_string):
        """Write data to file with automatic backup rotation

        If file does not exist, creates new file.
        If file exists, renames it to fname,N (where N is 0-99) before writing.

        Keyword Arguments:
        fname       -- file name
        data_string -- string data to write

        Returns:
        True if successful, False if error occurred
        """
        if os.path.exists(fname):
            backup_created = False
            for backup_index in range(MAX_BACKUP_COUNT):
                backup_fname = '%s,%s' % (fname, backup_index)
                if not os.path.exists(backup_fname):
                    try:
                        os.rename(fname, backup_fname)
                        print('renamed old file to %s' % backup_fname)
                        backup_created = True
                        break
                    except OSError:
                        print('+-----------------------------------+')
                        print('| Error! Cannot rename file: \'%s\'' % fname)
                        print('+-----------------------------------+')
                        return False
            if not backup_created:
                print('+-----------------------------------+')
                print('| Warning! All %d backup slots full for: \'%s\'' % (MAX_BACKUP_COUNT, fname))
                print('| Overwriting existing file without backup')
                print('+-----------------------------------+')
        return self.write2file(fname, data_string)

    def write2file(self, fname, s):
        """Write data to file with error handling
        Keyword Arguments:
        fname -- file name
        s     -- string data to write
        Returns:
        True if successful, False if error occurred
        """
        f = None
        try:
            f = open(fname, 'w')
            f.write(s)
            return True
        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot write file: \'%s\'' % fname)
            print('+-----------------------------------+')
            return False
        finally:
            if f:
                f.close()

    def get_file_mtime(self, fname):
        """Get file modification time as formatted string
        Keyword Arguments:
        fname -- file name
        Returns:
        Formatted time string or 'N/A' if file doesn't exist
        """
        try:
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(fname)))
        except OSError:
            return 'N/A'

    def select_netlist(self):
        """Show file dialog to select Cadence netlist file"""
        self.update_and_save_config()
        fname = askopenfilename(filetypes=(("Cadence Netlist", "pstxnet.dat"), ("All files", "*.*")))
        if fname != '':
            self.cnl_fname = fname
            self.update_self2gui()

    def select_qp_file(self):
        """Show file dialog to select Quartus Pin file"""
        self.update_and_save_config()
        fname = askopenfilename(filetypes=(("Quartus Pin File", "*.pin"), ("All files", "*.*")))
        if fname != '':
            self.qp_fname = fname
            self.update_self2gui()

    def save_and_exit(self):
        """Save configuration and exit application"""
        self.update_and_save_config()
        self.quit()


if __name__ == '__main__':
    QuartusCadenceMerger().mainloop()
