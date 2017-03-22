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

####################################################################
### Functions for getjb.py and sendjb.py

import json


def add_CommonToName(name):
        if name.find('/') < 0:
                name = "/Common/" + name
        #print "Name + Common: %s" % name
        return name

def nameToPath(name):
        s1='/'
        s2='~'
        list = name.split(s1)
        return s2.join(list)

def get_version(bigip, basePath):
	version = { 'digit': [0, 0, 0], 'string': '', 'number': 0.0, 'product': ''}
        response = bigip.get(basePath + '/mgmt/tm/sys/version')
	#print "Response: %s" % response.status_code
        if response.status_code != 200:
                return version
	jcontent = json.loads(response.content)
	buf = jcontent.get('entries')
	buf_v11_5 = jcontent.get('apiRawValues')
	if buf != None:
		buf = buf.get('https://localhost/mgmt/tm/sys/version/0')
		if buf != None:
			buf = buf.get('nestedStats')
			if buf != None:
				buf = buf.get('entries')
				if buf != None:
                                	buf1 = buf.get('Version')
		                        if buf1 != None:
                		                buf1 = buf1.get('description')
						if buf1 != None:
							version['digits'] = buf1.split('.')
							if len(version['digits']) == 3:
								version['string'] = buf1
								version['number'] = float(version['digits'][0]) + float(version['digits'][1]) * 0.1 + float(version['digits'][2]) * 0.001
					buf1 = buf.get('Product')
                                        if buf1 != None:
                                                buf1 = buf1.get('description')
                                                if buf1 != None:
                                                        version['product'] = buf1
	# Get Version for v11.5.x
	elif buf_v11_5 != None:
		buf_v11_5 = buf_v11_5.get('apiAnonymous')
		if buf_v11_5 != None:
			list = buf_v11_5.split('\n')
			for line in list:
				if line.find('  Product') == 0:
					version['product'] = line[11:]
				elif line.find('  Version') == 0:
					version['string'] = line[11:]
					version['digits'] = version['string'].split('.')
					version['number'] = float(version['digits'][0]) + float(version['digits'][1]) * 0.1 + float(version['digits'][2]) * 0.001
						

	print "Host %s: %s v%s" % ( basePath.split('//')[1], version['product'], version['string'] )
        return version


def get_pathFromJson(jdata):
	
        selfLink = jdata.get('selfLink')
	if selfLink != None:
        	pos = selfLink.find('//');
        	start = selfLink.find('/', pos + 2)
        	end = selfLink.find('?')
		return selfLink[start:end]
	else:
		return ""



