from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class RawInspection:
    '''
    A deserialized <localInpection/> or <globalInspection/> element.
    '''
    group_key: str
    group_name: str
    group_path: str
    implementation_class: str
    language: str
    short_name: str

    key: Optional[str]
    display_name: Optional[str]

    @staticmethod
    def from_xml(xml):
        return RawInspection(display_name=xml.get("displayName"),
                             group_key=xml.get("groupKey"),
                             group_name=xml.get("groupName"),
                             group_path=xml.get("groupPath"),
                             implementation_class=xml.get("implementationClass"),
                             key=xml.get("key"),
                             language=xml.get("language"),
                             short_name=xml.get("shortName"))

    # deprecated
    def path(self, properties: Dict[str, str]) -> Tuple[str]:
        p = []
        if self.group_path:
            p += self.group_path.split(',')
        if self.group_key in properties:
            p.append(properties[self.group_key])
        if not p:
            p.append(self.group_name)
        return tuple(p)

    # deprecated
    def menu_name(self, properties: Dict[str, str]) -> str:
        name = properties.get(inspection.key, inspection.display_name)
        return name.replace("''", '"')

    # Deprecated
    def class_name_prefix(self, properties: Dict[str, str]) -> str:
        return to_pascal(self.menu_name(properties))


