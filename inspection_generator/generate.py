# TODO: Separate this out into separate classes.
from dataclasses import dataclass
import itertools
from pathlib import Path
import string
from typing import List, Optional, Dict, Tuple
import zipfile

import jinja2
import jproperties
from lxml import objectify

from inspection_generator.raw_inspection import RawInspection
from inspection_generator.inspection_package import InspectionPackage
from inspection_generator.inspection import Inspection

# Contains the jars and files inside that contain (localInspection|globalInspection)
# elements.
INSPECTIONS_FILES = {
    'plugins/Docker/lib/Docker-compose.jar': 'META-INF/yaml-specific.xml',
    'plugins/Docker/lib/Docker-file.jar': 'META-INF/dockerfile-language.xml',
    'plugins/java/lib/java-impl.jar': 'META-INF/InspectionGadgets.xml',
    'plugins/JavaScriptLanguage/lib/JavaScriptLanguage.jar': 'META-INF/plugin.xml',
}

# Contains the properties files that contain values to the keys stored in the
# (localInspection|globalInspection) elements.
PROPERTIES_FILES = {
    'lib/resources_en.jar': 'messages/InspectionsBundle.properties',
    'plugins/Docker/lib/Docker-compose.jar': 'resources/DockerCompose.properties',
    'plugins/Docker/lib/Docker-core.jar': 'resources/DockerBundle.properties',
    'plugins/java/lib/java_resources_en.jar': 'com/siyeh/InspectionGadgetsBundle.properties',
    'plugins/JavaScriptLanguage/lib/resources_en.jar': 'messages/JavaScriptBundle.properties',
}

properties = jproperties.Properties()
for key, value in PROPERTIES_FILES.items():
    jar = 'bazel-idea-settings/external/idea-IU/' + key
    with zipfile.ZipFile(jar, 'r') as zipped:
        with zipped.open(value) as properties_file:
            properties.load(properties_file)
properties = {k: v.data for k, v in properties.items()}

def to_pascal(description: str) -> str:
    return ''.join(description.translate(str.maketrans(string.punctuation, ' '*len(string.punctuation))).title().split(' '))

inspections: List[Inspection] = []
for key, value in INSPECTIONS_FILES.items():
    jar = 'bazel-idea-settings/external/idea-IU/' + key
    with zipfile.ZipFile(jar, 'r') as zipped:
        with zipped.open(value) as xml_file:
            idea_plugin = objectify.fromstring(xml_file.read())
            raw_inspections = map(
                RawInspection.from_xml,
                list(getattr(idea_plugin.extensions, 'localInspection', [])) + list(getattr(idea_plugin.extensions, 'globalInspection', [])))
            inspections.extend(Inspection(inspection, properties)
                               for inspection in raw_inspections)

# To minimise surface area, only look at a certain subset
inspections = [inspection
               for inspection in inspections
               if inspection.path == ('Java', 'Probable bugs')]

sorting_key = lambda i: i.path
inspections.sort(key=sorting_key)
grouped_inspections = {k: list(v) for k, v in itertools.groupby(inspections, sorting_key)}

env = jinja2.Environment(loader=jinja2.PackageLoader('inspection_generator'))

# TODO: make a 'InspectionPackage' class for 'path' - can give us the folder,
# package, build_rule, etc.
def main():
    for path, inspections in grouped_inspections.items():

        inspection_package = InspectionPackage(path)
        sub_package = inspection_package.sub_package
        sub_folder = inspection_package.sub_folder
        build_rule = inspection_package.build_rule
        class_name_prefix = inspection_package.class_name_prefix

        layout_folder = Path('src/main/kotlin/com/github/alexandrecarlton/idea/settings/layout/editor/inspections/') / sub_folder
        layout_folder.mkdir(parents=True, exist_ok=True)
        with (layout_folder / 'BUILD').open('w') as build_file:
            build_file.write(env.get_template('layout/BUILD.j2').render(build_rule=build_rule))

        # Generate *InspectionOptionsSettings objects
        for inspection in inspections:
            options_settings_filename = layout_folder / (inspection.class_name_prefix + 'InspectionOptionsSettings.kt')
            # We generate a basic 'object' for basic functionality - however, we
            # might have already generated a more sophisticated data class for it.
            if not options_settings_filename.exists():
                with options_settings_filename.open('w') as options_settings_file:
                    options_settings_file.write(env.get_template('layout/_InspectionOptionsSettings.kt.j2').render(
                        inspection=inspection))

        # Generate *InspectionsSettings
        main_settings_path = layout_folder / (class_name_prefix + 'InspectionsSettings.kt')
        with main_settings_path.open('w') as main_settings_file:
            main_settings_file.write(env.get_template('layout/_InspectionSettings.kt.j2').render(
                class_name_prefix=class_name_prefix,
                inspections=inspections,
                sub_package=inspection.sub_package))

        # Generate the appliers BUILD file
        applier_folder = Path('src/main/kotlin/com/github/alexandrecarlton/idea/settings/applier/impl/editor/inspections/') / sub_folder
        applier_folder.mkdir(parents=True, exist_ok=True)
        build_path = applier_folder / 'BUILD'
        if not build_path.exists():
            with build_path.open('w') as build_file:
                build_file.write(env.get_template('applier/BUILD.j2').render(build_rule=build_rule, sub_folder=sub_folder))

        # Generate *InspectionsSettingsApplier appliers
        main_settings_applier_path = applier_folder / (class_name_prefix + 'InspectionsSettingsApplier.kt')
        with main_settings_applier_path.open('w') as main_settings_applier_file:
            main_settings_applier_file.write(env.get_template('applier/_InspectionsSettingsApplier.kt.j2').render(
                class_name_prefix=class_name_prefix,
                inspections=inspections,
                sub_package=sub_package))

    all_inspections = [inspection
                       for inspections in grouped_inspections.values()
                       for inspection in inspections]

    # ToolsImplModule
    tools_impl_module_path = Path('src/main/kotlin/com/github/alexandrecarlton/idea/settings/dagger/project/ToolsImplModule.kt')
    with tools_impl_module_path.open('w') as tools_impl_module_file:
        tools_impl_module_file.write(env.get_template('ToolsImplModule.kt.j2').render(
            short_names=sorted([inspection.short_name
                                for inspection in all_inspections])))

    # InspectionSettingsApplierModule
    # TODO
    inspection_settings_applier_module_path = Path('src/main/kotlin/com/github/alexandrecarlton/idea/settings/dagger/project/InspectionSettingsApplierModule.kt')
    with inspection_settings_applier_module_path.open('w') as inspection_settings_applier_module_file:
        inspection_settings_applier_module_file.write(env.get_template('InspectionSettingsApplierModule.kt.j2').render(
            inspections=inspections))


    # NoOpInspectionOptionsSettingsApplierModule
    applier_folder = Path('src/main/kotlin/com/github/alexandrecarlton/idea/settings/applier/impl/editor/inspections')
    no_op_inspections = [inspection
                         for inspection in all_inspections
                         if not (applier_folder / inspection.sub_package / (inspection.class_name_prefix + 'InspectionOptionsSettingsApplier.kt')).exists()]
    no_op_inspection_options_settings_applier_module_path = Path('src/main/kotlin/com/github/alexandrecarlton/idea/settings/dagger/inspections/NoOpInspectionOptionsSettingsApplierModule.kt')
    with no_op_inspection_options_settings_applier_module_path.open('w') as no_op_inspection_options_settings_applier_module_file:
        no_op_inspection_options_settings_applier_module_file.write(env.get_template('NoOpInspectionOptionsSettingsApplierModule.kt.j2').render(
            inspections=no_op_inspections))


    # InspectionOptionsSettingsApplier
    inspection_options_settings_applier_path = Path('src/main/kotlin/com/github/alexandrecarlton/idea/settings/dagger/inspections/InspectionOptionsSettingsApplier.kt')
    with inspection_options_settings_applier_path.open('w') as inspection_options_settings_applier_file:
        inspection_options_settings_applier_file.write(env.get_template('InspectionOptionsSettingsApplier.kt.j2').render(
            inspections=[inspection
                         for inspection in all_inspections]))
