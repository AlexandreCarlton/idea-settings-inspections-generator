import string
from typing import Tuple

class InspectionPackage:

    def __init__(self, path: Tuple[str]):
        self._path = path

    @property
    def sub_package(self) -> str:
        return '.'.join(p.lower().replace(' ', '_').replace('-', '_') for p in self._path)

    @property
    def sub_folder(self) -> str:
        return self.sub_package.replace('.', '/')

    @property
    def build_rule(self) -> str:
        return self._path[-1].lower().replace(' ', '_')

    @property
    def class_name_prefix(self) -> str:
        """Class name prefix for 'main' inspection settings (and applier)"""
        return to_pascal(' '.join(self._path))

# TODO: Consolidate these pascal methods
def to_pascal(description: str) -> str:
    return ''.join(description.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation))).title().split(' '))
