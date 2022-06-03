"""
Created on May 4, 2015

@author: Derek Wood
"""

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Union

from bi_etl.informatica.exceptions import NoObjects
from bi_etl.informatica.pm_config import PMCMDConfig
from bi_etl.utility import dict_to_str, line_counter


class PMREP(object):
    SETTINGS_SECTION = 'INFORMATICA'

    def __init__(self, config: PMCMDConfig):
        self.config = config
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.f_dev_null = open(os.devnull, 'w')
        self.control_file_name = "Control_import_No_folder_rep_change.xml"
        self._folder = None

    def setup_inf_path(self):
        user_dir = os.path.expanduser('~')
        os.environ['PATH'] = ':'.join([os.path.join(user_dir, 'bin'),
                                       self.informatica_bin_dir(),
                                       '/usr/bin',
                                       ]
                                      )
        os.environ['LD_LIBRARY_PATH'] = self.informatica_bin_dir()

    def infa_home(self) -> Union[str, None]:
        if 'INFA_HOME' in os.environ:
            return os.environ['INFA_HOME']
        else:
            return self.config.INFA_HOME

    def informatica_bin_dir(self):
        return os.path.join(self.infa_home(), 'server', 'bin')

    def informatica_pmcmd(self):
        return os.path.join(self.informatica_bin_dir(), 'pmcmd')

    def usersecuritydomain(self):
        return self.config.USER_SECURITY_DOMAIN

    def user_id(self):
        return self.config.user_id

    def password(self):
        return self.config.get_password()

    def set_password_in_env(self):
        os.environ['INFA_PM_PASSWORD'] = self.password()

    def repository(self):
        return self.config.REPOSITORY

    def service(self):
        return self.config.SERVICE

    def domain(self):
        return self.config.DOMAIN

    def folder(self):
        if self._folder is None:
            self._folder = self.config.DEFAULT_FOLDER
        return self._folder

    def informatica_pmrep(self):
        return os.path.join(self.informatica_bin_dir(), 'pmrep')

    def connect(self):
        pmrep_cmd = [self.informatica_pmrep(),
                     'connect',
                     '-r', self.repository(),
                     '-d', self.domain(),
                     '-n', self.user_id(),
                     '-X', 'INFA_PM_PASSWORD'
                     ]
        self.set_password_in_env()
        self.setup_inf_path()

        self.log.info("pmrep Connecting to Informatica")
        try:
            if self.log.getEffectiveLevel() >= logging.DEBUG:
                file_out = sys.stdout
            else:
                file_out = self.f_dev_null
            subprocess.check_call(pmrep_cmd, stdout=file_out)
        except subprocess.CalledProcessError as e:
            self.log.error("Error code " + str(e.returncode))
            self.log.error("From " + ' '.join(e.cmd))
            self.log.error(e.output)
            raise e

    def cleanup(self):
        pmrep_cmd = [self.informatica_pmrep(), 'cleanup']
        try:
            messages = subprocess.check_output(pmrep_cmd, stderr=subprocess.STDOUT)
            self.log.debug(messages)
        except subprocess.CalledProcessError as e:
            self.log.error("Error code " + str(e.returncode))
            self.log.error("From " + ' '.join(e.cmd))
            self.log.error(e.output)
        finally:
            self.f_dev_null.close()

    def get_objects(self, object_type, folder_name):
        # print "pmrep ListObjects -o " + objectType + ' -f ' + folderName
        object_list = list()
        process = subprocess.Popen(
            [
                self.informatica_pmrep(),
                'ListObjects',
                '-o', object_type,
                '-f', folder_name
            ],
            stdout=subprocess.PIPE
        )
        count = 0
        found_invoked = False
        found_blank_line = False
        for line in iter(process.stdout.readline, ''):
            # End on line .ListObjects completed successfully.
            if line.startswith(b'.ListObjects'):
                break
            if found_blank_line:
                count += 1
                # if count >= 15: break
                parts = line.rstrip(b'\n').split(b' ')
                subtype = parts[0]
                if len(parts) == 2:
                    reusable = 'reusable'
                    name = parts[1]
                else:
                    reusable = parts[1]
                    name = parts[2]
                # print "parts = " + pformat(parts)
                if reusable == 'reusable':
                    # print "subtype = " + subtype + " name = " + name
                    object_dict = {'objectType': object_type,
                                   'subtype': subtype,
                                   'name': name,
                                   'folderName': folder_name
                                   }
                    object_list.append(object_dict)
            if line.startswith(b'Invoked'):
                found_invoked = True
            if found_invoked and line == '\n':
                found_blank_line = True
        return object_list

    def get_objects_from_query(self, query_name):
        # pmrep  executequery -q $INFA_QUERY_NAME -t shared -u ${OUTPUT_PATH}\${INFA_QUERY_NAME}_results.txt
        tempDir = tempfile.mkdtemp()
        temp_file = os.path.join(tempDir, 'query.out')
        obj_list = list()
        try:
            if self.log.getEffectiveLevel() >= logging.DEBUG:
                file_out = sys.stdout
            else:
                file_out = self.f_dev_null
            subprocess.check_call([self.informatica_pmrep(),
                                   'executequery',
                                   '-q', query_name,
                                   '-u', temp_file
                                   ],
                                  stdout=file_out)
            if os.path.exists(temp_file):
                count = 0
                with open(temp_file, 'r') as f:
                    for line in f:
                        count += 1
                        # if count >= 15: break
                        parts = line.rstrip('\n').split(',')
                        folder = parts[1]
                        name = parts[2]
                        object_type = parts[3]
                        subtype = parts[4]
                        # version = parts[5]
                        if len(parts) == 7:
                            reusable = parts[6]
                        else:
                            reusable = 'reusable'
                        if reusable == 'reusable':
                            # print("parts {} = 0-excluded {}" .format(len(parts),[parts[i] for i in range(1,7)]))
                            object_dict = {'objectType': object_type,
                                           'subtype': subtype,
                                           'name': name,
                                           'folder': folder
                                           }
                            obj_list.append(object_dict)
            else:  # query.out not created
                pass
        except subprocess.CalledProcessError:
            raise RuntimeError("Error executing query {name}".format(name=query_name))
        finally:
            # Cleanup temp
            shutil.rmtree(tempDir)
        return obj_list

    def deleteObject(self, objectDict):
        # pmrep  DeleteObject -o <object_type> -f <folder_name> -n <object_name>
        pmrep_cmd = [self.informatica_pmrep(),
                     'DeleteObject',
                     '-f', objectDict['folder'],
                     '-o', objectDict['type'],
                     '-n', objectDict['name']
                     ]

        # Include subtype if required
        if objectDict['type'].lower() in ('task', 'transformation'):
            pmrep_cmd.append('-t')
            pmrep_cmd.append(objectDict['subtype'])

        try:
            if self.log.getEffectiveLevel() >= logging.DEBUG:
                file_out = sys.stdout
            else:
                file_out = self.f_dev_null
            subprocess.check_call(pmrep_cmd, stdout=file_out)
        except subprocess.CalledProcessError as e:
            self.log.error("Error code " + str(e.returncode))
            self.log.error("From " + ' '.join(e.cmd))
            self.log.error(e.output)

    def exportObject(self, objectDict, dependents, outputPath):
        # pmrep  objectexport -f $FOLDER -n "$NAME" -o "$TYPE" -t "$SUBTYPE" $DEPENDENTS_OPTIONS -u "${TYPE}s/${NAME}.xml"
        pmrep_cmd = [
            self.informatica_pmrep(),
            'objectexport',
            '-f', objectDict['folder'],
            '-n', objectDict['name'],
            '-o', objectDict['type']
        ]

        # Include subtype if required
        if objectDict['type'].lower() in ('task', 'transformation'):
            pmrep_cmd.append('-t')
            pmrep_cmd.append(objectDict['subtype'])

        # include all dependents or only non-reusable dependents
        if dependents:
            pmrep_cmd.append('-m')  # [-m (export pk-fk dependency)]
            pmrep_cmd.append('-s')  # [-s (export objects referred by shortcut)]
            pmrep_cmd.append('-b')  # [-b (export non-reusable dependents)]
            pmrep_cmd.append('-r')  # [-r (export reusable dependents)]
        else:
            pmrep_cmd.append('-b')  # [-b (export non-reusable dependents)]

        pmrep_cmd.append('-u')
        pmrep_cmd.append(outputPath)

        try:
            messages = subprocess.check_output(pmrep_cmd, stderr=subprocess.STDOUT)
            count_xml_lines = line_counter.bufcount(outputPath)
            errors = re.findall('^.*<Warning>.*$|^.*<Error>.*$', messages, re.MULTILINE)
            if len(errors) > 0:
                self.log.error(errors)
                # noinspection PyTypeChecker
                return '\n'.join(errors)
            elif count_xml_lines <= 3:
                print("WARNING: No valid objects exported")
                os.remove(outputPath)
                raise NoObjects()
        except subprocess.CalledProcessError as e:
            messages = e.output
            print("Error code " + str(e.returncode))
            print("From " + ' '.join(e.cmd))
            print(messages)
            return messages

    def validateObject(self, objectDict):
        #
        # pmrep validate {{-n <object_name>  -o <object_type (mapplet, mapping, session, worklet, workflow)>
        #              [-v <version_number>] [-f <folder_name>]} |  -i <persistent_input_file>}
        #              [-s (save upon valid) [-k (check in upon valid) [-m <check_in_comments>]]]
        #              [-p <output_option_types (valid, saved, skipped, save_failed, invalid_before, invalid_after, or all)>
        #              [-u <persistent_output_file_name>]  [-a (append)]
        #              [-c <column_separator>] [-r <end-of-record_separator>] [-l <end-of-listing_indicator>] [-b (verbose)]
        #
        pmrep_cmd = [self.informatica_pmrep(),
                     'validate',
                     '-f', objectDict['folder'],
                     '-n', objectDict['name'],
                     '-o', objectDict['type'],
                     '-s',
                     '-b'
                     ]

        try:
            messages = subprocess.check_output(pmrep_cmd, stderr=subprocess.STDOUT)
            errors = re.findall('^.*<Warning>.*$|^.*<Error>.*$', messages, re.MULTILINE)
            if len(errors) > 0:
                print(errors)
                # noinspection PyTypeChecker
                return '\n'.join(errors)
        except subprocess.CalledProcessError as e:
            messages = e.output
            print("Error code " + str(e.returncode))
            print("From " + ' '.join(e.cmd))
            print(messages)
            return messages

    # Export only mappings with reusable dependents included
    def exportObjectAutoDependents(self, objectDict, outputPath):
        if objectDict['type'].lower() == 'mapping':
            dependents = True
        else:
            dependents = False
        return self.exportObject(objectDict, dependents, outputPath)

    @staticmethod
    def getFolderName(objectDict):
        return objectDict['type'].capwords() + 's'

    @staticmethod
    def getFileName(objectDict):
        return objectDict['name'] + '.xml'

    @staticmethod
    def attributesString(element):
        s = element.tag
        # print 'attributesString ' + xml.tostring(element)
        if list(element.items()) is not None:
            for attr in sorted(element.items()):
                s += ' ' + ' '.join(attr)
        # print 'end attributesString = ' + s
        return s

    def exportObjectList(self, objectList):
        messageList = list()
        tempDir = tempfile.mkdtemp()
        try:
            newFilesDict = dict()

            self.log.info("{cnt} objects to export".format(cnt=len(objectList)))

            for objectDict in objectList:
                self.log.debug(dict_to_str(objectDict))

                fullTempDir = os.path.join(tempDir, self.getFolderName(objectDict))
                os.makedirs(fullTempDir)
                tempFilePath = os.path.join(fullTempDir, self.getFileName(objectDict))

                self.log.info("Exporting {}/{}".format(self.getFolderName(objectDict),
                                                       self.getFileName(objectDict)
                                                       )
                              )
                try:
                    messages = self.exportObject(objectDict, False, tempFilePath)
                    if messages is not None and len(messages) > 0:
                        messageList.append((self.getFileName(objectDict), messages))

                    targetDir = os.path.join(os.getcwd(), self.getFolderName(objectDict))
                    os.makedirs(targetDir)
                    targetFilePath = os.path.join(targetDir, self.getFileName(objectDict))

                    newFilesDict[targetFilePath] = 1

                    self.log.debug("Copying to {}".format(targetFilePath))
                except NoObjects:
                    pass
        finally:
            # Cleanup temp
            shutil.rmtree(tempDir)
        return messageList

    def validateObjectList(self, objectList):
        messageList = list()

        self.log.info("{cnt} objects to validate".format(cnt=len(objectList)))

        for objectDict in objectList:
            self.log.debug(dict_to_str(objectDict))

            self.log.info("Validating {}/{}".format(self.getFolderName(objectDict),
                                                    self.getFileName(objectDict)
                                                    )
                          )
            try:
                messages = self.validateObject(objectDict)
                if messages is not None and len(messages) > 0:
                    messageList.append((self.getFileName(objectDict), messages))
            except NoObjects:
                pass
        return messageList

    def importXMLFile(self, path, control_file):
        # pmrep objectimport -c "${CONTROL_FILE}" -i "${FILE}" -p
        pmrep_cmd = [
            self.informatica_pmrep(),
            'objectimport',
            '-c', control_file,
            '-i', path,
            '-p',
        ]

        try:
            messages = subprocess.check_output(pmrep_cmd, stderr=subprocess.STDOUT)
            errors = re.findall('^.*<Warning>.*$|^.*<Error>.*$', messages, re.MULTILINE)
            if len(errors) > 0:
                print(errors)
                # noinspection PyTypeChecker
                return '\n'.join(errors)
        except subprocess.CalledProcessError as e:
            messages = e.output
            if e.returncode == 1 and messages.find('No objects to import into repository') != -1:
                messages = "WARNING: No objects to import into repository"
                print(messages)
                return messages
            else:
                print("pmrep Error code " + str(e.returncode))
                print("From " + ' '.join(e.cmd))
                print(messages)
                return messages

    def specifizeControlFile(self, controlFile, workingControlFile):
        with open(controlFile, 'r') as sf:
            with open(workingControlFile, 'w') as tf:
                for line in sf:
                    # Replace generic repository name with our specific one
                    line = re.sub(r'impcntl.dtd',
                                  os.path.join(self.informatica_bin_dir(), 'impcntl.dtd'),
                                  line)

                    tf.write(line)

    def importFileObj(self, fileObj):
        print("Importing {}".format(fileObj.name))
        tempDir = tempfile.mkdtemp()
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        try:
            (_, fileName) = os.path.split(fileObj.name)
            workingFile = os.path.join(tempDir, fileName)
            controlFile = os.path.join(scriptDir, self.control_file_name)
            workingControlFile = os.path.join(tempDir, self.control_file_name)
            self.specifizeControlFile(controlFile, workingControlFile)
            messages = self.importXMLFile(workingFile, workingControlFile)
        except Exception as e:
            messages = e
        finally:
            # Cleanup temp
            shutil.rmtree(tempDir)
        return messages

    def importFile(self, folderName, fileName):
        path = os.path.join(folderName, fileName)
        try:
            with open(path, 'r') as sf:
                messages = self.importFileObj(sf)
        except Exception as e:
            messages = e
        return messages
