"""Get arguments from command line
"""

try:
    from argparse import ArgumentParser
except ImportError:  # for version < 3.0
    from ArgParse import ArgumentParser

from .__init__ import __version__

__prog__ = "qp_cnl_merger"
__description__ = "Quartus pin and Cadence Allegro Net-List merger (cnl - Cadence Net-List)"
__version_string__ = '%s version %s' % (__prog__, __version__)


def get_args():
    """Run Argument Parser and get argument from command line"""
    parser = ArgumentParser(prog=__prog__,
                            description=__description__)
    parser.add_argument('-V', '--version',
                        action='version',
                        version=__version_string__)
    return parser.parse_args()
