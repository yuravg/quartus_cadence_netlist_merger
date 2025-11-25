#!/usr/bin/env python

"""
Unit tests for commandlinearg.py module
"""

from __future__ import print_function
import pytest
import sys

from quartus_cadence_netlist_merger.commandlinearg import get_args
from quartus_cadence_netlist_merger import __version__


@pytest.mark.unit
def test_get_args_version(monkeypatch):
    """Test get_args handles --version flag"""
    monkeypatch.setattr(sys, 'argv', ['qp_cnl_merger', '--version'])

    with pytest.raises(SystemExit) as exc_info:
        get_args()

    # --version causes exit with code 0
    assert exc_info.value.code == 0


@pytest.mark.unit
def test_get_args_default(monkeypatch):
    """Test get_args returns defaults with no arguments"""
    monkeypatch.setattr(sys, 'argv', ['qp_cnl_merger'])

    args = get_args()

    # Should return successfully without errors
    assert args is not None
