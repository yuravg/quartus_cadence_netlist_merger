"""Quartus pin and Cadence Allegro net-list merger application package."""

try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("quartus_cadence_netlist_merger")
except (ImportError, PackageNotFoundError):
    __version__ = "unknown"

# Define public interface
__all__ = ["__version__"]
