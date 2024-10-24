from pathlib import Path

from junitparser import JUnitXml
from junit2htmlreport.runner import run as junit2html_run

def merge_junit_files():
    root = Path(__file__).parent
    main_filename = 'junit.xml'
    main_path = root / main_filename
    # if main_path.exists():
    #     main_xml = JUnitXml.fromfile(str(main_path))
    # else:
    #     main_xml = JUnitXml()
    for xml_file in root.glob('*.xml'):
        if xml_file != main_path:
            print(f"Updating {xml_file}")
            xml = JUnitXml.fromfile(str(xml_file))
            needs_save = False
            names = dict()
            for suite in xml:
                # if suite in main_xml:
                #     print("Starting with a clean JUnitXml")
                #     main_xml = JUnitXml()
                for case in suite:
                    classname = case.classname
                    if '/' in classname:
                        _, classname = classname.split('/')
                    class_parts = classname.split('.')
                    classname = class_parts[-1]
                    if classname in names:
                        classname = '.'.join(class_parts)
                    names[classname] = class_parts
                    needs_save = True
                    case.classname = f"{xml_file.stem}.{classname}"
            # main_xml += xml
            # xml_file.unlink()
            if needs_save:
                xml.write()
            html_file = xml_file.with_suffix('.html')

            # if not html_file.exists():
            if True:
                # junit2html_run([str(xml_file), str(html_file), '--summary-matrix', '--max-failures', '1'])
                junit2html_run([str(xml_file), str(html_file)])

    # main_xml.write(str(root / main_filename))


if __name__ == '__main__':
    merge_junit_files()
