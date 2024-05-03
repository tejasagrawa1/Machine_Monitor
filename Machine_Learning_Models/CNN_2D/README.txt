Steps to run the script
	1. Set Up the Treon sensors and Sql Database
	Setting up: 
		1. Create MSQL database and insert the database details in the parameters
            	2. Create the following tables in the database:
                	a. treon_vibration_raw_data_1 (data_time, message)
                	b. treon_vibration_test_data (Date_time, Sensor_id, Temperature, Battery_voltage, X_P2P, X_RMS, X_Z2P, X_Kurtosis, Y_P2P, Y_RMS, Y_Z2P, Y_Kurtosis, Z_P2P, Z_RMS, Z_Z2P, Z_Kurtosis, FFT_X, FFT_Y, FFT_Z)
                	c. treon_vibration_test_fft_data (Sensor_id, Datetime, FFT_dictionary)
            	3. Create an MQQT server account on https://www.emqx.io/ 
            	4. Enter the account details on the Main function
	1. Run the command 'python Treon_to_CNNmodel_prediction.py'
	3. The prediction is shown in the terminal and it will move on and start collecting the next dataset

