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
MAX_FILE_SIZE = 100000
MAX_PATCH_PROPERTIES = 2

def clean_path(path):
        list = path.split('localhost')
        list = list[1].split('?')
        return list[0]

def create_element_list():
	list = {}
	for el in restStructure.OBJECT_TYPE:
		eList = restStructure.OBJECT_TYPE[el]
		keyList = eList.keys()
		for item in keyList:
			list[item] = []
	return list

def erase_element_list(list):
        for item in list:
		del item[:]

def print_element_list(list):
	print "\nDeployed elements:"
	for type in list:
	        if len(list[type]) > 0:
        	        print "type: %s (%s)" % ( type,  len(list[type]))
        	for element in list[type]:
                	print element

def path2type(path):
	s='/'
	#print "Path: %s" % path
	list = path.split(s)
	#print "Path join: %s" % s.join(list[:4])
	typeList = restStructure.OBJECT_TYPE.get(s.join(list[:4]))
	if typeList != None:
		sList = sorted(typeList.iteritems(), key=lambda (k,v): (v,k), reverse=True)
		for key, value in sList:
			#print "key: %s value: %s" % (key, value)
			pstart = value
			if pstart[-1] == '*':
				pstart = pstart [:-1]
			if path.startswith(pstart):
				return key
	return None

def add_element(elements, path, fpath):
        type = path2type(path)
        if type != None:
		#print "Found Type: %s" % type
		elements[type].append(fpath)
 

def exists_element(elements, path, fpath):
	#print "function exists_element path -%s-" % path 
        type = path2type(path)
	if type != None:
		try:
			elements[type].index(fpath)
			return True
		except ValueError:
			return False

def exists_element2(elements, type, fpath):
        if type != None:
                try:
                        elements[type].index(fpath)
                        return True
                except ValueError:
                        return False


## Remove some elements not needed for creation
def remove_elements(data):
	if data.get('selfLink'):
		del data['selfLink']
	if data.get('generation'):
		del data['generation']
        if data.get('state'):
                del data['state']
        if data.get('session'):
                del data['session']
        if data.get('appService'):
                del data['appService']

def adapt_subPath(jdata, appName, draft):
	if appName != "":
		if draft:
			jdata['subPath'] = appName + ".app/Drafts" 
		else:
			jdata['subPath'] = appName + ".app"
		#print "Add iApp %s" % jdata['subPath']
	elif draft:
		jdata['subPath'] = appName + "Drafts"
                #print "Add iApp %s" % jdata['subPath']
	elif jdata.get('subPath') != None:
		del jdata['subPath']

# check if the Element can be moved into iApp or Partition
def is_element_moveable(jdata):
        kind = jdata.get('kind')
        if kind != None:
                element = restStructure.KIND_TO_OBJECT.get(kind)
                if element != None:
                        if element[3] != None and not element[3]:
                                return False
        return True

# check if the Element has to be deployed first as draft like a policy
def is_element_draft(jdata):
        kind = jdata.get('kind')
        if kind != None:
                element = restStructure.KIND_TO_OBJECT.get(kind)
                if element != None:
			#print "### DRAFT ### %s" % element[1]
			list = element[1].split(' ')
			if len(list) == 3 and list[1] == 'draft':
				res =  float(BIGIP_VERSION['number']) >= float(list[2])
                        	#print "Draft len: %s str: %s" % (len(list), list[1])
                        	#print "BIG-IP version: %s str: %s res: %s" % ( BIGIP_VERSION['number'], list[2], res)
				return res
        return False


def get_path(jdata, appName, partition):
	## Gets the path information out of the selfLink.
	## Partitions and application names will be placed in
	selfLink = jdata.get('selfLink')
	fullPath = jdata.get('fullPath')
	pos = selfLink.find('//');
	start = selfLink.find('/', pos + 2)
	end = selfLink.find('?')
        if fullPath != None:
		## If fullPath exist, the last element in the selfLink need to be removed
		end = selfLink.rfind('/', start, end)
		## If fullPath exist, the partition need to be set
		if is_element_moveable(jdata):
			if partition != "":
				jdata['partition'] = partition

	s1 = '/'
	parts1 = selfLink[start:end].split(s1)
	if parts1[-1] == 'members' or parts1[-1] == 'profiles':
		s2 = '~'
		if s2 in parts1[-2]:
			parts2 = parts1[-2].split(s2)
	                if partition != "":
				parts2[1] = partition
		else:
			if  partition != "": 	p = partition
			else:			p = "Common"
			parts2 = [ '', p, parts1[-2] ]

		if len(parts2) > 3:
			if appName != "":
                       		parts2[2] = appName + ".app"
			else:
				del parts2[2]
		elif appName != "":
			parts2.insert(2, appName + ".app")

		parts1[-2] = s2.join(parts2)
		return s1.join(parts1)			

	return selfLink[start:end]


### Remove:
def get_fpath_from_element(jdata, name):
	appName = jdata.get('subPath')
	partition = jdata.get('partition')

	if partition != None:
		res = "/" + partition
	else:
		res = "/Common"

	if appName != None:
		res = res + "/" + appName + ".app"

	return res + "/" + name

def rewrite_reference_path( elements, type, fPath, appName, partition):

        if exists_element2(elements, type, fPath):
                # This path need to be adapted
                #print "------Path hit for fPath: %s" % fPath
                s1 = '/'
                if fPath.find(s1) < 0:
                        fPath = "/Common/" + fPath
                parts1 = fPath.split(s1)
                if partition != "":
                        parts1[1] = partition
                if len(parts1) > 3:
                        if appName != "":
				parts1[2] = appName + ".app"
			else:
				del parts1[2]
		elif appName != "":
                        	parts1.insert(2, appName + ".app")
                fPath = s1.join(parts1)
                #val = val[:pos+1] + name + ".app" + val[pos:]
		#print "------New fPath: %s" % fPath
                return fPath
        else:
                #print "Not created -> Type: %s fPath: %s" % (type, fPath)
                return ""

def rewrite_reference_element( jdata, elements, type, fPath, appName, partition):

        if exists_element2(elements, type, fPath):
                # This path need to be adapted
                #print "------Path hit for fPath: %s" % fPath

		if partition != "":
			jdata['partition'] = partition
		else:
			del jdata['partition']

                if appName != "":
                        jdata['subPath'] = appName + ".app"
                else:
                        del jdata['subPath']

        #else:
        #        print "Not created -> Type: %s fPath: %s" % (type, fPath)



def adapt_reference_path(jdata, elements, appName, partition):
	## Check if it is a reference to an element, which was deployed in this json blob.
	## If this is the case, the Partition and the iApp-Path must be adapted in the path
	#print "Adapt reference path:"

	kind = jdata.get('kind')
	if kind != None: ## The element has sub elements where we need to adapt the path towards the elements.
		#print "Kind: %s" % kind
		refList = restStructure.REFERENCE_KIND_LIST.get(kind);
		if refList != None:
			#############################work#######################	
			for item in refList:
				ref = refList.get(item)
				type = ref[0]
				if ref[1].find("direct") == 0 and ref[3]:
					#print "Item to get fPath: %s" % item
					fPath = jdata.get(item)
					if fPath != None:
                                                #START - Check for sub elements
                                                subList = ref[1].split('-')
                                                if len(subList) == 2:
                                                        name = fPath.get(subList[1])
                                                        if name != None:
                                                                fPath = name
                                               	#END - Check for sub elements
						
						res = rewrite_reference_path(elements, type, fPath, appName, partition)
						if res != "":
							if len(subList) == 2:
								jdata[item][subList[1]] = res
								
							else:
								jdata[item] = res

				elif ref[1].find('items') == 0:
			                if jdata.get(item) != None and jdata[item].get('items'):
                        			for element in jdata[item]['items']:
							fPath = element.get('fullPath')
							if fPath != None:
								res = rewrite_reference_path(elements, type, fPath, appName, partition)
								if res != "":
									element['fullPath'] = res
									if partition != "":
										element['partition'] = partition
									if ref[3]: # Only moveable elements put into apps:
										# Set draft flag for policy
										adapt_subPath(element, appName, False)

                                elif ref[1].find('list') == 0:
                                        #print "Item to get fPath: %s" % item
                                        list = jdata.get(item)
                                        if list != None:
						l = len(list)
						for i in range( 0, l ):
		                                        #START - Check for sub elements
		                                        subList = ref[1].split('-')
		                                        if len(subList) == 2: # A list of structured properties
		                                                subName = list[i].get(subList[1])
		                                                if subName != None:
									fPath = get_fpath_from_element(list[i], subName)
									rewrite_reference_element( list[i], elements, type, fPath, appName, partition)
                                                        #END - Check for sub elements
 

							else: # A simple list like of properties
								fPath = list[i]
								fPath = shared.add_CommonToName(fPath)
								res = rewrite_reference_path(elements, type, fPath, appName, partition)
								list[i] = res



                                elif ref[1] == "and":
                                        #print "Item to get fPath: %s" % item
                                        fPath = jdata.get(item)
                                        if fPath != None:
						s = ' and '
						r = []
						monList = fPath.split(' ')
						for mon in monList:
							if mon != "" and mon != "and":
								res = rewrite_reference_path(elements, type, mon, appName, partition)
								#print "Mon : %s" % res
								if res != "": 	r.append(res) #use new Path
								else: 		r.append(mon) #keep old Path
						jdata[item] = s.join(r)


def create_element(bigip, jdata, path):
	Method = "POST"
	fullPath = jdata.get('fullPath')
	command =  jdata.get('command') # command need to be POST
	methods = jdata.get('methods')
	if fullPath == None and command == None: # This are always existing static elements or PATCH requests
		#print "Number of properties in JSON object: %s" % len(jdata)
		if len(jdata) <= MAX_PATCH_PROPERTIES: # We need just to change this property in the JSON object
			if BIGIP_VERSION['digits'][0] != 11: # PATCH is needed
				response = bigip.patch('%s%s' % (BIGIP_URL_BASE, path), data=json.dumps(jdata))
				Method = "PATCH"
			else: # In version 11 PUT is needed
				response = bigip.put('%s%s' % (BIGIP_URL_BASE, path), data=json.dumps(jdata))
				Method = "PUT"
		else:
			response = bigip.put('%s%s' % (BIGIP_URL_BASE, path), data=json.dumps(jdata))
			Method = "PUT"
	elif methods != None:
		# Element has been deployed already and should be redeployed.
		del jdata['methods']
		if methods == 'put':
                	response = bigip.put('%s%s' % (BIGIP_URL_BASE, path + "/" + jdata.get('name')), data=json.dumps(jdata))
			Method = "PUT"
                elif methods == 'patch':
                        response = bigip.patch('%s%s' % (BIGIP_URL_BASE, path + "/" + jdata.get('name')), data=json.dumps(jdata))
			Method = "PATCH"

	else:
                response = bigip.post('%s%s' % (BIGIP_URL_BASE, path), data=json.dumps(jdata))

        if response.status_code == 401:
		exit("Authentication failed!")
	elif response.status_code != 200:
                print "Response: %s" % response.content
		print "%s: %s" % ( Method, path)
		print "Content:"
                print json.dumps(jdata, sort_keys = True, indent = 4, separators=(',', ': '))	
                return False
	else:
		if fullPath == None:
			fullPath = ""
		else:
			fullPath = "/" + fullPath.split('/')[-1]
		if Method == 'POST':
			action = 'Created '
		else:
			action = 'Modified'
		print "%s: %s%s" % (action, path, fullPath)

        return True

def create_iApp(bigip, name, partition):
	## iApps are not working together with transactions. Therefore we need to clean up here
	if bigip.headers.get('X-F5-REST-Coordination-Id') != None:
		del bigip.headers['X-F5-REST-Coordination-Id']
	if partition != "":
		str = "\"partition\": \"" + partition + "\","
	else:
		str = ""
	content =  "{\"name\": \"" + name + "\"," + str + "\"template\": \"\"}"
	#print "content: %s" % content
	#print '%s/mgmt/tm/sys/application/service' % BIGIP_URL_BASE
	response = bigip.post('%s/mgmt/tm/sys/application/service' % BIGIP_URL_BASE, data=content)
        if response.status_code != 200:
                print "Response: %s" % response.content
                return False
	else:
		print "Created : iApp %s" % name
        return True

def create_transaction(bigip):
        print "Create Transaction"
        content =  "{}"
        response = bigip.post('%s/mgmt/tm/transaction' % BIGIP_URL_BASE, data=content)
        #print "Response: %s" % response.content
	if response.status_code == 200:
		jdata=json.loads(response.content)
		transID = jdata.get('transId')
		if transID != None:
			bigip.headers.update({'X-F5-REST-Coordination-Id' : str(transID) })
			return transID
	
	return -1

def commit_transaction(bigip, transID):
	print "Commit Transaction"
        ## For the commit the transaction header need to be removed
        if bigip.headers.get('X-F5-REST-Coordination-Id') != None:
                del bigip.headers['X-F5-REST-Coordination-Id']
	content = "{\"state\":\"VALIDATING\"}"
	response = bigip.patch('%s/mgmt/tm/transaction/%s' % (BIGIP_URL_BASE, transID), content)
        if response.status_code != 200:
		print "Response: %s" % response.content
		return False
	return True

def replace_parameters(item, parameters):
	for param in parameters:
                item = item.replace(param, parameters[param] )
	return item

################
##### MAIN #####
################

# Parse Parameter
ex = False
if len(sys.argv) == 3:
        source = sys.argv[1]
        sourceList = source.split('@')
        ex = len(sourceList) != 2
        filename = sys.argv[2]

else:
        ex = True

if ex:
        print "Usage: %s <username>@f5-mgmt-ip <jb_filename>" % (sys.argv[0])
        sys.exit()

username = sourceList[0]
bigipAddr = sourceList[1]
BIGIP_URL_BASE = 'https://%s' % bigipAddr

# Get Password
passwd = getpass.getpass("Pasword for " + source + ":")

# HTTPS resource for BIG-IP to send out all rest requests
bigip = requests.session()
bigip.auth = (username, passwd)
bigip.verify = False
bigip.headers.update({'Content-Type' : 'application/json'})


BIGIP_VERSION = shared.get_version(bigip, BIGIP_URL_BASE) 

# Open json blob file
f = open ( filename, 'r')
sts = f.read(100000)

# Default Partition
partition = ""

# No Trans ID
transID = -1

# No iApp
iApp = ""


items = sts.split('\n\n')

elements = create_element_list()

parameters = {}
for item in items:
	if len(item) < 10:
		continue
	jdata = {}
	try:
		if parameters != None:
			jdata = json.loads(replace_parameters(item, parameters))
		else:
        		jdata = json.loads(item)
	except ValueError:
		print "Json parser Error"
		print item
		#continue
	if jdata.get('kind') == 'jb-header':
		print "Found jb-header!"
		# If transaction is open, we should finalize it now before we start a new json blob
		if transID >= 0:
			commit_transaction(bigip, transID)
			transID = -1

		#erase_element_list(elements)
		elements = create_element_list()

		if jdata.get('partition') != None and jdata.get('partition') != "":
			partition = jdata.get('partition').encode('utf8', 'replace')
		elif jdata.get('application') != None and jdata.get('application') != "":
			partition = "Common"
		else:
			partition = ""

		if jdata.get('application') != None and jdata.get('application') != "":
			iApp = jdata['application'].encode('utf8', 'replace')
			create_iApp(bigip, iApp, partition)

                if jdata.get('transaction') != None and jdata.get('transaction') == "true":
			transID = create_transaction(bigip)

		parameters = jdata.get('parameters')

	else:
		path = get_path(jdata, iApp, partition)
       		#print "path: ", path
        	remove_elements(jdata)
                if jdata.get('fullPath') != None:
			fPath = jdata['fullPath']
			fPath = shared.add_CommonToName(fPath)
			#print "fPath-> %s" % fPath
			if exists_element(elements, path, fPath):
				# The element was already deployed.
				# Therefore we need to deploy it via PUT.
				#print "Found Element." 
				jdata['methods'] = "put"
			else:
				# The element is new and need to be added to the list:
				#print "Element is not in list."
				add_element(elements, path, fPath)

		if partition != "":
			adapt_reference_path(jdata, elements, iApp, partition)

		if is_element_moveable(jdata):
			adapt_subPath(jdata, iApp, is_element_draft(jdata))

	        create_element(bigip, jdata, path)

		# Draft elements need to be published. Needed for policies since v12.1
		if is_element_draft(jdata) and ( jdata.get('status') == None or jdata.get('status') == "published" ):
			partition = jdata.get('partition')
			if partition == None:
				partition = "Common"
			subPath = jdata.get('subPath')
			name = jdata.get('name')
			#print " --- -- Draft: %s" % "/" + partition + "/" + subPath + "/" + name
			jd = {"command": "publish"}
			jd['name'] = "/" + partition + "/" + subPath + "/" + name
			create_element(bigip, jd, path)


if transID >= 0:
	commit_transaction(bigip, transID)

#print_element_list(elements)

