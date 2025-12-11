#!/usr/bin/env python

"""Get data from Cadence Allegro net-list
"""

from __future__ import print_function
import datetime

# Constants for netlist parsing
SINGLE_NET_MAX_NODES = 100  # Max nodes for a net to be considered "single"

# Constants for netlist parsing
SINGLE_NET_MAX_NODES = 100  # Max nodes for a net to be considered "single"


class AllegroNetList(object):
    """Cadence Allegro net-list data

    Arguments:
    date/time -- date/time of create net-list
    version   -- version of Cadence Allegro net-list
    net_list  -- net-list data
                    [['net_name1', [['D1', '1'], ['C1', '1']]],
                     ['net_name2', [['D2', '2'], ['R2', '2']]]]
    fname     -- net-list file name
    refdes_list -- list of pins and nets belong refdes
                (to build list need run method: build_refdes_list(REFDES)
                    [['REFDES0',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']],
                     ['REFDES1',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']],
                     ['REFDESN',['net1', 'pin1'], ['net1', 'pin2'], ..., ['netN', 'pinN']]]
    """

    def __init__(self, fname):
        """Get data from net-list (read from file)
        """
        # Initialize instance variables
        self.net_list = []
        self.date = 0
        self.time = 0
        self.version = 0
        self.refdes_list = []
        self.fname = fname
        # Lookup dictionaries for O(1) access
        self._pin_name_lookup = {}  # (refdes, pin) -> name
        self._net_name_lookup = {}  # (refdes, pin) -> net_name
        # Read file data
        self.read_file(fname)

    def read_file(self, fname):
        """Read and parse Cadence Allegro netlist file

        The netlist file has a specific format with NET_NAME and NODE_NAME sections.
        This method uses a state machine approach to parse the file:
        - State 1: Looking for NET_NAME keyword (find_net_name flag)
        - State 2: Reading net name on next line
        - State 3: Collecting NODE_NAME entries until next NET_NAME or END
        """
        file_handle = None
        try:
            file_handle = open(fname, 'r')
            with file_handle:
                self._parse_netlist_content(file_handle)
            self.net_list.sort()
            self._build_lookup_dicts()
        except OSError:
            print('+-----------------------------------+')
            print('| Error! With file: \'%s\'' % fname)
            print('+-----------------------------------+')
        finally:
            if file_handle:
                file_handle.close()

    def _parse_netlist_content(self, file_handle):
        """Parse netlist content from file handle

        Keyword Arguments:
        file_handle -- open file handle to read from
        """
        # State machine flags
        expecting_net_name = False
        inside_net_block = False
        # Current net data being collected
        current_net_name = []
        current_nodes = []
        # Pin name reading state (pin name appears 2 lines after NODE_NAME)
        pin_name_countdown = 0
        current_node_ref = None
        # Header parsing
        header_line_count = 0

        self.net_list = []

        for line in file_handle:
            stripped_line = line.rstrip()
            try:
                # Handle net name capture (line after NET_NAME keyword)
                if expecting_net_name:
                    expecting_net_name = False
                    inside_net_block = True
                    # Strip surrounding quotes from net name
                    if len(stripped_line) >= 2:
                        current_net_name = stripped_line[1:-1]
                    else:
                        current_net_name = stripped_line

                # Check for NET_NAME or END markers
                if stripped_line.startswith('NET_NAME') or stripped_line.startswith('END.'):
                    if inside_net_block:
                        # Save completed net block
                        inside_net_block = False
                        self.net_list.append([current_net_name, current_nodes])
                        current_net_name = []
                        current_nodes = []
                    expecting_net_name = True
                    current_net_name = stripped_line
                elif stripped_line.startswith('NODE_NAME'):
                    # Parse NODE_NAME line: NODE_NAME REFDES PIN
                    parts = stripped_line.split()
                    refdes = parts[1]
                    pin = parts[2]
                    current_node_ref = [refdes, pin]
                    current_nodes.append(current_node_ref)
                    # Start countdown to capture pin name (2 lines later)
                    pin_name_countdown = 2

                # Capture pin name (appears 2 lines after NODE_NAME)
                if pin_name_countdown > 0:
                    pin_name_countdown -= 1
                    if pin_name_countdown == 0:
                        # Clean pin name by removing special characters
                        pin_name = stripped_line
                        for char in " \\';:":
                            pin_name = pin_name.replace(char, '')
                        current_node_ref.append(pin_name)

                # Parse header info from line 2 (PSTWRITER version info)
                if header_line_count < 3:
                    header_line_count += 1
                if header_line_count == 2:
                    self._parse_header_line(stripped_line)

            except OSError:
                print('+-----------------------------------+')
                print('| Error! With Net-list handler      |')
                print('+-----------------------------------+')

    def _parse_header_line(self, line):
        """Parse header line to extract version, date and time

        Expected format: { Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }

        Keyword Arguments:
        line -- header line string
        """
        parts = line.split()
        if len(parts) >= 7:
            self.version = parts[3]
            date_field = parts[4]
            if len(date_field) > 4:
                self.date = date_field[4:]  # Strip prefix like 'p002'
            else:
                self.date = date_field
            self.time = parts[6]

    def _build_lookup_dicts(self):
        """Build lookup dictionaries from net_list for fast access"""
        self._pin_name_lookup = {}
        self._net_name_lookup = {}
        for net in self.net_list:
            net_name = net[0]
            for node in net[1]:
                refdes = node[0]
                pin = node[1]
                key = (refdes, pin)
                self._net_name_lookup[key] = net_name
                if len(node) > 2:
                    self._pin_name_lookup[key] = node[2]

    def net_list_length(self):
        """Returns length of net-list"""
        return len(self.net_list)

    def check_net_index(self, i):
        """Check valid net-list index (to get net name)
        Keyword Arguments:
        i -- net-list index
        Returns:
        Returns true if index is valid
        """
        length = self.net_list_length()
        if i >= length:
            print('Error! Index of net=%d, more then net-list length=%d (from 0 to %d)' %
                  (i, length-1, length-1))
            return False
        else:
            return True

    def net_name(self, i):
        """Returns net name from net-list
        Keyword Arguments:
        i -- net name index
        Returns:
        Net name or false
        """
        if self.check_net_index(i):
            net = self.net_list[i][0]
            return net
        else:
            return False

    def node_list(self, i):
        """Returns refdes and pin list from net-list
        Keyword Arguments:
        i -- net name index
        """
        if self.check_net_index(i):
            node = []
            net = self.net_list[i][1]
            for i in net:
                v = i[:2]
                node.append(v)
            return node
        else:
            return 0

    def get_refdes_pin_name(self, p_refdes, p_pin):
        """Return refdes pin name as string
        Uses O(1) lookup dictionary for fast access
        """
        return self._pin_name_lookup.get((p_refdes, p_pin), "")

    def node2string(self, i):
        """Returns node (refdes, pin) as string
        Keyword Arguments:
        i -- net name index
        """
        node_list = self.node_list(i)
        parts = []
        for item in node_list:
            parts.append(' '.join(item))
        return ' '.join(parts)

    def find_in_refdes_list(self, refdes):
        """Find refdes in refdes list
        Keyword Arguments:
        refdes -- refdes value
        Returns:
        Returns true if find refdes in refdes_netlist
        """
        for i in self.refdes_list:
            if i[0] == refdes:
                return True
        return False

    def build_refdes_list(self, refdes):
        """Build list of nets and pins belong of refdes - refdes list
        Keyword Arguments:
        refdes -- refdes value
        Returns:
        Returns true if find refdes and just added it to refdes list,
        or false in there are not refdes in net-list
        """
        refdes_list = [refdes]
        find_net = 0
        if self.find_in_refdes_list(refdes):
            return True
        for i in self.net_list:
            net = i[0]
            ref_pin = i[1]
            for j in ref_pin:
                if j[0] == refdes:
                    refdes_list.append([net, j[1]])
                    find_net = 1
        self.refdes_list.append(refdes_list)
        if find_net:
            return True
        else:
            print('Error! Can\'t find refdes: \'%s\' in net-list: %s' % (refdes, self.fname))
            return False

    def get_net_name4refdes_pin(self, refdes, pin):
        """Returns net name for refdes and pin
        Uses O(1) lookup dictionary for fast access
        Keyword Arguments:
        refdes -- refdes value
        pin    -- pin number
        Returns:
        Net name or '' (empty string) if there are not net for selected refdes and pin
        """
        return self._net_name_lookup.get((refdes, pin), '')

    def refdes_list2string(self, refdes):
        """Returns refdes_list (for selected refdes) as string
        Keyword Arguments:
        refdes -- refdes value
        """
        if self.find_in_refdes_list(refdes):
            for i in self.refdes_list:
                if i[0] == refdes:
                    parts = [i[0]]
                    net_pin = i[1:]
                    for j in net_pin:
                        parts.append('%s:%s' % (j[0], j[1]))
                    return ' '.join(parts)
            return ''
        else:
            print('Error! Can\'t find refdes: \'%s\'' % refdes)
            return ''

    def net2string(self, i):
        """Returns full net as string (net name and its refdes and pins)
        Keyword Arguments:
        i -- net name index
        """
        net = self.net_name(i)
        node = self.node2string(i)
        # print('net: %s' % net)
        # print('node: %s' % node)
        net_and_node = '%s %s' % (net, node)
        # print('d: %s' % net_and_node)
        return net_and_node

    def __str__(self):
        """Returns net-list as string
        """
        lines = []
        for i in range(self.net_list_length()):
            lines.append(self.net2string(i))
        return '\n'.join(lines)

    def net_list2string(self):
        """Return net-list data as string
        """
        lines = []
        for i in range(self.net_list_length()):
            lines.append(self.net2string(i))
        return '\n'.join(lines) + '\n'

    def single_net_list2string(self):
        """Return single net-list data as string

        A "single net" is one with few connections (typically dangling or stub nets).
        """
        lines = []
        for i in range(self.net_list_length()):
            net_string = self.net2string(i)
            word_count = len(net_string.split())
            if word_count < SINGLE_NET_MAX_NODES + 1:
                lines.append(net_string)
        return '\n'.join(lines) + '\n' if lines else ''

    def net_list_title(self):
        """Return net-list title as string
        """
        date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        lines = [
            '+-------------------------------------------------------------------------+',
            '| File contains Cadence PCB Editor netlist                                |',
            '| NOTE: this file was auto-generated                                      |',
            '| generation date, time: %s                              |' % date,
            '+-------------------------------------------------------------------------+',
            '| Cadence net-list file info:                                             |',
            '|  %s' % self.net_list_info(),
            '|  %s' % self.fname,
            '+-------------------------------------------------------------------------+'
        ]
        return '\n'.join(lines)

    def single_net_warnings(self):
        """Return single net warning as string
        """
        lines = [
            '',
            '',
            '',
            '+-------------------------------------------------------------------------+',
            '| Warnings: Single node name                                              |',
            '+-------------------------------------------------------------------------+'
        ]
        w_string = self.single_net_list2string()
        if w_string == '':
            lines.append('- (Empty)')
        else:
            lines.append(w_string.rstrip('\n'))
        return '\n'.join(lines)

    def all_data2string(self):
        """Return all net-list data (title, data, warnings) as string
        """
        s = self.net_list_title() + '\n'
        s = s + self.net_list2string()
        s = s + self.single_net_warnings()
        return s

    def net_list2file(self, fname='NetList.rpt', message_en=False):
        """Write net-list data (with title to string) to file
        Keyword Arguments:
        fname -- output file name
        message_en -- enable success message
        Returns:
        True if successful, False if error occurred
        """
        s = self.all_data2string()
        f = None
        try:
            f = open(fname, 'w')
            f.write(s)
            if message_en:
                print('Write Net-List report file: %s' % fname)
            return True
        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot write file: \'%s\'' % fname)
            print('+-----------------------------------+')
            return False
        finally:
            if f:
                f.close()

    def net_list_info(self):
        """Returns net-list info as string
        """
        return 'Net-list %s %s (version: %s)' % (self.date, self.time, self.version)


if __name__ == '__main__':
    print('____________________________________________')
    fname1 = '../test/pstxnet_simple1.dat'
    fname1rpt = '../test/NetList_simple1.rpt'
    netlist1 = AllegroNetList(fname1)
    netlist1.net_list2file(fname1rpt, True)

    fname2 = '../test/pstxnet_simple2.dat.dat'
    fname2rpt = '../test/NetList_simple2.rpt'
    netlist2 = AllegroNetList(fname2)
    netlist2.net_list2file(fname2rpt, True)

    print('')
    print(netlist1.net_list_info())
    print('Net-list data (begin):')
    print(netlist1)
    print('Net-list data (end).')
    print('')
    print('')
    print('Run: Build net list')
    netlist1.build_refdes_list('DD2')
    netlist1.build_refdes_list('DA153')
    RD = 'DD2'
    PIN = 'G3'
    print('Get net name by refdes(%s) and pin(%s): %s(net name)' %
          (RD, PIN, netlist1.get_net_name4refdes_pin(RD, PIN)))
    print('')
    print('refdes_list = %s' % netlist1.refdes_list)
    print('')
    RD = 'DD2'
    print('Search in refdes_list \'%s\', result: %s' % (RD, netlist1.find_in_refdes_list(RD)))
    print('')
    print('Refdes to string: %s' % netlist1.refdes_list2string('DD2'))
    print(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'))
    print('*****')
    print('Check net name:')
    print('node_n-DIFFIO_L1N ?= %s' % netlist1.get_refdes_pin_name('DD2', 'G3'))
    print('node_n-VCCIO1_D4  ?= %s' % netlist1.get_refdes_pin_name('DD2', 'D4'))
