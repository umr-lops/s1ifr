from importlib.metadata import version

try:
    __version__ = version("s1ifr")
except Exception:
    __version__ = "999"