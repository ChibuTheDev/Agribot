import os
import requests
import datetime
import json


def get_5day_forecast(location):
    api_key = os.getenv("WEATHER") 
    base_url = "http://api.openweathermap.org/data/2.5/forecast?"
    if not api_key:
        return "Error: Weather API key is missing." 

    complete_url = base_url + "appid=" + api_key + "&q=" + location + "&units=metric"

    try:
        response = requests.get(complete_url)
        response.raise_for_status()
        x = response.json()

        if x["cod"] != "404" and x["cod"] != "400":
            forecasts = []
            for forecast in x["list"]:
                date = datetime.datetime.fromtimestamp(forecast["dt"]).strftime("%Y-%m-%d %H:%M") #to make the dats and time simpler 
                temp = forecast["main"]["temp"]
                description = forecast["weather"][0]["description"]
                forecasts.append([date, description, temp])  # Store as a list of lists

            # This markdown table helps to like format the weather data in a table 
            table_header = "| Date/Time | Description | Temperature (°C) |\n|---|---|---|"
            table_rows = "\n".join([f"| {date} | {desc} | {temp} |" for date, desc, temp in forecasts])
            markdown_table = f"{table_header}\n{table_rows}"
            return markdown_table
        elif x["cod"] == "404":
            return "Location not found."
        elif x["cod"] == "400":
            return "Invalid Query"
        else:
            return "Unknown Error"

    except requests.exceptions.RequestException as e:  #error handlinggg
        return f"Error fetching weather data: {e}"
    except (KeyError, IndexError) as e:
        return f"Error parsing weather data: {e}. The API response format might have changed."

