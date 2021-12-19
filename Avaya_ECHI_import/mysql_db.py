#!/usr/bin/python

#    Created on 19.12.2021

#    @author: uschoen

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
from echi_helper import defaultEXC

#    constants
__version__='1.0'
__author__ = 'ullrich schoen'

#    Logging
LOG=logging.getLogger(__name__)

class mysql_db(object):
    '''
     create a mysql connection
    '''


    def __init__(self, cfg={}):
        '''
        cfg={
                'host':'127.0.0.1',
                'database':'databaseName',
                'user':'username'
                'password':'password'
                'port':3306
                }
        '''
        self.cfg=cfg
        self.dbcon=False
        self.dbConnect(self.cfg)
        LOG.info("build mysql_db connection , version %s"%(__version__))
        
    def dbConnect(self,cfg={}):
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
            self.dbcon = mysql.connector.connect(**cfg)
                                                
            #self.dbcon.apilevel = "2.0"
            #self.dbcon.threadsafety = 3
            #self.dbcon.paramstyle = "format" 
            #self.dbcon.autocommit=True
            LOG.info("mysql connect succecfull")
        except (mysql.connector.Error) as e:
            self.dbClose()  
            self.dbcon=False
            raise defaultEXC("can't not connect to database: %s"%(e))
        except:
            raise defaultEXC("unkown error in modul",True)
    
    def dbClose(self):
        '''
        
        close the database connection
        
        catch all errors and exception with no error or LOG
        
        @var: dbconnection, a databse object
        
        return: none
        
        exception: none
        '''
        try:
            if self.dbcon:
                LOG.info("close database")
                self.dbcon.close()
                self.dbcon=False
        except:
            pass
    
    def sqlExecute(self,sql):
        """
        excecute a sql statment
         
        @var: sql , a well form sql statment.
        
        exception: defaultEXC 
         
        """
        try:
            LOG.debug("sqlExecute: %s"%(sql))
            
            cursor  = self.dbcon.cursor()
            cursor.execute(sql)
            self.dbcon.commit()  
        except (mysql.connector.Error) as e:
            raise defaultEXC("mysql error %s"%(e))
        except :
            raise defaultEXC("unkown error sql:%s"%(sql),True) 
        
    def sqlSelect(self,sql):
        """
        excecute a sql statment
         
        @var: sql , a well form sql statment.
        
        return: sql result
        
        exception: defaultEXC 
         
        """
        try:
            LOG.debug("sqlExecute: %s"%(sql))
            
            cursor  = self.dbcon.cursor()
            cursor.execute(sql)
            result=cursor.fetchall()
            return result
        except (mysql.connector.Error) as e:
            raise defaultEXC("mysql error %s"%(e))
        except :
            raise defaultEXC("unkown error sql:%s"%(sql),True) 
    
    def checkTableExists(self, tablename):
        '''
            check if database table exits
            
            @var tablename: Tabel to check
            
            return: true/if tabel exits , false/ not exits
        '''
        try:    
            dbcur = self.dbcon.cursor()
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
        