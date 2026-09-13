"""Alias temporário para persistência canônica em :mod:`src.shared`."""

import sys

from src.shared import persistence as _persistence

sys.modules[__name__] = _persistence
