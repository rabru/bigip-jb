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
### sendjb.py:
### This elements are needed to classify the different configuration
### types to avoid name collisions for the list creation.

LTM_OBJECT_TYPE = {    'member':	'/mgmt/tm/ltm/pool/',
                        'pool':		'/mgmt/tm/ltm/pool',
                        'monitor':	'/mgmt/tm/ltm/monitor/*',
                        'virtual':	'/mgmt/tm/ltm/virtual',
			'rules':	'/mgmt/tm/ltm/rule',
                        'profile':	'/mgmt/tm/ltm/profile/*',
			'policy': 	'/mgmt/tm/ltm/policy',
			'persist':	'/mgmt/tm/ltm/persistence/*',
			'snatpool':     '/mgmt/tm/ltm/snatpool',
			'virtual':	'/mgmt/tm/ltm/virtual',
			'rest':		'/'
                 }


NET_OBJECT_TYPE = {    'vlan':		'/mgmt/tm/net/vlan',
                        'self':		'/mgmt/tm/net/self',
                        'route-domain': '/mgmt/tm/net/route-domain',
                        'route': 	'/mgmt/tm/net/route',
 			'rateClass':	'/mgmt/tm/net/rate-shaping/class',
			'rest':		'/'
                 }

AUTH_OBJECT_TYPE = { 	'partition':	'/mgmt/tm/auth/partition',
			'rest':		'/'
                 }

OBJECT_TYPE = {        '/mgmt/tm/net': NET_OBJECT_TYPE,
                        '/mgmt/tm/ltm': LTM_OBJECT_TYPE,
                        '/mgmt/tm/auth': AUTH_OBJECT_TYPE
                }

### REFERENCE TYPE LIST 
####################################################################
### This elements are needed to find related elements in get2jb.py
### and to adapt the reference paths in sendjb.py
### If you use any iApp or Partition adaptations, the path will be
### only adapted properly, if all used element types are listed below

## Structure: 
## ItemName: [type, how to parse, relevant path list, Movable, expected properties ]
## - 'sub' means the sub path of the ItemName. 
## - Movable is False, if the object is only allowed to be used in
##   the Common partition and in no iApps. Example: rateClass
## - expected properties will keep a list of properties, which need to be present. Otherwise it will be skiped.
##   This is implemented to skip default profiles which do not have the defaultsFrom property
 
REFERENCE_TYPE_LIST_POOL = {	'monitor': ['monitor', 'and', LTM_OBJECT_TYPE, True, ['defaultsFrom']],
				'pool': ['members', 'sub', LTM_OBJECT_TYPE, True, []] 
                        }

REFERENCE_TYPE_LIST_VIRTUAL = { 'pool':                 	['pool', 'direct', LTM_OBJECT_TYPE, True, []],
                                'rules':    			['rules', 'list', LTM_OBJECT_TYPE, True, []],
                                'profilesReference':    	['profile', 'items', LTM_OBJECT_TYPE, True, ['defaultsFrom']],
				'policiesReference':    	['policy', 'items draft 12.1', LTM_OBJECT_TYPE, True, []],
                                'persist':			['persist', 'list-name', LTM_OBJECT_TYPE, True, ['defaultsFrom']],
				'fallbackPersistence':		['persist', 'direct', LTM_OBJECT_TYPE, True, ['defaultsFrom']],
                                'sourceAddressTranslation':	['snatpool', 'direct-pool', LTM_OBJECT_TYPE, True, []],
				'rateClass':			['rateClass', 'direct', NET_OBJECT_TYPE, False, []]
                        }

REFERENCE_TYPE_LIST_VIRTUAL_ADDRESS = {    'virtual': ['virtual', 'address', LTM_OBJECT_TYPE, True, []]
                        		}

### KIND POINTER
####################################################################

REFERENCE_KIND_LIST = {	'tm:ltm:virtual-address:virtual-addressstate': REFERENCE_TYPE_LIST_VIRTUAL_ADDRESS,
			'tm:ltm:virtual:virtualstate': REFERENCE_TYPE_LIST_VIRTUAL,
                        'tm:ltm:pool:poolstate' : REFERENCE_TYPE_LIST_POOL
                        }


KIND_TO_OBJECT = {
			'tm:net:rate-shaping:class:classstate':	REFERENCE_TYPE_LIST_VIRTUAL['rateClass'],
			'tm:ltm:policy:policystate': REFERENCE_TYPE_LIST_VIRTUAL['policiesReference']
			}

####################################################################
### getjb.py:
### List of all elements which need to be collected via expandSubcollections

EXPAND_SUBCOLLECTION_LIST = { 	'/mgmt/tm/ltm/virtual/',
				'/mgmt/tm/ltm/policy',
				'/mgmt/tm/net/vlan',
				'/mgmt/tm/sys/application/template'
				}


