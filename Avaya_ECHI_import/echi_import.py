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

import mysql.connector
import logging
import logging.config
import os
import json
import sys
import hashlib
from echi_helper import defaultEXC
import shutil
import zipfile
import datetime


#    constants
__version__='1.0'
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
            database=dbConnect(cfgFile['db']['server'])
            
            # check if tabel exists
            if not (checkTableExists(database,cfgFile["db"]["table"])):
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
                        secound=False
                        tableString=""
                        valueString=""
                        
                        #     build sql string
                        for dataRAW in echiCFG:
                            dataRow=int(dataRAW)              
                            # if secound entry use ","
                            if secound:
                                tableString+=","
                                valueString+=","
                            secound=True
                            
                            if echiCFG[dataRAW]['source']=="cust":
                                # custommer fields
                                tableString+=("`%s`"%(echiCFG[dataRAW]['name']))
                                valueString+=("'%s'"%(md5Hash))
                            else:
                                # data fields
                                tableString+=("`%s`"%(echiCFG[dataRAW]['name']))
                                valueString+=("'%s'"%(echiData[dataRow]))
                        
                        sql=("INSERT INTO %s (%s) VALUES (%s);"%(cfgFile['db']["table"],tableString,valueString))
                        LOG.debug("build sql string: %s"%(sql))
                        sqlExecute(database, sql)
                    
                    
                    fileData.close() 
                except:
                    LOG.critical("some error in %s"%(echiFile),exc_info=True)
                
                #    close file
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
            numberOfEntrys=sqlSelect(database,sql)[0][0]
            if numberOfEntrys>cfgFile['db']['maxEntry']:
                LOG.info("found %s entry in %s"%(numberOfEntrys,cfgFile['db']['table']))
                
                #    delete old archive database
                echiArchive="%s_oldEntry"%(cfgFile['db']['table'])
                if checkTableExists(database, echiArchive):
                    sql="DROP TABLE `%s`"%(echiArchive)
                    sqlExecute(database,sql)
                sql="RENAME TABLE `%s` TO `echi_db`.`%s`;"%(cfgFile['db']['table'],echiArchive)
                sqlExecute(database, sql) 
                createNewTable(database,cfgFile["db"]["table"],echiCFG)
            
            #    close database
            dbClose(database)
            
        #    end
        LOG.info("echi import finish")
        
    except (defaultEXC) as e:
        LOG.critical("%s"%(e),exc_info=True)
    except: 
        LOG.critical("unkown error ",exc_info=True)

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
                   
def dbConnect(cfg={}):
        '''
            build a new database connection
            
        @var: cfg={
                'host':'127.0.0.1',
                'database':'databaseName',
                'user':'username'
                'password':'password'
                'port':3306
                }
                
            return: dabase connection object
            exception: defaultEXC
            
        '''
        LOG.info("try connect to host:%s:%s with user:%s table:%s"%(cfg['host'],cfg['port'],cfg['user'],cfg['database']))
        try:
            dbConnection = mysql.connector.connect(**cfg)
                                                
            #self.__dbConnection.apilevel = "2.0"
            #self.__dbConnection.threadsafety = 3
            #self.__dbConnection.paramstyle = "format" 
            #self.__dbConnection.autocommit=True
            LOG.info("mysql connect succecfull")
            return dbConnection
        except (mysql.connector.Error) as e:
            dbClose(dbConnection)  
            dbConnection=False
            raise defaultEXC("can't not connect to database: %s"%(e))
        except:
            raise defaultEXC("unkown error in modul",True)
    
def dbClose(dbConnection):
        '''
        
        close the database connection
        
        catch all errors and exception with no error or LOG
        
        @var: dbconnection, a databse object
        
        return: none
        
        exception: none
        '''
        try:
            if dbConnection:
                LOG.info("close database")
                dbConnection.close()
                dbConnection=False
        except:
            pass

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

def checkTableExists(dbcon, tablename):
    '''
        check if database table exits
        
        @var dbcon: databse object
        @var tablename: Tabel to check
        
        return: true/if tabel exits , false/ not exits
    '''
    try:    
        dbcur = dbcon.cursor()
        dbcur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{0}'
            """.format(tablename.replace('\'', '\'\'')))
        if dbcur.fetchone()[0] == 1:
            return True
        return False
    except:
        raise defaultEXC("unkown error to checkTableExits %s"%(tablename))
    
def sqlExecute(dbcon,sql):
        """
        excecute a sql statment
         
        @var: sql , a well form sql statment.
        
        exception: defaultEXC 
         
        """
        try:
            LOG.debug("sqlExecute: %s"%(sql))
            
            cursor  = dbcon.cursor()
            cursor.execute(sql)
            dbcon.commit()  
        except (mysql.connector.Error) as e:
            raise defaultEXC("mysql error %s"%(e))
        except :
            raise defaultEXC("unkown error sql:%s"%(sql),True) 
        
def sqlSelect(dbcon,sql):
        """
        excecute a sql statment
         
        @var: sql , a well form sql statment.
        
        return: sql result
        
        exception: defaultEXC 
         
        """
        try:
            LOG.debug("sqlExecute: %s"%(sql))
            
            cursor  = dbcon.cursor()
            cursor.execute(sql)
            result=cursor.fetchall()
            return result
        except (mysql.connector.Error) as e:
            raise defaultEXC("mysql error %s"%(e))
        except :
            raise defaultEXC("unkown error sql:%s"%(sql),True)  

def createNewTable(dbcon,table,echiFields):
    '''
        add a echi table
    
        @var: dbcon, a databse obejct
        @var: table, tablename
        @var: echiFields  "0": {
                                 "source":"file",
                                 "name":"feld1",
                                 "type":"int",
                                 "length":"10"
                                 },
                          "...": {...}
                          
    '''
    try:
        LOG.info("create new table %s"%(table))
        
        #    set vars to default
        sql="CREATE TABLE `%s` ("%(table)
        secound=False
        
        for fieldNumber in echiFields:
            if secound:
                sql+=","
            secound=True
            sql+="`%s` %s(%s)"%(echiFields[fieldNumber]['name'],echiFields[fieldNumber]['type'],echiFields[fieldNumber]['length'])
        sql+=") ENGINE=InnoDB DEFAULT CHARSET=utf8;"    
        LOG.debug("sql: %s"%(sql))
        sqlExecute(dbcon, sql)
    except (defaultEXC) as e:
        raise e
    except:
        raise defaultEXC("unkown error in createNewTable",True)


if __name__ == '__main__':
    main()