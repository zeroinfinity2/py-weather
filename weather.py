import requests
import json
import datetime
import time
import weather_config as config
import csv


def fetch_ip(ip):
	try:
		get_location = requests.get(f"http://ip-api.com/json/{ip}?fields=country,region,regionName,city,zip,lat,lon,timezone,isp,org,query").json()		

		location = {
			"country": get_location["country"],
			"state": get_location["regionName"],
			"city": get_location["city"],
			"latitude": get_location["lat"],
			"longitude": get_location["lon"],
		}

		print("Successfully fetched location...")
		return location

	except:
		print("Unable to fetch location!")
		return


def fetch_weatherdata(location, update_time, current_epoch, scale):
	try:
		with open("weather_cache.json", "r") as file:
			weather_data = json.load(file)
			print("Fetched data from local cache...")

		# clear our weather data if it is older than the update time
		cache_epoch = int(weather_data["current_weather"]["time"])
		if current_epoch - cache_epoch >= update_time:
			weather_data = None

	except (FileNotFoundError, json.JSONDecodeError):
		print("No local cache found!")
		weather_data = None

	if not weather_data:
		print("Fetching new json data!")

		try:
			get_forecast = requests.get(
				f"https://api.open-meteo.com/v1/forecast?latitude={location['latitude']}&longitude={location['longitude']}&current_weather=true&temperature_unit={scale['Temp']}&hourly=temperature_2m,relativehumidity_2m,visibility,apparent_temperature,windspeed_10m&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&temperature_unit={scale['Temp']}&windspeed_unit={scale['Wind']}&precipitation_unit={scale['Precip']}&timeformat=unixtime&timezone=auto").json()
		except:
			print("There was an error fetching your api request. Check if the api is working or the location is correct.")
			print("Attempting to read from cache...")

		with open("weather_cache.json", "w") as file:
			json.dump(get_forecast, file, indent=6)
			print("Success writing to cache!")

		with open("weather_cache.json", "r") as file:
			weather_data = json.load(file)
			print("Fetched data from local cache...")
	return weather_data


def parse_current_weather(data):
	t = datetime.datetime.now()
	currenthour = int(t.strftime("%H"))
	current = {
		"temperature": data["current_weather"]["temperature"],
		"windspeed": data["current_weather"]["windspeed"],
		"winddirection": data["current_weather"]["windspeed"],
		"weathercode": data["current_weather"]["weathercode"],
		"rel_humidity": data["hourly"]["relativehumidity_2m"][currenthour],
		"visibility": data["hourly"]["visibility"][currenthour],
		"feels_like": data["hourly"]["apparent_temperature"][currenthour],
		"maxtemp": data["daily"]["temperature_2m_max"][0],
		"mintemp": data["daily"]["temperature_2m_min"][0],
		"total_precip": data["daily"]["precipitation_sum"][0],
	}
	return current


def parse_weekly_forecast(data):
	weekly = []

	for day in range(len(data["daily"]["time"])):
		weekly.append(
			{
				"day": day + 1,
				"maxtemp": data["daily"]["temperature_2m_max"][day],
				"mintemp": data["daily"]["temperature_2m_min"][day],
				"weathercode": data["daily"]["weathercode"][day],
				"precipitation": data["daily"]["precipitation_sum"][day],
			}
		)
	return weekly

def export_weather_csv(export, data_current, data_forecast):
	if export:
		with open("weathercurrent.csv", "w") as file:
			writer = csv.DictWriter(file, fieldnames=["temperature", "windspeed", "winddirection", "weathercode", "rel_humidity", "visibility", "feels_like", "maxtemp", "mintemp", "total_precip"])
			writer.writeheader()
			writer.writerow({
				"temperature": data_current["temperature"], 
				"windspeed": data_current["windspeed"], 
				"winddirection": data_current["winddirection"], 
				"weathercode": data_current["weathercode"], 
				"rel_humidity": data_current["rel_humidity"], 
				"visibility": data_current["visibility"], 
				"feels_like": data_current["feels_like"], 
				"maxtemp": data_current["maxtemp"], 
				"mintemp": data_current["mintemp"], 
				"total_precip": data_current["total_precip"]})
			print("Weather data sucessfully exported to CSV...")
	return


def main():
	match config.preferred_scale:
		case "imperial": 
			scale = {"Temp": "fahrenheit","Wind": "mph","Precip": "inch","Dist": "miles",}		
		case _:
			scale = {"Temp": "celsius", "Wind": "kmh", "Precip": "mm", "Dist": "km"}

	current_epoch = int(round(time.time()))
	location = fetch_ip(config.ipaddress)

	forecast_data = fetch_weatherdata(location, config.update_time, current_epoch, scale)

	current_weather = parse_current_weather(forecast_data)

	weekly_forecast = parse_weekly_forecast(forecast_data)
	
	export_csv = export_weather_csv(config.export_csv, current_weather, weekly_forecast)


if __name__ == "__main__":
	main()
