#!/usr/bin/env python
"""Shared pytest fixtures and configuration

This module provides common fixtures for all tests.
Compatible with Python 2.7 and Python 3.4+
"""

from __future__ import print_function

import os
import sys
import tempfile
import shutil

import pytest

# Import toml for reading pyproject.toml
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Python 3.6-3.10
    except ImportError:
        try:
            import toml as tomllib  # Python 2.7+ fallback
        except ImportError:
            tomllib = None


@pytest.fixture
def test_data_dir():
    """Return path to test data directory
    Returns:
    Absolute path to tests/data/ directory
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'data')


@pytest.fixture
def test_inputs_dir(test_data_dir):
    """Return path to test input files directory
    Returns:
    Absolute path to tests/data/inputs/ directory
    """
    return os.path.join(test_data_dir, 'inputs')


@pytest.fixture
def test_expected_dir(test_data_dir):
    """Return path to expected output files directory
    Returns:
    Absolute path to tests/data/expected/ directory
    """
    return os.path.join(test_data_dir, 'expected')


@pytest.fixture
def sample_quartus_pin(test_inputs_dir):
    """Return path to sample Quartus pin file
    Returns:
    Path to quartus.pin test file
    """
    return os.path.join(test_inputs_dir, 'quartus.pin')


@pytest.fixture
def sample_cadence_netlist(test_inputs_dir):
    """Return path to sample Cadence netlist file
    Returns:
    Path to pstxnet.dat test file
    """
    return os.path.join(test_inputs_dir, 'pstxnet.dat')


@pytest.fixture
def expected_merged_report(test_expected_dir):
    """Return path to expected merged report output
    Returns:
    Path to expected MergedQC.rpt file
    """
    return os.path.join(test_expected_dir, 'MergedQC.rpt')


@pytest.fixture
def expected_summary_report(test_expected_dir):
    """Return path to expected summary report output
    Returns:
    Path to expected MergedQC.summary.rpt file
    """
    return os.path.join(test_expected_dir, 'MergedQC.summary.rpt')


@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs
    Returns:
    Path to temporary directory (automatically cleaned up after test)
    """
    tmpdir = tempfile.mkdtemp(prefix='qpcnl_test_')
    yield tmpdir
    # Cleanup after test
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)


@pytest.fixture
def temp_file(temp_dir):
    """Create temporary file factory for testing
    Returns:
    Factory function that creates temporary files with given names
    """
    def _temp_file_factory(filename):
        """Create a temporary file with the given filename
        Keyword Arguments:
        filename -- name of the file to create
        Returns:
        Absolute path to the temporary file
        """
        return os.path.join(temp_dir, filename)
    return _temp_file_factory


@pytest.fixture
def temp_config_file(temp_dir):
    """Create temporary config file for testing
    Returns:
    Path to temporary .qp_cnl_merger.dat file
    """
    config_path = os.path.join(temp_dir, '.qp_cnl_merger.dat')
    return config_path


@pytest.fixture
def sample_config_dict():
    """Return sample configuration dictionary
    Returns:
    Dictionary with default configuration values
    """
    return {
        'PATH': {
            'quartus_pin_file': '/path/to/quartus.pin',
            'cadence_netlist_file': '/path/to/pstxnet.dat'
        },
        'FILTER': {
            'refdes_mask': 'DD2',
            'show_signal': '1',
            'show_power': '1',
            'show_nc': '1'
        }
    }


@pytest.fixture
def mock_quartus_pin_content():
    """Return mock content for Quartus pin file
    Returns:
    String with sample Quartus pin file content
    """
    return '''# Quartus pin file
# Sample data for testing
Pin_1  Net_A  Input
Pin_2  Net_B  Output
Pin_3  Net_C  Bidir
'''


@pytest.fixture
def mock_cadence_netlist_content():
    """Return mock content for Cadence netlist file
    Returns:
    String with sample Cadence netlist content
    """
    return '''( { Cadence Netlist }
  ( Net_A DD2.1 )
  ( Net_B DD2.2 )
  ( Net_C DD2.3 )
)
'''


# Aliases for backward compatibility with existing tests
@pytest.fixture
def sample_netlist_file(sample_cadence_netlist):
    """Alias for sample_cadence_netlist (real data - for integration tests)
    Returns:
    Path to pstxnet.dat test file
    """
    return sample_cadence_netlist


@pytest.fixture
def sample_quartus_pin_file(sample_quartus_pin):
    """Alias for sample_quartus_pin (real data - for integration tests)
    Returns:
    Path to quartus.pin test file
    """
    return sample_quartus_pin


# Mock data files for unit tests (small, predictable data)
@pytest.fixture
def mock_netlist_file(temp_dir):
    """Create mock Cadence netlist file with known test data
    Returns:
    Path to temporary mock netlist file
    """
    mock_file = os.path.join(temp_dir, 'mock_pstxnet.dat')
    content = '''FILE_TYPE = EXPANDEDNETLIST;
{ Using PSTWRITER 16.3.0 p002Mar-22-2016 at 10:54:51 }
NET_NAME
'GND'
 '@CAPTURENAME.sometext':
 C_SIGNAL='some_text';
NODE_NAME	DD2 A1
 '@CAPTURENAME.sometext':
 'A1':;
NODE_NAME	DD2 B2
 '@CAPTURENAME.sometext':
 'B2':;
NET_NAME
'net1'
 '@CAPTURENAME.sometext':
 C_SIGNAL='some_text';
NODE_NAME	DD2 C3
 '@CAPTURENAME.sometext':
 'C3':;
NODE_NAME	DD2 D4
 '@CAPTURENAME.sometext':
 'D4':;
NET_NAME
'net2'
 '@CAPTURENAME.sometext':
 C_SIGNAL='some_text';
NODE_NAME	DD2 E5
 '@CAPTURENAME.sometext':
 'E5':;
'''
    with open(mock_file, 'w') as f:
        f.write(content)
    return mock_file


@pytest.fixture
def mock_quartus_file(temp_dir):
    """Create mock Quartus pin file with known test data
    Returns:
    Path to temporary mock Quartus pin file
    """
    mock_file = os.path.join(temp_dir, 'mock_quartus.pin')
    content = '''-- Copyright (C) 1991-2015 Altera Corporation. All rights reserved.
-- Device: Test Device
CHIP  "quartus"  ASSIGNED TO AN: EP4CE30F23C7

Pin Name/Usage               : Location  : Dir.   : I/O Standard      : Voltage : I/O Bank  : User Assignment
-------------------------------------------------------------------------------------------------------------
GND                          : A1        : gnd    :                   :         :           :
net1                         : A2        : input  : 2.5 V             : 2.5V    : 1         : Y
net2                         : A3        : output : 2.5 V             : 2.5V    : 1         : Y
NC                           : A4        :        :                   :         : 1         :
'''
    with open(mock_file, 'w') as f:
        f.write(content)
    return mock_file


# =============================================================================
# Pytest hooks for test count validation
# =============================================================================

def pytest_collection_finish(session):
    """Validate test count after collection to prevent accidental test removal

    This hook runs after pytest collects all tests and validates that the
    actual test count matches the expected count defined in pyproject.toml.

    Configuration location:
    [tool.quartus_cadence_netlist_merger.testing]
    expected_test_count = 47

    Keyword Arguments:
    session -- pytest session object
    """
    if tomllib is None:
        # Skip validation if toml library is not available
        return

    # Find pyproject.toml
    rootdir = session.config.rootdir
    if hasattr(rootdir, 'strpath'):  # pytest < 7
        pyproject_path = os.path.join(rootdir.strpath, 'pyproject.toml')
    else:  # pytest >= 7
        pyproject_path = os.path.join(str(rootdir), 'pyproject.toml')

    if not os.path.exists(pyproject_path):
        return

    # Read expected test count from pyproject.toml
    try:
        if hasattr(tomllib, 'load'):
            # tomllib/tomli interface
            with open(pyproject_path, 'rb') as f:
                config = tomllib.load(f)
        else:
            # toml (Python 2.7) interface
            with open(pyproject_path, 'r') as f:
                config = tomllib.load(f)
    except (IOError, OSError, ValueError) as e:
        # Only catch config file reading errors, not pytest.exit()
        print('Warning: Could not read test count config: %s' % str(e))
        return

    try:
        expected_count = config.get('tool', {}).get(
            'quartus_cadence_netlist_merger', {}
        ).get('testing', {}).get('expected_test_count')

        if expected_count is None:
            return

        # Get actual test count
        actual_count = len(session.items)

        # Validate test count
        if actual_count != expected_count:
            # Print error message
            print('')
            print('=' * 70)
            print('ERROR: Test count validation failed!')
            print('=' * 70)
            print('Expected test count: %d' % expected_count)
            print('Actual test count:   %d' % actual_count)
            print('')
            if actual_count < expected_count:
                print('WARNING: Tests may have been accidentally removed!')
                print('  - Review recent changes to test files')
                print('  - Check if tests were renamed or moved')
                print('  - If intentional, update expected_test_count in pyproject.toml')
            else:
                print('New tests added:')
                print('  - Update expected_test_count in pyproject.toml')
                print('  - Set: expected_test_count = %d' % actual_count)
            print('=' * 70)
            print('')

            # Fail the test session - this will stop pytest from running tests
            pytest.exit('Test count mismatch: expected %d, got %d' % (
                expected_count, actual_count
            ), returncode=1)

    except (KeyError, AttributeError, TypeError) as e:
        # Only catch config parsing errors, not pytest.exit()
        print('Warning: Could not parse test count config: %s' % str(e))
        return
