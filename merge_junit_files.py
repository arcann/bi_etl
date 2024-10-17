from pathlib import Path

from junitparser import JUnitXml


def merge_junit_files():
    root = Path(__file__).parent
    main_filename = 'junit.xml'
    main_path = root / main_filename
    if main_path.exists():
        main_xml = JUnitXml.fromfile(str(main_path))
    else:
        main_xml = JUnitXml()
    for xml_file in root.glob('*.xml'):
        if xml_file != main_path:
            xml = JUnitXml.fromfile(str(xml_file))
            for suite in xml:
                for case in suite:
                    case.classname = f"{xml_file.stem}/{case.classname}"
            main_xml += xml
            xml_file.unlink()

    main_xml.write(str(root / main_filename))


if __name__ == '__main__':
    merge_junit_files()
