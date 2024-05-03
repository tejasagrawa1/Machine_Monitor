This file is to explain the items inside Dashboard_Final

assets: Directory contains images and stylesheets for the dashboard

Collected_Data: stores incoming data csv files (fft.csv, raw.csv, test.csv)

History_Data: Stores the archived incoming data and names the directory based on date-time for use in the history tab

ModelCNN_2D_Final.h5: Our CNN model that we used

Dashboard.py: Main Dashboard class that creates the dashboard

Run_Dashboard.py: Program To run the dashboard

Treon_to_model_Mac.py: For Apple Silicon. A program to connect to MQTT server, process data and store the data in an SQL database.

Treon_to_model_Rest.py: Same program as Treon_to_model_Mac.py but for remaining operating systems and Intel/AMD based Macs. 
