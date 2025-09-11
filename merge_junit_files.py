from pathlib import Path

from junitparser import JUnitXml

try:
    from junit2htmlreport.runner import run as junit2html_run
except (ImportError, ModuleNotFoundError):
    junit2html_run = None


def merge_junit_files():
    # TODO: Move existing junit files into subdir below

    root = Path(__file__).parent / 'junit'
    root.mkdir(exist_ok=True)
    for xml_file in root.glob('*.xml'):
        # if xml_file.name != 'junit-py312-sqlalchemy20-slack_sdk-cw.xml':
        #     continue
        print(f"Updating {xml_file}")
        xml_file_backup = xml_file.with_suffix('.xml-backup')
        if xml_file_backup.exists():
            xml = JUnitXml.fromfile(str(xml_file_backup))
        else:
            xml = JUnitXml.fromfile(str(xml_file))
            xml.write(str(xml_file_backup), pretty=True)
        for suite in xml:
            for case in suite:
                classname = case.classname
                class_parts = classname.split('.')
                classname = class_parts[-1]
                case.classname = f"{xml_file.stem}.{classname}"
        xml.write(xml_file, pretty=True)
        html_file = xml_file.with_suffix('.html')

        if junit2html_run is not None:
            if not html_file.exists() or html_file.stat().st_mtime < xml_file.stat().st_mtime:
                print(f"Generating HTML report for {xml_file}")
                junit2html_run([str(xml_file), str(html_file)])


if __name__ == '__main__':
    merge_junit_files()
