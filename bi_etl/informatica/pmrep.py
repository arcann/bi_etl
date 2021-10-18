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

import bi_etl.bi_config_parser
from bi_etl.informatica.exceptions import NoObjects
from bi_etl.utility import dict_to_str, line_counter


class PMREP(object):
    SETTINGS_SECTION = 'INFORMATICA'

    def __init__(self, config=None):
        if config is None:
            self.config = bi_etl.bi_config_parser.BIConfigParser()
            self.config.read_config_ini()
            self.config.set_dated_log_file_name('pmrep', '.log')
            self.config.setup_logging()
        else:
            self.config = config
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.f_dev_null = open(os.devnull, 'w')
        self.control_file_name = "Control_import_No_folder_rep_change.xml"
        self.infa_home = os.environ['INFA_HOME']

    def setup_inf_path(self):
        user_dir = os.path.expanduser('~')
        os.environ['PATH'] = ':'.join([os.path.join(user_dir, 'bin'),
                                       self.informatica_bin_dir(),
                                       '/usr/bin',
                                       ]
                                      )
        os.environ['LD_LIBRARY_PATH'] = self.informatica_bin_dir()

    def informatica_bin_dir(self):
        return os.path.join(self.infa_home, 'server', 'bin')

    def informatica_pmrep(self):
        return os.path.join(self.informatica_bin_dir(), 'pmrep')

    def user_id(self):
        return self.config.get(self.SETTINGS_SECTION, 'USER_ID')

    def password(self):
        return self.config.get(self.SETTINGS_SECTION, 'PASSWORD')

    def set_password_in_env(self):
        os.environ['INFA_PM_PASSWORD'] = self.password()

    def repository(self):
        return self.config.get(self.SETTINGS_SECTION, 'REPOSITORY')

    def domain(self):
        return self.config.get(self.SETTINGS_SECTION, 'DOMAIN')

    def folder(self):
        return self.config.get(self.SETTINGS_SECTION, 'DEFAULTFOLDER')

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
            ]
            , stdout=subprocess.PIPE
        )
        count = 0
        found_invoked = False
        found_blank_line = False
        for line in iter(process.stdout.readline, ''):
            # End on line .ListObjects completed successfully.
            if line.startswith('.ListObjects'): break
            if found_blank_line:
                count += 1
                # if count >= 15: break
                parts = line.rstrip('\n').split(' ')
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
                                   'subtype':    subtype,
                                   'name':       name,
                                   'folderName': folder_name
                                  }
                    object_list.append(object_dict)
            if line.startswith('Invoked'): 
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
                                           'subtype':    subtype,
                                           'name':       name,
                                           'folder':     folder
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
        pmrep_cmd = []
        pmrep_cmd.append(self.informatica_pmrep())
        pmrep_cmd.append('objectexport')
        pmrep_cmd.append('-f')
        pmrep_cmd.append(objectDict['folder'])
        pmrep_cmd.append('-n')
        pmrep_cmd.append(objectDict['name'])
        pmrep_cmd.append('-o')
        pmrep_cmd.append(objectDict['type'])

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

    def getFolderName(self, objectDict):
        return objectDict['type'].capwords() + 's'

    def getFileName(self, objectDict):
        return objectDict['name'] + '.xml'

    def attributesString(self, element):
        s = element.tag
        # print 'attributesString ' + xml.tostring(element)
        if list(element.items()) != None:
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

                self.log.ingo("Exporting {}/{}".format(self.getFolderName(objectDict),
                                                       self.getFileName(objectDict)
                                                       )
                              )
                try:
                    messages = self.exportObject(objectDict, False, tempFilePath)
                    if messages != None and len(messages) > 0:
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
                if messages != None and len(messages) > 0:
                    messageList.append((self.getFileName(objectDict), messages))
            except NoObjects:
                pass
        return messageList

    def importXMLFile(self, path, control_file):
        # pmrep objectimport -c "${CONTROL_FILE}" -i "${FILE}" -p
        pmrep_cmd = []
        pmrep_cmd.append(self.informatica_pmrep())
        pmrep_cmd.append('objectimport')
        pmrep_cmd.append('-c')
        pmrep_cmd.append(control_file)
        pmrep_cmd.append('-i')
        pmrep_cmd.append(path)
        pmrep_cmd.append('-p')

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
                    ## Replace generic repository name with our specific one
                    line = re.sub(r'impcntl.dtd',
                                  os.path.join(self.informatica_bin_dir(), 'impcntl.dtd'),
                                  line)

                    tf.write(line)

    def importFileObj(self, fileObj):
        print("Importing {}".format(fileObj.name))
        tempDir = tempfile.mkdtemp()
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        messages = ""
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
        messages = ""
        try:
            with open(path, 'r') as sf:
                messages = self.importFileObj(sf)
        except Exception as e:
            messages = e
        return messages
