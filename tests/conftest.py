#!/usr/bin/env python

"""
Pytest configuration and shared fixtures
"""

from __future__ import print_function
import pytest
import os
import sys
import tempfile
import shutil

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def temp_dir(tmpdir):
    """Temporary directory for test files"""
    return str(tmpdir)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file path"""
    def _make_temp_file(filename):
        return os.path.join(temp_dir, filename)
    return _make_temp_file


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing"""
    return {
        'Section1': {'key1': 'value1', 'key2': 'value2'},
        'Section2': {'key3': 'value3', 'key4': 'value4'}
    }


@pytest.fixture
def sample_netlist_file(temp_file):
    """Create a sample Cadence netlist file for testing"""
    fname = temp_file('test_netlist.dat')
    # Parser increments cnt_string, then checks if cnt_string==2
    # Line 0: cnt=0->1, check 1==2? no
    # Line 1: cnt=1->2, check 2==2? YES - parse line 1
    # So line 1 should be: { Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
    content = """{
{ Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
}
NET_NAME
'net1'
NODE_NAME DD2 A1
  DD2
  A1
  node_name_a1
NET_NAME
'net2'
NODE_NAME DD2 B2
  DD2
  B2
  node_name_b2
NODE_NAME R1 1
  R1
  1
  resistor_pin
NET_NAME
'GND'
NODE_NAME DD2 G1
  DD2
  G1
  gnd_pin
END.
"""
    with open(fname, 'w') as f:
        f.write(content)
    return fname


@pytest.fixture
def sample_quartus_pin_file(temp_file):
    """Create a sample Quartus pin file for testing"""
    fname = temp_file('test_pin.pin')
    content = """
Header line 1
Header line 2
Pin Name/Usage               : Location  : Dir.     : I/O Standard      : Voltage : I/O Bank  : User Assignment
---------------------------------------------------------------------------------------------------------------------
GND : A1 : gnd :  :  :  :
net1 : B2 : output : SSTL-18 Class I :  : 4 : Y
net2 : C3 : input : SSTL-18 Class I :  : 4 : Y
NC : D4 : output :  :  :  :
"""
    with open(fname, 'w') as f:
        f.write(content)
    return fname


@pytest.fixture
def data_dir():
    """Return path to test data directory"""
    test_dir = os.path.dirname(__file__)
    data_path = os.path.join(test_dir, 'data')
    return data_path


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory"""
    test_dir = os.path.dirname(__file__)
    fixtures_path = os.path.join(test_dir, 'fixtures')
    return fixtures_path
