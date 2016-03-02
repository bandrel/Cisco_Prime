#/usr/bin/env python
'''
Script to download all running configs from a Cisco Prime 3.0 instance.

Instructions:  Rename config.json.example to config.json and edit the fields to meet your deployment.

The username and password must have NBI Read access for sanitized configs and NBI Write access for unsanitized configs.
See https://developer.cisco.com/site/prime-infrastructure/documents/api-reference/rest-api-v3-0/ for more information

'''
import requests
import json
import base64
import sys
import getopt
import re
import getpass

def helpmsg():
    print >> sys.stderr, 'Usage: download-configs.py [Options]>' \
          '  -h or --help:  This help screen\n' \
          '  -u or --username: specifies a username to use\n' \
          '  -p or --password: Specifies the password to use\n' \
          '  -c or --config: Specifies an alternate config file (defaults to config.json)\n'\
          '  -d or --device: Specify hostname of single device to download config file for\n'\
          '  -f or --file: Specify a file which contains one or more hostnames to download config file for\n'

config_file = 'config.json'
username = ''
password = ''
verbose = ''
hostnames = []
try:
    opts, args = getopt.getopt(sys.argv[1:],"u:p:c:hvd:f:",["input=", "user=", "password=", "config=","help","verbose",
                                                        "device=","file="])
except getopt.GetoptError:
    helpmsg()
    sys.exit(2)
for opt, arg in opts:
    if opt in ('-h', '--help'):
        helpmsg()
        sys.exit()
    elif opt in ('-c', '--config'):
        config_file = True
    elif opt in ('-v', '--verbose'):
        verbose = True
    elif opt in ('-u', '--user'):
        username = arg
    elif opt in ('-p', '--password'):
        password = arg
    elif opt in ('-d', '--device'):
        hostnames.append(arg.upper().rstrip())
    elif opt in ('-f', '--file'):
        try:
            with open(arg) as input_file:
                for host in input_file:
                    hostnames.append(host.upper().rstrip())
        except:
            helpmsg()
            sys.exit(2)

#Parse config.json for configuration data
with open(config_file) as data_file:
    config = json.load(data_file)

if username is '':
    try:
        username = config['username']
    except:
        username = raw_input('Enter Username:')
if password is '':
    try:
        password = config['password']
    except:
        password = getpass.getpass('Enter password:')
sanitized = bool(config['sanitized'])
maxResults = config['maxResults']
prime_url = config['prime_url']
if verbose is '':
    verbose = config['verbose']
#base64 encode the username and password combination for the HTTP authentication
encoded_username_password = base64.encodestring(username + ':' + password).rstrip()

#setup request session and add appropriate authentication headers
s = requests.session()
s.headers.update({'Authorization':'Basic ' + encoded_username_password})
s.headers._store.pop('connection')

first_device = 0
fileid_running = ''
total_device_count = 0
#set base url depending on if requesting santized configs
if sanitized is True:
    config_url = '/webacs/api/v1/op/configArchiveService/extractSanitizedFile.json?fileId='
else:
    config_url = '/webacs/api/v1/op/configArchiveService/extractUnsanitizedFile.json?fileId='
#set base url for the inital gathering of device IDs
get_devices_url = prime_url + '/webacs/api/v1/data/ConfigVersions.json'
get_devices_response = s.get(get_devices_url,verify=False)
if get_devices_response.status_code == 401:
    print >> sys.stderr,'[!] Invalid username or password'
    sys.exit(2)
elif get_devices_response.status_code == 403:
        print >> sys.stderr,'[!] Username does not have the correct level of authorization'
        sys.exit(2)
get_devices_json = get_devices_response.json()
total_device_count = int(get_devices_json[u'queryResponse'][u'@count'])

total_paging_iterations = total_device_count / int(maxResults)
if total_device_count % int(maxResults) > 0:
    total_paging_iterations += total_paging_iterations

#iterate through the all of the devices using the max results as the paging number
def get_all():
    global first_device
    for x in range(total_paging_iterations):
        filter_options = '?.full=true&.firstResult='+str(first_device)+'&.maxResults='+str(maxResults)
        #initiate request using for device IDs and using filtering for paging the max number of devices at a time.
        get_devices_response = s.get(get_devices_url + filter_options,verify=False)
        first_device = first_device + maxResults
        #parse response as json object
        get_devices_json = get_devices_response.json()
        #iterate through json object to collect all of the fileIDs of the configurations
        for y in range(len(get_devices_json[u'queryResponse'][u'entity'])):
            try:
                if get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'][0].values()[0] == u'RUNNINGCONFIG':
                    fileid_running = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'][0].values()[2]
                    devicename = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'deviceName']
                    if re.search(r'[\()]',devicename):
                        re.sub(r'[\()]','_',devicename)
                    with open(devicename+'.txt','w') as outputfile:
                        if fileid_running is not "":
                            url = prime_url + config_url + str(fileid_running)
                            get_config_response = s.get(url,verify=False)
                            if get_config_response.status_code == 403:
                                print >> sys.stderr,'[!] Username does not have the correct level of authorization'
                                sys.exit(2)
                            get_config_json = get_config_response.json()
                            if verbose:
                                print '[*] Creating '+devicename+'.txt'
                            outputfile.write(get_config_json[u'mgmtResponse'][u'extractFileResult'][u'fileData'])
            except KeyError:
                if get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'].values()[0] == u'RUNNINGCONFIG':
                    fileid_running = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'].values()[2]
                    devicename = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'deviceName']
                    if re.search(r'[\()]',devicename):
                        re.sub(r'[\()]','_',devicename)
                    with open(devicename+'.txt','w') as outputfile:
                        if fileid_running is not "":
                            url = prime_url + config_url + str(fileid_running)
                            get_config_response = s.get(url,verify=False)
                            if get_config_response.status_code == 403:
                                print >> sys.stderr,'[!] Username does not have the correct level of authorization'
                                sys.exit(2)
                            get_config_json = get_config_response.json()
                            if verbose:
                                print '[*] Creating '+devicename+'.txt'
                            outputfile.write(get_config_json[u'mgmtResponse'][u'extractFileResult'][u'fileData'])
def get_select():
    global first_device
    global hostnames
    while True:
        for x in range(total_paging_iterations):
            filter_options = '?.full=true&.firstResult='+str(first_device)+'&.maxResults='+str(maxResults)
            #initiate request using for device IDs and using filtering for paging the max number of devices at a time.
            get_devices_response = s.get(get_devices_url + filter_options,verify=False)
            first_device = first_device + maxResults
            #parse response as json object
            get_devices_json = get_devices_response.json()
            try:
                len(get_devices_json[u'queryResponse'][u'entity'])
            except:
                return
            #iterate through json object to collect all of the fileIDs of the configurations
            for y in range(len(get_devices_json[u'queryResponse'][u'entity'])):
                try:
                    if get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'][0].values()[0] == u'RUNNINGCONFIG':
                        fileid_running = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'][0].values()[2]
                        devicename = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'deviceName']
                        if re.search(r'[\()]',devicename):
                            re.sub(r'[\()]','_',devicename)
                        if devicename.upper().split('.')[0] in hostnames:
                            with open(devicename+'.txt','w') as outputfile:
                                if fileid_running is not "":
                                    url = prime_url + config_url + str(fileid_running)
                                    get_config_response = s.get(url,verify=False)
                                    if get_config_response.status_code == 403:
                                        print >> sys.stderr,'[!] Username does not have the correct level of authorization'
                                        sys.exit(2)
                                    get_config_json = get_config_response.json()
                                    if verbose:
                                        print '[*] Creating '+devicename+'.txt'
                                    outputfile.write(get_config_json[u'mgmtResponse'][u'extractFileResult'][u'fileData'])
                                    hostnames.remove(devicename.upper().split('.')[0])
                except KeyError:
                    if get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'].values()[0] == u'RUNNINGCONFIG':
                        fileid_running = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'fileInfos'][u'fileInfo'].values()[2]
                        devicename = get_devices_json[u'queryResponse'][u'entity'][y][u'configVersionsDTO'][u'deviceName']
                        if devicename.upper().split('.')[0] in hostnames:
                            with open(devicename+'.txt','w') as outputfile:
                                if fileid_running is not "":
                                    url = prime_url + config_url + str(fileid_running)
                                    get_config_response = s.get(url,verify=False)
                                    if get_config_response.status_code == 403:
                                        print >> sys.stderr,'[!] Username does not have the correct level of authorization'
                                        sys.exit(2)
                                    get_config_json = get_config_response.json()
                                    if verbose:
                                        print '[*] Creating '+devicename+'.txt'
                                    outputfile.write(get_config_json[u'mgmtResponse'][u'extractFileResult'][u'fileData'])
                                    hostnames.remove(devicename.upper().split('.')[0])
                finally:
                    if len(hostnames) == 0:
                        return


if len(hostnames) == 0:
    get_all()
else:
    get_select()
