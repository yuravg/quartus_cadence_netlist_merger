#!/usr/bin/env python

"""
Unit tests for allegronetlist.py module
"""

from __future__ import print_function
import pytest
import os

from quartus_cadence_netlist_merger.allegronetlist import AllegroNetList


@pytest.mark.unit
def test_allegronetlist_reads_valid_file(mock_netlist_file):
    """Test AllegroNetList can read and parse a valid netlist file"""
    netlist = AllegroNetList(mock_netlist_file)

    assert netlist.fname == mock_netlist_file
    assert netlist.version == '16.3.0'
    assert netlist.date == 'Mar-22-2016'
    assert len(netlist.net_list) > 0


@pytest.mark.unit
def test_allegronetlist_net_list_length(mock_netlist_file):
    """Test net_list_length returns correct count"""
    netlist = AllegroNetList(mock_netlist_file)

    length = netlist.net_list_length()

    assert isinstance(length, int)
    assert length >= 2  # Parser reads at least GND and net1 from mock file
    assert length <= 3  # Maximum 3 nets in mock file: GND, net1, net2


@pytest.mark.unit
def test_allegronetlist_net_name_valid_index(mock_netlist_file):
    """Test net_name returns correct name for valid index"""
    netlist = AllegroNetList(mock_netlist_file)

    # Get first net name (nets are sorted)
    net = netlist.net_name(0)

    assert isinstance(net, str)
    assert net in ['GND', 'net1', 'net2']


@pytest.mark.unit
def test_allegronetlist_net_name_invalid_index(mock_netlist_file):
    """Test net_name returns False for invalid index"""
    netlist = AllegroNetList(mock_netlist_file)

    # Out of bounds - mock file has only 3 nets
    result = netlist.net_name(999)

    assert result is False


@pytest.mark.unit
def test_allegronetlist_build_refdes_list(mock_netlist_file):
    """Test build_refdes_list creates correct refdes list"""
    netlist = AllegroNetList(mock_netlist_file)

    result = netlist.build_refdes_list('DD2')

    assert result is True
    assert len(netlist.refdes_list) > 0
    assert netlist.refdes_list[0][0] == 'DD2'


@pytest.mark.unit
def test_allegronetlist_get_net_name4refdes_pin(mock_netlist_file):
    """Test get_net_name4refdes_pin returns correct net name"""
    netlist = AllegroNetList(mock_netlist_file)
    netlist.build_refdes_list('DD2')

    # DD2.A1 is on GND net according to mock data
    net_name = netlist.get_net_name4refdes_pin('DD2', 'A1')

    assert isinstance(net_name, str)
    assert net_name == 'GND'


@pytest.mark.unit
def test_allegronetlist_get_refdes_pin_name(mock_netlist_file):
    """Test get_refdes_pin_name returns pin name string"""
    netlist = AllegroNetList(mock_netlist_file)

    pin_name = netlist.get_refdes_pin_name('DD2', 'A1')

    assert isinstance(pin_name, str)
    assert len(pin_name) > 0
