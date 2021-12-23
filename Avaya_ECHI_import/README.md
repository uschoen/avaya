# ECHI Avaya import script
## Python script to import the Avaya ECHI data to a mysql Database
The script if locking in a source directory for new echi files. The Script will be importing all Scripts in this directory. Alle data will by import to a mysql table. The files where move to the archive directory. Alle files in the directory are zip and copy to the archive zip dir. Zip files where delete after a time. For alle function you can use the configuration file to define the values.
The best way is use a cron Job to execute the script every hour.
## Changelog
1.0 First Version

## License
Copyright 2021 by Ullrich Schoen

his program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

## Requierment
### Windows
Python Version 3.7.9

mysql-connector-python-8.0.27-windows-x86-64bit.msi 

mysql db (maria db 5 or 10)

### Linux
Python Version 3.7

mysqlclient-2.1.0 

mysql db (maria db 5 or 10)

## Installing 
### Windows
install python for windows with Version 3.7.9. 

download Link: <https://www.python.org/ftp/python/3.7.9/python-3.7.9-amd64.exe>

install Mysql Connector for Python with Version 8.0.27

Download Link:<https://dev.mysql.com/downloads/file/?id=508346>

### Linux
use sudo apt-get install python3 to install python 3.x

use sudo pip3 install mysql to install the mysql connector.

## Setup
Install the Avaya ECHi Script in any directory. Copy the file. Importent: change
the owner and the file mask to the user it have to run.

Directories:

/..YOURE directory

/archive:	files to store the imported schi files and zip files

/data:	new echi files
/echi_format:	echi format description
/etc:	configuration file
/excample:	echi exmaple from Avaya
/log:	log directory

### echi description
comming soon

### configuration:
Copy the excample_config.json in /etc/ to config.json

#### cms section
"cms":
	{"version":"r18.json"} : Json File with definitions

use the import definition for your echi format. See in /echi_format for the your need version. See 
under custommer echi formats for more information.

#### data section
"data":{...}
	
"sourceFilePath": absolute path to the echi file for import

"archiveFilePath": absolute path to the achive path

"archiveInterval": "1" intervall (days) to zip the archive echi files (stored in ../archiveFilePath/zip)

"holdArchiveFiles": "2" number for hold zip files in ../archiveFilePath/zip

"lastarchive": "2020,12,19" change it for the first runn to today -1. The script save the last arcihve date here

"separator": "|" separator betwen the data, see the format discription 
    
!!!Importent: in json file you have to ecape special characters !!!

#### db	section
"db":{...}

"maxEntry": 1000000 mx entry for entrys in db database. If more entrys in the table, the script copy the table to backup and add new empty table.

"table":"echi",

"server":{...} Database connection data, see server section

##### "server" section
server:{...}

"database": Database name

"host": "127.0.0.1" Database host/ip

"user": "unkown" Dtatabse user
 
"password": "password" Database password
 
 "port": 3306 Database port
 
 "raise_on_warnings": true/false 
           

#### logging section
see for discription in the documationen for the pthon modul logging/ configuration with dictory and json file


"logging":{
        "disable_existing_loggers": false,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)30s - %(lineno)d - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": "DEBUG",
                "stream": "ext://sys.stdout"
            },
            "warning_handler": {
                "backupCount": 5,
                "class": "logging.handlers.RotatingFileHandler",
                "encoding": "utf8",
                "filename": "absolute path (escape\\)warning.log",
                "formatter": "simple",
                "level": "WARNING",
                "maxBytes": 1200000,
                "mode": "a"
            },
            "info_handler": {
                "backupCount": 5,
                "class": "logging.handlers.RotatingFileHandler",
                "encoding": "utf8",
                "filename": "absolute path (escape\\)info.log",
                "formatter": "simple",
                "level": "INFO",
                "maxBytes": 1200000,
                "mode": "a"
            }
        },
        "root": {
            "handlers": [
                "warning_handler","info_handler","console"],
            "level": "DEBUG"
        },
        "version": 1
    }
}
	