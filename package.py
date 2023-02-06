#!/bin/python3

import argparse
import os.path
import shutil
import tempfile
import xml.dom.minidom
from os import PathLike
from xml.etree import ElementTree


class ModulePackager:

    def __init__(self,
                 template_path: str | PathLike,
                 font_path: str | PathLike,
                 base_font_xml_path: str | PathLike,
                 font_name: str) -> None:
        self.__template_path = template_path
        self.__font_path = font_path
        self.__font_file_name = os.path.basename(font_path)
        self.__base_font_xml_path = base_font_xml_path
        self.__font_name = font_name
        pass

    def __parse_font_xml(self) -> str | bytes:
        tree = ElementTree.parse(self.__base_font_xml_path)
        root = tree.getroot()

        familyset = ElementTree.Element("familyset", {"version": "23"})

        # Write fonts config

        # 1, Empty fonts
        sans_serif_family = ElementTree.fromstring(
            """
    <family name="sans-serif">
        <font weight="100" style="normal">EmptyFont-Thin.ttf</font>
        <font weight="100" style="italic">EmptyFont-ThinItalic.ttf</font>
        <font weight="300" style="normal">EmptyFont-Light.ttf</font>
        <font weight="300" style="italic">EmptyFont-LightItalic.ttf</font>
        <font weight="400" style="normal">EmptyFont-Regular.ttf</font>
        <font weight="400" style="italic">EmptyFont-Italic.ttf</font>
        <font weight="500" style="normal">EmptyFont-Medium.ttf</font>
        <font weight="500" style="italic">EmptyFont-MediumItalic.ttf</font>
        <font weight="900" style="normal">EmptyFont-Black.ttf</font>
        <font weight="900" style="italic">EmptyFont-BlackItalic.ttf</font>
        <font weight="700" style="normal">EmptyFont-Bold.ttf</font>
        <font weight="700" style="italic">EmptyFont-BoldItalic.ttf</font>
    </family>
            """
        )
        familyset.append(sans_serif_family)

        custom_family = ElementTree.Element("family")
        # 2, Custom fonts
        for i in range(100, 1000, 100):
            font = ElementTree.Element("font", {"weight": f"{i}", "style": "normal"})
            font.text = self.__font_file_name
            custom_family.append(font)
        familyset.append(custom_family)

        family_with_lang_inserted = False
        for child in root:
            if child.tag == "family":
                if "name" in child.attrib and child.attrib["name"] == "sans-serif":
                    del child.attrib["name"]
                if "lang" in child.attrib and not family_with_lang_inserted:
                    family_with_lang = ElementTree.Element("family", {"lang": "zh-Hans"})
                    for i in range(100, 1000, 100):
                        font = ElementTree.Element("font", {"weight": f"{i}", "style": "normal"})
                        font.text = self.__font_file_name
                        family_with_lang.append(font)
                    familyset.append(family_with_lang)
                    family_with_lang_inserted = True
            familyset.append(child)
        node_content = ElementTree.tostring(familyset, "utf-8")
        temp_xml = xml.dom.minidom.parseString(node_content)
        pretty_xml = temp_xml.toprettyxml(indent="\t", encoding="utf-8")
        dom_string = os.linesep.join([s for s in str(pretty_xml, "utf-8").splitlines() if s.strip()])
        return dom_string

    def package_module(self, **kwargs: dict) -> str | PathLike:
        with tempfile.TemporaryDirectory() as temp:
            cwd = os.path.join(temp, os.path.basename(self.__template_path))
            shutil.copytree(self.__template_path, cwd)
            shutil.copy(self.__font_path, os.path.join(cwd, "system", "fonts"))
            module_prop_file = os.path.join(cwd, "module.prop")
            with open(module_prop_file, "w+") as module_prop:
                for k, v in kwargs.items():
                    module_prop.write(f"{k}={v}\n")
            font_xml_path = os.path.join(cwd, "system", "etc", "fonts.xml")
            with open(font_xml_path, "w+") as font_xml:
                font_xml.write(self.__parse_font_xml())

            dest_zip_name = os.path.join(tempfile.gettempdir(), self.__font_name)
            dest_zip_file = shutil.make_archive(
                base_name=dest_zip_name,
                format="zip",
                root_dir=cwd,
                verbose=True
            )
            return dest_zip_file


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--font-config",
        type=str,
        required=False,
        help="""Font config file "fonts.xml" path, 
        you can download from your android phone in path "/system/etc/fonts.xml" """
    )
    arg_parser.add_argument(
        "--font",
        type=str,
        required=True,
        help="Font file path"
    )
    arg_parser.add_argument(
        "--font-name",
        type=str,
        required=False,
        help="Human readable font name"
    )
    config = arg_parser.parse_args()

    cwd = os.path.dirname(__file__)

    font_xml_path = os.path.join(cwd, "template", "system", "etc", "fonts.xml")
    if config.font_config:
        font_xml_path = config.font_config

    if not os.path.exists(font_xml_path):
        print("Font config file not exists!")

    if not config.font or not os.path.exists(config.font):
        print("No font file set or font file not exists!")
        exit(-1)

    template_path = os.path.join(cwd, "template")

    font_name = config.font_name
    if not font_name:
        font_name = os.path.basename(config.font)
        font_name = os.path.splitext(font_name)[0]
    module_props = {
        "id": font_name,
        "name": font_name,
        "version": "1.0",
        "versionCode": "1",
        "author": os.getlogin(),
        "description": f"Replace default font with {font_name}"
    }

    module_packager = ModulePackager(template_path=template_path,
                                     font_path=config.font,
                                     base_font_xml_path=font_xml_path,
                                     font_name=font_name)
    zip_file = module_packager.package_module(**module_props)
    shutil.copy(zip_file, cwd)


if __name__ == '__main__':
    main()
