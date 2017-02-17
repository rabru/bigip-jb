#!/usr/bin/python
#
# Copyright 2017 Ralf Bruenig
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, string

def preprocessorExit(str):
	exit("Preprocessor error: " + str)

def parseDefine(str, propDict):
	s = ' '
	str = str[8:].lstrip()
	name, str = str.split(s, 1)
	propDict[name] = str.split()
	if preDEBUG:
		preDEBUGoutput("#define", "%s = %s" % (name, propDict[name]))

def parseIf(str):
	s = ' '
	sList = str.split(s, 1)
	if len(sList) != 2:
		preprocessorExit("Parameter is missing at " + sList[0] + " statement!")
	str = sList[1].lstrip()

	#Blacklisting:
	if str.find('__') >= 0:
		preprocessorExit("\'__\' is not allowed in " + sList[0] + " statement!")
	try:
		res = eval(str)
	except:
		preprocessorExit("%s in %s statement!" % (sys.exc_info()[1], sList[0]))

	return res


def parseLoop(str, propDict):
        s = ' '
        sList = str.split(s, 1)
        if len(sList) != 2:
                preprocessorExit("Parameter is missing at " + sList[0] + " statement!")
        str = sList[1].strip()
	list = propDict.get(str)
	if list == None:
		preprocessorExit("Parameter " + str + " at " + sList[0] + " statement need to be defined first!")
	return str

def preDEBUGoutput( element, response ):
	if element.find('#if') == 0:
		iter = preITERATIONS
	else:
		iter = preITERATIONS - 1
	if response == "": 
		print "%s%s" % (' '*iter, element)
	else:
                print "%s%s -> %s" % (' '*iter, element, response)
 
def preprocessor(lineList, skip, skipAll, mode, result):
	global preITERATIONS

	#print "PREPROCESSOR started: mode = %s" % mode
	propDict = result[0]

	
	# Loop cleanup
	loopName = ""
	loopPointer = 0
	if mode.find("#loop ") == 0:
		loopName = parseLoop(mode, propDict)
		loopList = propDict[loopName]
		propDict[loopName] = loopList[:1]
		#print "Loop Ini - listLen: %s" % len(loopList)
		#print propDict[loopName]
        	if preDEBUG:
			if skip:
	                	preDEBUGoutput("#loop", "skipped")
			else:
                                preDEBUGoutput("#loop", "%s = %s" % (loopName, loopList))
		mode = mode[:5]

	counter = 0 
	while counter < len(lineList):
		line = lineList[counter]
		counter = counter + 1
		#print "counter %s" % counter
		# Replace #define parameter - #loop will be an exception since we need the parameter name there
		if line.find("#loop ") != 0:
			for prop in propDict:
				#if prop != loopName: # Skip loopName
				propLen = len(propDict[prop])
				#print "proplen: %s" % propLen
				if propLen == 1:
					j = 0
				elif propLen > loopPointer:
					j = loopPointer 
				else:
					preprocessorExit("List of \'" + prop + "\' is to short!")
				line = line.replace(prop, propDict[prop][j])
		
		# Replace Loop Parameter:
		#if mode == "#loop":
		#	#print "line: %s" % line
		#	line = line.replace(loopName, loopList[loopPointer])

 		# Search for preprocessor comment lines		
		if len(line) >= 1 and line[0] == '#':
			# Make sure, it is not a comment line
			if len(line) > 1 and line[1] != '#' and line[1] != ' ':
				if line.find("#define ") == 0:
					if not skip:
						parseDefine(line, propDict)
				elif line.find("#if ") == 0:
					# If this #if is already on skip mode, all following elements should be also skipped
					res = parseIf(line)
					if preDEBUG:
						if skip:
							preDEBUGoutput( line, "skipped" )
						else: 
							preDEBUGoutput( line, res )
					preITERATIONS = preITERATIONS + 1
					counter = counter + preprocessor(lineList[counter:], skip or not res, skip, "#if", result) + 1
					preITERATIONS = preITERATIONS - 1
                        	elif line.find("#endif") == 0:
					if preDEBUG:
						if skipAll:
							preDEBUGoutput( line, "skipped" )
						else:
							preDEBUGoutput( line, "")
					if mode == '#if' or mode == '#else':
						#print "Return Counter %s" % counter
						return counter - 1 
					else:
						preprocessorExit("Found unexpected #endif")
                                elif line.find("#elif") == 0 and not skipAll:

                                        if mode == '#if':
						if not skip: # All following elements are skipped
							skipAll = True
							skip = True
							if preDEBUG:
								preDEBUGoutput( "#elif", "skipped" )
						elif not skipAll and skip:
                                                	skip = not parseIf(line)
                                                        if preDEBUG:
                                                                preDEBUGoutput( "#elif", (not skip))
						else:
							skip = True
							if preDEBUG:
                                                                preDEBUGoutput( "#elif", "skipped" )
                                        else:
                                                preprocessorExit("Found unexpected #elif in mode '%s'" % mode)
				elif line.find("#else") == 0:
					if not skipAll:
						if mode == '#if':			
                                			skip = not skip
							mode = '#else'
						else:
							preprocessorExit("Found unexpected #else in mode '%s'" % mode)
					if preDEBUG:
						if skipAll:
							preDEBUGoutput( "#else", "skipped" )
						else:
							preDEBUGoutput( "#else", "" )
				elif line.find("#loop ") == 0:
					preITERATIONS = preITERATIONS + 1
					counter = counter + preprocessor(lineList[counter:], skip, skip, line, result) + 1
					preITERATIONS = preITERATIONS - 1
				elif line.find("#loopend") == 0:
					if mode != "#loop":
						preprocessorExit("Found unexpected #endloop in mode '%s'" % mode)
					elif loopPointer + 1 >= len(loopList) or skip:
						if preDEBUG:
							if skip:
								preDEBUGoutput( "#loopend", "skipped" )
							else:
								preDEBUGoutput( "#elif", "" )
						propDict[loopName] = loopList
						return counter -1
					else:
						loopPointer = loopPointer + 1
						propDict[loopName] = loopList[loopPointer:loopPointer + 1]
						#print "Pointer: %s listlen: %s" % (loopPointer, len(loopList))
						counter = 0 # Start from the beginning of the loop
						
						

			else: # it is a comment line
				if preDEBUG:
					print line		
	
		elif not skip:
			result[1] = result[1] + line + "\n"
		
	#print "Return Counter %s" % counter
	if mode != "":
		preprocessorExit("End of Line! Couldn't find any propper ending for '%s'" % mode)
	return counter




##############
#### Test ####
##############

preDEBUG = False
preITERATIONS = 0	

if sys.argv[0].endswith('preprocessor.py'):
	preDEBUG = True
	filename = sys.argv[1]
	# Open json blob file
	f = open ( filename, 'r')
	str = f.read(100000)

	lineList = str.split('\n')

	Result = [{}, ""]
	preprocessor(lineList, False, False, "", Result)
	print ""
	print "Result:"
	print Result[1]

	print "Parameters:"
	for param in Result[0]:
		print " %s = %s" % (param, Result[0][param]) 
