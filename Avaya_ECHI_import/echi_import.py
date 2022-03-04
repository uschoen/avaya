#!/usr/bin/python

#    Copyright 2021 by Ullrich Schoen
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import logging.config
import os
import json
import sys
import hashlib
import shutil
import zipfile
import datetime


#    constants
__version__='1.1'
__author__ = 'ullrich schoen'

#    PATH: the absolute path of the script
PATH='' if not os.path.dirname(sys.argv[0]) else '%s/'%(os.path.dirname(sys.argv[0]))

#    Script absolut root path
ROOTPATH=("%s/%s"%(os.getcwd(),os.path.dirname(sys.argv[0])))

#
CONFIG_FILE="%s%s"%(PATH,"etc/config.json")

#    Logging
LOG=logging.getLogger(__name__)
LOG.info("start up echi import , version %s, path:%s , rootPath: %s , config:%s"%(__version__,PATH,ROOTPATH,CONFIG_FILE))


def main():       
    try:
        #    Load configuration file
        cfgFile=loadJSON(CONFIG_FILE)
    
        #    Logging
        logging.config.dictConfig(cfgFile["logging"])  
        
        
        #    loading Database Class
        if cfgFile['db']['databaseType']:
            from mysql_db import mysql_db as databaseOBJ
        else:
            raise defaultEXC("unknown database Typ %s"%(cfgFile['db']['databaseType']))
        '''
            load cms ech converter
        
            echiCFG=config
        '''
        echiFormatFile="%sechi_format/%s"%(PATH,cfgFile["cms"]["version"])
        LOG.info("loaad echi file %s"%(echiFormatFile))
        echiCFG=loadJSON(echiFormatFile)
        '''
            archive old echi files
        '''
        (yearA,monthA,dayA)=cfgFile['data']['lastarchive'].split(",")
        
        lastArchive=datetime.datetime.now()-datetime.datetime(int(yearA),int(monthA),int(dayA))
        
        if int(lastArchive.days)>=int(cfgFile['data']['archiveInterval']):
            sourcePath="%s"%(cfgFile['data']['archiveFilePath'])
            zipPath='%szip\echi_%s_%s_%s.zip'%(sourcePath,yearA,monthA,dayA)
            
            #    zip old echi files in archive    
            zipFiles(sourcePath, zipPath)
            
            #    delte old echi files in archive
            delteFiles(sourcePath)
            
            #     check to delete old acrive zip files
            checkOldArchiveFiles("%s\zip"%(sourcePath),cfgFile['data']['holdArchiveFiles'])
            
            cfgFile['data']['lastarchive']=datetime.datetime.now().strftime(format = "%Y,%m,%d")    
            writeJSON(CONFIG_FILE, cfgFile)
              
        '''
            search ech data file
        '''
        echiDataFiles="%s"%(cfgFile['data']['sourceFilePath'])
        LOG.info("search in %s for new echi files"%(echiDataFiles))
        echiFiles = os.listdir(echiDataFiles)
        LOG.info("found %s files"%(len(echiFiles)))
        
        #    found files in dir
        if (len(echiFiles)>0):
            
            #    create db connection
            database=databaseOBJ(cfgFile['db']['server'])
            
            
            # check if tabel exists
            if not (database.checkTableExists(cfgFile["db"]["table"])):
                createNewTable(database,cfgFile["db"]["table"],echiCFG)
                
            #    read each file in echiFiles
            for echiFile in echiFiles:
                
                try:
                    echiPathFile="%s%s"%(echiDataFiles,echiFile)
                    LOG.debug("import %s"%(echiPathFile))
                    
                    #    read each line in file
                    fileData= open(echiPathFile, "r")
                    for dataLine in fileData:
                        echiData=dataLine.split(cfgFile['data']['separator'])
                        
                        #    build md5Hash
                        md5Hash= hashlib.md5(dataLine.encode()).hexdigest()
                        
                        #     prepare vars for new run
                        tableString=""
                        valueString=""
                        
                        #     build sql string
                        for echiDefinition in echiCFG:
                            echIFileIndex=int(echiCFG.index(echiDefinition))
                            
                            # if secound entry use ","
                            if not (tableString==""):
                                tableString+=","
                                valueString+=","
                            
                            if echiDefinition['source']=="cust":
                                # custommer fields
                                tableString+=("`%s`"%(echiDefinition['name']))
                                valueString+=("'%s'"%(md5Hash))
                            else:
                                # data fields
                                tableString+=("`%s`"%(echiDefinition['name']))
                                valueString+=("'%s'"%(formatFieldLength(echiData[echIFileIndex],echiDefinition['length'])))
                        
                        sql=("INSERT INTO %s (%s) VALUES (%s);"%(cfgFile['db']["table"],tableString,valueString))
                        LOG.debug("build sql string: %s"%(sql))
                        try:
                            database.sqlExecute(sql)
                        except:
                            LOG.critical("can't do sqlExecute")
                    
                    fileData.close() 
                except (IndexError) as e:
                    LOG.critical("index error at INDEX: %s and echiImport file %s %s"%(echIFileIndex,cfgFile['cms']['version'],e))
                except:
                    LOG.critical("some error in %s"%(echiFile),exc_info=True)
                finally:
                    fileData.close() 
                #    copy file to archive
                toFile="%s%s"%(cfgFile['data']['archiveFilePath'],echiFile)
                LOG.debug("copy file %s to %s"%(echiPathFile,toFile))
                shutil.move(echiPathFile,toFile)   
            
            '''
                clear up database
            
                if more then max entry in [db][maxentry] copy old db to tableName_backup
            '''
            
            sql="SELECT COUNT(*) FROM `%s`"%(cfgFile['db']['table'])
            numberOfEntrys=database.sqlSelect(sql)[0][0]
            if numberOfEntrys>cfgFile['db']['maxEntry']:
                LOG.info("found %s entry in %s"%(numberOfEntrys,cfgFile['db']['table']))
                
                #    delete old archive database
                echiArchive="%s_oldEntry"%(cfgFile['db']['table'])
                if database.checkTableExists(echiArchive):
                    sql="DROP TABLE `%s`"%(echiArchive)
                    database.sqlExecute(sql)
                sql="RENAME TABLE `%s` TO `echi_db`.`%s`;"%(cfgFile['db']['table'],echiArchive)
                database.sqlExecute(sql) 
                createNewTable(database,cfgFile["db"]["table"],echiCFG)
            
            #    close database
            database.dbClose()
            
        #    end
        LOG.info("echi import finish")
        
    except (defaultEXC) as e:
        LOG.critical("%s"%(e),exc_info=True)
    except: 
        LOG.critical("unkown error ",exc_info=True)

def formatFieldLength(field,length):
    '''
        check if the value field grater as the legth field of the
        database definition. If the Field grader, the field value will 
        be cut
        
        @var: field: field to check as string
        @var: length: length of the field var
        
        return: string (field value)
    '''
    try:
        if (len(field))>length:
            field="%s..."%(field[0:(length-3)])
        return field
    except:
        raise defaultEXC("unkown error in formatFieldLength",True)
        

def checkOldArchiveFiles(archivePath,archiveToStore):
    '''
        check the archivePath how many files, and delete if more
        then archiveToStore
        
        @var: archivePath: absolute path (dir) to zip archive files
        @var: archiveToStore: how many files to be hold
    '''
    try:
        while  deleteOldArchive(archivePath,archiveToStore):
            pass
    except:
        raise defaultEXC("unkown error in checkOldArchiveFiles",True)

def deleteOldArchive(archivePath,archiveToStore):
    '''
        delete old zip file in archive
        
        @var: archivePath: absolute path (dir) to zip archive files
        @var: archiveToStore: how many files to be hold
        
        return: true found file to delete / false no files to delete
        
    '''
    list_of_files = os.listdir(archivePath)
    full_path = [archivePath+"\{0}".format(x) for x in list_of_files]
    if len(list_of_files) > int(archiveToStore):
        oldest_file = min(full_path, key=os.path.getctime)
        os.remove(oldest_file)
        LOG.info("delete old archive file %s"%(oldest_file))
        return True
    return False
        
def delteFiles(sourcePath):
    '''
        delete all files in sourcePath
        
        @var: sourcePath: absolute path to sourcePath
    
    '''
    try:
        LOG.info("delete all files in  %s"%(sourcePath))
        filesToDelete=getFiles(sourcePath)
        
        for fileName in filesToDelete:
            absFileName="%s%s"%(sourcePath,fileName)
            LOG.debug("delete %s"%(absFileName))
            os.remove(absFileName)
    except:
        raise defaultEXC("unkown error in deleteFiles %s"%(sourcePath),True)
    
def zipFiles(sourcePath,zipPath):
    '''
        zip all files in sourcePath to a archive
        
        @var: sourcePath=path for files to zip (absolute Path)
        @var: zipPath= file name of archive file (absolute Path)
        
    '''
    try:
        filesToArchive=getFiles(sourcePath)
        if len(filesToArchive)==0:
            return
        LOG.info("archive echi files in dir %s to file %s"%(sourcePath,zipPath))
        
        #    open new zip file
        echiZipFile = zipfile.ZipFile(zipPath, mode='w')
        
        for file in filesToArchive:
            
            fullFilePath="%s%s"%(sourcePath,file)
            echiZipFile.write(fullFilePath)
        echiZipFile.close()
    except:
        echiZipFile.close()
        raise defaultEXC("unkown error in zipFiles",True)
        
def getFiles(path):
    '''
        get only files in a directory back, no directorys
        
        @var: path: absolute path to dir
        
        return: a list of alle files
    '''
    try:
        files=[]
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                files.append(file)
        return files
    except: 
        raise defaultEXC("unkoun error in getfiles fpr path %s"%(path),True)
                   

def writeJSON(fileNameABS=None,jsonData={}):
        '''
        write a file with json data
        
        @var: fileNameABS: absolute filename to write
        @var: fileData= data to write
        
        Exception: defaultEXC
        '''
        if fileNameABS==None:
            raise defaultEXC("no fileNameABS given")
        try:
            LOG.debug("write json file to %s"%(fileNameABS))
            with open(os.path.normpath(fileNameABS),'w') as outfile:
                json.dump(jsonData, outfile,sort_keys=True, indent=4)
                outfile.close()
        except IOError:
            raise defaultEXC("can not find file: %s "%(os.path.normpath(fileNameABS)))
        except ValueError:
            raise defaultEXC("error in json find file: %s "%(os.path.normpath(fileNameABS)))
        except:
            raise defaultEXC("unkown error in json file to write: %s"%(os.path.normpath(fileNameABS)))
                       
def loadJSON(fileNameABS=None):
        '''
        load a file with json data
        
        @var: fileNameABS: absolute filename to load
        
        return: Dict 
        
        Exception: defaultEXC
        '''
        if fileNameABS==None:
            raise defaultEXC("no fileNameABS given")
        try:
            with open(os.path.normpath(fileNameABS)) as jsonDataFile:
                dateFile = json.load(jsonDataFile)
            return dateFile 
        except IOError:
            raise defaultEXC("can't find file: %s "%(os.path.normpath(fileNameABS)),False)
        except ValueError:
            raise defaultEXC("error in json file: %s "%(os.path.normpath(fileNameABS)))
        except:
            raise defaultEXC("unkown error to read json file %s"%(os.path.normpath(fileNameABS)))

def createNewTable(dbcon,table,echiFields):
    '''
        add a echi table
    
        @var: dbcon, a databse obejct
        @var: table, tablename
        @var: echiFields  [ 
                            {
                                 "source":"file",
                                 "name":"CALLID",
                                 "type":"int",
                                 "length":"10"
                                 },
                            {...},
                            ]
                          
    '''
    try:
        LOG.info("create new table %s"%(table))
        
        #    set vars to default
        sql="CREATE TABLE `%s` ("%(table)
        secound=False
        
        for echiDefinition in echiFields:
            if secound:
                sql+=","
            secound=True
            sql+="`%s` %s(%s)"%(echiDefinition['name'],echiDefinition['type'],echiDefinition['length'])
        sql+=")  ENGINE=InnoDB DEFAULT CHARSET=utf8;"    
        LOG.debug("sql: %s"%(sql))
        dbcon.sqlExecute(sql)
        sql="ALTER TABLE `%s`  ADD UNIQUE KEY `md5` (`md5`);"%(table)
        dbcon.sqlExecute(sql)
    except (defaultEXC) as e:
        raise e
    except:
        raise defaultEXC("unkown error in createNewTable",True)

class defaultEXC(Exception):
    '''
        Exception class
    '''
    def __init__(self, msg="unkown error occured",tracback=False):
        super(defaultEXC, self).__init__(msg)
        self.msg = msg
        LOG.critical(msg,exc_info=tracback)

if __name__ == '__main__':
    main()