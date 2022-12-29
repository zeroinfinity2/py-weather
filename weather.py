import requests
import json
import datetime
import time
import csv
import subprocess
import configparser

class Weather:
	def __init__(self, config):
		self.update_time = int(config["update_time"])
		self.ipaddress = str(config["ipaddress"])
		self.export_csv = bool(config["export_csv"])
		self.rainmeter_ctrl = bool(config["rainmeter_ctrl"])
		self.debug = bool(config["debug_mode"])
		self.current_epoch = int(round(time.time()))
		self.debug_message(14)
		match config["preferred_scale"]:
			case "imperial": 
				self.scale = {"Temp": "fahrenheit","Wind": "mph","Precip": "inch","Dist": "miles",}
				self.debug_message(15)	
			case _:
				self.scale = {"Temp": "celsius", "Wind": "kmh", "Precip": "mm", "Dist": "km"}
				self.debug_message(16)
		self.debug_message(17)

	def fetch_ip(self):
		try:
			get_location = requests.get(f"http://ip-api.com/json/{self.ipaddress}?fields=country,region,regionName,city,zip,lat,lon,timezone,isp,org,query").json()		

			self.location = {
				"country": get_location["country"],
				"state": get_location["regionName"],
				"city": get_location["city"],
				"latitude": get_location["lat"],
				"longitude": get_location["lon"],
			}

			self.debug_message(0)
			return self.location

		except:
			self.debug_message(1)
			return


	def fetch_weatherdata(self):
		try:
			with open("weather_cache.json", "r") as file:
				self.weather_data = json.load(file)
				self.debug_message(2)

			# clear our weather data if it is older than the update time
			self.cache_epoch = int(self.weather_data["current_weather"]["time"])
			if self.current_epoch - self.cache_epoch >= self.update_time:
				self.weather_data = None
				self.debug_message(3)

		except (FileNotFoundError, json.JSONDecodeError):
			self.debug_message(4)
			self.weather_data = None

		if not self.weather_data:
			self.debug_message(5)

			try:
				self.get_forecast = requests.get(
					f"https://api.open-meteo.com/v1/forecast?latitude={self.location['latitude']}&longitude={self.location['longitude']}&current_weather=true&temperature_unit={self.scale['Temp']}&hourly=temperature_2m,relativehumidity_2m,visibility,apparent_temperature,windspeed_10m&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&temperature_unit={self.scale['Temp']}&windspeed_unit={self.scale['Wind']}&precipitation_unit={self.scale['Precip']}&timeformat=unixtime&timezone=auto").json()
			except:
				self.debug_message(6)

			with open("weather_cache.json", "w") as file:
				json.dump(self.get_forecast, file, indent=6)
				self.debug_message(7)

			with open("weather_cache.json", "r") as file:
				self.weather_data = json.load(file)
				self.debug_message(2)
		return self.weather_data


	def parse_current_weather(self):
		self.currenthour = int(datetime.datetime.now().strftime("%H"))
		self.current = {
			"temperature": self.weather_data["current_weather"]["temperature"],
			"windspeed": self.weather_data["current_weather"]["windspeed"],
			"winddirection": self.weather_data["current_weather"]["windspeed"],
			"weathercode": self.weather_data["current_weather"]["weathercode"],
			"rel_humidity": self.weather_data["hourly"]["relativehumidity_2m"][self.currenthour],
			"visibility": self.weather_data["hourly"]["visibility"][self.currenthour],
			"feels_like": self.weather_data["hourly"]["apparent_temperature"][self.currenthour],
			"maxtemp": self.weather_data["daily"]["temperature_2m_max"][0],
			"mintemp": self.weather_data["daily"]["temperature_2m_min"][0],
			"total_precip": self.weather_data["daily"]["precipitation_sum"][0],
		}
		self.debug_message(8)
		return self.current


	def parse_weekly_forecast(self):
		self.weekly = []
		
		for day in enumerate(self.weather_data["daily"]["time"]):
			self.weekly.append(
				{
					"day": day[0] + 1,
					"maxtemp": self.weather_data["daily"]["temperature_2m_max"][day[0]],
					"mintemp": self.weather_data["daily"]["temperature_2m_min"][day[0]],
					"weathercode": self.weather_data["daily"]["weathercode"][day[0]],
					"precipitation": self.weather_data["daily"]["precipitation_sum"][day[0]],
				}
			)
		self.debug_message(9)
		return self.weekly


	def export(self):
		if self.export_csv:
			try:
				with open("weathercurrent.csv", "w") as file:
					self.writer = csv.DictWriter(file, fieldnames=["temperature", "windspeed", "winddirection", "weathercode", "rel_humidity", "visibility", "feels_like", "maxtemp", "mintemp", "total_precip"])
					self.writer.writeheader()
					self.writer.writerow({
						"temperature": self.current["temperature"], 
						"windspeed": self.current["windspeed"], 
						"winddirection": self.current["winddirection"], 
						"weathercode": self.current["weathercode"], 
						"rel_humidity": self.current["rel_humidity"], 
						"visibility": self.current["visibility"], 
						"feels_like": self.current["feels_like"], 
						"maxtemp": self.current["maxtemp"], 
						"mintemp": self.current["mintemp"], 
						"total_precip": self.current["total_precip"]})
				
				with open("weatherforecast.csv", "w") as file:
					self.writer = csv.DictWriter(file, fieldnames=["day", "maxtemp", "mintemp", "weathercode", "precip"])
					self.writer.writeheader()
					
					for day in self.weekly:
						self.writer.writerow({
							"day": day["day"],
							"maxtemp": day["maxtemp"],
							"mintemp": day["mintemp"],
							"precip": day["precipitation"]
						})

				self.debug_message(10)
			except:
				self.debug_message(11)
			
		return

	def rainmeter_controller(self):
		if self.rainmeter_ctrl:
			self.debug_message(12)
			#gather relevant data
			#update rainmeter bangs via rm_process = subprocess.run()
			#get return code with rm_process.returncode. 0 = pass
			self.debug_message(13)
		return

	def fetch_all(self):
		self.fetch_ip()
		self.fetch_weatherdata()
		self.parse_current_weather()
		self.parse_weekly_forecast()
		return
	

	def debug_message(self, index):
		if self.debug:
			self.debug_messages = (
				"Successfully fetched location...", 
				"Unable to fetch location! Check your internet connection...", 
				"Fetched data from local cache...", 
				"Older weather data cleared...", 
				"No local cache found!",
				"Fetching new json data!", 
				"There was an error fetching your api request. Check if the api is working or the location is correct. Attempting to read from cache...",
				"Success writing to cache!",
				"Current weather successfully parsed from cache...", 
				"Weekly weather successfully parsed from cache...",
				"Weather data sucessfully exported to CSV...",
				"Failed to export CSV. Check your API request.",
				"Updating Rainmeter...",
				"Rainmeter sucessfully updated...",
				"Alert! Debug Mode enabled... ",
				"Measurement scale set to imperial...",
				"Measurement scale set to metric...",
				"Config successfully loaded...")
		
			return print(self.debug_messages[index])
		return

def read_config(file_path):
	c_values={}
	config = configparser.ConfigParser()
	config.read(file_path)
	for section in config.sections():
		for key in config[section]:
			c_values.update({key: config[section][key]})
	return c_values
			
	
def main():
	config = read_config("weather_config.ini")
	forecast= Weather(config)
	forecast.fetch_all()
	forecast.export()
	

if __name__ == "__main__":
	main()
