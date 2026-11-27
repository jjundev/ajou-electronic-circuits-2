"""Load this skill's assemble.py by path; workbook/assemble.py shares the module name.

Whichever of the two a process imports first owns `sys.modules['assemble']`, so product code
never imports either one by that name.
"""
import importlib.util
from pathlib import Path
import sys

PATH = Path(__file__).resolve().with_name('assemble.py')
_MODULE = None


def note_module():
    """The note builder module, never bound to the name `assemble` by this loader."""
    global _MODULE
    loaded = sys.modules.get('assemble')
    if loaded is not None and Path(getattr(loaded, '__file__', '') or '.').resolve() == PATH:
        return loaded
    if _MODULE is None:  # load once: importing it inserts its folder into sys.path
        spec = importlib.util.spec_from_file_location('ec2_review_pack_assemble', PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULE = module
    return _MODULE
