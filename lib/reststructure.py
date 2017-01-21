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

LTM_ELEMENT_TYPE = {    'member':	'/mgmt/tm/ltm/pool/',
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


NET_ELEMENT_TYPE = {    'vlan':		'/mgmt/tm/net/vlan',
                        'self':		'/mgmt/tm/net/self',
                        'route-domain': '/mgmt/tm/net/route-domain',
                        'route': 	'/mgmt/tm/net/route',
 			'rateClass':	'/mgmt/tm/net/rate-shaping/class',
			'rest':		'/'
                 }

AUTH_ELEMENT_TYPE = { 	'partition':	'/mgmt/tm/auth/partition',
			'rest':		'/'
                 }

ELEMENT_TYPE = {        '/mgmt/tm/net': NET_ELEMENT_TYPE,
                        '/mgmt/tm/ltm': LTM_ELEMENT_TYPE,
                        '/mgmt/tm/auth': AUTH_ELEMENT_TYPE
                }

####################################################################
### This elements are needed to find related elements in get2jb.py
### and to adapt the reference paths in sendjb.py
### If you use any iApp or Partition adaptations, the path will be
### only adapted properly, if all used element types are listed below

## item: [ type, How to get the fullPath info]
## ItemName: [type, how to parse, relevant path list, Movable ]
## - 'sub' means the sub path of the ItemName. 
## - Movable is False, if the element is only allowed to be used in
##   the Common partition and in no iApps. Example: rateClass
 
REFERENCE_TYPE_LIST_POOL = {	'monitor': ['monitor', 'and', LTM_ELEMENT_TYPE, True],
				'pool': ['members', 'sub', LTM_ELEMENT_TYPE, True] 
                        }

REFERENCE_TYPE_LIST_VIRTUAL = { 'pool':                 	['pool', 'direct', LTM_ELEMENT_TYPE, True],
                                'rules':    			['rules', 'list', LTM_ELEMENT_TYPE, True],
                                'profilesReference':    	['profile', 'items', LTM_ELEMENT_TYPE, True],
				'policiesReference':    	['policy', 'items draft 12.1', LTM_ELEMENT_TYPE, True],
                                'persist':			['persist', 'list-name', LTM_ELEMENT_TYPE, True],
				'fallbackPersistence':		['persist', 'direct', LTM_ELEMENT_TYPE, True],
                                'sourceAddressTranslation':	['snatpool', 'direct-pool', LTM_ELEMENT_TYPE, True],
				'rateClass':			['rateClass', 'direct', NET_ELEMENT_TYPE, False]
                        }

REFERENCE_TYPE_LIST_VIRTUAL_ADDRESS = {    'virtual': ['virtual', 'address', LTM_ELEMENT_TYPE, True]
                        		}


REFERENCE_KIND_LIST = {	'tm:ltm:virtual-address:virtual-addressstate': REFERENCE_TYPE_LIST_VIRTUAL_ADDRESS,
			'tm:ltm:virtual:virtualstate': REFERENCE_TYPE_LIST_VIRTUAL,
                        'tm:ltm:pool:poolstate' : REFERENCE_TYPE_LIST_POOL
                        }


KIND_TO_ELEMENT = {
			'tm:net:rate-shaping:class:classstate':	REFERENCE_TYPE_LIST_VIRTUAL['rateClass'],
			'tm:ltm:policy:policystate': REFERENCE_TYPE_LIST_VIRTUAL['policiesReference']
			}

####################################################################
### getjb.py:
### List of all elements which need to be collected via expandSubcollections

EXPAND_SUBCOLLECTION_LIST = { 	'/mgmt/tm/ltm/virtual/',
				'/mgmt/tm/ltm/policy'
				}


