Origin Dataset: 
-	yamagata_snow_fall_translated.csv
-	yamagata_min_max_temp_p1.csv
-	yamagata_min_max_temp_p2.csv
-	akita_snow_fall_translated.csv
-	akita_min_max_temp_p1.csv
-	akita_min_max_temp_p2.csv

Process Dataset:
1. yamagata_snow_fall_translated.csv → yamagata_snowfall_average.csv
Actions taken:
•	Removed the "Kushibiki" location (13 locations remaining)
•	Filtered the dataset by Quality Flag: kept values with flag ≥ 5, and removed (left blank) any value with flag < 5
•	Removed all columns except Snowfall_Total_cm
•	Averaged the snowfall across the 13 locations

2. akita_snow_fall_translated.csv → akita_snowfall_average.csv
Actions taken:
•	All 14 locations retained
•	Filtered the dataset by Quality Flag: kept values with flag ≥ 5, and removed (left blank) any value with flag < 5
•	Removed all columns except Snowfall_Total_cm
•	Averaged the snowfall across the 14 locations

3. Temperature Data
•	yamagata_min_max_temp_p1.csv + yamagata_min_max_temp_p2.csv → yamagata_avg_temp.csv
•	akita_min_max_temp_p1.csv + akita_min_max_temp_p2.csv → akita_avg_temp.csv
Actions taken:
•	Removed any location that does not match those in yamagata_snow_fall_translated.csv / akita_snow_fall_translated.csv
•	Removed the Homogeneity Number columns
•	Blanked out any value whose Quality Flag is not 8 or 5 (i.e. 4, 3, 2, 1, or blank → removed)
•	Dropped the now-unused Quality info columns
•	Merged the two files (p1 and p2) by Date
•	Averaged the min and max values across all locations into single values

Definition: 
Dataset file	Meaning 
yamagata_snowfall_average.csv

akita_snowfall_average.csv	Stations counted = The number of locations that contributed to the daily average.

Snowfall values with a Quality Flag below 5 are removed and treated as blank. Those stations are not included in the average. So Stations_Counted shows how many stations had valid data:
•	Full count (e.g. 14 for Akita) = all stations contributed
•	Lower count = some stations were excluded
yamagata_avg_temp.csv


akita_avg_temp.csv
	Valid_Max_Count / Valid_Min_Count records how many stations contributed to each daily average, allowing unreliable low-coverage days to be identified and filtered out before training the heavy-snow risk model.


