#!/usr/bin/env python

# Time-stamp: <2017-02-14 12:27:28>

"""Get data from Quartus pin file
"""

__version__ = '0.1.0'


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

    header = ''
    table_header = ''
    table_line = ''
    data = []
    date = 0
    time = 0
    version = 0

    def __init__(self, fname):
        """Returns data from Quartus pin file (read file)
        """
        # print(fname)
        self.read_file(fname)
        self.fname = fname

    def read_file(self, fname):
        try:
            # print('read fname: ' + str(fname))
            with open(fname, 'r') as f:
                find_table = 0
                find_table_line = 0
                header = ''
                table_header = ''
                table_line = ''
                data = []
                self.data = []
                for line in f:
                    s = line.rstrip()
                    # print(str(s))
                    try:
                        if not find_table:
                            if 'Pin Name/Usage' in s:
                                table_header = s
                                find_table = 1
                            else:
                                header = '%s\n%s' % (header, s)
                        else:
                            if not find_table_line:
                                find_table_line = 1
                                table_line = s
                            else:
                                sf = s.split(':')
                                sfn = []
                                for i in sf:
                                    i = i.replace(' ', '')
                                    sfn.append(i)
                                # print('i = \'%s\'' % i)
                                # print('k = %s' % sfn)
                                data.append([s, sfn[0], sfn[1]])
                        self.header = header
                        self.table_header = table_header
                        self.table_line = table_line
                        self.data = data
                    except:
                        print('+-----------------------------------+')
                        print('| Error! With Quartus pin file      |')
                        print('+-----------------------------------+')
        except:
            print('+-----------------------------------+')
            print('| Error! With file: \'%s\'' % fname)
            print('+-----------------------------------+')
        finally:
            f.close()

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
            print('Error! Index of net=%d, more then net-list length=%d (from 0 to %d)' %
                  (i, length-1, length-1))
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
        Net name or false if there are note this net name
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
        """Returns net-list as sting
        """
        s = ''
        for i in range(self.data_length()):
            if s == '':
                s = 'net_name: %s, pin: %s' % (self.get_net_name(i), self.get_pin(i))
            else:
                s = '%s\nnet_name: %s, pin: %s' % (s, self.get_net_name(i), self.get_pin(i))
        return s


if __name__ == '__main__':
    def write_file(fname, s):
        f = open(fname, 'w')
        f.write(s)
        f.close()
        print('Write file: %s' % fname)

    import datetime
    print('____________________________________________')
    fname = 'files2self_test/measure_ctrl.pin'
    fname_rpt = 'files2self_test/measure_ctrl_formatted.pin'
    n = QuartusPin(fname)
    rpt = n.get_header() + '\n' + n.get_table_header() + '\n' + n.get_table_line()
    for i in range(n.data_length()):
        rpt = '%s\nname-pin: %s-%s, \t\t\tstring: %s' \
              % (rpt, n.get_net_name(i), n.get_pin(i), n.data_qpin2string(i))
    write_file(fname_rpt, rpt)

    print('')
    print('Get net name and pin from data[1]: \'%s\':\'%s\'' % (n.get_net_name(1), n.get_pin(1)))
    print('Get length of data: %s' % n.data_length())
    print('Get test from data[1]: %s' % n.data[1])
    print('')
    print('Quartus pin file data:')
    print(n)
    print('')
    print(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'))
