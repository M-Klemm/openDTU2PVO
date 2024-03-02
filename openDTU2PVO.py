#!/usr/bin/python3
# =============================================================================================================
#
# @file     openDTU2PVO.py
# @author   Matthias Klemm <Matthias_Klemm@gmx.net>
# @version  1.1.0
# @Python   >= 3.2 required
# @date     February, 2024
#
#
# @section  LICENSE
#
# Copyright (C) 2024, Matthias Klemm. All rights reserved.
#
# GNU GENERAL PUBLIC LICENSE
# Version 3, 29 June 2007
#
#
# @brief    A script to gather data from an OpenDTU device and upload it to www.pvoutput.org.
#           Provide OpenDTU IP address, inverter serial number, pvoutput API key and pvoutput system id in the config file.


import configparser
import ipaddress
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests


def isValidString(s):
    return bool(isinstance(s, str) and s and not s.isspace())


os.chdir(os.path.dirname(sys.argv[0]))

# handle config file
configParser = configparser.RawConfigParser()
configFilePath = Path(os.getcwd())
configFilePath = configFilePath.joinpath('config.cfg')
if not configFilePath.is_file():
    print('Config file not found at: ' + str(configFilePath))
    sys.exit(1)
configParser.read(configFilePath)
allowedLogLevels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
cfgLogLevel = configParser.get('general', 'log_level')
if not isValidString(cfgLogLevel) or not (cfgLogLevel.upper()) in allowedLogLevels:
    configParser.set('general', 'log_level', 'ERROR')
# check optional pvoutput.org parameters

# prepare log file
logPath = Path(configParser.get('general', 'log_path'))
if not logPath.is_dir():
    logPath = Path(os.getcwd())
logging.basicConfig(filename=logPath.joinpath('openDTU2PVO.log'), filemode='a',
                    level=getattr(logging, configParser.get('general', 'log_level')),
                    format='%(asctime)s - %(levelname)s: %(message)s')
openDTU_ip = configParser.get('openDTU', 'ip')
# check if ip address is valid
try:
    ipaddress.ip_address(openDTU_ip)
# check ip address
except Exception as err:
    logging.error('IP address: \'%s\' is not valid', str(openDTU_ip))
    print('IP address: \'' + str(openDTU_ip) + '\' is not valid.')
    sys.exit(1)

DTUData = {}
totalPower = 0
totalEnergy = 0
allDataTooOldFlag = True
nInv = len(configParser.options('openDTU'))
for invNumber in range(1, nInv, 1):
    try:
        openDTU_sn = int(configParser.get('openDTU', 'serial_number' + str(invNumber)))
    except Exception as err:
        if invNumber == 1:
            # try old config file format
            try:
                openDTU_sn = int(configParser.get('openDTU', 'sn'))
            except Exception as err2:
                logging.error('Could not find serial_number1 in openDTU section of config.cfg')
                print('Could not find serial_number1 in openDTU section of config.cfg')
                sys.exit(1)
        else:
            # the requested serial_number does not exist in config.cfg
            continue
    # read current pv data from the openDTU
    currentValues = ''
    maxRetries = 10
    requestStr = "http://" + openDTU_ip + "/api/livedata/status?inv=" + str(openDTU_sn)
    for retryCounter in range(1, maxRetries, 1):
        logging.debug('openDTU communication try #%d', retryCounter)
        response = requests.get(requestStr)
        logging.debug("Sent request to openDTU: %s", requestStr)
        if response.status_code != 200:
            # request was not successful -> wait a bit and retry
            logging.warning("Could not get data from openDTU: %s", response.text)
            time.sleep(10)
            continue
        else:
            currentValues = json.loads(response.content)
            break
    # sanity check
    if not currentValues:
        # something went wrong -> nothing to do ->exit
        logging.error("Failed to receive data from openDTU device")
        print("Failed to receive data from openDTU device")
        continue
    if 'inverters' not in currentValues:
        # no inverter data found
        tmpStr = "Could not get data from an inverter " + str(invNumber) + "- skipping..."
        logging.error(tmpStr)
        print(tmpStr)
        continue
    if len(currentValues['inverters']) == 0:
        # no inverter data found
        tmpStr = "Could not get data from inverter - exiting..."
        logging.error(tmpStr)
        print(tmpStr)
        continue
    invData = currentValues['inverters'][0]
    if 'data_age' in invData:
        allDataTooOldFlag = allDataTooOldFlag and (invData['data_age'] > 60)
    if 'AC' not in invData:
        # no AC data from inverter
        tmpStr = "Received no AC data from inverter - exiting..."
        logging.warning(tmpStr)
        print(tmpStr)
        continue
    if 'DC' not in invData:
        # no DC data from inverter
        tmpStr = "Received no DC data from inverter - exiting..."
        logging.warning(tmpStr)
        print(tmpStr)
        continue
    if 'INV' not in invData:
        # no INV data from inverter
        tmpStr = "Received no INV data from inverter - exiting..."
        logging.warning(tmpStr)
        print(tmpStr)
        continue
    # sanity checks passed
    DTUData['serial_number' + str(invNumber)] = invData
    totalPower += invData['AC']['0']['Power']['v']
    if invData['AC']['0']['Power']['v'] > 0:
        # the daily energy counter is reset, once power is fed into the grid
        # -> if power is still zero, the energy yield is from yesterday -> ignore it
        totalEnergy += invData['INV']['0']['YieldDay']['v']

if not DTUData:
    sys.exit(1)
if allDataTooOldFlag:
    # data from all inverters too old
    tmpStr = "Data from inverter all inverters older than 60 seconds"
    logging.warning(tmpStr)
    print(tmpStr)
    sys.exit(1)

# upload data to pvoutput.org
now = datetime.now()  # current date and time
uploadStr = configParser.get('pvoutput', 'pvo_single_url') + configParser.get('pvoutput', 'pvo_apikey') + "&sid=" + configParser.get('pvoutput', 'pvo_systemid') + "&d=" + str(now.strftime("%Y%m%d")) + "&t=" + str(
    now.strftime("%H:%M")) + "&c1=0" + "&v1=" + str(int(totalEnergy)) + "&v2=" + str(totalPower)
# handle optional pvoutput.org parameters
if bool(configParser.get('pvoutput', 'pvo_upload_temperature')) and 'serial_number1' in DTUData:
    uploadStr = uploadStr + "&v5=" + str(DTUData['serial_number1']['INV']['0']['Temperature']['v'])
if bool(configParser.get('pvoutput', 'pvo_upload_voltage'))  and 'serial_number1' in DTUData:
    uploadStr = uploadStr + "&v6=" + str(DTUData['serial_number1']['AC']['0']['Voltage']['v'])
for i in range(7, 13, 1):
    tmp = configParser.get('pvoutput', 'pvo_v' + str(i))
    if isValidString(tmp):
        try:
            tmp = tmp.split('.')
            uploadStr = uploadStr + "&v" + str(i) + "=" + str(int(DTUData[tmp[0]][tmp[1]][tmp[2]][tmp[3]]['v']))
        except Exception as err:
            logging.warning("Optional pvoutput parameter pvo_v%d failed: %s", i, err)
            continue
r = requests.get(uploadStr)
if r.status_code != 200:
    logging.error('Uploader to pvoutput.org failed: %s', r.text)
    print('Uploader to pvoutput.org failed: ', r.text)
