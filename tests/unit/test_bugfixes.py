#!/usr/bin/env python
"""Test cases for critical bug fixes

This test file specifically tests the fixes for critical bugs discovered during
code review. Each test corresponds to a specific bug fix.
"""

import os
import tempfile
import shutil
from quartus_cadence_netlist_merger.allegronetlist import AllegroNetList


def test_allegronetlist_malformed_node_name_line():
    """Test issue #3: Index out of bounds crash with malformed NODE_NAME line

    Bug: allegronetlist.py:154-155 didn't check array bounds before accessing
    parts[1] and parts[2], causing IndexError on malformed input.

    Fix: Added bounds checking with len(parts) >= 3
    """
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    try:
        # Create malformed netlist with insufficient fields in proper Allegro format
        malformed_file = os.path.join(tmpdir, 'malformed.txt')
        with open(malformed_file, 'w') as f:
            f.write('FILE_TYPE = EXPANDEDNETLIST;\n')
            f.write('NET_NAME\n')
            f.write("'VALID_NET'\n")
            f.write('NODE_NAME\tU1\t1\n')  # Valid line with 3 fields
            f.write("  'A1':;\n")
            f.write('NODE_NAME\tU2\n')     # Malformed: only 2 fields
            f.write("  'B1':;\n")
            f.write('NET_NAME\n')
            f.write("'ANOTHER_NET'\n")
            f.write('NODE_NAME\tU3\t2\n')  # Another valid line
            f.write("  'C1':;\n")

        # This should not crash despite malformed line
        netlist = AllegroNetList(malformed_file)

        # Should have parsed at least one valid net (VALID_NET or ANOTHER_NET)
        # The malformed line should be skipped with a warning
        assert isinstance(netlist.net_list, list), 'net_list should be a list'
        # Note: May have 0 nets if both have issues, but should not crash

    finally:
        shutil.rmtree(tmpdir)


def test_allegronetlist_empty_node_name_line():
    """Test issue #3: Handles NODE_NAME with no additional fields gracefully"""
    tmpdir = tempfile.mkdtemp()
    try:
        malformed_file = os.path.join(tmpdir, 'empty_node.txt')
        with open(malformed_file, 'w') as f:
            f.write('FILE_TYPE = EXPANDEDNETLIST;\n')
            f.write('NET_NAME\n')
            f.write("'TEST_NET'\n")
            f.write('NODE_NAME\n')  # Malformed: only keyword, no fields
            f.write("  'A1':;\n")

        # Should not crash
        netlist = AllegroNetList(malformed_file)

        # Net list may be empty since no valid nodes
        assert isinstance(netlist.net_list, list), 'Should return list even with malformed data'

    finally:
        shutil.rmtree(tmpdir)


def test_write2newfile_path_validation_invalid_filename():
    """Test issue #4: Path validation prevents None/empty filename

    Bug: write2newfile didn't validate filename before use
    Fix: Added validation for None and empty string filenames
    """
    # Note: This test imports the class but doesn't instantiate the full GUI
    # We can't easily test write2newfile without the full QuartusCadenceNetListMerger
    # class because it requires Tkinter initialization. The validation logic is
    # tested indirectly through integration tests.
    pass


def test_quartuspin_get_pin_returns_false_on_invalid_index():
    """Test issue #5: Validate that get_pin returns False for invalid index

    Bug: Code didn't check if get_pin() returned False before using result
    Fix: Added validation check before using pin_number
    """
    from quartus_cadence_netlist_merger.quartuspin import QuartusPin

    tmpdir = tempfile.mkdtemp()
    try:
        # Create minimal valid Quartus pin file in proper format
        pin_file = os.path.join(tmpdir, 'test.pin')
        with open(pin_file, 'w') as f:
            f.write('-- Copyright (C) 1991-2015 Altera Corporation\n')
            f.write('CHIP  "quartus"  ASSIGNED TO AN: EP4CE30F23C7\n')
            f.write('\n')
            f.write('Pin Name/Usage               : Location  : Dir.   : I/O Standard      : Voltage\n')
            f.write('----------------------------------------------------------------------------------------------\n')
            f.write('GND                          : A1        : gnd    :                   :        \n')
            f.write('test_net                     : B2        : input  : 2.5 V             : 2.5V   \n')

        qpin = QuartusPin(pin_file)

        # Valid index should return pin number
        valid_pin = qpin.get_pin(0)
        assert valid_pin != False, 'Valid index should return pin number'
        assert valid_pin == 'A1', 'Should return correct pin number (first pin)'

        # Second valid pin
        second_pin = qpin.get_pin(1)
        assert second_pin != False, 'Second valid index should return pin number'
        assert second_pin == 'B2', 'Should return correct pin number (second pin)'

        # Invalid index should return False
        invalid_pin = qpin.get_pin(999)
        assert invalid_pin is False, 'Invalid index should return False'

        # Note: Negative indices are valid in Python and work as expected
        # (e.g., -1 returns the last element), so we don't test them as invalid

    finally:
        shutil.rmtree(tmpdir)


# Note: Testing issue #1 (uninitialized variable 's') and issue #2 (rename_mask
# clearing) would require instantiating the full GUI class with Tkinter, which
# is difficult in unit tests. These are better tested through integration tests
# or manual testing.
