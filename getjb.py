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

import sys, getpass, string, requests, json

# disable Cert warnings:
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import restStructure
import shared

# define program-wide variables
PARAM_DESTADDR = "<<DestinationAddr>>"
PARAM_VSDEST   = "<<vsDestination>>"

def clean_path(path):
	list = path.split('localhost')
	list = list[1].split('?')
	return list[0]

def get_reference_link(jitem, referenceTag):
        if jitem.get(referenceTag) != None:
                path = jitem[referenceTag]['link']
		if path != None:
                	return clean_path(path)
	return ""

def get_element(bigip, path):
        response = bigip.get('%s%s' % (BIGIP_URL_BASE, path))
        #print "Response code: %s" % response.status_code
        if response.status_code != 200:
                #print "Response: %s" % response.content
                return None
        return response.content

def get_subpath(bigip, path, name):
	if path[-1] == '*':
		path = path[0:-2]
		#print "New Path in subpath: %s" % path
        monTypeList = get_element(bigip, path)
        if monTypeList != None:
                for item in json.loads(monTypeList).get('items'):
                        path = get_reference_link(item, 'reference')
                        if path != "":
                                path = path + "/" + name
                                response = get_element(bigip, path)
                                if response != None:
                                        return path
        return None

def concat_path(bigip, pstart, pend):
        if pstart[-1] == '*':
                return get_subpath(bigip, pstart, pend)
        else:
                return pstart + '/' + pend


def get_element_in_subpath(bigip, name, path):
	monTypeList = get_element(bigip, path)
	if monTypeList != None:
		for item in json.loads(monTypeList).get('items'):
			path = get_reference_link(item, 'reference')
			if path != "":
				path = path + "/" + name
				response = get_element(bigip, path)	
				if response != None:
					return response
	return None

def get_monitor(bigip, name):
        return get_element_in_subpath(bigip, name, "/mgmt/tm/ltm/monitor")

def create_jb_header(jdata):
	jheader = {"kind": "jb-header"}
	jheader['partition'] = ""
        jheader['application'] = ""
        jheader['transaction'] = "false"
	jheader['parameters'] = {}
	# Set default parameter for virtual server
	dest = jdata.get('destination')
	if dest != None:
		param = PARAM_VSDEST
		list = dest.split('/')
		dest = list[-1] 
		jheader['parameters'][param] = dest
		jdata['destination'] = param
	# Set default parameter for virtual address
        addr = jdata.get('address')
        if addr != None:
                param = PARAM_DESTADDR
                jheader['parameters'][param] = addr
                jdata['address'] = param
		jdata['name'] = param
	return jheader

def append_json(str, j, objectList):

        # Get the path for the global list
        objectList.append(shared.get_pathFromJson(j))
        print objectList[-1]

        str = str + "\n\n"
        str = str + json.dumps(j, sort_keys = False, indent = 4, separators=(',', ': '))
        return str

def exist_expectedProperties(jdata, ref):
        if ref != None:
		for obj in ref[4]:
                	if jdata.get(obj) == None:
                        	return False
                	#else:
                        #	print "obj: %s" % jdata.get(obj)
        return True

def write_json(file, j):
	file.write(json.dumps(j, sort_keys = False, indent = 4, separators=(',', ': ')))

def write_sep(file):
	file.write("\n\n")

def write_object(file, j, ref):
	if exist_expectedProperties(j, ref):
		write_json(file, j)
		write_sep(file)

def write_element(bigip, file, path, iteration, ref, objectList):
	# bigip		- target for REST requests to get configuration from the system.
	# file		- jb file to write the result in.
	# path		- path of the object (like: /mgmt/tm/ltm/pool/poolName)
	# iteration	- Iteration == 0 is the first request. All recursive requests will increase the iteration.
	# ref		- This is the result of the REFERENCE_TYPE_LIST of this element. this has only
	#		  a value, if it is a recursion. For iteration == 0 this is None.
	# objectList	- List of all collected objects, to avoid collection objects multiply times.

	# Address list need to be written first. Flag if this is done:
	isWritten = False

        # Check, if the object is alreeady in the list.
	if path in objectList:
		# Skip creation by settion isWritten as True
		isWritten = True
	else:
		# Load the object from the BIG-IP
	        element = get_element(bigip, path)
        	if element == None:
                	exit("Can't find %s!" % path)
        	jelement = json.loads(element)
		kind = jelement.get('kind')
		# Check if the onject need to be stored
		if kind != None and exist_expectedProperties(jelement, ref):
        		objectList.append(path)
        		print path
		else:
			# Skip creation by settion isWritten as True
			isWritten = True

	#exceptions:
	for item in restStructure.EXPAND_SUBCOLLECTION_LIST:
		if path.find(item) == 0:
        		path = path + "?expandSubcollections=true"
			#print "EXTENSION!!! %s" % path
			break

	element = get_element(bigip, path)
	if element == None:
		exit("Can't find %s!" % path)
	jelement = json.loads(element)

	#exceptions: Create jb-header only for objects with references 
        if iteration == 0 and not isWritten and restStructure.REFERENCE_KIND_LIST.get(kind) != None:
		jHeader = create_jb_header(jelement)
        	write_json(f, jHeader)
		write_sep(f)

	## empty sub in case of sub Elements like pool members:
	sub = ""

        if not isWritten:
                #print "Kind: %s" % kind
                refList = restStructure.REFERENCE_KIND_LIST.get(kind);

                # Replace jb-Header parameter in virtual server
		# Check if it is a virtual and iteration is not 0.
		if refList == restStructure.REFERENCE_TYPE_LIST_VIRTUAL and iteration != 0:
			dest = jelement.get('destination')
			if dest != None:
                		s1 = '/'
                		s2 = ':'
                		list1 = dest.split(s1)
                		list2 = list1[-1].split(s2)
                		list2[0] = PARAM_DESTADDR
                		list1[-1] = s2.join(list2)
                		jelement['destination'] = s1.join(list1)


                if refList != None:
                        #############################work#######################
                        for item in refList:
				#print "Item: %s" % item
				ref = refList.get(item)
                                type = ref[0]
                                if ref[1].find("direct") == 0:
                                        #print "Item to get name: %s" % item
                                        name = jelement.get(item)
                                        if name != None:
	                                        #START - Check for sub elements
        	                                subList = ref[1].split('-')
                	                        if len(subList) == 2:
                        	                        subName = name.get(subList[1])
							if subName != None:
								name = subName
							else:	name = None

					if name != None:
                                                #END - Check for sub elements
						#print "name %s" % name
						pname = shared.nameToPath(name)
						pstart = ref[2].get(type)
						if pstart != None:
							path = concat_path(bigip, pstart, pname)
							if path != None:
								write_element(bigip, file, path, iteration + 1, ref, objectList)
								write_sep(file)

                                elif ref[1].find("items") == 0:
                                        #print "Item to get name: %s" % item
                                        list = jelement.get(item)
					if list != None and list.get('items') != None:
                        			for element in list['items']:
							path = get_reference_link(element, "nameReference")
							#print "Path from link: %s" % path
							if path == "": # Only on v12 and higher we have a nameReference available
								name = element.get('name')
								path = ref[2].get(type)
								if name != None and path != None:
                                                                        path = concat_path(bigip, path, name)
                                                                        #print "PATH_concat = %s" % path
									#path = get_subpath(bigip, path, name)
									#print "PATH_sub = %s" % path
									if path == None:
										path = ""
									#print "SubPath: %s " % path
								else:
									path = ""
							if path != "":
								write_element(bigip, file, path, iteration + 1, ref, objectList)
								write_sep(file)

                                elif ref[1].find("list") == 0:
                                        #print "Item to get name: %s" % item
                                        list = jelement.get(item)
                                        if list != None:
                                                for name in list:
	                                                #START - Check for sub elements
        	                                        subList = ref[1].split('-')
                	                                if len(subList) == 2:
                        	                                subName = name.get(subList[1])
                                	                        if subName != None:
                                        	                        name = subName
								else:	name = None

							if name != None:
                                                		#END - Check for sub elements
                                                		path = shared.nameToPath(name)
	                                                	pstart = ref[2].get(type)
        	                                        	if pstart != None:
									path = concat_path(bigip, pstart, path)
									if path != None:
                                	                			write_element(bigip, file, path, iteration + 1, ref, objectList)
                                        	        			write_sep(file)

                                elif ref[1] == "and":
                                        #print "Item to get fPath: %s" % item
                                        names = jelement.get(item)
                                        if names != None:
                                                s = ' and '
                                                r = []
                                                monList = names.split(' ')
                                                for mon in monList:
                                                        if mon != "" and mon != "and":
                                                                #print "Mon first : %s" % mon

                                                		path = shared.nameToPath(mon)
 	           						pstart = ref[2].get(type)
        	                                                if pstart != None:
                	                                                path = concat_path(bigip, pstart, path)
                                                			if path != None:
										write_element(bigip, file, path, iteration + 1, ref, objectList)
                                                				write_sep(file)

                                                                
                                elif ref[1] == "sub":
                                        #print "Item to get fPath: %s" % item
                                        name = jelement.get('fullPath')
                                        if name != None:
                                                path = shared.nameToPath(name)
                                                path = ref[2].get(item) + '/' + path + '/' + type 
						response = get_element(bigip, path)
						if response != None:
							jres = json.loads(response)
							if jres.get('items') != None:
								for item in jres.get('items'):
									sub = append_json(sub, item, objectList)

				elif ref[1] == "address":
                                        #print "Item (address) to get fPath: %s" % item
					# Disable arp by default to avoid duplicated IP in case of migration
					arp = jelement.get('arp')
					if arp != None:
						jelement['arp'] = "disabled"
					#Create virtual-address upfront:
					write_json(file, jelement)
					write_sep(file)
					isWritten = True
					name = jelement.get('fullPath')
					if name != None:
						name = shared.add_CommonToName(name)
						print "Name: %s" % name
						searchPath = ref[2].get(ref[0])
						if searchPath != None:
							#print "SearchPath: %s" % searchPath
							response = get_element(bigip, searchPath)
                                                	if response != None:
								jres = json.loads(response)
								vsList = jres.get('items')
								if vsList != None:
									# Went through the list of virtuals:
									for jvs in vsList:
										dest = jvs.get('destination')
										if dest != None:
											#print "Destination: %s" % dest
											if dest.split(':')[0] == name:
												#print "Found vs: %s" % jvs.get('destination')  
												vsFullPath = jvs.get('fullPath')
												if vsFullPath != None:
													#print " FullPath: %s " % vsFullPath
													vsName = shared.nameToPath(vsFullPath)
													# Replace Header parameter in virtual server
													s1 = '/'
													s2 = ':'
													list1 = dest.split(s1)
													list2 = list1[-1].split(s2)
													list2[0] = PARAM_DESTADDR
													list1[-1] = s2.join(list2)
													jvs['destination'] = s1.join(list1)
													# Write virtual server elements 
													write_element(bigip, file, searchPath + "/" + vsName, iteration + 1, ref, objectList)
													write_sep(file)


	if not isWritten:
		write_json(file, jelement)
	### add sub objects behind the main object, since it depends on it:
	if sub != "":
		file.write(sub)
	

##############
#### MAIN ####
##############

# Parse Parameter
ex = False
if len(sys.argv) == 4:
	source = sys.argv[1]
	sourceList = source.split('@')
	ex = len(sourceList) != 2
	filename = sys.argv[2]
	ePath = sys.argv[3]

else:
        ex = True

if ex:
        print "Usage: %s <username>@f5-mgmt-ip <jb_filename> <path> " % (sys.argv[0])
        print "\t  <path> Points to the configuration on the BIG-IP"
        print "\t\t Example: /mgmt/tm/ltm/pool/poolname"
        sys.exit()

username = sourceList[0]
bigipAddr = sourceList[1]
BIGIP_URL_BASE = 'https://%s' % bigipAddr

# Get Password
passwd = getpass.getpass("Pasword for " + source + ":")


# REST resource for BIG-IP that all other requests will use
bigip = requests.session()
bigip.auth = (username, passwd)
bigip.verify = False
bigip.headers.update({'Content-Type' : 'application/json'})

# Open json blob file
f = open ( filename, 'w')

objectList = []
print "Gathering Objects:"

write_element(bigip, f, ePath, 0, None, objectList)

f.close()

