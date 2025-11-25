"""Run point"""

from .qp_cnl_merger import QuartusCadenceMerger
from .commandlinearg import get_args


def main():
    """Run point for the application script"""
    get_args()
    QuartusCadenceMerger().mainloop()
