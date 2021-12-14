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




#    Standard library imports
import logging

#    constants
__version__='0.9'
__author__ ='ullrich schoen'

#    logging
LOG=logging.getLogger(__name__)

class defaultEXC(Exception):
    '''
    
    '''
    def __init__(self, msg="unkown error occured",tracback=False):
        super(defaultEXC, self).__init__(msg)
        self.msg = msg
        LOG.critical(msg,exc_info=tracback)