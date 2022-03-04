# ECHI Avaya echi formte
## this file define the import format of the avaya echI Files
The import of the Avaya ECHII is defined in this file. From this file, the individual desired fields are then assigned to the target columns in the database. If necessary, a new database is also created from this file.

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


## custommer echi format
In the folder echi_format you can find the import format for your cms version. You can add
user defined formats. Do not use format files from this script, because after the next update
your change will be overwritten.

the script breaks the string down into small parts using the separator (definition in the config file)
, which are numbered from 0 to x.

###format of the fields
[ { field 0 },{field 1}, {field 2}, {field ...}]

[ 
	
	{
	"source":"file",
	"name":"CALLID",
	"type":"int",
	"length":"10"
	},
	{
	"source":"file",
	"name":"ACWTIME",
	"type":"int",
	"length":"4"
	},
	{
	"source":"file",
	"name":"ANSHOLDTIME",
	"type":"int",
	"length":"4"
	},
	{
	{...}
]

In this case is the split data from the echi file with the number "0" the CallID field
and the data field 2 the ANSHOLDTIME, and so on...

Every field need some data description:

"source":"file"      data are from file

"name":"ANSHOLDTIME" the tabel row name to insert

"type":"int"		 data type in the table

"length":"4"		 data lenght in the database table

This field are imported. The script maps the data an build from this information the
new database table in the database.	

IMPORTEND!:
At the end of the file alle format description need this section, for the md5 Hash.

{
	"source":"cust",
	
 	"name":"md5",
 	
 	"type":"varchar",
 
 	"length":"32"
}
