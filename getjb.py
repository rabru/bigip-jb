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

execfile("lib/reststructure.py")

# define program-wide variables
PARAM_DESTADDR = "<<DestinationAddr>>"
PARAM_VSDEST   = "<<vsDestination>>"

def clean_path(path):
	list = path.split('localhost')
	list = list[1].split('?')
	return list[0]

def name2path(name):
	s1='/'
	s2='~'
	list = name.split(s1)
	return s2.join(list)

def get_reference_link(jitem, referenceTag):
        if jitem.get(referenceTag) != None:
                path = jitem[referenceTag]['link']
                return clean_path(path)
	return ""

def get_element(bigip, path):
        response = bigip.get('%s%s' % (BIGIP_URL_BASE, path))
        #print "Response code: %s" % response.status_code
        if response.status_code != 200:
                #print "Response: %s" % response.content
                return None
        return response.content

def get_subpath(bigip, name, path):
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
                return get_subpath(bigip, pend, pstart)
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

def write_json(file, j):
	file.write(json.dumps(j, sort_keys = False, indent = 4, separators=(',', ': ')))

def write_sep(file):
	file.write("\n\n")

def append_json(str, j):
	str = str + "\n\n"	
	str = str + json.dumps(j, sort_keys = False, indent = 4, separators=(',', ': '))
	return str

def write_element(bigip, file, path, iteration):

	#print "=== %s. write_element Iteration! ===" % iteration

	# Address list need to be written first. Flag if this is done:
	isWritten = False
	#exceptions:
	for item in EXPAND_SUBCOLLECTION_LIST:
		if path.find(item) == 0:
        		path = path + "?expandSubcollections=true"
			#print "EXTENSION!!! %s" % path
			break

	element = get_element(bigip, path)
	if element == None:
		exit("Can't find %s!" % path)

	jelement = json.loads(element)

	#exceptions:
        if iteration == 0:
		jHeader = create_jb_header(jelement)
        	write_json(f, jHeader)
		write_sep(f)

	## empty sub:
	sub = ""

        kind = jelement.get('kind')
        if kind != None:
                #print "Kind: %s" % kind
                refList = REFERENCE_KIND_LIST.get(kind);

                # Replace jb-Header parameter in virtual server
		# Check if it is a virtual and iteration is not 0.
		if refList == REFERENCE_TYPE_LIST_VIRTUAL and iteration != 0:
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
						path = name2path(name)
						pstart = ref[2].get(type)
						if pstart != None:
							path = concat_path(bigip, pstart, path)
							if path != None:
								write_element(bigip, file, path, iteration + 1)
								write_sep(file)

                                elif ref[1].find("items") == 0:
                                        #print "Item to get name: %s" % item
                                        list = jelement.get(item)
					if list != None and list.get('items') != None:
                        			for element in list['items']:
							path = get_reference_link(element, "nameReference")
							if path != "":
								write_element(bigip, file, path, iteration + 1)
								write_sep(file)

#                                			response = get_element(bigip, get_reference_link(element, "nameReference"))
#                                			if response != None:
#                                        			write_json(file, json.loads(response))
#								write_sep(file)

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
                                                		path = name2path(name)
	                                                	pstart = ref[2].get(type)
        	                                        	if pstart != None:
									path = concat_path(bigip, pstart, path)
									if path != None:
                                	                			write_element(bigip, file, path, iteration + 1)
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

                                                		path = name2path(mon)
 	           						pstart = ref[2].get(type)
        	                                                if pstart != None:
                	                                                path = concat_path(bigip, pstart, path)
                                                			if path != None:
										write_element(bigip, file, path, iteration + 1)
                                                				write_sep(file)

                                                                
                                elif ref[1] == "sub":
                                        #print "Item to get fPath: %s" % item
                                        name = jelement.get('fullPath')
                                        if name != None:
                                                path = name2path(name)
                                                path = ref[2].get(item) + '/' + path + '/' + type 
						response = get_element(bigip, path)
						if response != None:
							jres = json.loads(response)
							if jres.get('items') != None:
								for item in jres.get('items'):
									sub = append_json(sub, item)
									#write_json(file, item)

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
						searchPath = ref[2].get(ref[0])
						if searchPath != None:
							response = get_element(bigip, searchPath)
                                                	if response != None:
								jres = json.loads(response)
								vsList = jres.get('items')
								if vsList != None:
									# Went through the list of virtuals:
									for jvs in vsList:
										destination = jvs.get('destination')
										if jvs.get('destination') != None and jvs.get('destination').find(name) == 0:
											#print "Found vs: %s" % jvs.get('destination')  
											vsFullPath = jvs.get('fullPath')
											if vsFullPath != None:
												#print " FullPath: %s " % vsFullPath
												vsName = name2path(vsFullPath)
												# Replace Header parameter in virtual server
												s1 = '/'
												s2 = ':'
												list1 = destination.split(s1)
												list2 = list1[-1].split(s2)
												list2[0] = PARAM_DESTADDR
												list1[-1] = s2.join(list2)
												jvs['destination'] = s1.join(list1)
												# Write virtual server elements 
												write_element(bigip, file, searchPath + "/" + vsName, iteration + 1)
												write_sep(file)


	if not isWritten:
		write_json(file, jelement)
	#write_sep(file)
	### add sub elements behind the main element, since it depends on it:
	if sub != "":
		#write_sep(file)
		file.write(sub)
	

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
        print "\t\t Example: /mgmt/ltm/pool/poolname"
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

write_element(bigip, f, ePath, 0)

f.close()

