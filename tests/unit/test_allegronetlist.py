#!/usr/bin/env python

"""
Unit tests for allegronetlist.py module
"""

from __future__ import print_function
import pytest
import os

from quartus_cadence_netlist_merger.allegronetlist import AllegroNetList


@pytest.mark.unit
def test_allegronetlist_reads_valid_file(sample_netlist_file):
    """Test AllegroNetList can read and parse a valid netlist file"""
    netlist = AllegroNetList(sample_netlist_file)

    assert netlist.fname == sample_netlist_file
    assert netlist.version == '16.3.0'
    assert netlist.date == 'Mar-22-2016'
    assert netlist.time == '10:54:51'
    assert len(netlist.net_list) > 0


@pytest.mark.unit
def test_allegronetlist_net_list_length(sample_netlist_file):
    """Test net_list_length returns correct count"""
    netlist = AllegroNetList(sample_netlist_file)

    length = netlist.net_list_length()

    assert isinstance(length, int)
    assert length == 3  # Based on sample file: net1, net2, GND


@pytest.mark.unit
def test_allegronetlist_net_name_valid_index(sample_netlist_file):
    """Test net_name returns correct name for valid index"""
    netlist = AllegroNetList(sample_netlist_file)

    # Get first net name (nets are sorted)
    net = netlist.net_name(0)

    assert isinstance(net, str)
    assert net in ['GND', 'net1', 'net2']


@pytest.mark.unit
def test_allegronetlist_net_name_invalid_index(sample_netlist_file):
    """Test net_name returns False for invalid index"""
    netlist = AllegroNetList(sample_netlist_file)

    result = netlist.net_name(999)

    assert result is False


@pytest.mark.unit
def test_allegronetlist_build_refdes_list(sample_netlist_file):
    """Test build_refdes_list creates correct refdes list"""
    netlist = AllegroNetList(sample_netlist_file)

    result = netlist.build_refdes_list('DD2')

    assert result is True
    assert len(netlist.refdes_list) > 0
    assert netlist.refdes_list[0][0] == 'DD2'


@pytest.mark.unit
def test_allegronetlist_get_net_name4refdes_pin(sample_netlist_file):
    """Test get_net_name4refdes_pin returns correct net name"""
    netlist = AllegroNetList(sample_netlist_file)
    netlist.build_refdes_list('DD2')

    net_name = netlist.get_net_name4refdes_pin('DD2', 'A1')

    assert isinstance(net_name, str)
    assert net_name == 'net1'


@pytest.mark.unit
def test_allegronetlist_get_refdes_pin_name(sample_netlist_file):
    """Test get_refdes_pin_name returns pin name string"""
    netlist = AllegroNetList(sample_netlist_file)

    pin_name = netlist.get_refdes_pin_name('DD2', 'A1')

    assert isinstance(pin_name, str)
    # The pin name comes from the 3rd element added after NODE_NAME parsing
    # In our simplified test fixture, this is just the pin number
    # In real netlists, this would be the full pin name from the netlist
    assert len(pin_name) > 0
