#!/usr/bin/env python

"""
Unit tests for configfile.py module
"""

from __future__ import print_function
import pytest
import os

from quartus_cadence_netlist_merger.configfile import ConfigFile


@pytest.mark.unit
def test_configfile_init_with_defaults(temp_file):
    """Test ConfigFile initialization with default values"""
    fname = temp_file('test_config.ini')
    default_keys = {
        'Section1': {'key1': 'default1', 'key2': 'default2'},
        'Section2': {'key3': 'default3'}
    }

    cfg = ConfigFile(fname, default_keys)

    assert cfg.fname == fname
    assert cfg.get_key('Section1', 'key1') == 'default1'
    assert cfg.get_key('Section1', 'key2') == 'default2'
    assert cfg.get_key('Section2', 'key3') == 'default3'


@pytest.mark.unit
def test_configfile_reads_existing_file(temp_file):
    """Test ConfigFile reads and overrides from existing file"""
    fname = temp_file('test_config.ini')

    # Create a config file
    with open(fname, 'w') as f:
        f.write('[Section1]\n')
        f.write('key1 = overridden1\n')
        f.write('key2 = overridden2\n')

    default_keys = {
        'Section1': {'key1': 'default1', 'key2': 'default2', 'key3': 'default3'}
    }

    cfg = ConfigFile(fname, default_keys)

    # Values from file should override defaults
    assert cfg.get_key('Section1', 'key1') == 'overridden1'
    assert cfg.get_key('Section1', 'key2') == 'overridden2'
    # Key not in file should keep default
    assert cfg.get_key('Section1', 'key3') == 'default3'


@pytest.mark.unit
def test_configfile_update_keys_merges_sections(temp_file):
    """Test update_keys merges new sections correctly"""
    fname = temp_file('test_config_update.ini')
    default_keys = {
        'SectionA': {'key1': 'value1'}
    }

    cfg = ConfigFile(fname, default_keys)

    new_keys = {
        'SectionA': {'key2': 'value2'},  # Add to existing section
        'SectionB': {'key3': 'value3'}   # New section
    }

    cfg.update_keys(new_keys)

    assert cfg.get_key('SectionA', 'key1') == 'value1'
    assert cfg.get_key('SectionA', 'key2') == 'value2'
    assert cfg.get_key('SectionB', 'key3') == 'value3'


@pytest.mark.unit
def test_configfile_edit_key_updates_value(temp_file):
    """Test edit_key updates existing key value"""
    fname = temp_file('test_config.ini')
    default_keys = {
        'Section1': {'key1': 'original'}
    }

    cfg = ConfigFile(fname, default_keys)
    cfg.edit_key('Section1', 'key1', 'updated')

    assert cfg.get_key('Section1', 'key1') == 'updated'


@pytest.mark.unit
def test_configfile_get_key_returns_correct_value(temp_file):
    """Test get_key returns correct value from section"""
    fname = temp_file('test_config_getkey.ini')
    default_keys = {
        'SectionX': {'keyX1': 'valueX1', 'keyX2': 'valueX2'},
        'SectionY': {'keyY1': 'valueY3'}  # Different section
    }

    cfg = ConfigFile(fname, default_keys)

    assert cfg.get_key('SectionX', 'keyX1') == 'valueX1'
    assert cfg.get_key('SectionX', 'keyX2') == 'valueX2'
    assert cfg.get_key('SectionY', 'keyY1') == 'valueY3'


@pytest.mark.unit
def test_configfile_write_and_read_persistence(temp_file):
    """Test write2file persists data that can be read back"""
    fname = temp_file('test_config_persist.ini')
    default_keys = {
        'SectionP': {'keyP1': 'valueP1', 'keyP2': 'valueP2'},
        'SectionQ': {'keyQ3': 'valueQ3'}
    }

    # Create and write config
    cfg1 = ConfigFile(fname, default_keys)
    cfg1.edit_key('SectionP', 'keyP1', 'modified')
    cfg1.write2file()

    # Read back and verify
    cfg2 = ConfigFile(fname, {})
    assert cfg2.get_key('SectionP', 'keyP1') == 'modified'
    assert cfg2.get_key('SectionP', 'keyP2') == 'valueP2'
    assert cfg2.get_key('SectionQ', 'keyQ3') == 'valueQ3'
