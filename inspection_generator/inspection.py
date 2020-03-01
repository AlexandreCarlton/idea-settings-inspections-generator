from typing import Dict, Tuple
import string

from inspection_generator.raw_inspection import RawInspection
from inspection_generator.inspection_package import InspectionPackage

class Inspection:

    def __init__(self, inspection: RawInspection, properties: Dict[str, str]):
        self._inspection = inspection
        self._properties = properties
        self._package = InspectionPackage(self.path)

    @property
    def path(self) -> Tuple[str]:
        p = []
        if self._inspection.group_path:
            p += self._inspection.group_path.split(',')
        if self._inspection.group_key in self._properties:
            p.append(self._properties[self._inspection.group_key])
        if not p:
            p.append(self._inspection.group_name)
        return tuple(p)

    @property
    def short_name(self):
        return self._inspection.short_name

    @property
    def menu_name(self) -> str:
        name = self._properties.get(self._inspection.key,
                                    self._inspection.display_name)
        # Somtimes we have ''ADD''/''COPY'' which looks weird - we want regular
        # double quotes
        name = name.replace("''", '"')
        return name

    @property
    def class_name_prefix(self) -> str:
        return Inspection._pascal(self.menu_name)

    @property
    def variable_name_prefix(self) -> str:
        prefix = self.class_name_prefix
        return prefix[0].lower() + prefix[1:]

    @property
    def sub_package(self) -> str:
        return self._package.sub_package

    @property
    def sub_folder(self) -> str:
        return self._package.sub_folder

    @staticmethod
    def _pascal(s: str) -> str:
        replaced = (s.replace('==', 'equals')
                    .replace('++', 'increment')
                    .replace('--', 'decrement'))
        return ''.join(replaced.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation))).title().split(' '))



