#!/usr/bin/env python

"""
Quartus Pin and Cadence Allegro Netlist Merger (CNL - Cadence Net List)
"""

import sys
import os
import subprocess
from pathlib import Path
from tkinter import Frame, Button, Label, StringVar, Entry, Text, Scrollbar
from tkinter import LEFT, RIGHT, IntVar, Toplevel, Checkbutton, W, END, VERTICAL, DISABLED, NORMAL
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import time
import datetime

from .configfile import ConfigFile
from .quartuspin import QuartusPin
from .allegronetlist import AllegroNetList

# TODO: make several output files
# FIXME: refdes field is cleared after selecting a file(after the first launch)

# Constants for GUI layout
MAIN_WINDOW_GEOMETRY = "620x580"
SETTINGS_DIALOG_GEOMETRY = "400x500"

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
        # Cadence Netlist File section
        Label(self, text='Cadence Netlist File:', font=('Arial', 11, 'bold')).pack(pady=(10, 2))
        fname = self.cnl_fname
        self.gui_cnl_fname = StringVar()
        self.gui_cnl_fname.set(self._get_display_filename(fname))
        Label(self, textvariable=self.gui_cnl_fname, font=('Arial', 11)).pack(pady=(0, 0))
        self.gui_cnl_path = StringVar()
        self.gui_cnl_path.set(self._get_display_path(fname))
        Label(self, textvariable=self.gui_cnl_path, fg='gray20', font=('Arial', 11)).pack(pady=(0, 5))
        Button(self, text='Browse...', command=self.select_netlist, height=1, width=10).pack(pady=(0, 5))

        # Quartus Pin File section
        Label(self, text='Quartus Pin File:', font=('Arial', 11, 'bold')).pack(pady=(10, 2))
        qp_fname = self.qp_fname
        self.gui_qp_fname = StringVar()
        self.gui_qp_fname.set(self._get_display_filename(qp_fname))
        Label(self, textvariable=self.gui_qp_fname, font=('Arial', 11)).pack(pady=(0, 0))
        self.gui_qp_path = StringVar()
        self.gui_qp_path.set(self._get_display_path(qp_fname))
        Label(self, textvariable=self.gui_qp_path, fg='gray20', font=('Arial', 11)).pack(pady=(0, 5))
        Button(self, text='Browse...', command=self.select_qp_file, height=1, width=10).pack(pady=(0, 5))

        # Capture Refdes section
        Label(self, text='Capture Refdes:', font=('Arial', 11, 'bold')).pack(pady=(10, 2))
        refdes_frame = Frame(self)
        refdes_frame.pack(pady=(0, 2))
        self.gui_refdes = StringVar()
        self.gui_refdes.set(self.refdes)
        ent = Entry(refdes_frame, textvariable=self.gui_refdes, width=8)
        ent.pack(side=LEFT, padx=(0, 5))
        Label(self, text='(e.g., D1 or DD1, etc.)', fg='gray').pack(pady=(0, 5))

        # Generate button and status
        Button(self, text='Generate Merged Report', command=self.build, height=2, width=25,
               bg='#4CAF50', fg='white', font=('Arial', 10, 'bold')).pack(pady=(15, 10))

        # Status message area with scrollbar
        status_frame = Frame(self)
        status_frame.pack(fill='both', expand=True, pady=(0, 5), padx=10)

        # Scrollbar for status text
        scrollbar = Scrollbar(status_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill='y')

        # Text widget for status messages
        self.status_text = Text(status_frame, height=6, wrap='word',
                                yscrollcommand=scrollbar.set, state=DISABLED,
                                font=('Arial', 10))
        self.status_text.pack(side=LEFT, fill='both', expand=True)
        scrollbar.config(command=self.status_text.yview)

        # Set initial status
        self._set_status('Ready')

        # Bottom buttons
        bottom_frame = Frame(self)
        bottom_frame.pack(side='bottom', fill='x', pady=10)
        Button(bottom_frame, text='Settings',
               command=self.run_config_dialog, height=1, width=10).pack(side=LEFT, padx=(10, 5))
        Button(bottom_frame, text='Open Output Dir',
               command=self._open_output_directory, height=1, width=13).pack(side=LEFT, padx=(5, 5))
        Button(bottom_frame, text='Exit',
               command=self.save_and_exit, height=1, width=10).pack(side=RIGHT, padx=(5, 10))

        # Keyboard shortcuts
        self.master.bind('<Control-q>', lambda event: self.save_and_exit())
        self.master.bind('<Control-s>', lambda event: self.run_config_dialog())
        self.master.bind('<Control-b>', lambda event: self.build())
        self.master.bind('<F5>', lambda event: self.build())
        self.master.bind('<Escape>', lambda event: self.save_and_exit())

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

        # Output files info section
        label_text = 'Output Files: MergedQC.rpt, MergedQC.summary.rpt'
        Label(win, text=label_text).pack(pady=(10, 5))

        # Columns section
        Label(win, text='Columns (All Files):').pack(pady=(10, 5))
        Checkbutton(win, text='Cadence Net Name',        variable=net_name        ).pack(anchor=W, padx=20)
        Checkbutton(win, text='Cadence Refdes Pin Name', variable=refdes_pin_name ).pack(anchor=W, padx=20)

        # Groups section
        Label(win, text='Groups in Summary File:').pack(pady=(10, 5))
        Checkbutton(win, text='Full Merged Summary',  variable=full_merged   ).pack(anchor=W, padx=20)
        Checkbutton(win, text='Signal Pins',          variable=signal        ).pack(anchor=W, padx=20)
        Checkbutton(win, text='Non-Signal Pins',      variable=nosignal      ).pack(anchor=W, padx=20)
        Checkbutton(win, text='Formatted Signal Pins', variable=format_signal ).pack(anchor=W, padx=20)
        Checkbutton(win, text='Power Pins',           variable=power         ).pack(anchor=W, padx=20)
        Checkbutton(win, text='Unconnected Pins',     variable=noconnect     ).pack(anchor=W, padx=20)

        # OK button
        Button(win, text='OK', command=win.destroy, height=1, width=10).pack(pady=(15, 10))

        # Template files section
        s = 'Create Template Files:'
        s = s + f'\n{self.fname_header} - header for summary file'
        s = s + f'\n{self.fname_rename} - rename mask file'
        Label(win, text=s, justify=LEFT).pack(pady=(10, 5))
        Button(win, text='Create Templates', command=self.write_template_file, height=1, width=15).pack(pady=(0, 10))

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
        if not Path(self.fname_rename).exists():
            self.write2file(self.fname_rename, 'old_name new_name')
        if not Path(self.fname_header).exists():
            self.write2file(self.fname_header, '')

    def update_gui2self(self):
        """Update internal state from GUI variables"""
        # Note: File paths are updated in select_* methods, only refdes is updated here
        # gui_cnl_fname and gui_qp_fname are display-only (show just filename)
        self.refdes = self.gui_refdes.get()

    def update_self2gui(self):
        """Update GUI variables from internal state"""
        self.gui_cnl_fname.set(self._get_display_filename(self.cnl_fname))
        self.gui_cnl_path.set(self._get_display_path(self.cnl_fname))
        self.gui_qp_fname.set(self._get_display_filename(self.qp_fname))
        self.gui_qp_path.set(self._get_display_path(self.qp_fname))
        self.gui_refdes.set(self.refdes)

    def update_and_save_config(self):
        """Update internal state from GUI and save configuration"""
        self.update_gui2self()
        self.save_config()

    def show_error(self, title, message):
        """Show error dialog to user
        Keyword Arguments:
        title   -- error dialog title
        message -- error message to display
        """
        messagebox.showerror(title, message)

    def _get_display_filename(self, filepath):
        """Get display name for file (just filename, or message if empty)
        Keyword Arguments:
        filepath -- full file path
        Returns:
        Filename only, or '(not selected)' if empty
        """
        if not filepath or not filepath.strip():
            return '(not selected)'
        return Path(filepath).name

    def _get_display_path(self, filepath):
        """Get directory path for display
        Keyword Arguments:
        filepath -- full file path
        Returns:
        Directory path, or empty string if no file selected
        """
        if not filepath or not filepath.strip():
            return ''
        dirpath = Path(filepath).parent
        if not str(dirpath) or str(dirpath) == '.':
            dirpath = Path.cwd()
        return str(dirpath)

    def _clear_refdes(self):
        """Clear the refdes entry field"""
        self.gui_refdes.set('')

    def _open_output_directory(self):
        """Open the output directory in file manager"""
        output_dir = Path.cwd()

        # Validate output directory exists and is a directory
        if not output_dir.exists() or not output_dir.is_dir():
            print('+-----------------------------------+')
            print('| Error! Invalid output directory   |')
            print(f'| Directory: \'{output_dir}\'')
            print('+-----------------------------------+')
            messagebox.showinfo('Output Directory', str(output_dir))
            return

        try:
            # Try different methods depending on OS
            if sys.platform == 'win32':
                os.startfile(str(output_dir))
            elif sys.platform == 'darwin':
                # Use Popen to launch without blocking, suppress all output
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(['open', str(output_dir)],
                                     stdout=devnull,
                                     stderr=devnull,
                                     close_fds=True)
            else:
                # Use Popen to launch without blocking, suppress all output
                # (prevents FFmpeg warnings from file manager thumbnail generation)
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(['xdg-open', str(output_dir)],
                                     stdout=devnull,
                                     stderr=devnull,
                                     close_fds=True)
        except (OSError, ValueError):
            messagebox.showinfo('Output Directory', str(output_dir))

    def _set_status(self, message, append=False):
        """Update status message in text widget
        Keyword Arguments:
        message -- status message to display
        append  -- if True, append to existing text; if False, replace
        """
        self.status_text.config(state=NORMAL)
        if not append:
            self.status_text.delete(1.0, END)
        else:
            # Add newline before appending if there's existing content
            current = self.status_text.get(1.0, END).strip()
            if current:
                self.status_text.insert(END, '\n')
        self.status_text.insert(END, message)
        self.status_text.config(state=DISABLED)
        self.status_text.see(END)  # Auto-scroll to bottom

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

        # Clear rename_mask to prevent data corruption on repeated builds
        self.rename_mask = []

        # Validate input files before processing
        if not self.cnl_fname or not self.cnl_fname.strip():
            error_msg = 'Please select a Cadence netlist file using the Browse button.'
            self.show_error('No Netlist File', error_msg)
            self._set_status('Error! No netlist file selected')
            print('+-----------------------------------+')
            print('| Error! No netlist file selected   |')
            print('| Please select a netlist file      |')
            print('+-----------------------------------+')
            return

        if not Path(self.cnl_fname).exists():
            error_msg = f'Netlist file not found:\n{self.cnl_fname}\n\nPlease check the file path.'
            self.show_error('File Not Found', error_msg)
            self._set_status('Error! Netlist file not found')
            print('+-----------------------------------+')
            print('| Error! Netlist file not found     |')
            print(f'| File: \'{self.cnl_fname}\'')
            print('| Please check the file path        |')
            print('+-----------------------------------+')
            return

        if not self.qp_fname or not self.qp_fname.strip():
            error_msg = 'Please select a Quartus pin file using the Browse button.'
            self.show_error('No Pin File', error_msg)
            self._set_status('Error! No pin file selected')
            print('+-----------------------------------+')
            print('| Error! No pin file selected       |')
            print('| Please select a Quartus pin file  |')
            print('+-----------------------------------+')
            return

        if not Path(self.qp_fname).exists():
            error_msg = f'Pin file not found:\n{self.qp_fname}\n\nPlease check the file path.'
            self.show_error('File Not Found', error_msg)
            self._set_status('Error! Pin file not found')
            print('+-----------------------------------+')
            print('| Error! Pin file not found         |')
            print(f'| File: \'{self.qp_fname}\'')
            print('| Please check the file path        |')
            print('+-----------------------------------+')
            return

        if not self.refdes or not self.refdes.strip():
            error_msg = 'Please enter a component refdes (e.g., DD2, U1, IC5).'
            self.show_error('No Refdes Specified', error_msg)
            self._set_status('Error! No refdes specified')
            print('+-----------------------------------+')
            print('| Error! No refdes specified        |')
            print('| Please enter a component refdes   |')
            print('| (e.g., DD2, U1, IC5)              |')
            print('+-----------------------------------+')
            return

        # self._set_status('Reading netlist and pin files...')
        self.update_idletasks()  # Force GUI update

        fname = 'MergedQC.rpt'
        fname_summary = 'MergedQC.summary.rpt'
        date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

        # self._set_status('Building merged data...', append=True)
        self.update_idletasks()
        self.build_merged_data(self.refdes_pin_name, self.net_name)

        # s = ''
        # self._set_status('Generating main report...', append=True)
        self.update_idletasks()
        s = self.header2string(date)
        s = s + self.qp_pin_header2string(self.refdes_pin_name, self.net_name)
        s = s + self.merged_data
        self.write2newfile(fname, s)

        # self._set_status('Generating summary report...', append=True)
        self.update_idletasks()
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

        # self._set_status('Writing output files...', append=True)
        self.update_idletasks()
        self.write2newfile(fname_summary, s)

        work_dir = Path.cwd()
        done_msg = f'Files created: {fname}, {fname_summary}\nOutput directory: {work_dir}\nCompleted: {date}'
        self._set_status(done_msg, append=True)

    def header2string(self, date):
        time_cnl_fname = self.get_file_mtime(self.cnl_fname)
        time_qp_fname = self.get_file_mtime(self.qp_fname)
        lines = [
            '|--------------------------------------------------------------------------------|',
            '| File contains merged Quartus Pin and Cadence PCB Editor (Allegro) Netlist      |',
            '| NOTE: This file was auto-generated                                             |',
            f'| Report creation date: {date}                                      |',
            '|--------------------------------------------------------------------------------|',
            '| Quartus, Cadence files and Refdes info:                                        |',
            f'|  {time_cnl_fname} - {self.cnl_fname} ',
            f'|  {time_qp_fname} - {self.qp_fname} ',
            f'|  Refdes = {self.refdes}',
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

            # Validate pin_number - skip invalid pins
            if pin_number is False:
                print(f'Warning! Invalid pin at index {pin_index}, skipping')
                continue

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
            prefix_columns = f'{pin_name_column}{net_name_column}'
            quartus_pin_text = quartus_pin.data_qpin2string(pin_index).replace(
                'RESERVED_INPUT_WITH_WEAK_PULLUP', 'RESERVED_INPUT_WITH_WEAK_PUL')
            output_lines.append(f'{prefix_columns} {quartus_pin_text}')

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
            '| No Connect (Repeating part of pin list):                                       |\n',
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
            '| POWER Pins Only (Repeating part of pin list):                                  |\n',
            '|--------------------------------------------------------------------------------|\n'
        ]
        for voltage_rail in POWER_RAIL_NAMES:
            matching_pins = self.find_in_merged_data(voltage_rail)
            if matching_pins != '':
                parts.append(f'\n** Power: {voltage_rail}\n')
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
            '| SIGNAL Pins Only (Repeating part of pin list):                                 |\n',
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
            '| FORMATTED SIGNAL Pins Only (Repeating part of pin list):                       |\n',
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

        if not Path(fname).exists():
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
                        print(f'Warning! Rename mask line {line_num} has only 1 field (expected 2)')
        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot read rename mask    |')
            print(f'| File: \'{fname}\'')
            print('| Check file permissions            |')
            print('+-----------------------------------+')
        except (OSError, ValueError, UnicodeDecodeError):
            print('+-----------------------------------+')
            print('| Error! Parsing rename mask file   |')
            print(f'| File: \'{fname}\'')
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

        if not Path(fname).exists():
            # Silently ignore missing header file (it's optional)
            return s

        try:
            with open(fname) as f:
                s = f.read()
        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot read header file    |')
            print(f'| File: \'{fname}\'')
            print('| Check file permissions            |')
            print('+-----------------------------------+')
        except (OSError, ValueError, UnicodeDecodeError):
            print('+-----------------------------------+')
            print('| Error! Reading header file        |')
            print(f'| File: \'{fname}\'')
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
            '| Non-Signal Pins (Repeating part of pin list):                                  |\n',
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
        # Validate filename to prevent path traversal
        if not fname or not isinstance(fname, str):
            print('+-----------------------------------+')
            print('| Error! Invalid filename           |')
            print('+-----------------------------------+')
            return False

        # Get absolute path and ensure it doesn't escape current directory
        abs_fname = Path(fname).resolve()
        cwd = Path.cwd().resolve()
        # Check if the file would be created in a subdirectory of cwd or cwd itself
        try:
            abs_fname.relative_to(cwd)
        except ValueError:
            print('+-----------------------------------+')
            print('| Error! Invalid file path          |')
            print('| Path must be in current directory |')
            print(f'| File: \'{fname}\'')
            print('+-----------------------------------+')
            return False

        if Path(fname).exists():
            backup_created = False
            for backup_index in range(1, MAX_BACKUP_COUNT + 1):
                backup_fname = f'{fname},{backup_index:02d}'
                if not Path(backup_fname).exists():
                    try:
                        Path(fname).rename(backup_fname)
                        backup_msg = f'Renamed old file to: {backup_fname}'
                        self._set_status(backup_msg, append=True)
                        self.update_idletasks()
                        backup_created = True
                        break
                    except OSError:
                        print('+-----------------------------------+')
                        print(f'| Error! Cannot rename file: \'{fname}\'')
                        print('+-----------------------------------+')
                        return False
            if not backup_created:
                print('+-----------------------------------+')
                print(f'| Warning! All {MAX_BACKUP_COUNT} backup slots full for: \'{fname}\'')
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
        try:
            with open(fname, 'w') as f:
                f.write(s)
            return True
        except IOError:
            print('+-----------------------------------+')
            print(f'| Error! Cannot write file: \'{fname}\'')
            print('+-----------------------------------+')
            return False

    def get_file_mtime(self, fname):
        """Get file modification time as formatted string
        Keyword Arguments:
        fname -- file name
        Returns:
        Formatted time string or 'N/A' if file doesn't exist
        """
        try:
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(Path(fname).stat().st_mtime))
        except OSError:
            return 'N/A'

    def select_netlist(self):
        """Show file dialog to select Cadence netlist file"""
        self.update_and_save_config()
        # Set initial directory based on current file if it exists
        initial_dir = ''
        if self.cnl_fname and Path(self.cnl_fname).exists():
            initial_dir = str(Path(self.cnl_fname).parent)
        elif self.cnl_fname:
            parent_dir = Path(self.cnl_fname).parent
            initial_dir = str(parent_dir) if str(parent_dir) and str(parent_dir) != '.' else str(Path.cwd())
        else:
            initial_dir = str(Path.cwd())

        fname = askopenfilename(
            title='Select Cadence Allegro Netlist File',
            filetypes=(("Cadence Netlist", "pstxnet.dat"), ("All files", "*.*")),
            initialdir=initial_dir
        )
        if fname != '':
            self.cnl_fname = fname
            self.update_self2gui()
            # Invalidate cache when file changes
            self._invalidate_quartus_pin_cache()

    def select_qp_file(self):
        """Show file dialog to select Quartus Pin file"""
        self.update_and_save_config()
        # Set initial directory based on current file if it exists
        initial_dir = ''
        if self.qp_fname and Path(self.qp_fname).exists():
            initial_dir = str(Path(self.qp_fname).parent)
        elif self.qp_fname:
            parent_dir = Path(self.qp_fname).parent
            initial_dir = str(parent_dir) if str(parent_dir) and str(parent_dir) != '.' else str(Path.cwd())
        else:
            initial_dir = str(Path.cwd())

        fname = askopenfilename(
            title='Select Quartus Pin File',
            filetypes=(("Quartus Pin File", "*.pin"), ("All files", "*.*")),
            initialdir=initial_dir
        )
        if fname != '':
            self.qp_fname = fname
            self.update_self2gui()
            # Invalidate cache when file changes
            self._invalidate_quartus_pin_cache()

    def save_and_exit(self):
        """Save configuration and exit application"""
        self.update_and_save_config()
        self.quit()


if __name__ == '__main__':
    QuartusCadenceMerger().mainloop()
