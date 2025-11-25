#!/usr/bin/env python

"""
Integration and regression tests for full merge workflow
"""

from __future__ import print_function
import pytest
import os
import re

from quartus_cadence_netlist_merger.allegronetlist import AllegroNetList
from quartus_cadence_netlist_merger.quartuspin import QuartusPin


@pytest.mark.integration
def test_regression_full_merge(sample_netlist_file, sample_quartus_pin_file):
    """Test full merge workflow with sample data - validates exact output"""
    # Load both files
    netlist = AllegroNetList(sample_netlist_file)
    pin = QuartusPin(sample_quartus_pin_file)

    # Build refdes list for DD2
    result = netlist.build_refdes_list('DD2')
    assert result is True

    # Verify data structure is correct
    assert pin.data_length() == 4  # GND, net1, net2, NC
    assert netlist.net_list_length() == 3  # GND, net1, net2

    # Verify exact pin-to-net mappings
    assert netlist.get_net_name4refdes_pin('DD2', 'A1') == 'net1'
    assert netlist.get_net_name4refdes_pin('DD2', 'B2') == 'net2'
    assert netlist.get_net_name4refdes_pin('DD2', 'G1') == 'GND'

    # Verify missing pin returns empty string
    assert netlist.get_net_name4refdes_pin('DD2', 'XX') == ''

    # Verify netlist contains expected nets (sorted alphabetically)
    net_names = [netlist.net_name(i) for i in range(netlist.net_list_length())]
    assert 'GND' in net_names
    assert 'net1' in net_names
    assert 'net2' in net_names


@pytest.mark.integration
def test_regression_summary_report(sample_netlist_file, sample_quartus_pin_file):
    """Test summary report generation - validates output structure"""
    netlist = AllegroNetList(sample_netlist_file)
    pin = QuartusPin(sample_quartus_pin_file)

    netlist.build_refdes_list('DD2')

    # Verify header contains expected metadata
    header = pin.get_header()
    assert header != ''
    assert 'Header line 1' in header
    assert 'Header line 2' in header

    # Verify table header format
    table_header = pin.get_table_header()
    assert 'Pin Name' in table_header
    assert 'Location' in table_header
    assert 'I/O Standard' in table_header

    # Verify netlist output format
    net_string = netlist.net_list2string()
    assert len(net_string) > 0

    # Verify all expected nets are present in output
    assert 'GND' in net_string
    assert 'net1' in net_string
    assert 'net2' in net_string

    # Verify net contains correct refdes/pin pairs
    assert 'DD2' in net_string
    assert 'R1' in net_string

    # Verify netlist info format
    info = netlist.net_list_info()
    assert '16.3.0' in info  # version
    assert 'Mar-22-2016' in info  # date
    assert '10:54:51' in info  # time


@pytest.mark.integration
@pytest.mark.regression
def test_regression_netlist_parsing_consistency(sample_netlist_file):
    """Test netlist parsing produces deterministic results"""
    # Parse the same file twice
    netlist1 = AllegroNetList(sample_netlist_file)
    netlist2 = AllegroNetList(sample_netlist_file)

    # Results should be identical
    assert netlist1.net_list_length() == netlist2.net_list_length()
    assert netlist1.version == netlist2.version
    assert netlist1.date == netlist2.date
    assert netlist1.time == netlist2.time

    # Net names should be identical in same order
    for i in range(netlist1.net_list_length()):
        name1 = netlist1.net_name(i)
        name2 = netlist2.net_name(i)
        assert name1 == name2, "Net name at index %d differs: %s != %s" % (i, name1, name2)

    # Node lists should be identical
    for i in range(netlist1.net_list_length()):
        nodes1 = netlist1.node_list(i)
        nodes2 = netlist2.node_list(i)
        assert nodes1 == nodes2, "Node list at index %d differs" % i

    # Refdes lists should be buildable identically
    netlist1.build_refdes_list('DD2')
    netlist2.build_refdes_list('DD2')

    # Verify same refdes data
    refdes_str1 = netlist1.refdes_list2string('DD2')
    refdes_str2 = netlist2.refdes_list2string('DD2')
    assert refdes_str1 == refdes_str2


@pytest.mark.integration
@pytest.mark.regression
def test_regression_quartus_pin_parsing_consistency(sample_quartus_pin_file):
    """Test Quartus pin file parsing produces deterministic results"""
    # Parse the same file twice
    pin1 = QuartusPin(sample_quartus_pin_file)
    pin2 = QuartusPin(sample_quartus_pin_file)

    # Results should be identical
    assert pin1.data_length() == pin2.data_length()
    assert pin1.get_header() == pin2.get_header()
    assert pin1.get_table_header() == pin2.get_table_header()
    assert pin1.get_table_line() == pin2.get_table_line()

    # All pin data should be identical
    for i in range(pin1.data_length()):
        assert pin1.get_net_name(i) == pin2.get_net_name(i), \
            "Net name at index %d differs" % i
        assert pin1.get_pin(i) == pin2.get_pin(i), \
            "Pin number at index %d differs" % i
        assert pin1.data_qpin2string(i) == pin2.data_qpin2string(i), \
            "Pin data string at index %d differs" % i


@pytest.mark.integration
def test_regression_merged_data_validation(sample_netlist_file, sample_quartus_pin_file, temp_dir):
    """Test complete merge operation produces expected output structure"""
    from quartus_cadence_netlist_merger.allegronetlist import AllegroNetList
    from quartus_cadence_netlist_merger.quartuspin import QuartusPin

    netlist = AllegroNetList(sample_netlist_file)
    pin = QuartusPin(sample_quartus_pin_file)

    # Build refdes list
    netlist.build_refdes_list('DD2')

    # Simulate building merged data (what qp_cnl_merger.build_merged_data does)
    max_length = 20
    merged_lines = []

    for i in range(pin.data_length()):
        pin_in_pin_file = pin.get_pin(i)
        net_in_net_file = netlist.get_net_name4refdes_pin('DD2', pin_in_pin_file)

        # Pad net name
        net_padded = net_in_net_file + ' ' * (max_length - len(net_in_net_file))

        # Get pin name
        pin_name = netlist.get_refdes_pin_name('DD2', pin_in_pin_file)
        pin_name_padded = pin_name + ' ' * (max_length - len(pin_name))

        summary = '%s%s' % (pin_name_padded, net_padded)
        pin_text = pin.data_qpin2string(i)

        merged_line = '%s %s' % (summary, pin_text)
        merged_lines.append(merged_line)

    # Validate merged output
    assert len(merged_lines) == 4  # 4 pins in test data

    # Verify each line has expected structure
    for line in merged_lines:
        assert len(line) > 0
        # Each line should have pin name, net name, and pin data
        parts = line.split()
        assert len(parts) >= 3  # At minimum: pin_name net_name location

    # Verify specific pin mappings are in output
    merged_text = '\n'.join(merged_lines)
    assert 'net1' in merged_text
    assert 'net2' in merged_text
    assert 'GND' in merged_text

    # Verify pin locations are preserved
    assert 'A1' in merged_text
    assert 'B2' in merged_text
    assert 'C3' in merged_text
    assert 'D4' in merged_text
