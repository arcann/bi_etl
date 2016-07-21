'''
Created on May 4, 2015

@author: woodd
'''

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
    
    def __init__(self, config=None):
        if config is None:
            self.config = bi_etl.bi_config_parser.BIConfigParser()
            self.config.read_config_ini()
            self.config.set_dated_log_file_name('pmrep','.log')
            self.config.setup_logging()
        else:
            self.config = config
        self.log = logging.getLogger('Informatica')
        self.f_dev_null = open(os.devnull, 'w')
        self.control_file_name = "Control_import_No_folder_rep_change.xml"
    
    def setup_inf_path(self):
        userDir = os.path.expanduser('~')
        os.environ['PATH']=os.path.join(userDir,'bin') + ':' + os.path.join(self.infa_home(),'server','bin') + ':/usr/bin'
        os.environ['LD_LIBRARY_PATH']=os.path.join(os.environ['INFA_HOME'],'server','bin')

    def informatica_bin_dir(self):
        return os.path.join(os.environ['INFA_HOME'],'server','bin')

    def informatica_pmrep(self):
        return os.path.join(self.informatica_bin_dir(),'pmrep')

    def user_id(self):
        return self.config.get('INFORMATICA','USER_ID')

    def password(self):
        return self.config.get('INFORMATICA','PASSWORD')

    def set_password_in_env(self):
        os.environ['INFA_PM_PASSWORD'] = self.password()

    def repository(self):
        return self.config.get('INFORMATICA','REPOSITORY')

    def domain(self):
        return self.config.get('INFORMATICA','DOMAIN')

    def folder(self):
        if self._folder is None:
            self._folder = self.config.get('INFORMATICA','DEFAULTFOLDER')
        return self._folder 
    
    def connect(self):
        pmrep_cmd= []
        pmrep_cmd.append(self.informatica_pmrep())
        pmrep_cmd.append('connect')
        pmrep_cmd.append('-r')
        pmrep_cmd.append(self.repository())
        pmrep_cmd.append('-d')
        pmrep_cmd.append(self.domain())
        pmrep_cmd.append('-n')
        pmrep_cmd.append(self.user_id())
        pmrep_cmd.append('-X')
        self.set_password_in_env()
        self.setup_inf_path()
        pmrep_cmd.append('INFA_PM_PASSWORD')  # Informatica will read environment variable
    
    
        self.log.info("pmrep Connecting to Informatica")
        try:            
            if self.log.getEffectiveLevel() >= logging.DEBUG:
                FOUT = sys.stdout
            else:
                FOUT = self.f_dev_null
            subprocess.check_call(pmrep_cmd, stdout=FOUT)
        except subprocess.CalledProcessError as e:
            self.log.error( "Error code " + str(e.returncode ) )
            self.log.error( "From " + ' '.join(e.cmd) )
            self.log.error( e.output )
            raise e
    
    def cleanup(self):
        pmrep_cmd= []
        pmrep_cmd.append(self.informatica_pmrep())
        pmrep_cmd.append('cleanup')
        try:
            messages = subprocess.check_output(pmrep_cmd, stderr=subprocess.STDOUT)
            self.log.debug(messages)
        except subprocess.CalledProcessError as e:
            self.log.error( "Error code " + str(e.returncode ) )
            self.log.error( "From " + ' '.join(e.cmd) )
            self.log.error( e.output )
        finally:
            self.f_dev_null.close()

    def getObjects(self, objectType, folderName):
        #print "pmrep ListObjects -o " + objectType + ' -f ' + folderName
        objectList = list()
        proc = subprocess.Popen(
                                [
                                    self.informatica_pmrep(),
                                    'ListObjects',
                                    '-o',objectType,
                                    '-f',folderName
                                 ]
                                ,stdout=subprocess.PIPE
                                )
        count = 0
        found_invoked = False
        found_blank_line = False
        for line in iter(proc.stdout.readline,''):
            ## End on line .ListObjects completed successfully.
            if line.startswith('.ListObjects'): break
            if found_blank_line:
                count += 1
                #if count >= 15: break
                parts = line.rstrip('\n').split(' ')
                subtype = parts[0]
                if len(parts) == 2:
                    reusable = 'reusable'
                    name = parts[1]
                else:
                    reusable = parts[1]
                    name = parts[2]
                #print "parts = " + pformat(parts)
                if reusable == 'reusable':
                    #print "subtype = " + subtype + " name = " + name
                    objectDict = {'objectType':objectType,
                                  'subtype':subtype,
                                  'name':name,
                                  'folderName':folderName
                                  }
                    objectList.append(objectDict)
            if line.startswith('Invoked'): found_invoked = True
            if found_invoked and line == '\n': found_blank_line = True
        return objectList
    
    def getObjectsFromQuery(self, queryName):
        #pmrep  executequery -q $INFA_QUERY_NAME -t shared -u ${OUTPUT_PATH}\${INFA_QUERY_NAME}_results.txt
        global settings
        tempDir = tempfile.mkdtemp()
        tempFile = os.path.join(tempDir,'query.out')
        objList = list()
        try:
            if self.log.getEffectiveLevel() >= logging.DEBUG:
                FOUT = sys.stdout
            else:
                FOUT = self.f_dev_null
            subprocess.check_call([settings.informatica_pmrep(),'executequery','-q',queryName,'-u',tempFile],stdout=FOUT)
            if os.path.exists(tempFile):
                count = 0
                with open(tempFile, 'r') as f:
                    for line in f:
                        count += 1
                        #if count >= 15: break
                        parts = line.rstrip('\n').split(',')
                        folder = parts[1]
                        name = parts[2]
                        objectType = parts[3]
                        subtype = parts[4]
                        #version = parts[5]
                        if len(parts) == 7:
                            reusable = parts[6]
                        else:
                            reusable = 'reusable'
                        if reusable == 'reusable':
                            #print "parts {} = 0-excluded {}" .format(len(parts),[parts[i] for i in range(1,7)])
                            objectDict = {'objectType':objectType,
                                          'subtype':subtype,
                                          'name':name,
                                          'folder':folder
                                         }
                            objList.append(objectDict)
            else: #query.out not created
                pass
        except subprocess.CalledProcessError:
            raise RuntimeError("Error executing query {name}".format(name=queryName))
        finally:
            #Cleanup temp
            shutil.rmtree(tempDir)
        return objList
    
    def deleteObject(self, objectDict):
        #pmrep  DeleteObject -o <object_type> -f <folder_name> -n <object_name>
        pmrep_cmd= []
        pmrep_cmd.append(self.informatica_pmrep())
        pmrep_cmd.append('DeleteObject')
        pmrep_cmd.append('-f')
        pmrep_cmd.append(objectDict['folder'])
        pmrep_cmd.append('-o')
        pmrep_cmd.append(objectDict['type'])
        pmrep_cmd.append('-n')
        pmrep_cmd.append(objectDict['name'])
    
        ## Include subtype if required
        if objectDict['type'].lower() in ('task','transformation'):
            pmrep_cmd.append('-t')
            pmrep_cmd.append(objectDict['subtype'])
    
        try:
            if self.log.getEffectiveLevel() >= logging.DEBUG:
                FOUT = sys.stdout
            else:
                FOUT = self.f_dev_null
            subprocess.check_call(pmrep_cmd, stdout=FOUT)
        except subprocess.CalledProcessError as e:
            self.log.error( "Error code " + str(e.returncode ) )
            self.log.error( "From " + ' '.join(e.cmd) )
            self.log.error( e.output )
    
    def exportObject(self, objectDict, dependents, outputPath):
        #pmrep  objectexport -f $FOLDER -n "$NAME" -o "$TYPE" -t "$SUBTYPE" $DEPENDENTS_OPTIONS -u "${TYPE}s/${NAME}.xml"
        pmrep_cmd= []
        pmrep_cmd.append(self.informatica_pmrep())
        pmrep_cmd.append('objectexport')
        pmrep_cmd.append('-f')
        pmrep_cmd.append(objectDict['folder'])
        pmrep_cmd.append('-n')
        pmrep_cmd.append(objectDict['name'])
        pmrep_cmd.append('-o')
        pmrep_cmd.append(objectDict['type'])
    
        ## Include subtype if required
        if objectDict['type'].lower() in ('task','transformation'):
            pmrep_cmd.append('-t')
            pmrep_cmd.append(objectDict['subtype'])
    
        ## include all dependents or only non-reusable dependents
        if dependents:
            pmrep_cmd.append('-m') #[-m (export pk-fk dependency)]
            pmrep_cmd.append('-s') #[-s (export objects referred by shortcut)]
            pmrep_cmd.append('-b') #[-b (export non-reusable dependents)]
            pmrep_cmd.append('-r') #[-r (export reusable dependents)]
        else:
            pmrep_cmd.append('-b') #[-b (export non-reusable dependents)]
    
        pmrep_cmd.append('-u')
        pmrep_cmd.append(outputPath)
    
        try:
            messages = subprocess.check_output(pmrep_cmd, stderr=subprocess.STDOUT)
            countXMLlines = line_counter.bufcount(outputPath)
            errors = re.findall('^.*<Warning>.*$|^.*<Error>.*$', messages, re.MULTILINE)
            if len(errors) > 0:
                self.log.error(errors)
                return '\n'.join(errors)
            elif countXMLlines <= 3:
                print("WARNING: No valid objects exported")
                os.remove(outputPath)
                raise NoObjects()
        except subprocess.CalledProcessError as e:
            messages = e.output
            print("Error code " + str(e.returncode ))
            print("From " + ' '.join(e.cmd))
            print(messages)
            return messages
    
    def validateObject(self, objectDict):
        #pmrep validate {{-n <object_name>  -o <object_type (mapplet, mapping, session, worklet, workflow)>
        #              [-v <version_number>] [-f <folder_name>]} |  -i <persistent_input_file>}
        #              [-s (save upon valid) [-k (check in upon valid) [-m <check_in_comments>]]]
        #              [-p <output_option_types (valid, saved, skipped, save_failed, invalid_before, invalid_after, or all)>
        #              [-u <persistent_output_file_name>]  [-a (append)]
        #              [-c <column_separator>] [-r <end-of-record_separator>] [-l <end-of-listing_indicator>] [-b (verbose)]
        pmrep_cmd= []
        pmrep_cmd.append(self.informatica_pmrep())
        pmrep_cmd.append('validate')
        pmrep_cmd.append('-f')
        pmrep_cmd.append(objectDict['folder'])
        pmrep_cmd.append('-n')
        pmrep_cmd.append(objectDict['name'])
        pmrep_cmd.append('-o')
        pmrep_cmd.append(objectDict['type'])
    
        pmrep_cmd.append('-s') #(save upon valid)
    
        pmrep_cmd.append('-b') #(verbose)
    
        try:
            messages = subprocess.check_output(pmrep_cmd, stderr=subprocess.STDOUT)
            errors = re.findall('^.*<Warning>.*$|^.*<Error>.*$', messages, re.MULTILINE)
            if len(errors) > 0:
                print(errors)
                return '\n'.join(errors)
        except subprocess.CalledProcessError as e:
            messages = e.output
            print("Error code " + str(e.returncode ))
            print("From " + ' '.join(e.cmd))
            print(messages)
            return messages
    
    ## Export only mappings with reusable dependents included
    def exportObjectAutoDependents(self, objectDict, outputPath ):
        if objectDict['type'].lower() == 'mapping':
            dependents = True
        else:
            dependents = False
        return self.exportObject(objectDict,dependents)
    
    def getFolderName(self, objectDict):
        return objectDict['type'].capwords() + 's'
    
    def getFileName(self, objectDict):
        return objectDict['name']+'.xml'
    
    def attributesString(self, element):
        s = element.tag
        #print 'attributesString ' + xml.tostring(element)
        if list(element.items()) != None:
            for attr in sorted(element.items()):
                s += ' ' + ' '.join(attr)
        #print 'end attributesString = ' + s
        return s
    
    def exportObjectList(self, objectList):
        messageList = list()
        tempDir = tempfile.mkdtemp()
        try:
            newFilesDict = dict()
    
            self.log.info("{cnt} objects to export".format(cnt=len(objectList)))
    
            for objectDict in objectList:
                self.log.debug(dict_to_str(objectDict))
    
                fullTempDir = os.path.join(tempDir,self.getFolderName(objectDict))
                os.makedirs(fullTempDir)
                tempFilePath = os.path.join(fullTempDir, self.getFileName(objectDict))
    
                self.log.ingo("Exporting {}/{}".format(self.getFolderName(objectDict),
                                                       self.getFileName(objectDict)
                                                       )
                              )
                try:
                    messages = self.exportObject(objectDict,False,tempFilePath)
                    if messages != None and len(messages) > 0:
                        messageList.append( (self.getFileName(objectDict), messages) )
    
                    targetDir = os.path.join(os.getcwd(), self.getFolderName(objectDict))
                    os.makedirs(targetDir)
                    targetFilePath = os.path.join(targetDir,self.getFileName(objectDict))
    
                    newFilesDict[targetFilePath] = 1
    
                    self.log.debug("Copying to {}".format(targetFilePath))
                except NoObjects:
                    pass
        finally:
            #Cleanup temp
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
                    messageList.append( (self.getFileName(objectDict), messages) )
            except NoObjects:
                pass
        return messageList
    
    def importXMLFile(self, path, control_file):
        #pmrep objectimport -c "${CONTROL_FILE}" -i "${FILE}" -p
        pmrep_cmd= []
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
                return '\n'.join(errors)
        except subprocess.CalledProcessError as e:
            messages = e.output
            if e.returncode == 1 and messages.find('No objects to import into repository') != -1:
                messages = "WARNING: No objects to import into repository"
                print(messages)
                return messages
            else:
                print("pmrep Error code " + str(e.returncode ))
                print("From " + ' '.join(e.cmd))
                print(messages)
                return messages
    
    def specifizeControlFile(self, controlFile, workingControlFile):
        with open(controlFile, 'r') as sf:
            with open(workingControlFile, 'w') as tf:
                for line in sf:
                    ## Replace generic repository name with our specific one
                    line = re.sub(r'impcntl.dtd',
                                  os.path.join(settings.informatica_bin_dir(),'impcntl.dtd'),
                                  line)
    
                    tf.write(line)
    
    def importFileObj(self, fileObj):
        print("Importing {}".format(fileObj.name))
        tempDir = tempfile.mkdtemp()
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        messages = ""
        try:
            (_, fileName) = os.path.split(fileObj.name)
            workingFile = os.path.join(tempDir,fileName)
            controlFile = os.path.join(scriptDir,self.control_file_name)
            workingControlFile = os.path.join(tempDir,self.control_file_name)
            self.specifizeControlFile(controlFile,workingControlFile)
            messages = self.importXMLFile(workingFile,workingControlFile)
        except Exception as e:
            messages = e
        finally:
            #Cleanup temp
            shutil.rmtree(tempDir)
        return messages
    
    def importFile(self, folderName,fileName):
        path = os.path.join(folderName,fileName)
        messages = ""
        try:
            with open(path, 'r') as sf:
                messages = self.importFileObj(sf)
        except Exception as e:
            messages = e
        return messages