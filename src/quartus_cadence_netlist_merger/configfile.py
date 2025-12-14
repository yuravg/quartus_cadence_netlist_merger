#!/usr/bin/env python

"""
Work with configuration file by ConfigParser
"""

try:
    from configparser import ConfigParser
except ImportError:  # for version < 3.0
    from ConfigParser import ConfigParser

config = ConfigParser()


class ConfigFile(object):
    """Work with configuration file, read and write keys from/to INI files

    The configuration is stored internally as a nested dictionary:
        self.k = {
            'section0': {'key_name0': value0, 'key_name1': value1},
            'section1': {'key_name0': value0, 'key_name1': value1}
        }

    Note: 'k' is used throughout as shorthand for 'keys' (the configuration dictionary).
    """

    def __init__(self, fname='fname.ini', k={}, verbosity=0):
        """Open configuration file name, read keys
        If configuration file has key, its value will override initial value
        Keyword Arguments:
        fname     -- file name
        k         -- configuration keys
        verbosity -- verbosity for work with config file (1 - for enable verbosity)
        """
        # Validate filename
        if not fname or not isinstance(fname, str):
            print('+-----------------------------------+')
            print('| Error! Invalid config filename    |')
            print('| Please provide a valid filename   |')
            print('+-----------------------------------+')
            raise ValueError('Invalid config filename: %s' % str(fname))

        if verbosity == 1:
            self.verbosity = 1
        else:
            self.verbosity = 0
        self.fname = fname
        config.optionxform = str
        # ConfigParser.read() silently ignores missing files, which is OK for config files
        config.read(fname)
        # override from file:
        for section in k:
            for i in k[section]:
                if config.has_option(section, i):
                    k[section][i] = config.get(section, i)
                    if self.verbosity:
                        print('read config: section: %s, keys: %s=%s' %
                              (section, i, k[section][i]))
        # get all section from file: kf - keys of file
        sections = config.sections()
        kf = {}
        for section in sections:
            ki = {}
            keys = list(config[section].keys())
            for i in keys:
                val = config.get(section, i)
                ki[i] = val
                kf[section] = ki
        self.k = kf
        self.update_keys(k)

    def update_keys(self, k):
        """Update configuration keys with new keys
        Keyword Arguments:
        k -- new key
        """
        keys_self = list(self.k.keys())
        keys_new = list(k.keys())
        eq_list = [i for i in self.k if i in k]
        new_key_list = list(set(keys_new) - set(keys_self))
        for i in eq_list:
            self.k[i].update(k[i])
        for i in new_key_list:
            self.k[i] = k[i]

    def edit_key_dict(self, k):
        """Edit configuration keys, edit existing or add new
        Input keys in dictionary format
        Keyword Arguments:
        k -- keys of configuration file
        """
        self.update_keys(k)
        if self.verbosity:
            for section in k:
                for i in k[section]:
                    print('Edit key: section: %s, keys: %s=%s' % (section, i, str(k[section][i])))

    def edit_key(self, section, kname, kval):
        """Edit key using field names
        Keyword Arguments:
        section -- section of key
        kname   -- name of key
        kval    -- value of key
        """
        if self.verbosity:
            print('Edit key: section: %s, keys: %s=%s' % (str(section), str(kname), str(kval)))
        self.k[str(section)][str(kname)] = kval

    def get_all_keys(self):
        """Returns all keys as dictionary
        """
        return self.k

    def get_key(self, section, name):
        """Returns key value from section and name
        Keyword Arguments:
        section -- section of key
        name    -- name for key
        """
        return self.k[section][name]

    def write2file(self):
        """Write keys to configuration file
        Returns:
        True if successful, False if error occurred
        """
        if not self.fname or not isinstance(self.fname, str):
            print('+-----------------------------------+')
            print('| Error! Invalid config filename    |')
            print('+-----------------------------------+')
            return False

        f = None
        try:
            sections = config.sections()
            for section in sorted(self.k):
                if section not in sections:
                    config.add_section(section)
                for i in sorted(self.k[section]):
                    config.set(section, i, self.k[section][i])
            f = open(self.fname, 'w')
            config.write(f)
            return True
        except IOError:
            print('+-----------------------------------+')
            print('| Error! Cannot write config file   |')
            print('| File: \'%s\'' % self.fname)
            print('| Check file permissions and disk   |')
            print('| space                              |')
            print('+-----------------------------------+')
            return False
        except (OSError, ValueError):
            print('+-----------------------------------+')
            print('| Error! Writing configuration      |')
            print('| File: \'%s\'' % self.fname)
            print('+-----------------------------------+')
            return False
        finally:
            if f:
                f.close()

    def __str__(self):
        s = 'File name: %s' % str(self.fname)
        for section in sorted(self.k):
            s = '%s\nSection: %s:' % (s, section)
            for i in sorted(self.k[section]):
                s = '%s \'%s\'=%s' % (s, i, self.k[section][i])
        return '%s;' % s


if __name__ == '__main__':
    def write_template_file(fname):
        f = open(fname, 'w')
        f.write('[Default1]\n')
        f.write('name10 = origin10\n')
        f.write('name11 = origin11\n')
        f.write('\n')
        f.write('[Default0]\n')
        f.write('name01 = origin01\n')
        f.write('name00 = origin00\n')
        f.close()

    fname = 'configfile.ini'
    write_template_file(fname)
    from shutil import copyfile
    copyfile(fname, 'tmp_configfile.ini')
    key1 = {}
    key1 = {'Default0': {'name00': 'init00', 'name01': 'init01', 'name_empty': 'some_name'},
            'Feature': {'option1': 'init_option1'}}
    print('\nRun test:')
    c = ConfigFile(fname, key1, 1)
    print('--------------------------------------------------------')
    print('* Config: ' + str(c))
    print('--------------------------------------------------------')
    new_k1 = {'Default0': {'name00': 'edited00', 'name02': 'new_edit_value02'}}
    c.edit_key_dict(new_k1)
    new_k2 = {'Default0': {'name00': 'edited00_2'},
              'Default2': {'name99': '99', 'name02': 'edited02_0'}}
    c.edit_key_dict(new_k2)
    print('--------------------------------------------------------')
    print('* Config: ' + str(c))
    print('--------------------------------------------------------')
    print('Write2file')
    c.edit_key('Default2', 'name99', 'new_name99')
    c.write2file()
    print('-------------')
    print('get_all_keys: %s' % c.get_all_keys())
    print('Some key[%s][%s] = %s' % ('Default0', 'name00', c.get_key('Default0', 'name00')))
    print('Done')
