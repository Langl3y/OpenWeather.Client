import json
import os
import threading
import time
import dotenv
import requests
import datetime

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tkinter import *

from bounding_box import BoundingBox
from city import City

dotenv.load_dotenv()
api_key = os.getenv('API_KEY')
get_cities_api = 'https://api.openweathermap.org/data/2.5/box/city?bbox={lon_min},{lat_min},{lon_max},{lat_max},10&appid={api_key}'
weather_api = 'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}'


def request_city_list(bounding_box: BoundingBox, api_key: str):
    limiting_coordinates = bounding_box.get_bounding_box()
    query_url = get_cities_api.format(
        lon_min=limiting_coordinates.get('lon_min'),
        lat_min=limiting_coordinates.get('lat_min'),
        lon_max=limiting_coordinates.get('lon_max'),
        lat_max=limiting_coordinates.get('lat_max'),
        api_key=api_key
    )
    return requests.get(query_url).json()


class App:
    def __init__(self):
        self.window = Tk()
        self.window.title("OpenWeather")
        self.window.geometry('550x700')

        # timer for handling OpenWeather's requests quota
        self.timer = time.time()

        # Requests made counter
        self.requests_made = 0

        # Coordinate entry labels and fields for bbox coordinates with a frame
        self.coord_frame = Frame(self.window)
        self.coord_frame.pack(pady=10)

        Label(self.coord_frame, text="Latitude Top").grid(row=0, column=0, padx=5, pady=5)
        self.lat_top_entry = Entry(self.coord_frame)
        self.lat_top_entry.grid(row=0, column=1, padx=5, pady=5)

        Label(self.coord_frame, text="Latitude Bottom").grid(row=1, column=0, padx=5, pady=5)
        self.lat_bottom_entry = Entry(self.coord_frame)
        self.lat_bottom_entry.grid(row=1, column=1, padx=5, pady=5)

        Label(self.coord_frame, text="Longitude Left").grid(row=2, column=0, padx=5, pady=5)
        self.lon_left_entry = Entry(self.coord_frame)
        self.lon_left_entry.grid(row=2, column=1, padx=5, pady=5)

        Label(self.coord_frame, text="Longitude Right").grid(row=3, column=0, padx=5, pady=5)
        self.lon_right_entry = Entry(self.coord_frame)
        self.lon_right_entry.grid(row=3, column=1, padx=5, pady=5)

        # Button to get cities
        self.handler_btn = Button(self.coord_frame, text='Get city list', command=self.submit_coordinates)
        self.handler_btn.grid(row=4, column=0, columnspan=2, pady=10)

        # Button to show selected city and get weather data for that city
        self.show_selected_btn = Button(self.coord_frame, text='Get weather data for selected city',
                                        command=self.get_data_for_selected_city)
        self.show_selected_btn.grid(row=3, column=3, pady=10)

        # Button to get all cities' weather data at once (in parallel)
        self.get_all_data_para = Button(self.coord_frame, text='Get all cities weather data (In parallel)',
                                   command=self.get_all_weather_data_parallel)
        self.get_all_data_para.grid(row=4, column=3, pady=10)

        # Button to get all cities' weather data at once (in sequence)
        self.get_all_data_seq = Button(self.coord_frame, text='Get all cities weather data (In sequence)',
                                   command=self.get_all_weather_data_sequence)
        self.get_all_data_seq.grid(row=5, column=3, pady=10)

        # Button to dump all weather data to json files
        self.dump_json_data = Button(self.coord_frame, text='Dump all weather data to json files',
                                     command=self.dump_weather_data)
        self.dump_json_data.grid(row=6, column=3, pady=10)

        # Text widget to display city names
        self.city_display = Text(self.window, height=15, width=50, wrap=WORD)
        self.city_display.pack(pady=10)
        self.city_display.insert(END, "Waiting for coordinate inputs...\n")

        # Listbox of cities
        self.frame = Frame(self.window)
        self.frame.pack(pady=20)
        self.city_listbox = Listbox(self.frame, width=30, height=1, selectmode=SINGLE)
        self.city_listbox.pack(side=LEFT, fill=BOTH)

        # City list scrollbar
        self.scrollbar = Scrollbar(self.frame, orient=VERTICAL)
        self.scrollbar.config(command=self.city_listbox.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.city_listbox.config(yscrollcommand=self.scrollbar.set)

        self.selected_label = Label(self.window, text="Selected city will appear here")
        self.selected_label.pack(pady=10)

        # City metadata (coordinates...of given city)
        self.metadata = {}

        # Result weather data of all cities (within the defined bbox)
        self.weather_data_in_bbox = {}

        # App icon
        icon = PhotoImage(file='icon.png')
        self.window.iconphoto(False, icon)

    def submit_coordinates(self):
        # Get coordinates from entries
        lat_top = self.lat_top_entry.get()
        lat_bottom = self.lat_bottom_entry.get()
        lon_left = self.lon_left_entry.get()
        lon_right = self.lon_right_entry.get()

        self.get_cities(lat_bottom, lat_top, lon_left, lon_right)

    def get_cities(self, lat_bottom, lat_top, lon_left, lon_right):
        bounding_box = BoundingBox(lat_top, lat_bottom, lon_left, lon_right)
        self.city_display.delete(1.0, END)

        # Request for city list in the defined bbox from OpenWeather
        result = request_city_list(bounding_box, api_key)
        if not result:
            self.city_display.insert(END, "There are no cities in the given region\n")
            return

        cities = result.get('list')

        if cities:
            for city in cities:
                city_name = city.get('name')
                coord = city.get('coord', {})
                # Store the coordinates in property metadata for fetching the city's weather data
                self.metadata[city_name] = coord
                self.city_display.insert(END, f"City: {city_name}\n")
                self.add_city_to_listbox(city_name)
        else:
            self.city_display.insert(END, "No cities found in the specified region.")

    def add_city_to_listbox(self, city_name):
        self.city_listbox.insert(END, city_name)

    def get_data_for_selected_city(self):
        selected_index = self.city_listbox.curselection()
        if selected_index:
            selected_city = self.city_listbox.get(selected_index[0])
            self.selected_label.config(text=f"Selected City: {selected_city}")

            # Get selected city's coordinate
            coords = self.metadata.get(selected_city)
            if coords:
                lat = coords.get('Lat')
                lon = coords.get('Lon')

                # Request for weather data from OpenWeather
                weather_data = self.request_weather_data(City(lat, lon), api_key)

                self.display_weather_data(selected_city, weather_data)
            else:
                self.selected_label.config(text="No metadata available for this city.")
        else:
            self.selected_label.config(text="No city selected.")

    def request_weather_data(self, city: City, api_key: str):
        print(city.lat, city.lon)
        query_url = weather_api.format(lat=city.lat, lon=city.lon, api_key=api_key)

        # Check if requests have exceeded 60
        if self.requests_made >= 60:
            # Get app's elapse time
            elapsed_time = time.time() - self.timer

            # Check if requests made in 1 minute exceeded OpenWeather's quota
            if elapsed_time < 60 <= self.requests_made:
                print('Requests made exceeded the limit (60 reqs/min)')
                self.city_display.delete(1.0, END)

                # Pause the program for {pause_time} seconds before allowing User to interact with it again
                pause_time = 60 - elapsed_time
                self.selected_label.config(text=f'Requests made exceeded the limit (60 reqs/min), app is locked for {pause_time}!')
                time.sleep(pause_time)

                # Reset everything for the next requests
                self.requests_made = 0
                self.timer = time.time()
        result = requests.get(query_url).json()

        if result:
            self.requests_made += 1
        return result

    # Parallel requests
    def get_all_weather_data_parallel(self):
        # clear the all the data of this temporary dict before proceeding
        self.weather_data_in_bbox.clear()

        start_time = time.time()
        # Format the timestamp before adding it to file name
        timestamp = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")

        with ThreadPoolExecutor(max_workers=8) as executor:
            # Map futures to city names
            futures = {
                executor.submit(self.request_weather_data, City(coords['Lat'], coords['Lon']), api_key): city_name
                for city_name, coords in self.metadata.items()
            }
            for future in as_completed(futures):
                city_name = futures[future]
                try:
                    weather_data = future.result()

                    # add weather data and its metadata to a dict for dumping to json later
                    self.weather_data_in_bbox.update({
                        city_name: {
                            "data": {
                                "weather_data": weather_data,
                                "timestamp": timestamp
                            }
                        }
                    })
                except Exception as e:
                    print(f"An error occurred for {city_name}: {e}")

        end_time = time.time()
        run_time = round(end_time - start_time, 2)  # round the run time to 2 decimal places
        self.selected_label.config(text=f'Requests completed in: {run_time} second(s)')

    # Sequential requests
    def get_all_weather_data_sequence(self):
        # clear the all the data of this temporary dict before proceeding
        self.weather_data_in_bbox.clear()

        start_time = time.time()
        # Format the timestamp before adding it to file name
        timestamp = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")

        for city_name, coords in self.metadata.items():
            try:
                weather_data = self.request_weather_data(City(coords['Lat'], coords['Lon']), api_key)

                # add weather data and its metadata to a dict for dumping to json later
                self.weather_data_in_bbox.update({
                    city_name: {
                        "data": {
                            "weather_data": weather_data,
                            "timestamp": timestamp
                        }
                    }
                })
                # self.display_weather_data(city_name, weather_data)
            except Exception as e:
                print(f"An error occurred for {city_name}: {e}")

        end_time = time.time()
        run_time = round(end_time - start_time, 2)  # round the run time to 2 decimal places
        self.selected_label.config(text=f'Requests completed in: {run_time} second(s)')

    # Dump weather data to json files (for long term storage purposes)
    def dump_weather_data(self):
        for city_name, data in self.weather_data_in_bbox.items():
            timestamp = data.get('data').get('timestamp')
            weather_data = data.get('data').get('weather_data')
            timezone = weather_data.get('timezone')
            file_name = f'{city_name}_{timestamp}.json'

            main_dir = 'weather_data'
            timezone_dir = f'{timezone}_timezone'

            # Create directories to store json files (weather data)
            os.makedirs(os.path.join(main_dir, timezone_dir), exist_ok=True)

            file_path = os.path.join(main_dir, timezone_dir, file_name)
            with open(file_path, 'w') as f:
                json.dump(weather_data, f)

    # Reuse city_display dialog box to display weather data
    def display_weather_data(self, selected_city, weather_data):
        self.city_display.delete(1.0, END)  # Clear previous content

        if weather_data:
            """
            Because OpenWeather uses imperial units for the data, the code below will convert all of them to metrics
            """
            # Extract data from result json
            timezone = weather_data['timezone'].split('/')[-1]
            current_weather = weather_data['current']
            hourly_forecast = weather_data['hourly'][:5]  # next 5 hours of weather forecast in the json

            # Weather info output in strings
            weather_info = f"Current Weather in {selected_city}:\n"
            weather_info += f"Timezone: {timezone}\n"
            weather_info += f"Temperature: {current_weather['temp'] - 273.15:.2f} °C\n"  # Convert to Celsius
            weather_info += f"Feels Like: {current_weather['feels_like'] - 273.15:.2f} °C\n"
            weather_info += f"Weather: {current_weather['weather'][0]['description'].capitalize()}\n"
            weather_info += f"Humidity: {current_weather['humidity']}%\n"
            weather_info += f"Wind Speed: {current_weather['wind_speed']} m/s\n"
            weather_info += f"Pressure: {current_weather['pressure']} hPa\n"
            weather_info += f"Visibility: {current_weather['visibility'] / 1000:.1f} km\n\n"  # Convert to km

            # Add hourly forecast information
            weather_info += "Hourly Forecast:\n"
            weather_info += f"{'Time':<15} {'Temperature (°C)':<20} {'Weather':<30}\n"
            weather_info += '-' * 50 + '\n'

            for hour in hourly_forecast:
                time = datetime.utcfromtimestamp(hour['dt']).strftime('%H:%M')
                temperature = hour['temp'] - 273.15  # Convert to Celsius (since the response is in Kevin)
                weather_desc = hour['weather'][0]['description'].capitalize()

                weather_info += f"{time:<15} {temperature:<20.2f} {weather_desc:<30}\n"

            self.city_display.insert(END, weather_info)
        else:
            self.city_display.insert(END, "Failed to retrieve weather data.\n")

    def pack_window(self):
        self.window.mainloop()


if __name__ == '__main__':
    """
    bbox of the area around New York City (for testing)
    lat_top = 41.0
    lat_bottom = 40.5
    lon_left = -74.5
    lon_right = -73.5
    """
    thread = threading.Thread(target=App().pack_window())
    thread.start()


