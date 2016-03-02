##Collection of scripts that utilize the Cisco Prime Infrastructure APIs. 
* download-configs.py - Used to download configurations that are stored within Prime Infrastucture 3.x+. 

###download-configs.py
####Instructions
Rename config.json.example to config.json and edit the fields to meet your deployment.

The username and password fields are optional CLI arguments.
The username and passwords can also be presented in the config.json file.  CLI arguments override the config file, but in order to be 
prompted for a username or password the corresponding field needs to be removed from the config file.  

The config files will be saved as hostname.txt in the working directory of the script.  

The username and password must have NBI Read access for sanitized configs and NBI Write access for unsanitized configs.
See https://developer.cisco.com/site/prime-infrastructure/documents/api-reference/rest-api-v3-0/ for more information


```
Usage: download-configs.py [Options]
       -h or --help:  This help screen
       -u or --username: specifies a username to use (optional)
       -p or --password: Specifies the password to use (optional)
       -c or --config: Specifies an alternate config file (defaults to config.json)
       -d or --device: Specify hostname of single device to download config file for
       -f or --file: Specify a file which contains one or more hostnames to download a config file for
```
