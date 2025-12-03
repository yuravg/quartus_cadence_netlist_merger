#!/usr/bin/env python

"""
Unit tests for quartuspin.py module
"""

from __future__ import print_function
import pytest
import os

from quartus_cadence_netlist_merger.quartuspin import QuartusPin


@pytest.mark.unit
def test_quartuspin_reads_valid_file(sample_quartus_pin_file):
    """Test QuartusPin can read and parse a valid pin file"""
    pin = QuartusPin(sample_quartus_pin_file)

    assert pin.fname == sample_quartus_pin_file
    assert len(pin.data) > 0
    assert pin.header != ''
    assert pin.table_header != ''
    assert pin.table_line != ''


@pytest.mark.unit
def test_quartuspin_data_length(mock_quartus_file):
    """Test data_length returns correct count"""
    pin = QuartusPin(mock_quartus_file)

    length = pin.data_length()

    assert isinstance(length, int)
    assert length == 4  # Based on mock file: GND, net1, net2, NC


@pytest.mark.unit
def test_quartuspin_get_net_name_valid(sample_quartus_pin_file):
    """Test get_net_name returns correct name for valid index"""
    pin = QuartusPin(sample_quartus_pin_file)

    # Get first pin's net name
    net_name = pin.get_net_name(0)

    assert isinstance(net_name, str)
    assert net_name in ['GND', 'net1', 'net2', 'NC']


@pytest.mark.unit
def test_quartuspin_get_pin_valid(sample_quartus_pin_file):
    """Test get_pin returns correct pin number for valid index"""
    pin = QuartusPin(sample_quartus_pin_file)

    # Get first pin number
    pin_num = pin.get_pin(0)

    assert isinstance(pin_num, str)
    assert pin_num in ['A1', 'B2', 'C3', 'D4']


@pytest.mark.unit
def test_quartuspin_check_data_index_invalid(sample_quartus_pin_file):
    """Test check_data_index returns False for invalid index"""
    pin = QuartusPin(sample_quartus_pin_file)

    result = pin.check_data_index(999)

    assert result is False


@pytest.mark.unit
def test_quartuspin_data_qpin2string(sample_quartus_pin_file):
    """Test data_qpin2string returns formatted string"""
    pin = QuartusPin(sample_quartus_pin_file)

    result = pin.data_qpin2string(0)

    assert isinstance(result, str)
    assert len(result) > 0
