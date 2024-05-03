import paho.mqtt.client as mqtt
from datetime import datetime
import json
import pymysql
from threading import Timer
import matplotlib.pyplot as plt
import csv
import numpy as np
import tensorflow as tf
import os
import csv
import json


"""
Description: This script has been designed to collect, process and store the data from the Treon IoT sensors.

Setting up: 1. Create MSQL database and insert the database details in the parameters
            2. Create the following tables in the database:
                a. treon_vibration_raw_data_1 (data_time, message)
                b. treon_vibration_test_data (Date_time, Sensor_id, Temperature, Battery_voltage, X_P2P, X_RMS, X_Z2P, X_Kurtosis, Y_P2P, Y_RMS, Y_Z2P, Y_Kurtosis, Z_P2P, Z_RMS, Z_Z2P, Z_Kurtosis, FFT_X, FFT_Y, FFT_Z)
                c. treon_vibration_test_fft_data (Sensor_id, Datetime, FFT_dictionary)
            3. Create an MQQT server account on https://www.emqx.io/ 
            4. Enter the account details on the Main function
            
Author: Luca Garagnani, Machinemonitor            
Modified by: Group 3,UNSW
"""

########################################################################################################################
#PARAMATERS

#Database - MYSLQ - INSERT DATABASE DETAILS
MYSQL_Host = "localhost"
MYSQL_User = "root"
MYSQL_Password = "#Tej@s@2610"
MYSQL_Database = "machine_monitor"


#message number - do not change
num= 0
#Change BC and Set as needed, keep the set number the number you want-1
set=0
BC=0



#FUNCTION

# loop the software every 10 second
def loop():
    #to loop the code and verify continuosly the new data - time interval of only 10 seconds
    t2 = Timer(interval=10, function=Main)
    t2.start()

# to increase the number of message
def counter():
    global num
    num +=1
    return num

#Connection success callback - create the connection to the MQQT server in the right folder
def on_connect(client, userdata, flags, rc):
    print('Connected with result code '+str(rc))
    client.subscribe('treon/devices/8fdeec5a/#')

# Message receiving callback - To save the messages into the database
def on_message(client, userdata, msg):

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    print(msg.topic + " " + str(msg.payload))

    message = msg.payload

    #verify if there are multiple posts or one single
    message_number = counter()

    #upload raw data to the data base
    # connect to database
    sqlCon = pymysql.connect(host="{}".format(MYSQL_Host),
                                 user="{}".format(MYSQL_User),
                                 password="{}".format(MYSQL_Password),
                                 database="{}".format(MYSQL_Database))
    cursor = sqlCon.cursor()


    print("Message number: {}".format(message_number))




    raw_data = [now, message]

    #to insert raw data into a temporary table within the database
    mysql_treon_raw_data_script = """INSERT INTO machine_monitor.treon_vibration_raw_data_1 (data_time, message) VALUES(%s,%s)"""

    cursor.execute(mysql_treon_raw_data_script, raw_data)

    sqlCon.commit()
    sqlCon.close()

#Raw data verification - to verify that only complete raw data set are processed
def split_function():
    # possible to verify lenght of raw data table and based on that process the data or cancel it
    sqlCon = pymysql.connect(host="{}".format(MYSQL_Host),
                                 user="{}".format(MYSQL_User),
                                 password="{}".format(MYSQL_Password),
                                 database="{}".format(MYSQL_Database))
    cursor = sqlCon.cursor()

    cursor.execute("SELECT * FROM machine_monitor.treon_vibration_raw_data_1")
    resultssaved =cursor.fetchall()
    print(len(resultssaved))



    if len(resultssaved)<=83 or len(resultssaved) >84:
        print("Dataset Error")
        cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_test_fft_data WHERE Datetime>0")
        cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_test_data WHERE Date_time>0")
        cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_raw_data_1 WHERE data_time>0")
    elif len(resultssaved) == 84:
        print('Done')
        global set
        set=set+1
        data_processing()
    
    

    #set the timer at the acquistion interval - about 1 hour - important to be done as soon as finished
    t1 = Timer(interval=300, function=split_function)
    t1.start()
    sqlCon.commit()
    sqlCon.close()

def data_processing():
    print('Data Processing')
    sqlCon = pymysql.connect(host="{}".format(MYSQL_Host),
                                    user="{}".format(MYSQL_User),
                                    password="{}".format(MYSQL_Password),
                                    database="{}".format(MYSQL_Database))
    cursor = sqlCon.cursor()

    cursor.execute("SELECT * FROM machine_monitor.treon_vibration_raw_data_1")
    records = cursor.fetchall()

    # create raw data list
    raw_data_list = [i[:][1] for i in records]
    global set
    set_num=set
    global BC

    folder_name=f'SET{set_num}_BC{BC}'
    print(folder_name)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    # convert bytes to string
    raw_data_string_list = [str(i[:]).replace("\x00", "") for i in raw_data_list]
    #print(raw_data_string_list)
    raw_data_dictionary_list = [json.loads(i) for i in raw_data_string_list]



    # organise the data by sensors
    # run through all the dictionaries and separate the list based on the Sensor node ID
    sensor_1_raw_data_list = []
    sensor_2_raw_data_list = []
    index = 0
    SensorID = raw_data_dictionary_list[index]["SensorNodeId"]

    while index < len(raw_data_dictionary_list):
        if raw_data_dictionary_list[index]["SensorNodeId"] == SensorID:
            sensor_1_raw_data_list.insert(index, raw_data_dictionary_list[index])
        if raw_data_dictionary_list[index]["SensorNodeId"] != SensorID:
            sensor_2_raw_data_list.insert(index, raw_data_dictionary_list[index])
        index += 1
        if index > len(raw_data_dictionary_list):
            break


    # sensor #1

    data_sensor_1_dict = {}

    try:

        data_sensor_1_dict["Datetime"] = datetime.fromtimestamp(sensor_1_raw_data_list[0]["Timestamp"])
        data_sensor_1_dict["Temperature"] = sensor_1_raw_data_list[0]["Temperature"]
        data_sensor_1_dict["BatteryVoltage"] = sensor_1_raw_data_list[0]["BatteryVoltage"]
        data_sensor_1_dict["SensorNodeId"] = sensor_1_raw_data_list[0]["SensorNodeId"]
        # X
        data_sensor_1_dict["X_RMS"] = sensor_1_raw_data_list[1]["Vibration"]["RMS"]["X"] / 100
        data_sensor_1_dict["X_P2P"] = sensor_1_raw_data_list[1]["Vibration"]["P2P"]["X"]
        data_sensor_1_dict["X_Kurtosis"] = sensor_1_raw_data_list[1]["Vibration"]["Kurtosis"]["X"] / 100
        data_sensor_1_dict["X_Z2P"] = sensor_1_raw_data_list[1]["Vibration"]["Z2P"]["X"]
        # Y
        data_sensor_1_dict["Y_RMS"] = sensor_1_raw_data_list[15]["Vibration"]["RMS"]["Y"] / 100
        data_sensor_1_dict["Y_P2P"] = sensor_1_raw_data_list[15]["Vibration"]["P2P"]["Y"]
        data_sensor_1_dict["Y_Kurtosis"] = sensor_1_raw_data_list[15]["Vibration"]["Kurtosis"]["Y"] / 100
        data_sensor_1_dict["Y_Z2P"] = sensor_1_raw_data_list[15]["Vibration"]["Z2P"]["Y"]
        # Z
        data_sensor_1_dict["Z_RMS"] = sensor_1_raw_data_list[29]["Vibration"]["RMS"]["Z"] / 100
        data_sensor_1_dict["Z_P2P"] = sensor_1_raw_data_list[29]["Vibration"]["P2P"]["Z"]
        data_sensor_1_dict["Z_Kurtosis"] = sensor_1_raw_data_list[29]["Vibration"]["Kurtosis"]["Z"] / 100
        data_sensor_1_dict["Z_Z2P"] = sensor_1_raw_data_list[29]["Vibration"]["Z2P"]["Z"]

    except KeyError:
        data_sensor_1_dict["Datetime"] = datetime.fromtimestamp(sensor_1_raw_data_list[0]["Timestamp"])
        data_sensor_1_dict["Temperature"] = sensor_1_raw_data_list[0]["Temperature"]
        data_sensor_1_dict["BatteryVoltage"] = None
        data_sensor_1_dict["SensorNodeId"] = sensor_1_raw_data_list[0]["SensorNodeId"]
        # X
        data_sensor_1_dict["X_RMS"] = sensor_1_raw_data_list[0]["Vibration"]["RMS"]["X"] / 100
        data_sensor_1_dict["X_P2P"] = sensor_1_raw_data_list[0]["Vibration"]["P2P"]["X"]
        data_sensor_1_dict["X_Kurtosis"] = sensor_1_raw_data_list[0]["Vibration"]["Kurtosis"]["X"] / 100
        data_sensor_1_dict["X_Z2P"] = sensor_1_raw_data_list[0]["Vibration"]["Z2P"]["X"]
        # Y
        data_sensor_1_dict["Y_RMS"] = sensor_1_raw_data_list[14]["Vibration"]["RMS"]["Y"] / 100
        data_sensor_1_dict["Y_P2P"] = sensor_1_raw_data_list[14]["Vibration"]["P2P"]["Y"]
        data_sensor_1_dict["Y_Kurtosis"] = sensor_1_raw_data_list[14]["Vibration"]["Kurtosis"]["Y"] / 100
        data_sensor_1_dict["Y_Z2P"] = sensor_1_raw_data_list[14]["Vibration"]["Z2P"]["Y"]
        # Z
        data_sensor_1_dict["Z_RMS"] = sensor_1_raw_data_list[28]["Vibration"]["RMS"]["Z"] / 100
        data_sensor_1_dict["Z_P2P"] = sensor_1_raw_data_list[28]["Vibration"]["P2P"]["Z"]
        data_sensor_1_dict["Z_Kurtosis"] = sensor_1_raw_data_list[28]["Vibration"]["Kurtosis"]["Z"] / 100
        data_sensor_1_dict["Z_Z2P"] = sensor_1_raw_data_list[28]["Vibration"]["Z2P"]["Z"]

    FFT_sensor_1_dict = {}
    ########################## X   ############################################################
    # axes X

    FFT_sensor_1_dict_x = {}
    FFT_sensor_1_list_x = []

    FragCount = 0
    while FragCount <= 10:

        first_windwos = sensor_1_raw_data_list[FragCount + 2]['Values']


        # print(first_windwos)

        # convert to hex and process the data as per the uncropession procedure
        nbits = 16
        # conversion formula for negative numbers
        # hex = '{:04X}'.format(val & ((1 << nbits)-1)).replace('FF', '0x')

        first_windwos_elaborated = []

        # hex_nox = str(hex(first_windwos[1])).removeprefix("0x")
        # print(hex_nox)
        index = 2
        iteration = 0
        # evaluate the first valu

        if first_windwos[0] >= 0:
            coefficient_0_part2 = str(hex(first_windwos[0])).removeprefix("0x")

        if first_windwos[0] < 0:
            coefficient_0_part2 = '{:04X}'.format(first_windwos[0] & ((1 << nbits) - 1)).removeprefix("FF")

        if first_windwos[1] >= 0:
            coefficient_0_part1 = hex(first_windwos[1])

        if first_windwos[1] < 0:
            coefficient_0_part1 = '{:04X}'.format(first_windwos[1] & ((1 << nbits) - 1)).replace('FF', '0x')

        coefficient_0 = coefficient_0_part1 + coefficient_0_part2

        first_windwos_elaborated.insert(iteration, int(coefficient_0, 16))
        while index < len(first_windwos):
            # print(first_windwos_elaborated)
            # print (index)
            # print(iteration)
            # print(first_windwos[index])
            if index == 2:
                if first_windwos[index] == int(-128):
                    index += 2
                    iteration += 1
                    # print(index)
                    # print(iteration)

                if first_windwos[index] != int(-128) and index != 4:
                    # sum the int to the previous int combined value
                    cefficient_n = first_windwos_elaborated[0] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, cefficient_n)
                    # print(index, cefficient_n)
            if index > 2:
                # print(first_windwos[index] == int(-128))
                if first_windwos[index] == int(-128):
                    # indicate that the next two values have to be calculated as combined hex
                    index += 2
                    iteration += 1
                    print(index)
                    print(iteration)
                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index-1] != int(-128) and first_windwos[index-2] != int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 1] != int(-128) and first_windwos[
                    index - 2] != int(-128) and index != 4:
                    # sum the int to the previous coefficient value
                    coefficient_n = first_windwos_elaborated[-1] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128):
                    # calculate coeffiecietn
                    if first_windwos[index - 1] >= 0:
                        coefficient_n_part2 = str(hex(first_windwos[index - 1])).removeprefix("0x")

                    if first_windwos[index - 1] < 0:
                        coefficient_n_part2 = '{:04X}'.format(
                            first_windwos[index - 1] & ((1 << nbits) - 1)).removeprefix("FF")

                    if first_windwos[index] >= 0:
                        coefficient_n_part1 = hex(first_windwos[index])

                    if first_windwos[index] < 0:
                        coefficient_n_part1 = '{:04X}'.format(first_windwos[index] & ((1 << nbits) - 1)).replace('FF',
                                                                                                                    '0x')

                    coefficient_n_hex = coefficient_n_part1 + coefficient_n_part2
                    # print(first_windwos[index], hex(abs(first_windwos[index])))
                    # print(first_windwos[index-1],hex(first_windwos[index-1]))
                    # print(coefficient_n_hex)
                    coefficient_n = int(coefficient_n_hex, 16)
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

            index += 1
            iteration += 1
            if index > len(first_windwos):
                break

        # print(first_windwos_elaborated)

        first_windwos_elaborated_revalued = [item / 100 for item in first_windwos_elaborated]

        # print(first_windwos_elaborated_revalued)

        # add to the list of fraction as extended list
        FragCount += 1
        # FFT_sensor_1_list_x_test.insert(FragCount, first_windwos_elaborated_revalued)
        FFT_sensor_1_list_x.extend(first_windwos_elaborated_revalued)
        # print(len(FFT_sensor_1_list_x))

        if FragCount > 10:
            break

    FFT_sensor_1_dict_x["FFT_X"] = FFT_sensor_1_list_x

    # print(FFT_sensor_1_dict_x)

    ######################    Y     #####################################################

    # axes Y

    FFT_sensor_1_dict_y = {}
    FFT_sensor_1_list_y = []

    FragCount = 0
    while FragCount <= 10:
        #print(FragCount)
        #print(sensor_1_raw_data_list[FragCount + 16])
        first_windwos = sensor_1_raw_data_list[FragCount + 16]["Values"]
        # print(first_windwos)

        # convert to hex and process the data as per the uncropession procedure
        nbits = 16
        # conversion formula for negative numbers
        # hex = '{:04X}'.format(val & ((1 << nbits)-1)).replace('FF', '0x')

        first_windwos_elaborated = []

        # hex_nox = str(hex(first_windwos[1])).removeprefix("0x")
        # print(hex_nox)
        index = 2
        iteration = 0
        # evaluate the first valu

        if first_windwos[0] >= 0:
            coefficient_0_part2 = str(hex(first_windwos[0])).removeprefix("0x")

        if first_windwos[0] < 0:
            coefficient_0_part2 = '{:04X}'.format(first_windwos[0] & ((1 << nbits) - 1)).removeprefix("FF")

        if first_windwos[1] >= 0:
            coefficient_0_part1 = hex(first_windwos[1])

        if first_windwos[1] < 0:
            coefficient_0_part1 = '{:04X}'.format(first_windwos[1] & ((1 << nbits) - 1)).replace('FF', '0x')

        coefficient_0 = coefficient_0_part1 + coefficient_0_part2

        first_windwos_elaborated.insert(iteration, int(coefficient_0, 16))
        while index < len(first_windwos):
            # print(first_windwos_elaborated)
            # print (index)
            # print(iteration)
            # print(first_windwos[index])
            if index == 2:
                if first_windwos[index] == int(-128):
                    index += 2
                    iteration += 1
                    # print(index)
                    # print(iteration)

                if first_windwos[index] != int(-128) and index != 4:
                    # sum the int to the previous int combined value
                    cefficient_n = first_windwos_elaborated[0] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, cefficient_n)
                    # print(index, cefficient_n)
            if index > 2:
                # print(first_windwos[index] == int(-128))
                if first_windwos[index] == int(-128):
                    # indicate that the next two values have to be calculated as combined hex
                    index += 2
                    iteration += 1
                    print(index)
                    print(iteration)
                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index-1] != int(-128) and first_windwos[index-2] != int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 1] != int(-128) and first_windwos[
                    index - 2] != int(-128) and index != 4:
                    # sum the int to the previous coefficient value
                    coefficient_n = first_windwos_elaborated[-1] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128):
                    # calculate coeffiecietn
                    if first_windwos[index - 1] >= 0:
                        coefficient_n_part2 = str(hex(first_windwos[index - 1])).removeprefix("0x")

                    if first_windwos[index - 1] < 0:
                        coefficient_n_part2 = '{:04X}'.format(
                            first_windwos[index - 1] & ((1 << nbits) - 1)).removeprefix("FF")

                    if first_windwos[index] >= 0:
                        coefficient_n_part1 = hex(first_windwos[index])

                    if first_windwos[index] < 0:
                        coefficient_n_part1 = '{:04X}'.format(first_windwos[index] & ((1 << nbits) - 1)).replace('FF',
                                                                                                                    '0x')

                    coefficient_n_hex = coefficient_n_part1 + coefficient_n_part2
                    # print(first_windwos[index], hex(abs(first_windwos[index])))
                    # print(first_windwos[index-1],hex(first_windwos[index-1]))
                    # print(coefficient_n_hex)
                    coefficient_n = int(coefficient_n_hex, 16)
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

            index += 1
            iteration += 1
            if index > len(first_windwos):
                break

        # print(first_windwos_elaborated)

        first_windwos_elaborated_revalued = [item / 100 for item in first_windwos_elaborated]

        # print(first_windwos_elaborated_revalued)

        # add to the list of fraction as extended list
        FragCount += 1
        # FFT_sensor_1_list_x_test.insert(FragCount, first_windwos_elaborated_revalued)
        FFT_sensor_1_list_y.extend(first_windwos_elaborated_revalued)
        # print(len(FFT_sensor_1_list_x))

        if FragCount > 10:
            break

    FFT_sensor_1_dict_y["FFT_Y"] = FFT_sensor_1_list_y

    # print(FFT_sensor_1_dict_y)

    ######################    Z     #####################################################

    # axes Z

    FFT_sensor_1_dict_z = {}
    FFT_sensor_1_list_z = []

    FragCount = 0
    while FragCount <= 10:

        #print(FragCount)
        #print(sensor_1_raw_data_list[FragCount + 30])
        first_windwos = sensor_1_raw_data_list[FragCount + 30]["Values"]
        # print(first_windwos)

        # convert to hex and process the data as per the uncropession procedure
        nbits = 16
        # conversion formula for negative numbers
        # hex = '{:04X}'.format(val & ((1 << nbits)-1)).replace('FF', '0x')

        first_windwos_elaborated = []

        # hex_nox = str(hex(first_windwos[1])).removeprefix("0x")
        # print(hex_nox)
        index = 2
        iteration = 0
        # evaluate the first valu

        if first_windwos[0] >= 0:
            coefficient_0_part2 = str(hex(first_windwos[0])).removeprefix("0x")

        if first_windwos[0] < 0:
            coefficient_0_part2 = '{:04X}'.format(first_windwos[0] & ((1 << nbits) - 1)).removeprefix("FF")

        if first_windwos[1] >= 0:
            coefficient_0_part1 = hex(first_windwos[1])

        if first_windwos[1] < 0:
            coefficient_0_part1 = '{:04X}'.format(first_windwos[1] & ((1 << nbits) - 1)).replace('FF', '0x')

        coefficient_0 = coefficient_0_part1 + coefficient_0_part2

        first_windwos_elaborated.insert(iteration, int(coefficient_0, 16))
        while index < len(first_windwos):
            # print(first_windwos_elaborated)
            # print (index)
            # print(iteration)
            # print(first_windwos[index])
            if index == 2:
                if first_windwos[index] == int(-128):
                    index += 2
                    iteration += 1
                    # print(index)
                    # print(iteration)

                if first_windwos[index] != int(-128) and index != 4:
                    # sum the int to the previous int combined value
                    cefficient_n = first_windwos_elaborated[0] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, cefficient_n)
                    # print(index, cefficient_n)
            if index > 2:
                # print(first_windwos[index] == int(-128))
                if first_windwos[index] == int(-128):
                    # indicate that the next two values have to be calculated as combined hex
                    index += 2
                    iteration += 1
                    #print(index)
                    #print(iteration)
                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index-1] != int(-128) and first_windwos[index-2] != int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 1] != int(-128) and first_windwos[
                    index - 2] != int(-128) and index != 4:
                    # sum the int to the previous coefficient value
                    coefficient_n = first_windwos_elaborated[-1] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128):
                    # calculate coeffiecietn
                    if first_windwos[index - 1] >= 0:
                        coefficient_n_part2 = str(hex(first_windwos[index - 1])).removeprefix("0x")

                    if first_windwos[index - 1] < 0:
                        coefficient_n_part2 = '{:04X}'.format(
                            first_windwos[index - 1] & ((1 << nbits) - 1)).removeprefix("FF")

                    if first_windwos[index] >= 0:
                        coefficient_n_part1 = hex(first_windwos[index])

                    if first_windwos[index] < 0:
                        coefficient_n_part1 = '{:04X}'.format(first_windwos[index] & ((1 << nbits) - 1)).replace('FF',
                                                                                                                    '0x')

                    coefficient_n_hex = coefficient_n_part1 + coefficient_n_part2
                    # print(first_windwos[index], hex(abs(first_windwos[index])))
                    # print(first_windwos[index-1],hex(first_windwos[index-1]))
                    # print(coefficient_n_hex)
                    coefficient_n = int(coefficient_n_hex, 16)
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

            index += 1
            iteration += 1
            if index > len(first_windwos):
                break

        # print(first_windwos_elaborated)

        first_windwos_elaborated_revalued = [item / 100 for item in first_windwos_elaborated]

        # print(first_windwos_elaborated_revalued)

        # add to the list of fraction as extended list
        FragCount += 1
        # FFT_sensor_1_list_x_test.insert(FragCount, first_windwos_elaborated_revalued)
        FFT_sensor_1_list_z.extend(first_windwos_elaborated_revalued)
        # print(len(FFT_sensor_1_list_x))

        if FragCount > 10:
            break

    FFT_sensor_1_dict_z["FFT_Z"] = FFT_sensor_1_list_z

    # print(FFT_sensor_1_dict_z)

    # add the FFT dictionaries for each axes into the main dictionary

    FFT_sensor_1_dict["FFT_X"] = FFT_sensor_1_list_x
    FFT_sensor_1_dict["FFT_Y"] = FFT_sensor_1_list_y
    FFT_sensor_1_dict["FFT_Z"] = FFT_sensor_1_list_z

    # print(len(FFT_sensor_1_dict["FFT_Z"]))

    # for now only save as picture to reduce space on database

    frequency_value_list = []
    index = 0
    while index < 980:
        frequency_value_list.insert(index, index)
        index += 1
        if index > 980:
            break

    # x
    # clean the data if more than 980 are recorded in the FFT -- algorithm to be reviewed)

    if len(frequency_value_list) != len(FFT_sensor_1_list_x):
        if len(FFT_sensor_1_list_x) > len(frequency_value_list):
            index = 0
            while len(FFT_sensor_1_list_x) > len(frequency_value_list):
                FFT_sensor_1_list_x.pop(-1 + index)

                index += 1
                if len(FFT_sensor_1_list_x) == len(frequency_value_list):
                    break

    plt.bar(frequency_value_list, FFT_sensor_1_list_x, width=0.5, color='blue')
    # determina max value
    max_scale = max(FFT_sensor_1_list_x)

    # print(max_scale)
    plt.title('FFT')
    plt.ylabel('[mm/2]')
    plt.xlabel('Frequency [Hz]')
    plt.ylim([0, max_scale * 1.2])
    plt.xlim([-10, 300])
    plt.savefig(os.path.join(folder_name, 'FFT_X_sensor_1.jpg'))

    plt.close()


    # clean the data if more than 980 are recorded in the FFT -- algorithm to be reviewed)

    if len(frequency_value_list) != len(FFT_sensor_1_list_y):
        if len(FFT_sensor_1_list_y) > len(frequency_value_list):
            index = 0
            while len(FFT_sensor_1_list_y) > len(frequency_value_list):
                FFT_sensor_1_list_y.pop(-1 + index)

                index += 1
                if len(FFT_sensor_1_list_y) == len(frequency_value_list):
                    break

    plt.bar(frequency_value_list, FFT_sensor_1_list_y, width=0.5, color='blue')
    # # determina max value
    max_scale = max(FFT_sensor_1_list_y)

    # # print(max_scale)
    plt.title('FFT')
    plt.ylabel('[mm/2]')
    plt.xlabel('Frequency [Hz]')
    plt.ylim([0, max_scale * 1.2])
    plt.xlim([-10, 300])
    plt.savefig(os.path.join(folder_name,"FFT_Y_sensor_1.jpg"))
    plt.close()

    # z

    # clean the data if more than 980 are recorded in the FFT -- algorithm to be reviewed)

    if len(frequency_value_list) != len(FFT_sensor_1_list_z):
        if len(FFT_sensor_1_list_z) > len(frequency_value_list):
            index = 0
            while len(FFT_sensor_1_list_z) > len(frequency_value_list):
                FFT_sensor_1_list_z.pop(-1 + index)

                index += 1
                if len(FFT_sensor_1_list_z) == len(frequency_value_list):
                    break

    plt.bar(frequency_value_list, FFT_sensor_1_list_z, width=0.5, color='blue')
    # # determina max value
    max_scale = max(FFT_sensor_1_list_z)

    # # print(max_scale)
    plt.title('FFT')
    plt.ylabel('[mm/2]')
    plt.xlabel('Frequency [Hz]')
    plt.ylim([0, max_scale * 1.2])
    plt.xlim([-10, 300])
    plt.savefig(os.path.join(folder_name,"FFT_Z_sensor_1.jpg"))
    plt.close()

    # convert FFT dictionaty to JSon for export

    FFT_sensor_1_JSON = json.dumps(FFT_sensor_1_dict)

    ##########################################################3

    # sensor #2

    data_sensor_2_dict = {}

    try:
        data_sensor_2_dict["Datetime"] = datetime.fromtimestamp(sensor_2_raw_data_list[0]["Timestamp"])
        data_sensor_2_dict["Temperature"] = sensor_2_raw_data_list[0]["Temperature"]
        data_sensor_2_dict["BatteryVoltage"] = sensor_2_raw_data_list[0]["BatteryVoltage"]
        data_sensor_2_dict["SensorNodeId"] = sensor_2_raw_data_list[0]["SensorNodeId"]

        # X
        data_sensor_2_dict["X_RMS"] = sensor_2_raw_data_list[1]["Vibration"]["RMS"]["X"] / 100
        data_sensor_2_dict["X_P2P"] = sensor_2_raw_data_list[1]["Vibration"]["P2P"]["X"]
        data_sensor_2_dict["X_Kurtosis"] = sensor_2_raw_data_list[1]["Vibration"]["Kurtosis"]["X"] / 100
        data_sensor_2_dict["X_Z2P"] = sensor_2_raw_data_list[1]["Vibration"]["Z2P"]["X"]
        # Y
        data_sensor_2_dict["Y_RMS"] = sensor_2_raw_data_list[15]["Vibration"]["RMS"]["Y"] / 100
        data_sensor_2_dict["Y_P2P"] = sensor_2_raw_data_list[15]["Vibration"]["P2P"]["Y"]
        data_sensor_2_dict["Y_Kurtosis"] = sensor_2_raw_data_list[15]["Vibration"]["Kurtosis"]["Y"] / 100
        data_sensor_2_dict["Y_Z2P"] = sensor_2_raw_data_list[15]["Vibration"]["Z2P"]["Y"]
        # Z
        data_sensor_2_dict["Z_RMS"] = sensor_2_raw_data_list[29]["Vibration"]["RMS"]["Z"] / 100
        data_sensor_2_dict["Z_P2P"] = sensor_2_raw_data_list[29]["Vibration"]["P2P"]["Z"]
        data_sensor_2_dict["Z_Kurtosis"] = sensor_2_raw_data_list[29]["Vibration"]["Kurtosis"]["Z"] / 100
        data_sensor_2_dict["Z_Z2P"] = sensor_2_raw_data_list[29]["Vibration"]["Z2P"]["Z"]

    except KeyError:
        data_sensor_2_dict["Datetime"] = datetime.fromtimestamp(sensor_2_raw_data_list[0]["Timestamp"])
        data_sensor_2_dict["Temperature"] = sensor_2_raw_data_list[0]["Temperature"]
        data_sensor_2_dict["SensorNodeId"] = sensor_2_raw_data_list[0]["SensorNodeId"]
        data_sensor_2_dict["BatteryVoltage"] = None

        # X
        data_sensor_2_dict["X_RMS"] = sensor_2_raw_data_list[0]["Vibration"]["RMS"]["X"] / 100
        data_sensor_2_dict["X_P2P"] = sensor_2_raw_data_list[0]["Vibration"]["P2P"]["X"]
        data_sensor_2_dict["X_Kurtosis"] = sensor_2_raw_data_list[0]["Vibration"]["Kurtosis"]["X"] / 100
        data_sensor_2_dict["X_Z2P"] = sensor_2_raw_data_list[0]["Vibration"]["Z2P"]["X"]
        # Y
        data_sensor_2_dict["Y_RMS"] = sensor_2_raw_data_list[14]["Vibration"]["RMS"]["Y"] / 100
        data_sensor_2_dict["Y_P2P"] = sensor_2_raw_data_list[14]["Vibration"]["P2P"]["Y"]
        data_sensor_2_dict["Y_Kurtosis"] = sensor_2_raw_data_list[14]["Vibration"]["Kurtosis"]["Y"] / 100
        data_sensor_2_dict["Y_Z2P"] = sensor_2_raw_data_list[14]["Vibration"]["Z2P"]["Y"]
        # Z
        data_sensor_2_dict["Z_RMS"] = sensor_2_raw_data_list[28]["Vibration"]["RMS"]["Z"] / 100
        data_sensor_2_dict["Z_P2P"] = sensor_2_raw_data_list[28]["Vibration"]["P2P"]["Z"]
        data_sensor_2_dict["Z_Kurtosis"] = sensor_2_raw_data_list[28]["Vibration"]["Kurtosis"]["Z"] / 100
        data_sensor_2_dict["Z_Z2P"] = sensor_2_raw_data_list[28]["Vibration"]["Z2P"]["Z"]

    FFT_sensor_2_dict = {}

    ########################## X   ############################################################
    # axes X

    FFT_sensor_2_dict_x = {}
    FFT_sensor_2_list_x = []

    FragCount = 0
    while FragCount <= 10:
        #print(sensor_2_raw_data_list[FragCount + 2])
        first_windwos = sensor_2_raw_data_list[FragCount + 2]["Values"]
        #print(first_windwos)

        # convert to hex and process the data as per the uncropession procedure
        nbits = 16
        # conversion formula for negative numbers
        # hex = '{:04X}'.format(val & ((1 << nbits)-1)).replace('FF', '0x')

        first_windwos_elaborated = []

        # hex_nox = str(hex(first_windwos[1])).removeprefix("0x")
        # print(hex_nox)
        index = 2
        iteration = 0
        # evaluate the first valu

        if first_windwos[0] >= 0:
            coefficient_0_part2 = str(hex(first_windwos[0])).removeprefix("0x")

        if first_windwos[0] < 0:
            coefficient_0_part2 = '{:04X}'.format(first_windwos[0] & ((1 << nbits) - 1)).removeprefix("FF")

        if first_windwos[1] >= 0:
            coefficient_0_part1 = hex(first_windwos[1])

        if first_windwos[1] < 0:
            coefficient_0_part1 = '{:04X}'.format(first_windwos[1] & ((1 << nbits) - 1)).replace('FF', '0x')

        coefficient_0 = coefficient_0_part1 + coefficient_0_part2

        first_windwos_elaborated.insert(iteration, int(coefficient_0, 16))
        while index < len(first_windwos):
            # print(first_windwos_elaborated)
            # print (index)
            # print(iteration)
            # print(first_windwos[index])
            if index == 2:
                if first_windwos[index] == int(-128):
                    index += 2
                    iteration += 1
                    # print(index)
                    # print(iteration)

                if first_windwos[index] != int(-128) and index != 4:
                    # sum the int to the previous int combined value
                    cefficient_n = first_windwos_elaborated[0] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, cefficient_n)
                    # print(index, cefficient_n)
            if index > 2:
                # print(first_windwos[index] == int(-128))
                if first_windwos[index] == int(-128):
                    # indicate that the next two values have to be calculated as combined hex
                    index += 2
                    iteration += 1

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index-1] != int(-128) and first_windwos[index-2] != int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 1] != int(-128) and first_windwos[
                    index - 2] != int(-128) and index != 4:
                    # sum the int to the previous coefficient value
                    coefficient_n = first_windwos_elaborated[-1] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128):
                    # calculate coeffiecietn
                    if first_windwos[index - 1] >= 0:
                        coefficient_n_part2 = str(hex(first_windwos[index - 1])).removeprefix("0x")

                    if first_windwos[index - 1] < 0:
                        coefficient_n_part2 = '{:04X}'.format(
                            first_windwos[index - 1] & ((1 << nbits) - 1)).removeprefix("FF")

                    if first_windwos[index] >= 0:
                        coefficient_n_part1 = hex(first_windwos[index])

                    if first_windwos[index] < 0:
                        coefficient_n_part1 = '{:04X}'.format(first_windwos[index] & ((1 << nbits) - 1)).replace('FF',
                                                                                                                    '0x')

                    coefficient_n_hex = coefficient_n_part1 + coefficient_n_part2
                    # print(first_windwos[index], hex(abs(first_windwos[index])))
                    # print(first_windwos[index-1],hex(first_windwos[index-1]))
                    # print(coefficient_n_hex)
                    coefficient_n = int(coefficient_n_hex, 16)
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

            index += 1
            iteration += 1
            if index > len(first_windwos):
                break

        # print(first_windwos_elaborated)

        first_windwos_elaborated_revalued = [item / 100 for item in first_windwos_elaborated]

        # print(first_windwos_elaborated_revalued)

        # add to the list of fraction as extended list
        FragCount += 1
        # FFT_sensor_1_list_x_test.insert(FragCount, first_windwos_elaborated_revalued)
        FFT_sensor_2_list_x.extend(first_windwos_elaborated_revalued)
        # print(len(FFT_sensor_1_list_x))

        if FragCount > 10:
            break

    FFT_sensor_2_dict_x["FFT_X"] = FFT_sensor_2_list_x

    # print(FFT_sensor_1_dict_x)

    ######################    Y     #####################################################

    # axes Y

    FFT_sensor_2_dict_y = {}
    FFT_sensor_2_list_y = []

    FragCount = 0
    while FragCount <= 10:
        #print(sensor_2_raw_data_list[FragCount + 16])
        first_windwos = sensor_2_raw_data_list[FragCount + 16]["Values"]
        # print(first_windwos)

        # convert to hex and process the data as per the uncropession procedure
        nbits = 16
        # conversion formula for negative numbers
        # hex = '{:04X}'.format(val & ((1 << nbits)-1)).replace('FF', '0x')

        first_windwos_elaborated = []

        # hex_nox = str(hex(first_windwos[1])).removeprefix("0x")
        # print(hex_nox)
        index = 2
        iteration = 0
        # evaluate the first valu

        if first_windwos[0] >= 0:
            coefficient_0_part2 = str(hex(first_windwos[0])).removeprefix("0x")

        if first_windwos[0] < 0:
            coefficient_0_part2 = '{:04X}'.format(first_windwos[0] & ((1 << nbits) - 1)).removeprefix("FF")

        if first_windwos[1] >= 0:
            coefficient_0_part1 = hex(first_windwos[1])

        if first_windwos[1] < 0:
            coefficient_0_part1 = '{:04X}'.format(first_windwos[1] & ((1 << nbits) - 1)).replace('FF', '0x')

        coefficient_0 = coefficient_0_part1 + coefficient_0_part2

        first_windwos_elaborated.insert(iteration, int(coefficient_0, 16))
        while index < len(first_windwos):
            # print(first_windwos_elaborated)
            # print (index)
            # print(iteration)
            # print(first_windwos[index])
            if index == 2:
                if first_windwos[index] == int(-128):
                    index += 2
                    iteration += 1
                    # print(index)
                    # print(iteration)

                if first_windwos[index] != int(-128) and index != 4:
                    # sum the int to the previous int combined value
                    cefficient_n = first_windwos_elaborated[0] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, cefficient_n)
                    # print(index, cefficient_n)
            if index > 2:
                # print(first_windwos[index] == int(-128))
                if first_windwos[index] == int(-128):
                    # indicate that the next two values have to be calculated as combined hex
                    index += 2
                    iteration += 1

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index-1] != int(-128) and first_windwos[index-2] != int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 1] != int(-128) and first_windwos[
                    index - 2] != int(-128) and index != 4:
                    # sum the int to the previous coefficient value
                    coefficient_n = first_windwos_elaborated[-1] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128):
                    # calculate coeffiecietn
                    if first_windwos[index - 1] >= 0:
                        coefficient_n_part2 = str(hex(first_windwos[index - 1])).removeprefix("0x")

                    if first_windwos[index - 1] < 0:
                        coefficient_n_part2 = '{:04X}'.format(
                            first_windwos[index - 1] & ((1 << nbits) - 1)).removeprefix("FF")

                    if first_windwos[index] >= 0:
                        coefficient_n_part1 = hex(first_windwos[index])

                    if first_windwos[index] < 0:
                        coefficient_n_part1 = '{:04X}'.format(first_windwos[index] & ((1 << nbits) - 1)).replace('FF',
                                                                                                                    '0x')

                    coefficient_n_hex = coefficient_n_part1 + coefficient_n_part2
                    # print(first_windwos[index], hex(abs(first_windwos[index])))
                    # print(first_windwos[index-1],hex(first_windwos[index-1]))
                    # print(coefficient_n_hex)
                    coefficient_n = int(coefficient_n_hex, 16)
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

            index += 1
            iteration += 1
            if index > len(first_windwos):
                break

        # print(first_windwos_elaborated)

        first_windwos_elaborated_revalued = [item / 100 for item in first_windwos_elaborated]

        # print(first_windwos_elaborated_revalued)

        # add to the list of fraction as extended list
        FragCount += 1
        # FFT_sensor_1_list_x_test.insert(FragCount, first_windwos_elaborated_revalued)
        FFT_sensor_2_list_y.extend(first_windwos_elaborated_revalued)
        # print(len(FFT_sensor_1_list_x))

        if FragCount > 10:
            break

    FFT_sensor_2_dict_y["FFT_Y"] = FFT_sensor_2_list_y

    # print(FFT_sensor_1_dict_y)

    ######################    Z     #####################################################

    # axes Z

    FFT_sensor_2_dict_z = {}
    FFT_sensor_2_list_z = []

    FragCount = 0
    while FragCount <= 10:
        
        first_windwos = sensor_2_raw_data_list[FragCount + 30]["Values"]
        # print(first_windwos)

        # convert to hex and process the data as per the uncropession procedure
        nbits = 16
        # conversion formula for negative numbers
        # hex = '{:04X}'.format(val & ((1 << nbits)-1)).replace('FF', '0x')

        first_windwos_elaborated = []

        # hex_nox = str(hex(first_windwos[1])).removeprefix("0x")
        # print(hex_nox)
        index = 2
        iteration = 0
        # evaluate the first valu

        if first_windwos[0] >= 0:
            coefficient_0_part2 = str(hex(first_windwos[0])).removeprefix("0x")

        if first_windwos[0] < 0:
            coefficient_0_part2 = '{:04X}'.format(first_windwos[0] & ((1 << nbits) - 1)).removeprefix("FF")

        if first_windwos[1] >= 0:
            coefficient_0_part1 = hex(first_windwos[1])

        if first_windwos[1] < 0:
            coefficient_0_part1 = '{:04X}'.format(first_windwos[1] & ((1 << nbits) - 1)).replace('FF', '0x')

        coefficient_0 = coefficient_0_part1 + coefficient_0_part2

        first_windwos_elaborated.insert(iteration, int(coefficient_0, 16))
        while index < len(first_windwos):
            # print(first_windwos_elaborated)
            # print (index)
            # print(iteration)
            # print(first_windwos[index])
            if index == 2:
                if first_windwos[index] == int(-128):
                    index += 2
                    iteration += 1
                    # print(index)
                    # print(iteration)

                if first_windwos[index] != int(-128) and index != 4:
                    # sum the int to the previous int combined value
                    cefficient_n = first_windwos_elaborated[0] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, cefficient_n)
                    # print(index, cefficient_n)
            if index > 2:
                # print(first_windwos[index] == int(-128))
                if first_windwos[index] == int(-128):
                    # indicate that the next two values have to be calculated as combined hex
                    index += 2
                    iteration += 1
                    # print(index)
                    # print(iteration)
                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index-1] != int(-128) and first_windwos[index-2] != int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 1] != int(-128) and first_windwos[
                    index - 2] != int(-128) and index != 4:
                    # sum the int to the previous coefficient value
                    coefficient_n = first_windwos_elaborated[-1] + first_windwos[index]
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

                # if different from market and also the previous two values just add
                # print(first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128))
                if first_windwos[index] != int(-128) and first_windwos[index - 2] == int(-128):
                    # calculate coeffiecietn
                    if first_windwos[index - 1] >= 0:
                        coefficient_n_part2 = str(hex(first_windwos[index - 1])).removeprefix("0x")

                    if first_windwos[index - 1] < 0:
                        coefficient_n_part2 = '{:04X}'.format(
                            first_windwos[index - 1] & ((1 << nbits) - 1)).removeprefix("FF")

                    if first_windwos[index] >= 0:
                        coefficient_n_part1 = hex(first_windwos[index])

                    if first_windwos[index] < 0:
                        coefficient_n_part1 = '{:04X}'.format(first_windwos[index] & ((1 << nbits) - 1)).replace('FF',
                                                                                                                    '0x')

                    coefficient_n_hex = coefficient_n_part1 + coefficient_n_part2
                    # print(first_windwos[index], hex(abs(first_windwos[index])))
                    # print(first_windwos[index-1],hex(first_windwos[index-1]))
                    # print(coefficient_n_hex)
                    coefficient_n = int(coefficient_n_hex, 16)
                    first_windwos_elaborated.insert(iteration, coefficient_n)
                    # print(index, coefficient_n)

            index += 1
            iteration += 1
            if index > len(first_windwos):
                break

        # print(first_windwos_elaborated)

        first_windwos_elaborated_revalued = [item / 100 for item in first_windwos_elaborated]

        # print(first_windwos_elaborated_revalued)

        # add to the list of fraction as extended list
        FragCount += 1
        # FFT_sensor_1_list_x_test.insert(FragCount, first_windwos_elaborated_revalued)
        FFT_sensor_2_list_z.extend(first_windwos_elaborated_revalued)
        # print(len(FFT_sensor_1_list_x))

        if FragCount > 10:
            break

    FFT_sensor_2_dict_z["FFT_Z"] = FFT_sensor_2_list_z

    # print(FFT_sensor_1_dict_z)

    # add the FFT dictionaries for each axes into the main dictionary

    FFT_sensor_2_dict["FFT_X"] = FFT_sensor_2_list_x
    FFT_sensor_2_dict["FFT_Y"] = FFT_sensor_2_list_y
    FFT_sensor_2_dict["FFT_Z"] = FFT_sensor_2_list_z

    # save as picture for data export
    # x
    #clean the data if more than 980 are recorded in the FFT -- algorithm to be reviewed)

    if len(frequency_value_list) != len(FFT_sensor_2_list_x):
        if len(FFT_sensor_2_list_x)> len(frequency_value_list):
            index=0
            while len(FFT_sensor_2_list_x)> len(frequency_value_list) :
                FFT_sensor_2_list_x.pop(-1+index)

                index +=1
                if len(FFT_sensor_2_list_x)== len(frequency_value_list):
                    break

    plt.bar(frequency_value_list, FFT_sensor_2_list_x, width=0.5, color='blue')
    # # determina max value
    max_scale = max(FFT_sensor_2_list_x)

    # # print(max_scale)
    plt.title('FFT')
    plt.ylabel('[mm/2]')
    plt.xlabel('Frequency [Hz]')
    plt.ylim([0, max_scale * 1.2])
    plt.xlim([-10, 300])
    plt.savefig(os.path.join(folder_name,"FFT_X_sensor_2.jpg"))
    plt.close()

    # y
    #clean the data if more than 980 are recorded in the FFT -- algorithm to be reviewed)
    if len(frequency_value_list) != len(FFT_sensor_2_list_y):
        if len(FFT_sensor_2_list_y)> len(frequency_value_list):
            index=0
            while len(FFT_sensor_2_list_y)> len(frequency_value_list) :
                FFT_sensor_2_list_y.pop(-1+index)

                index +=1
                if len(FFT_sensor_2_list_y)== len(frequency_value_list):
                    break

    plt.bar(frequency_value_list, FFT_sensor_2_list_y, width=0.5, color='blue')
    # # determina max value
    max_scale = max(FFT_sensor_2_list_y)

    # # print(max_scale)
    plt.title('FFT')
    plt.ylabel('[mm/2]')
    plt.xlabel('Frequency [Hz]')
    plt.ylim([0, max_scale * 1.2])
    plt.xlim([-10, 300])
    plt.savefig(os.path.join(folder_name,"FFT_Y_sensor_2.jpg"))
    plt.close()

    # z
    #clean the data if more than 980 are recorded in the FFT -- algorithm to be reviewed)
    if len(frequency_value_list) != len(FFT_sensor_2_list_z):
        if len(FFT_sensor_2_list_z)> len(frequency_value_list):
            index=0
            while len(FFT_sensor_2_list_z)> len(frequency_value_list) :
                FFT_sensor_2_list_z.pop(-1+index)

                index +=1
                if len(FFT_sensor_2_list_z)== len(frequency_value_list):
                    break

    # print(FFT_sensor_2_list_z)
    # print(len(FFT_sensor_2_list_z))
    # print(FFT_sensor_2_list_z)
    # print(fuck)

    plt.bar(frequency_value_list, FFT_sensor_2_list_z, width=0.5, color='blue')
    # # determina max value
    max_scale = max(FFT_sensor_2_list_z)

    # # print(max_scale)
    plt.title('FFT')
    plt.ylabel('[mm/2]')
    plt.xlabel('Frequency [Hz]')
    plt.ylim([0, max_scale * 1.2])
    plt.xlim([-10, 300])
    plt.savefig(os.path.join(folder_name,"FFT_Z_sensor_2.jpg"))
    plt.close()

    # convert FFT dictionaty to JSon for export

    FFT_sensor_2_JSON = json.dumps(FFT_sensor_2_dict)


    # import picture as blob

    # read the file and conver to binary
    FFTX_pict_1 = open(os.path.join(folder_name,"FFT_X_sensor_1.jpg"), 'rb').read()
    FFTY_pict_1 = open(os.path.join(folder_name,"FFT_Y_sensor_1.jpg"), 'rb').read()
    FFTZ_pict_1 = open(os.path.join(folder_name,"FFT_Z_sensor_1.jpg"), 'rb').read()

    FFTX_pict_2 = open(os.path.join(folder_name,"FFT_X_sensor_2.jpg"), 'rb').read()
    FFTY_pict_2 = open(os.path.join(folder_name,"FFT_Y_sensor_2.jpg"), 'rb').read()
    FFTZ_pict_2 = open(os.path.join(folder_name,"FFT_Z_sensor_2.jpg"), 'rb').read()



    list_data_sensor_1 = [data_sensor_1_dict["Datetime"],data_sensor_1_dict["SensorNodeId"],
                            data_sensor_1_dict["Temperature"], data_sensor_1_dict["BatteryVoltage"],
                            data_sensor_1_dict["X_P2P"], data_sensor_1_dict["X_RMS"], data_sensor_1_dict["X_Z2P"],
                            data_sensor_1_dict["X_Kurtosis"],
                            data_sensor_1_dict["Y_P2P"], data_sensor_1_dict["Y_RMS"], data_sensor_1_dict["Y_Z2P"],
                            data_sensor_1_dict["Y_Kurtosis"], data_sensor_1_dict["Z_P2P"], data_sensor_1_dict["Z_RMS"],
                            data_sensor_1_dict["Z_Z2P"], data_sensor_1_dict["Z_Kurtosis"],FFTX_pict_1,FFTY_pict_1,FFTZ_pict_1]

    list_data_sensor_2 = [data_sensor_2_dict["Datetime"],data_sensor_2_dict["SensorNodeId"],
                            data_sensor_2_dict["Temperature"],data_sensor_2_dict["BatteryVoltage"],
                            data_sensor_2_dict["X_P2P"],data_sensor_2_dict["X_RMS"], data_sensor_2_dict["X_Z2P"],
                            data_sensor_2_dict["X_Kurtosis"],
                            data_sensor_2_dict["Y_P2P"], data_sensor_2_dict["Y_RMS"], data_sensor_2_dict["Y_Z2P"],
                            data_sensor_2_dict["Y_Kurtosis"], data_sensor_2_dict["Z_P2P"], data_sensor_2_dict["Z_RMS"],
                            data_sensor_2_dict["Z_Z2P"], data_sensor_2_dict["Z_Kurtosis"],FFTX_pict_2,FFTY_pict_2,FFTZ_pict_2]

    mysql_treon_organised_data_script = """INSERT INTO machine_monitor.treon_vibration_test_data (Date_time, Sensor_id,Temperature, Battery_voltage, X_P2P, X_RMS, X_Z2P, X_Kurtosis, Y_P2P, Y_RMS, Y_Z2P, Y_Kurtosis, Z_P2P, Z_RMS, Z_Z2P, Z_Kurtosis, FFT_X, FFT_Y, FFT_Z) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    #mysql_treon_organised_data_script = """INSERT INTO treon_vibration_test_data (Date_time) VALUES (%s)"""
    #cursor.execute(mysql_treon_organised_data_script, (list_data_sensor_1[0],))
    #cursor.execute(mysql_treon_organised_data_script, (list_data_sensor_2[0],))

    #print(list_data_sensor_1[0])
    cursor.execute(mysql_treon_organised_data_script, list_data_sensor_1)
    cursor.execute(mysql_treon_organised_data_script, list_data_sensor_2)

    # export Json of FFT


    list_fft_data_sensor_1 = [data_sensor_1_dict["SensorNodeId"], data_sensor_1_dict["Datetime"] , FFT_sensor_1_JSON]
    list_fft_data_sensor_2 = [data_sensor_2_dict["SensorNodeId"],data_sensor_2_dict["Datetime"], FFT_sensor_2_JSON]


    #Insert data into the database
    #print(list_data_sensor_1[0])
    mysql_treon_FFT_data_script = """INSERT INTO machine_monitor.treon_vibration_test_fft_data (Sensor_id, Datetime, FFT_dictionary) VALUES(%s,%s,%s)"""

    cursor.execute(mysql_treon_FFT_data_script, list_fft_data_sensor_1)
    cursor.execute(mysql_treon_FFT_data_script, list_fft_data_sensor_2)

    try:
        # Export table data to CSV
        cursor.execute(f"SELECT * FROM machine_monitor.treon_vibration_raw_data_1")
        with open(os.path.join(folder_name,'raw.csv'), 'w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow([i[0] for i in cursor.description])  # Write headers
            csv_writer.writerows(cursor.fetchall())  # Write rows
        print(f"Table machine_monitor.treon_vibration_raw_data_1 exported to raw.csv")
        
        # Empty the table
        cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_raw_data_1 WHERE data_time>0")
        print(f"Table machine_monitor.treon_vibration_test_raw_data_1 emptied successfully")
        
        # Commit changes
        sqlCon.commit()

        # Export table data to CSV
        cursor.execute(f"SELECT * FROM machine_monitor.treon_vibration_test_data")
        with open(os.path.join(folder_name,'test.csv'), 'w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow([i[0] for i in cursor.description])  # Write headers
            csv_writer.writerows(cursor.fetchall())  # Write rows
        print(f"Table machine_monitor.treon_vibration_test_data exported to test.csv")
        
        # Empty the table
        cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_test_data WHERE Date_time>0")
        print(f"Table machine_monitor.treon_vibration_test_data emptied successfully")
        
        # Commit changes
        sqlCon.commit()

        # Export table data to CSV
        cursor.execute(f"SELECT * FROM machine_monitor.treon_vibration_test_fft_data")
        with open(os.path.join(folder_name,'fft.csv'), 'w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow([i[0] for i in cursor.description])  # Write headers
            csv_writer.writerows(cursor.fetchall())  # Write rows
        print(f"Table machine_monitor.treon_vibration_test_fft_data exported to fft.csv")
        
        # Empty the table
        cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_test_fft_data WHERE Datetime>0")
        print(f"Table machine_monitor.treon_vibration_test_fft_data emptied successfully")
        
        # Commit changes
        sqlCon.commit()
    except Exception as e:
        # Rollback changes if any error occurs
        sqlCon.rollback()
        print("Error:", e)
    finally:
        # Close cursor and connection
        sqlCon.commit()

        sqlCon.close()
        print(data_sensor_1_dict["SensorNodeId"])
        print(data_sensor_2_dict["SensorNodeId"])
        print("Data organised and uploaded")   


#Raw Data processing and save into the MSQL database

def cancel_data():
    #client.loop_stop()

    # connect to database
    sqlCon = pymysql.connect(host="{}".format(MYSQL_Host),
                                 user="{}".format(MYSQL_User),
                                 password="{}".format(MYSQL_Password),
                                 database="{}".format(MYSQL_Database))
    cursor = sqlCon.cursor()


    cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_test_fft_data WHERE Datetime>0")
    cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_test_data WHERE Date_time>0")
    cursor.execute(f"DELETE FROM machine_monitor.treon_vibration_raw_data_1 WHERE data_time>0")

    sqlCon.commit()
    sqlCon.close()
    global num
    num = 0


#######################################################################################################################


# START the connection
def Main():
    num = 0
    client = mqtt.Client()

    # Specify callback function
    client.on_connect = on_connect
    client.on_message = on_message

    # Establish a connection
    #####################################################################################
    # enter the MQQT details
    client.username_pw_set("Tejas", "machinemonitor_0")

    client.connect('k2a11de7.emqx.cloud', 1883, 60)
    ###################################################################################3

    #loop the connection to listen for messages continuosly

    client.loop_forever()

#timer to be set based on the last measurement time (sensors acquire every hour)
t1 = Timer(interval=300, function=split_function)
t1.start()
Main()

