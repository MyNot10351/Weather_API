import os
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import functions_framework

@functions_framework.cloud_event
def hourly_weather():
    LATITUDE = float(os.getenv("WEATHER_LATITUDE", "13.945583"))
    LONGITUDE = float(os.getenv("WEATHER_LONGITUDE", "100.716417"))
    TIMEZONE = os.getenv("WEATHER_TIMEZONE", "auto")
    GCS_OUTPUT_URI = os.getenv(
        "WEATHER_GCS_OUTPUT_URI",
        "gs://data-low-cost/Final Data/hourly_weather.parquet",
    )
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ["temperature_2m", "relative_humidity_2m", "weather_code", "apparent_temperature"],
        "timezone": TIMEZONE,
    }
    responses = openmeteo.weather_api(url, params = params)

    # Process first location.
    response = responses[0]
    hourly = response.Hourly()
        
    # ดึงข้อมูลช่วงเวลา (Time) มาด้วยเพื่อสร้างเป็นคอลัมน์ใน DataFrame
    # Open-Meteo ให้เวลาเป็น Timestamp วินาที ต้องคูณช่วงเวลาตามระยะข้อมูล
    time_data = pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.to_timedelta(hourly.Interval(), unit="s"),
        inclusive="left"
    )

    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(2).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(3).ValuesAsNumpy()

    # [แก้ไขจุดพัง] ประกาศสร้าง Dictionary เพื่อเก็บข้อมูลก่อนแปลงเป็น DataFrame
    hourly_data = {
        "date": time_data,
        "temperature_2m": hourly_temperature_2m,
        "relative_humidity_2m": hourly_relative_humidity_2m,
        "weather_code": hourly_weather_code,
        "apparent_temperature": hourly_apparent_temperature
    }

    hourly_dataframe = pd.DataFrame(data = hourly_data)
        
    # บันทึกไฟล์ลง GCS (Cloud Run จะดึงสิทธิ์จากสิทธิ์เครื่องโดยอัตโนมัติในการเขียนลงถัง)
    hourly_dataframe.to_parquet("hourly_weather.parquet", index=False, engine="pyarrow")

hourly_weather()