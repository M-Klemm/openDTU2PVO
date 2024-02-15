# OpenDTU to pvoutput.org
Small utility to read data from an OpenDTU device and upload it to pvoutput.org.
Fill in the necessary info in the config file before running the script.
Only a single inverter is supported at the moment. If you have multiple inverters or multiple OpenDTUs,
copy this script and its (modified) config file to a different folder for each inverter / OpenDTU. 
Optionally, additional parameters, such as e.g. inverter temperature, voltage / current / power of each string, can also be uploaded.

The script will try up to 10 times to connect to the OpenDTU device and obtain valid data.

*OpenDTU: https://github.com/tbnobody/OpenDTU

OpenDTU 24.2.12 or later is required.
Python 3.2 or later is required to run the script.
Use cron (linux) or the task scheduler (Windows) to run the script every 5 minutes 


# Required python modules
To run, the script requires the following python modules:
```
requests
```

# Configuration
Edit the config.cfg and enter the following data:
```
[general]
log_path=                       # path to log file (without file name), if empty, the current folder is used
log_level=ERROR                 # possible log levels: 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'
                                # there are no 'CRITICAL' errors defined -> 'CRITICAL' will result in an empty log file
[openDTU]
ip=X.X.X.X                      # OpenDTU IP address
sn=XXXXXXXXXX                   # inverter serial number

[pvoutput]
pvo_apikey=XXXXXXXXXX           # API key from pvoutput.org
pvo_systemid=XXXX               # ID of the system to upload to
pvo_upload_temperature=true     # if true, upload inverter temperature 
pvo_upload_voltage=true         # if true, upload line voltage
pvo_v7=DC.0.Power               # optional parameter
pvo_v8=DC.1.Power               # optional parameter
pvo_v9=DC.0.Voltage             # optional parameter
pvo_v10=DC.0.Voltage            # optional parameter
pvo_v11=DC.0.YieldDay           # optional parameter
pvo_v12=DC.1.YieldDay           # optional parameter
pvo_single_url=https://pvoutput.org/service/r2/addstatus.jsp?key=       # do NOT edit
```

# Run
```
python3 openDTU2PVO.py  or ./openDTU2PVO.py
```
There is no output, unless an error occurs. Errors may be also written to the log file.

# Contribution
You're welcome to send me errors or ideas for improvement.
Please fork your own project if you want to rewrite or/add change something yourself.