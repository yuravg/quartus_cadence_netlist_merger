#!/usr/bin/env python

"""Get data from Quartus pin file
"""

from pathlib import Path


class QuartusPin(object):
    """Quartus pin file data

    Arguments:
    date/time    -- date/time of Quartus pin file
    version      -- version of Quartus
    header       -- header of Quartus pin file
    table_header -- header of pin table
    table_line   -- line of pin table
    data         -- pin data
                    [['text', 'net_name', 'pin'],
                     ['text', 'net_name', 'pin']
                     ...],
                      text:
                           'GND : A6 : gnd : : : :'
                           'mem_a.addr[12] : A7 : output : SSTL-18 Class I : : 4 : Y'
    fname        -- Quartus pin file name
    """

    def __init__(self, fname):
        """Returns data from Quartus pin file (read file)
        """
        # Initialize instance variables
        self.header = ''
        self.table_header = ''
        self.table_line = ''
        self.data = []
        self.date = 0
        self.time = 0
        self.version = 0
        self.fname = fname
        # Read file data
        self.read_file(fname)

    def read_file(self, fname):
        """Read and parse Quartus pin file

        The Quartus pin file has three sections:
        1. Header: Everything before "Pin Name/Usage" line
        2. Table header: The "Pin Name/Usage" line with column names
        3. Table line: Separator line (dashes)
        4. Data: Pin entries in format "net_name : pin : direction : io_standard : ..."

        Keyword Arguments:
        fname -- file name to read
        """
        # Validate filename
        if not fname or not isinstance(fname, str):
            print('+-----------------------------------+')
            print('| Error! Invalid pin file name      |')
            print('| Please provide a valid filename   |')
            print('+-----------------------------------+')
            return

        if not Path(fname).exists():
            print('+-----------------------------------+')
            print('| Error! Pin file not found         |')
            print(f'| File: \'{fname}\'')
            print('| Please check the file path        |')
            print('+-----------------------------------+')
            return

        try:
            with open(fname, 'r') as file_handle:
                # Parsing state flags
                found_table_start = False
                found_table_separator = False
                # Accumulated data
                header_lines = ''
                table_header_line = ''
                table_separator_line = ''
                pin_data = []
                self.data = []

                for line in file_handle:
                    stripped_line = line.rstrip()
                    try:
                        if not found_table_start:
                            # Looking for table header (contains column names)
                            if 'Pin Name/Usage' in stripped_line:
                                table_header_line = stripped_line
                                found_table_start = True
                            else:
                                header_lines = f'{header_lines}\n{stripped_line}'
                        else:
                            if not found_table_separator:
                                # First line after header is the separator (dashes)
                                found_table_separator = True
                                table_separator_line = stripped_line
                            else:
                                # Parse pin data lines (colon-separated fields)
                                fields = stripped_line.split(':')
                                cleaned_fields = [field.replace(' ', '') for field in fields]
                                if len(cleaned_fields) >= 2:
                                    net_name = cleaned_fields[0]
                                    pin_number = cleaned_fields[1]
                                    pin_data.append([stripped_line, net_name, pin_number])

                        self.header = header_lines
                        self.table_header = table_header_line
                        self.table_line = table_separator_line
                        self.data = pin_data
                    except (ValueError, IndexError):
                        print('+-----------------------------------+')
                        print('| Error! Parsing pin data line      |')
                        print(f'| Line: \'{stripped_line[:40]}\'')
                        print('| Check file format                 |')
                        print('+-----------------------------------+')

            # Validate parsed data
            if not found_table_start:
                print('+-----------------------------------+')
                print('| Warning! No pin table found       |')
                print(f'| File: \'{fname}\'')
                print('| Expected \'Pin Name/Usage\' header  |')
                print('| Check Quartus pin file format     |')
                print('+-----------------------------------+')

            if len(pin_data) == 0:
                print('+-----------------------------------+')
                print('| Warning! No pins found in file    |')
                print(f'| File: \'{fname}\'')
                print('| Check file format and content     |')
                print('+-----------------------------------+')

        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot read pin file       |')
            print(f'| File: \'{fname}\'')
            print('| Check file permissions            |')
            print('+-----------------------------------+')
        except (OSError, ValueError, UnicodeDecodeError):
            print('+-----------------------------------+')
            print('| Error! Parsing pin file           |')
            print(f'| File: \'{fname}\'')
            print('| Check file format (expected       |')
            print('| Quartus pin file format)          |')
            print('+-----------------------------------+')

    def get_header(self):
        """Returns Quartus file header as string
        """
        return self.header

    def get_table_header(self):
        """Returns Quartus file table header as string
        """
        return self.table_header

    def get_table_line(self):
        """Returns Quartus file table line as string
        """
        return self.table_line

    def data_length(self):
        """Returns length of data from Quartus pin file
        """
        return len(self.data)

    def check_data_index(self, i):
        """Check valid data index of Quartus pin file
        Keyword Arguments:
        i -- checked data index
        Returns:
        Returns true if index is correct
        """
        length = self.data_length()
        if i >= length:
            print(f'Error! Index of net={i}, more then net-list length={length-1} (from 0 to {length-1})')
            return False
        else:
            return True

    def data_qpin2string(self, i):
        """Returns data of Quartus pin file as string
        Keyword Arguments:
        i -- net name index
        Returns:
        Not formated data of Quartus pin file as string,
        or false if there are not data
        """
        if self.check_data_index(i):
            data = self.data[i][0]
            return data
        else:
            return False

    def get_net_name(self, i):
        """Returns net name from data Quartus pin file
        Keyword Arguments:
        i -- net name index
        Returns:
        Net name or false if there is no such net name
        """
        if self.check_data_index(i):
            net = self.data[i][1]
            return net
        else:
            return False

    def get_pin(self, i):
        """Returns pin number from data Quartus pin file
        Keyword Arguments:
        i -- net name index
        Returns:
        Net pin number or false if there are not this pin
        """
        if self.check_data_index(i):
            pin = self.data[i][2]
            return pin
        else:
            return False

    def __str__(self):
        """Returns net-list as string
        """
        s = ''
        for i in range(self.data_length()):
            if s == '':
                s = f'net_name: {self.get_net_name(i)}, pin: {self.get_pin(i)}'
            else:
                s = f'{s}\nnet_name: {self.get_net_name(i)}, pin: {self.get_pin(i)}'
        return s


if __name__ == '__main__':
    def write_file(fname, s):
        f = open(fname, 'w')
        f.write(s)
        f.close()
        print(f'Write file: {fname}')

    import datetime
    print('____________________________________________')
    fname = 'files2self_test/measure_ctrl.pin'
    fname_rpt = 'files2self_test/measure_ctrl_formatted.pin'
    n = QuartusPin(fname)
    rpt = n.get_header() + '\n' + n.get_table_header() + '\n' + n.get_table_line()
    for i in range(n.data_length()):
        rpt = f'{rpt}\nname-pin: {n.get_net_name(i)}-{n.get_pin(i)}, \t\t\tstring: {n.data_qpin2string(i)}'
    write_file(fname_rpt, rpt)

    print('')
    print(f'Get net name and pin from data[1]: \'{n.get_net_name(1)}\':\'{n.get_pin(1)}\'')
    print(f'Get length of data: {n.data_length()}')
    print(f'Get test from data[1]: {n.data[1]}')
    print('')
    print('Quartus pin file data:')
    print(n)
    print('')
    print(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'))
