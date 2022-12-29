import requests
import json
import datetime
import time
import weather_config as config
import csv
import subprocess

class Weather:
	def __init__(self, scale, update_time, ipaddress, export_csv, rainmeter_ctrl):
		match scale:
			case "imperial": 
				self.scale = {"Temp": "fahrenheit","Wind": "mph","Precip": "inch","Dist": "miles",}		
			case _:
				self.scale = {"Temp": "celsius", "Wind": "kmh", "Precip": "mm", "Dist": "km"}

		self.update_time = update_time
		self.ipaddress = ipaddress
		self.export_csv = export_csv
		self.rainmeter_ctrl = rainmeter_ctrl
		self.current_epoch = int(round(time.time()))
		

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

			print("Successfully fetched location...")
			return self.location

		except:
			print("Unable to fetch location! Check your internet connection...")
			return


	def fetch_weatherdata(self):
		try:
			with open("weather_cache.json", "r") as file:
				self.weather_data = json.load(file)
				print("Fetched data from local cache...")

			# clear our weather data if it is older than the update time
			self.cache_epoch = int(self.weather_data["current_weather"]["time"])
			if self.current_epoch - self.cache_epoch >= self.update_time:
				self.weather_data = None

		except (FileNotFoundError, json.JSONDecodeError):
			print("No local cache found!")
			self.weather_data = None

		if not self.weather_data:
			print("Fetching new json data!")

			try:
				self.get_forecast = requests.get(
					f"https://api.open-meteo.com/v1/forecast?latitude={self.location['latitude']}&longitude={self.location['longitude']}&current_weather=true&temperature_unit={self.scale['Temp']}&hourly=temperature_2m,relativehumidity_2m,visibility,apparent_temperature,windspeed_10m&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&temperature_unit={self.scale['Temp']}&windspeed_unit={self.scale['Wind']}&precipitation_unit={self.scale['Precip']}&timeformat=unixtime&timezone=auto").json()
			except:
				print("There was an error fetching your api request. Check if the api is working or the location is correct.")
				print("Attempting to read from cache...")

			with open("weather_cache.json", "w") as file:
				json.dump(self.get_forecast, file, indent=6)
				print("Success writing to cache!")

			with open("weather_cache.json", "r") as file:
				self.weather_data = json.load(file)
				print("Fetched data from local cache...")
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
		return self.weekly


	def export_weather_csv(self):
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

				print("Weather data sucessfully exported to CSV...")
			except:
				print("Failed to export CSV. Check your API request.")
			
		return

	def rainmeter_controller(self):
		if self.rainmeter_ctrl:
			print("Updating Rainmeter...")
			#pull data from the calling function
			#update rainmeter bangs via rm_process = subprocess.run()
			#get return code with rm_process.returncode. 0 = pass
			print("Rainmeter sucessfully updated...")
		return

	def fetch_all(self):
		self.fetch_ip()
		self.fetch_weatherdata()
		self.parse_current_weather()
		self.parse_weekly_forecast()
	

def main():
	forecast = Weather(config.preferred_scale, config.update_time, config.ipaddress, config.export_csv, config.rainmeter_ctrl)
	forecast.fetch_all()


if __name__ == "__main__":
	main()
