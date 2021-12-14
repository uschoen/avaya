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
import csv
import shutil





#    constants
__version__='0.9'
__author__ = 'ullrich schoen'

#    PATH: the absolute path of the script
PATH='' if not os.path.dirname(sys.argv[0]) else '%s/'%(os.path.dirname(sys.argv[0]))

#    Script absolut root path
ROOTPATH=("%s/%s"%(os.getcwd(),os.path.dirname(sys.argv[0])))

#
CONFIG_FILE="%s%s"%(PATH,"etc/config.json")

#    Logging
LOG=logging.getLogger(__name__)
LOG.warning("start up echi import , version %s, path:%s , rootPath: %s , config:%s"%(__version__,PATH,ROOTPATH,CONFIG_FILE))


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
        
        #    create db connection
        database=dbConnect(cfgFile['db']['server'])
        
        # check if tabel exists
        if not (checkTableExists(database,cfgFile["db"]["table"])):
            createNewTable(database,cfgFile["db"]["table"],echiCFG)
        
        #    search ech data file
        echiDataFiles="%s"%(cfgFile['data']['sourceFilePath'])
        LOG.info("search in %s for new echi files"%(echiDataFiles))
        echiFiles = os.listdir(echiDataFiles)
        LOG.info("found %s files"%(len(echiFiles)))
        
        #    read each file in echiFiles
        for echiFile in echiFiles:
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
            #    close file
            fileData.close()
            
            #    copy file to archive
            toFile="%s%s"%(cfgFile['data']['archiveFilePath'],echiFile)
            LOG.debug("copy file %s to %s"%(echiPathFile,toFile))
            shutil.move(echiPathFile,toFile)
        
        #    close database
        dbClose(database)
        
        #    end
        LOG.info("echi import finish")
        
    except (defaultEXC) as e:
        LOG.critical("%s"%(e),exc_info=True)
    except: 
        LOG.critical("unkown error ",exc_info=True)
    
def dbConnect(cfg={}):
        '''
        build a new database connection
        
        cfg={
            'host':'127.0.0.1',
            'database':'databaseName',
            'user':'username'
            'password':'password'
            'port':3306
            }
            
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

def loadJSON(fileNameABS=None):
        '''
        load a file with json data
        
        fileNameABS: absolute filename to load
        
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
    dbcur = dbcon.cursor()
    dbcur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tablename.replace('\'', '\'\'')))
    if dbcur.fetchone()[0] == 1:
        return True
    return False

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

def createNewTable(dbcon,table,echiFields):
    '''
    --
    -- Tabellenstruktur für Tabelle `echi_daten`
    --
    
    CREATE TABLE `echi_daten` (
      `feld1` int(11) NOT NULL,
      `feld2` int(11) NOT NULL,
      `seg_start` int(11) NOT NULL,
      `md5` varchar(25) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    
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