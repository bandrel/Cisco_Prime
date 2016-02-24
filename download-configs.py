#/usr/bin/env python
import requests
import json
import base64

with open('config.json') as data_file:
    config = json.load(data_file)

username = config['username']
password = config['password']
sanitized = config['sanitized']
maxResults = config['maxResults']
prime_url = config['prime_url']
verbose = config['verbose']

encoded_username_password = base64.encodestring(username + ':' + password).rstrip()

s = requests.session()
s.headers.update({'Authorization':'Basic ' + encoded_username_password})
s.headers._store.pop('connection')

first_device = 0
config_info = []
fileid_running = ''
if sanitized:
    config_url = '/webacs/api/v1/op/configArchiveService/extractSanitizedFile.json?fileId='
else:
    config_url = '/webacs/api/v1/op/configArchiveService/extractUnsanitizedFile.json?fileId='
get_devices_url = prime_url + '/webacs/api/v1/data/ConfigVersions.json'

for x in range(maxResults):
    filter_options = '?.full=true&.firstResult='+str(first_device)+'&.maxResults='+str(maxResults)
    get_devices_response = s.get(get_devices_url + filter_options,verify=False)
    first_device = first_device + maxResults
    get_devices_json = get_devices_response.json()
    for y in range(len(get_devices_json[u'queryResponse'][u'entity'])):
        try:
            if get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'][0].values()[0] == u'RUNNINGCONFIG':
                fileid_running = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'][0].values()[2]
                devicename = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'deviceName']
                print '[*] Creating '+devicename+'.txt'
                with open(devicename+'.txt','w') as outputfile:
                    if fileid_running is not "":
                        url = prime_url + config_url + str(fileid_running)
                        get_config_response = s.get(url,verify=False)
                        get_config_json = get_config_response.json()
                        outputfile.write(get_config_json[u'mgmtResponse'][u'extractFileResult'][u'fileData'])
        except KeyError:
            if get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'].values()[0] == u'RUNNINGCONFIG':
                fileid_running = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'].values()[2]
                devicename = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'deviceName']
                if verbose:
                    print '[*] Creating '+devicename+'.txt'
                with open(devicename+'.txt','w') as outputfile:
                    if fileid_running is not "":
                        url = prime_url + config_url + str(fileid_running)
                        get_config_response = s.get(url,verify=False)
                        get_config_json = get_config_response.json()
                        outputfile.write(get_config_json[u'mgmtResponse'][u'extractFileResult'][u'fileData'])


