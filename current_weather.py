import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta, timezone
import zoneinfo

# # Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 13.945585,
	"longitude": 100.716314,
	"current": ["temperature_2m", "relative_humidity_2m", "weather_code", "apparent_temperature"],
	"timezone": "auto",
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
# print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
# print(f"Elevation: {response.Elevation()} m asl")
# print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
# print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process current data. The order of variables needs to be the same as requested.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_relative_humidity_2m = current.Variables(1).Value()
current_weather_code = current.Variables(2).Value()
current_apparent_temperature = current.Variables(3).Value()

# print(f"\nCurrent time: {current.Time()}")
# print(f"Current temperature_2m: {current_temperature_2m}")
# print(f"Current relative_humidity_2m: {current_relative_humidity_2m}")
# print(f"Current weather_code: {current_weather_code}")
# print(f"Current apparent_temperature: {current_apparent_temperature}")
time = datetime.fromtimestamp(current.Time(), tz=zoneinfo.ZoneInfo("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M:%S")

current_dataframe = pd.DataFrame(columns=["time", "temperature_2m", 
                                          "relative_humidity_2m", 
                                          "weather_code", 
                                          "apparent_temperature"], 
                                 data=[[time, current_temperature_2m, 
                                        current_relative_humidity_2m, 
                                        current_weather_code, 
                                        current_apparent_temperature]])

current_dataframe.to_csv("current_weather.csv", index=False, mode='a', header=False)