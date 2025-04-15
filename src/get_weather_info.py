import os
from dotenv import load_dotenv
from pyowm.owm import OWM

from src.route_select.find_station_code import find_station_code

load_dotenv()
token_owm = os.getenv('TOKEN_OWM')

weather_emoji = {
    "clear sky": "☀️",
    "few clouds": "🌤",
    "light rain": "🌦",
    "broken clouds": "☁️",
    "overcast clouds": "☁️",
    "scattered clouds": "☁️",
    "snow": "🌨",
    "light snow": "❄🌥🌨",
    "rain and snow": "🌧❄️",
    "rain": "🌧",
    "thunderstorm": "⛈",
    "mist": "🌫"
}

def get_weather_code(station_code):
    weather = find_station_code(station_code)
    owm = OWM(token_owm)
    mgr = owm.weather_manager()
    observation = mgr.weather_at_coords(weather[0].latitude, weather[0].longitude)
    weather = observation.weather
    temp = round(weather.temperature('celsius')['temp'])
    status = weather.detailed_status
    emoji = weather_emoji.get(status.lower(), "🌡")
    return f"{temp}°C {emoji}"

def get_weather_title(city_name):
    owm = OWM(token_owm)
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place(city_name)
    weather = observation.weather
    temp = round(weather.temperature('celsius')['temp'])
    status = weather.detailed_status
    emoji = weather_emoji.get(status.lower(), "🌡")
    return f"{temp}°C {emoji}"