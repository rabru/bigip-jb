Introduction
============

This script can be helpful in the daily manually administrative jobs on a BIG-IP and is therefore targeted to any BIG-IP administrator and consultant. Even if it is based on REST, it is not ment ot be used for any automation or orchestration integration, since it is purely targeted for the manual administration.

The main idea behind this project is, to create an easy way to reproduce the same configuration in a simple way by storing it in a json blob. Also it should be easy to create a json blob, without learning a new json scheme. Therefor I simply use the json output of the BIG-IP as basic for the json blob, so that it can be created simply by copy and paste.

The project based mainly on two python scripts:

``getjb.py``
  This is helping you to create a json blob with the configuration you would like to implement.
  But still it is possible to create your own json blob manually simply by copy paste.

``sendjb.py``
  This will send the finalized configuration from a json blob (.jb) file towards the targeted BIG-IP.

To your attention
-----------------

The usage of this scripts is on your own risk and it is up to you to make sure that the usage is not causing potential outages of your environment. Especially in a productive environment use this scripts with care and validate the function always in a test environment first.

Installation of bigip-jb
------------------------

Make sure that python v2 is installed. 
I tested the following combinations:

- Debian Jessie with python v2.7.9
- Windows with python v2.7.13 

Missing python modules  like 'requests' need to be installed manually with pip::
 
	> pip install requests

Download all five python scripts from github in the same target folder.

Additional information for Windows user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python can be downloaded here:
https://www.python.org/downloads/windows/

To start the python scripts directly, select over the Explorer the default application for .py files. 

- Right click on a .py file -> 'Open with' -> 'Choose default program…'
- Select over 'Browse...' python.exe. For example: 'C:\Python27\python.exe'

To use the Python Scripts in Power Shell:

- Add .py to the environmental variable 'PATHEXT' 
- Optional add the location of the python scripts to the environmental variable 'Path' to be able to start the scripts on any location

