This file is to explain the items inside Dashboard_Final

assets: Directory contains images and stylesheets for the dashboard

Collected_Data: stores incoming data csv files (fft.csv, raw.csv, test.csv)

History_Data: Stores the archived incoming data and names the directory based on date-time for use in the history tab

ModelCNN_2D_Final.h5: Our CNN model that we used

Dashboard.py: Main Dashboard class that creates the dashboard

Run_Dashboard.py: Program To run the dashboard

Treon_to_model_Mac.py: For Apple Silicon. A program to connect to MQTT server, process data and store the data in an SQL database.

Treon_to_model_Rest.py: Same program as Treon_to_model_Mac.py but for remaining operating systems and Intel/AMD based Macs. 

Using Dashboard Tutorial:
1. Run the Run_Dashboard.py file. It will run the dashboard on localhost. 
2. Type in the address that the dashboard is running on to your browser.
3. Press the Start button to start the connection process.
4. you should now see the next update timer counting down.
5. after 5 minutes, data, fft plots and fault detection status should update and display.

Python Library requirements for Dashboard.py:
  Python version used during the dashboard developement: 3.10.14
  dash: 2.16.1                  
  dash-core-components: 2.0.0                   
  dash-html-components: 2.0.0                
  dash-table: 5.0.0        
  flask: 3.0.3     
  tensorflow: 2.16.1 
  plotly: 5.20.0 
  numpy: 1.26.4 

Python Library requirements for Treon_to_model_Mac.py & Treon_to_model_Rest.py:
  paho-mqtt 1.6.1
  DateTime 5.5
  jsons 1.6.3
  pymysql 1.1.0
  threaded 4.2.0
  matplotlib 3.7.1
  python-csv 0.0.13
  numpy 1.25.2
  tensorflow 2.15.0
  os-sys 2.1.4
  jsons 1.6.3
