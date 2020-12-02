#!/usr/bin/env python

"""
Quartus pin and Cadence Allegro Net-List merger (cnl - Cadence Net-List)
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


class QuartusCadenceMerger(Frame):
    """Quartus pin and Cadence Allegro net-list merger (cnl - Cadence net-list)
    """

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.read_config_file()
        self.master.title("Quartus pin and Cadence Allegro net-list merger")
        self.master.geometry("550x400")
        self.pack()
        self.make_widgets()

    fname_config = '.qp_cnl_merger.dat'
    fname_rename = '.qp_cnl_merger_rename.dat'
    fname_header = '.qp_cnl_merger_header.dat'

    def read_config_file(self):
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
             'Info': {'Description': 'Configuration file to Quartus pin and Cadence Allegro net-list merger'}
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
        Label(self,  text='Cadence net-list:').pack()
        fname = self.cnl_fname
        self.gui_cnl_fname = StringVar()
        self.gui_cnl_fname.set(fname)
        Label(self, textvariable=self.gui_cnl_fname).pack()
        Button(self, text='Browse', command=self.select_netlist, height=1, width=10).pack()

        Label(self, text='').pack()
        Label(self, text='Quartus pin file:').pack()
        qp_fname = self.qp_fname
        self.gui_qp_fname = StringVar()
        self.gui_qp_fname.set(qp_fname)
        Label(self, textvariable=self.gui_qp_fname).pack()
        Button(self, text='Browse', command=self.select_qp_file, height=1, width=10).pack()

        Label(self, text='').pack()
        Label(self, text='Capture Refdes:').pack()

        self.gui_refdes = StringVar()
        self.gui_refdes.set(self.refdes)
        ent = Entry(self, textvariable=self.gui_refdes)
        ent.pack()

        Label(self, text='').pack()
        Button(self, text='Build', command=self.build, height=1, width=10).pack()
        self.gui_state = StringVar()
        self.gui_state.set('Idle')
        Label(self, textvariable=self.gui_state).pack()
        Label(self, text='').pack()

        Button(self, text='Config',
               command=self.run_config_dialog, height=1, width=10).pack(side=LEFT)
        Button(self, text='Exit',
               command=self.save_and_exit, height=1, width=10).pack(side=RIGHT)

    def run_config_dialog(self):
        self.update_and_save_config()
        win = Toplevel()
        win.title('Output file settings')
        win.geometry("300x470")
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
        lebel_text = 'Output files: MergedQC.rpt, MergedQC.summary.rpt'
        Label(win, text=lebel_text).pack()
        Label(win, text='').pack()
        Label(win, text='Columns(all files):').pack()
        Checkbutton(win, text='Cadence Net name',        variable=net_name        ).pack(anchor=W)
        Checkbutton(win, text='Cadence Refdes pin name', variable=refdes_pin_name ).pack(anchor=W)
        Label(win, text='').pack()
        Label(win, text='Groups of summary file:').pack()
        Checkbutton(win, text='Summary',          variable=full_merged   ).pack(anchor=W)
        Checkbutton(win, text='Signal',           variable=signal        ).pack(anchor=W)
        Checkbutton(win, text='Not Signal',       variable=nosignal      ).pack(anchor=W)
        Checkbutton(win, text='Formatted Signal', variable=format_signal ).pack(anchor=W)
        Checkbutton(win, text='Power pins',       variable=power         ).pack(anchor=W)
        Checkbutton(win, text='Unconnected pins', variable=noconnect     ).pack(anchor=W)
        Label(win, text='').pack()
        Button(win, text='Set', command=win.destroy, height=1, width=10).pack()
        Label(win, text='').pack()
        s = 'Create templates:'
        s = s + '\n%s - header for summary file' % self.fname_header
        s = s + '\n%s - rename mask file' % self.fname_rename
        Label(win, text=s, justify=LEFT).pack()
        Button(win, text='templates', command=self.write_template_file, height=1, width=9).pack()
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
        if not os.path.exists(self.fname_rename):
            self.write2file(self.fname_rename, 'had_name has_name')
        if not os.path.exists(self.fname_header):
            self.write2file(self.fname_header, '')

    def update_gui2self(self):
        self.cnl_fname = self.gui_cnl_fname.get()
        self.qp_fname = self.gui_qp_fname.get()
        self.refdes = self.gui_refdes.get()

    def update_self2gui(self):
        self.gui_cnl_fname.set(self.cnl_fname)
        self.gui_qp_fname.set(self.qp_fname)
        self.gui_refdes.set(self.refdes)

    def update_and_save_config(self):
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
        self.update_and_save_config()
        self.gui_state.set('Runnig...')
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
        done_msg = 'Done: %s\nwrited file(s): %s, %s\n(output directory: %s)' % (date, fname, fname_summary, work_dir)
        self.gui_state.set(done_msg)

    def header2string(self, date):
        time_cnl_fname = self.get_file_mtime(self.cnl_fname)
        time_qp_fname = self.get_file_mtime(self.qp_fname)
        rpt = ''
        rpt = rpt + '|--------------------------------------------------------------------------------|\n'
        rpt = rpt + '| File contains merged Quartus pin and Cadence PCB Editor (Allegro) net-list     |\n'
        rpt = rpt + '| NOTE: this file was auto-generated                                             |\n'
        rpt = rpt + '| report creation date: %s                                      |\n' % date
        rpt = rpt + '|--------------------------------------------------------------------------------|\n'
        rpt = rpt + '| Quartus, Cadence files and refdes info:                                        |\n'
        rpt = rpt + '|  %s - %s \n' % (time_cnl_fname, self.cnl_fname)
        rpt = rpt + '|  %s - %s \n' % (time_qp_fname, self.qp_fname)
        rpt = rpt + '|  refdes = %s\n' % self.refdes
        rpt = rpt + '|--------------------------------------------------------------------------------|\n'
        return rpt

    def qp_pin_header2string(self, require_pin_name, req_net_name):
        pin = QuartusPin(self.qp_fname)
        rpt = ''
        rpt = rpt + '* MERGED Quartus pin file'
        rpt = rpt + pin.header
        if require_pin_name:
            rpt = rpt + 'Pin Name(capture) :  '
        if req_net_name:
            rpt = rpt + 'Net Name(capture) :  '
        rpt = rpt + pin.table_header
        rpt = rpt + '\n' + pin.table_line + '\n'
        return rpt

    def build_merged_data(self, require_pin_name, req_net_name):
        net = AllegroNetList(self.cnl_fname)
        net.build_refdes_list(self.refdes)
        pin = QuartusPin(self.qp_fname)
        max_length = 20
        rpt = ''
        for i in range(len(pin.data)):
            pin_in_pin_file = pin.get_pin(i)
            net_in_net_file = ''
            if req_net_name:
                net_in_net_file = net.get_net_name4refdes_pin(self.refdes, pin_in_pin_file)
                net_in_net_file = net_in_net_file + ' ' * (max_length - len(net_in_net_file))
            pin_name = ''
            if require_pin_name:
                pin_name = net.get_refdes_pin_name(self.refdes, pin_in_pin_file)
                pin_name = pin_name + ' ' * (max_length - len(pin_name))
            summary = '%s%s' % (pin_name, net_in_net_file)
            formated_pin_text = '%s' % pin.data_qpin2string(i).replace(
                'RESERVED_INPUT_WITH_WEAK_PULLUP', 'RESERVED_INPUT_WITH_WEAK_PUL')
            rpt = '%s%s %s\n' % (rpt, summary, formated_pin_text)
        self.merged_data = rpt

    def find_in_merged_data(self, d):
        s = ''
        data = self.merged_data.split('\n')
        for i in data:
            j = i.split()
            for k in j:
                if k == d:
                    s = s + i + '\n'
                    break
        return s

    nosignal_name = 'NC'

    def table_header2string(self, pin):
        s = '\n'
        if self.refdes_pin_name:
            s = s + 'Pin Name(capture) :  '
        if self.net_name:
            s = s + 'Net Name(capture) :  '
        s = s + pin.table_header
        s = s + '\n' + pin.table_line + '\n'
        return s

    def noconnect2string(self):
        pin = QuartusPin(self.qp_fname)
        s = '\n'*3
        s = s + '* NO connected pins\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + '| No Connect (repeating part of pin list):                                       |\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + self.table_header2string(pin)
        s = s + self.find_in_merged_data(self.nosignal_name)
        return s

    pwr_name = ['5.0V', '3.3V', '3.0V', '2.5V', '1.8V', '1.5V', '1.35V', '1.25V', '1.2V',
                '1.1V', '1.0V', '0.9V', '0.8V', '0.75V', '0.675V', 'GND', 'GNDA']

    def power_pins2string(self):
        pin = QuartusPin(self.qp_fname)
        s = '\n'*3
        s = s + '* POWERS pins\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + '| POWER pins only (repeating part of pin list):                                  |\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        for i in self.pwr_name:
            result = self.find_in_merged_data(i)
            if result != '':
                s = s + '\n** Power: %s\n' % i
                s = s + self.table_header2string(pin)
                s = s + result
        return s

    nosignal_strings = ''
    def only_signal2string(self):
        pin = QuartusPin(self.qp_fname)
        s = '\n'*3
        s = s + '* SIGNAL pins\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + '| SIGNAL pins only (repeating part of pin list):                                 |\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + self.table_header2string(pin)
        cut_name = self.pwr_name + [self.nosignal_name]
        data = self.merged_data.split('\n')
        for i in data:
            find = 0
            j = i.split()
            for k in j:
                for c in cut_name:
                    if c == k:
                        find = 1
            if not find:
                s = s + i + '\n'
            else:
                self.nosignal_strings = self.nosignal_strings + i + '\n'
        return s

    def only_formatted_signal2string(self):
        pin = QuartusPin(self.qp_fname)
        s = '\n'*3
        s = s + '* FORMATED SIGNAL pins\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + '| FORMATED SIGNAL pins only (repeating part of pin list):                        |\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + self.table_header2string(pin)
        cut_name = self.pwr_name + [self.nosignal_name]
        data = self.merged_data.split('\n')
        self.read_rename_mask_file(self.fname_rename)
        for i in data:
            find = 0
            j = i.split()
            for k in j:
                for c in cut_name:
                    if c == k:
                        find = 1
            if not find:
                i = i.upper()
                for m in self.rename_mask:
                    i = i.replace(m[0], m[1])
                i = i.replace('[', '')
                i = i.replace(']', '')
                i = i.replace('(', '')
                i = i.replace(')', '')
                s = s + i + '\n'
        return s

    rename_mask = []

    def read_rename_mask_file(self, fname):
        if os.path.exists(fname):
            try:
                with open(fname) as f:
                    for line in f:
                        a, b = line.split()
                        self.rename_mask.append([a, b])
            except:
                print('Error! Can\'t read rename mask file: \'%s\', wrong format' % fname)

    def read_header_file(self, fname):
        s = ''
        if os.path.exists(fname):
            try:
                with open(fname) as f:
                    s = f.read()
            except:
                print('Error! Can\'t read header file: \'%s\', wrong format' % fname)
        return s

    def nosignal2string(self):
        if self.nosignal_strings == '':
            self.only_signal2string()
        pin = QuartusPin(self.qp_fname)
        s = '\n'*3
        s = s + '* No singal pins\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + '| No Signal pins(repeating part of pin list):                                    |\n'
        s = s + '|--------------------------------------------------------------------------------|\n'
        s = s + self.table_header2string(pin)
        s = s + self.nosignal_strings
        return s

    def write2newfile(self, fname, s):
        """write data to file
        if file not exist new file will created
        if file exist it will renamed and new file will created"""
        if os.path.exists(fname):
            for i in range(100):
                new_fname = '%s,%s' % (fname, i)
                if not os.path.exists(new_fname):
                    os.rename(fname, new_fname)
                    print('renamed old file to %s' % new_fname)
                    break
        self.write2file(fname, s)

    def write2file(self, fname, s):
        f = open(fname, 'w')
        f.write(s)
        f.close()

    def get_file_mtime(self, fname):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(fname)))

    def select_netlist(self):
        self.update_and_save_config()
        fname = askopenfilename(filetypes=(("Cadence neltist", "pstxnet.dat"), ("All files", "*.*")))
        if fname != '':
            self.cnl_fname = fname
            self.update_self2gui()

    def select_qp_file(self):
        self.update_and_save_config()
        fname = askopenfilename(filetypes=(("Quartus pin file", "*.pin"), ("All files", "*.*")))
        if fname != '':
            self.qp_fname = fname
            self.update_self2gui()

    def save_and_exit(self):
        self.update_and_save_config()
        self.quit()


if __name__ == '__main__':
    QuartusCadenceMerger().mainloop()
