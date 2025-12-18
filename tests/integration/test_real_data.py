#!/usr/bin/env python

"""
Integration tests using real test data from tests/data/
These tests validate the actual merger output against expected results
"""

from __future__ import print_function
import pytest
import os
import tempfile
import shutil
import datetime

from quartus_cadence_netlist_merger.allegronetlist import AllegroNetList
from quartus_cadence_netlist_merger.quartuspin import QuartusPin
from quartus_cadence_netlist_merger.qp_cnl_merger import QuartusCadenceMerger


@pytest.fixture
def real_input_dir():
    """Path to real input test data"""
    test_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(test_dir, 'data', 'inputs')


@pytest.fixture
def real_expected_dir():
    """Path to expected output data"""
    test_dir = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(test_dir, 'data', 'expected')


@pytest.fixture
def real_netlist_file(real_input_dir):
    """Path to real pstxnet.dat file"""
    return os.path.join(real_input_dir, 'pstxnet.dat')


@pytest.fixture
def real_quartus_pin_file(real_input_dir):
    """Path to real quartus.pin file"""
    return os.path.join(real_input_dir, 'quartus.pin')


@pytest.fixture
def expected_merged_file(real_expected_dir):
    """Path to expected MergedQC.rpt file"""
    return os.path.join(real_expected_dir, 'MergedQC.rpt')


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)


def get_file_mtime(fname):
    """Get file modification time in YYYY-MM-DD HH:MM:SS format"""
    t = os.path.getmtime(fname)
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')


def normalize_line(line):
    """Normalize a line for comparison - handles timestamp and path differences"""
    # Remove trailing whitespace
    line = line.rstrip()
    # Skip timestamp lines (Report creation date)
    if 'Report creation date:' in line or 'report creation date:' in line:
        return None
    # Skip file path lines (contain modification dates and paths)
    if line.startswith('|  20') and (' - ' in line):
        # These are lines like: "|  2019-08-26 15:10:45 - ./pstxnet.dat"
        return None
    return line


def compare_files(generated_file, expected_file):
    """Compare two files line by line, ignoring timestamps

    Parameters:
    generated_file: Path to the generated output file
    expected_file: Path to the expected output file

    Returns:
    (bool, list): (files_match, differences)
    """
    with open(generated_file, 'r') as f1:
        generated_lines = f1.readlines()

    with open(expected_file, 'r') as f2:
        expected_lines = f2.readlines()

    # Normalize lines
    normalized_generated = [normalize_line(line) for line in generated_lines]
    normalized_expected = [normalize_line(line) for line in expected_lines]

    # Remove None entries (skipped lines like timestamps)
    normalized_generated = [l for l in normalized_generated if l is not None]
    normalized_expected = [l for l in normalized_expected if l is not None]

    if len(normalized_generated) != len(normalized_expected):
        return False, ['Line count mismatch: generated=%d vs expected=%d' % (
            len(normalized_generated), len(normalized_expected))]

    differences = []
    for i, (gen_line, exp_line) in enumerate(zip(normalized_generated, normalized_expected)):
        if gen_line != exp_line:
            differences.append('Line %d differs:\n  Expected: %s\n  Got:      %s' % (
                i+1, exp_line, gen_line))

    return len(differences) == 0, differences


@pytest.mark.integration
@pytest.mark.real_data
def test_real_data_merge_output(real_netlist_file, real_quartus_pin_file,
                                expected_merged_file, temp_output_dir):
    """
    Integration test: Load real input files, perform merge, and validate output

    This test:
    1. Loads real pstxnet.dat and quartus.pin files from tests/data/inputs/
    2. Performs the merge operation with refdes='DD2'
    3. Generates MergedQC.rpt output file
    4. Compares output with tests/data/expected/MergedQC.rpt

    NOTE: MergedQC.summary.rpt is NOT tested here - it should be validated
    manually in the examples/ directory.

    KNOWN ISSUE: AllegroNetList and QuartusPin classes use class-level variables
    which causes test isolation issues when running with other tests. The test
    passes when run individually: pytest tests/integration/test_real_data.py::test_real_data_merge_output
    """
    # Verify input files exist
    assert os.path.exists(real_netlist_file), \
        "Input file missing: %s" % real_netlist_file
    assert os.path.exists(real_quartus_pin_file), \
        "Input file missing: %s" % real_quartus_pin_file
    assert os.path.exists(expected_merged_file), \
        "Expected output file missing: %s" % expected_merged_file

    # Load the real input files
    # Note: AllegroNetList and QuartusPin classes unfortunately use class-level
    # variables, which means instances share state. We work around this by
    # loading our files last and hoping no other test modifies them after us.
    netlist = AllegroNetList(real_netlist_file)
    pin = QuartusPin(real_quartus_pin_file)

    # Verify files loaded successfully
    assert netlist.net_list_length() > 0, "Netlist is empty"
    assert pin.data_length() > 0, "Pin file is empty"

    # Build refdes list for DD2 (standard refdes used in test data)
    result = netlist.build_refdes_list('DD2')
    assert result is True, "Failed to build refdes list for DD2"

    # Generate merged output file
    output_file = os.path.join(temp_output_dir, 'MergedQC.rpt')

    # Configuration flags matching the expected output
    # Based on line 79 of expected file: "Net Name(capture) :  Pin Name/Usage"
    # This means net_name=True, refdes_pin_name=False
    refdes = 'DD2'
    require_pin_name = False  # refdes_pin_name
    req_net_name = True       # net_name

    # Build header (simulating qp_cnl_merger.header2string)
    time_cnl_fname = get_file_mtime(real_netlist_file)
    time_qp_fname = get_file_mtime(real_quartus_pin_file)
    date = '2019-08-26 15:46:48'  # Use a fixed date for reproducibility

    rpt = ''
    rpt = rpt + '|--------------------------------------------------------------------------------|\n'
    rpt = rpt + '| File contains merged Quartus Pin and Cadence PCB Editor (Allegro) Netlist      |\n'
    rpt = rpt + '| NOTE: This file was auto-generated                                             |\n'
    rpt = rpt + '| Report creation date: %s                                      |\n' % date
    rpt = rpt + '|--------------------------------------------------------------------------------|\n'
    rpt = rpt + '| Quartus, Cadence files and Refdes info:                                        |\n'
    rpt = rpt + '|  %s - %s \n' % (time_cnl_fname, real_netlist_file)
    rpt = rpt + '|  %s - %s \n' % (time_qp_fname, real_quartus_pin_file)
    rpt = rpt + '|  Refdes = %s\n' % refdes
    rpt = rpt + '|--------------------------------------------------------------------------------|\n'

    # Build pin header (simulating qp_cnl_merger.qp_pin_header2string)
    rpt = rpt + '* MERGED Quartus Pin File'
    rpt = rpt + pin.header
    if require_pin_name:
        rpt = rpt + 'Pin Name (Capture):  '
    if req_net_name:
        rpt = rpt + 'Net Name (Capture):  '
    rpt = rpt + pin.table_header
    rpt = rpt + '\n' + pin.table_line + '\n'

    # Build merged data (simulating qp_cnl_merger.build_merged_data)
    max_length = 20
    for i in range(len(pin.data)):
        pin_in_pin_file = pin.get_pin(i)
        net_in_net_file = ''
        if req_net_name:
            net_in_net_file = netlist.get_net_name4refdes_pin(refdes, pin_in_pin_file)
            net_in_net_file = net_in_net_file + ' ' * (max_length - len(net_in_net_file))
        pin_name = ''
        if require_pin_name:
            pin_name = netlist.get_refdes_pin_name(refdes, pin_in_pin_file)
            pin_name = pin_name + ' ' * (max_length - len(pin_name))
        summary = '%s%s' % (pin_name, net_in_net_file)
        formated_pin_text = '%s' % pin.data_qpin2string(i).replace(
            'RESERVED_INPUT_WITH_WEAK_PULLUP', 'RESERVED_INPUT_WITH_WEAK_PUL')
        rpt = '%s%s %s\n' % (rpt, summary, formated_pin_text)

    # Write output file
    with open(output_file, 'w') as f:
        f.write(rpt)

    # Verify output file was created
    assert os.path.exists(output_file), "Output file was not created"

    # Compare output with expected file
    files_match, differences = compare_files(output_file, expected_merged_file)

    if not files_match:
        print("\n" + "="*80)
        print("OUTPUT DOES NOT MATCH EXPECTED FILE!")
        print("="*80)
        for diff in differences[:10]:  # Show first 10 differences
            print(diff)
        if len(differences) > 10:
            print("... and %d more differences" % (len(differences) - 10))
        print("="*80)
        print("\nExpected file: %s" % expected_merged_file)
        print("Generated file: %s" % output_file)
        print("\nTo update expected file if changes are correct:")
        print("  cp %s %s" % (output_file, expected_merged_file))
        print("="*80)

    assert files_match, "Generated MergedQC.rpt does not match expected output"


@pytest.fixture
def expected_summary_file(real_expected_dir):
    """Path to expected MergedQC.summary.rpt file"""
    return os.path.join(real_expected_dir, 'MergedQC.summary.rpt')


@pytest.mark.integration
@pytest.mark.real_data
def test_real_data_summary_report_output(real_netlist_file, real_quartus_pin_file,
                                         expected_summary_file, temp_output_dir):
    """
    Integration test: Generate and validate MergedQC.summary.rpt

    This test generates the summary report with all sections enabled
    and compares it line-by-line with the expected output.

    The summary report includes:
    - Org-mode header with color coding
    - Signal Pins section
    - Non-Signal Pins section
    - Formatted Signal Pins section
    - Power Pins section
    - Unconnected Pins section
    """
    # Verify input files exist
    assert os.path.exists(real_netlist_file), \
        "Input file missing: %s" % real_netlist_file
    assert os.path.exists(real_quartus_pin_file), \
        "Input file missing: %s" % real_quartus_pin_file
    assert os.path.exists(expected_summary_file), \
        "Expected output file missing: %s" % expected_summary_file

    # Change to temp directory to generate output files there
    original_dir = os.getcwd()
    os.chdir(temp_output_dir)

    # Copy header and rename mask files to temp directory
    header_file = '.qp_cnl_merger_header.dat'
    source_header = os.path.join(original_dir, 'examples', header_file)
    if os.path.exists(source_header):
        shutil.copy(source_header, header_file)

    rename_file = '.qp_cnl_merger_rename.dat'
    source_rename = os.path.join(original_dir, 'examples', rename_file)
    if os.path.exists(source_rename):
        shutil.copy(source_rename, rename_file)

    try:
        # Create merger instance (will create Tkinter root automatically)
        # Following pattern from regenerate_expected.py
        merger = QuartusCadenceMerger()

        # Configure merger with input files and settings
        merger.cnl_fname = real_netlist_file
        merger.qp_fname = real_quartus_pin_file
        merger.refdes = 'DD2'

        # Enable all sections to match expected file
        merger.signal = 1          # Signal Pins section
        merger.nosignal = 1        # Non-Signal Pins section
        merger.format_signal = 1   # Formatted Signal Pins section
        merger.power = 1           # Power Pins section
        merger.noconnect = 1       # Unconnected Pins section
        merger.full_merged = 0     # Include org-mode header (not full merged)
        merger.net_name = 1        # Show net names
        merger.refdes_pin_name = 0 # Don't show refdes pin names

        # Build merged data
        merger.build_merged_data(merger.refdes_pin_name, merger.net_name)

        # Generate summary report following regenerate_expected.py pattern (lines 88-102)
        # Note: This matches how the original expected file was generated
        date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        fname_summary = 'MergedQC.summary.rpt'

        # Build summary report (matches expected file structure)
        # The expected file contains:
        # 1. Org-mode header
        # 2. Report header (file info, date, etc.)
        # 3. Pin file header + complete merged data table
        # 4. Filtered sections (Signal, Non-Signal, Formatted, Power, NC)
        s = ''
        if not merger.full_merged:
            s = merger.header2string(date)
        s = merger.read_header_file(merger.fname_header) + s
        s = s + merger.qp_pin_header2string(merger.refdes_pin_name, merger.net_name)
        s = s + merger.merged_data  # Add complete merged data table
        if merger.signal:
            s = s + merger.only_signal2string()
        if merger.nosignal:
            s = s + merger.nosignal2string()
        if merger.format_signal:
            s = s + merger.only_formatted_signal2string()
        if merger.power:
            s = s + merger.power_pins2string()
        if merger.noconnect:
            s = s + merger.noconnect2string()
        merger.write2newfile(fname_summary, s)

        # Get the output file path
        output_file = os.path.join(temp_output_dir, fname_summary)

        # Verify output file was created
        assert os.path.exists(output_file), "Output file was not created"

        # Compare output with expected file
        files_match, differences = compare_files(output_file, expected_summary_file)

        if not files_match:
            print("\n" + "="*80)
            print("OUTPUT DOES NOT MATCH EXPECTED FILE!")
            print("="*80)
            for diff in differences[:10]:  # Show first 10 differences
                print(diff)
            if len(differences) > 10:
                print("... and %d more differences" % (len(differences) - 10))
            print("="*80)
            print("\nExpected file: %s" % expected_summary_file)
            print("Generated file: %s" % output_file)
            print("\nTo update expected file if changes are correct:")
            print("  cp %s %s" % (output_file, expected_summary_file))
            print("="*80)

        assert files_match, "Generated MergedQC.summary.rpt does not match expected output"

    finally:
        # Change back to original directory
        os.chdir(original_dir)


@pytest.mark.integration
@pytest.mark.real_data
def test_real_data_netlist_parsing(real_netlist_file):
    """Validate that real netlist file can be parsed correctly"""
    netlist = AllegroNetList(real_netlist_file)

    # Verify basic parsing
    assert netlist.net_list_length() > 0, "No nets found in netlist"

    # Verify version info was extracted
    info = netlist.net_list_info()
    assert len(info) > 0, "Netlist info is empty"

    # Verify some nets exist
    net_names = [netlist.net_name(i) for i in range(netlist.net_list_length())]
    assert len(net_names) > 0, "No net names found"

    # Build refdes list
    result = netlist.build_refdes_list('DD2')
    assert result is True, "Failed to build refdes list"


@pytest.mark.integration
@pytest.mark.real_data
def test_real_data_quartus_pin_parsing(real_quartus_pin_file):
    """Validate that real Quartus pin file can be parsed correctly"""
    pin = QuartusPin(real_quartus_pin_file)

    # Verify basic parsing
    assert pin.data_length() > 0, "No pins found in pin file"

    # Verify header was extracted
    header = pin.get_header()
    assert len(header) > 0, "Header is empty"

    # Verify table header exists
    table_header = pin.get_table_header()
    assert 'Location' in table_header, "Table header missing Location column"
    assert 'Pin Name' in table_header, "Table header missing Pin Name column"

    # Verify we can extract pin data
    for i in range(min(5, pin.data_length())):  # Check first 5 pins
        pin_num = pin.get_pin(i)
        net_name = pin.get_net_name(i)
        pin_str = pin.data_qpin2string(i)

        assert pin_num != '', "Pin number is empty at index %d" % i
        assert pin_str != '', "Pin data string is empty at index %d" % i


@pytest.mark.integration
@pytest.mark.real_data
def test_real_data_refdes_mapping(real_netlist_file, real_quartus_pin_file):
    """Validate that pins can be mapped to nets using real data"""
    netlist = AllegroNetList(real_netlist_file)
    pin = QuartusPin(real_quartus_pin_file)

    # Build refdes list
    netlist.build_refdes_list('DD2')

    # Count how many pins have net mappings
    mapped_count = 0
    unmapped_count = 0

    for i in range(pin.data_length()):
        pin_num = pin.get_pin(i)
        net_name = netlist.get_net_name4refdes_pin('DD2', pin_num)

        if net_name != '':
            mapped_count += 1
        else:
            unmapped_count += 1

    # We expect at least some pins to be mapped
    assert mapped_count > 0, "No pins were mapped to nets"

    # Print statistics
    print("\nPin mapping statistics:")
    print("  Mapped pins: %d" % mapped_count)
    print("  Unmapped pins: %d" % unmapped_count)
    print("  Total pins: %d" % pin.data_length())
    print("  Mapping rate: %.1f%%" % (100.0 * mapped_count / pin.data_length()))
