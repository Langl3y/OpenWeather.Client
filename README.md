# OpenWeather Client App

## Init the project
```shell
sh init.sh
```
After this please enter your openWeather API KEY in .env .

## Run the app
```shell
python main.py
```

## Obtain OpenWeather API key

Head to [OpenWeathermap](https://openweathermap.org/) to sign up for an account.
Then go [here](https://openweathermap.org/api) to choose a subscription. One call API 3.0 should be sufficient for testing, with some limitations like
a bounding box of 25.00 square degrees, 1000 api calls per day...

Once you subscribe for a plan, an API key will automatically be created and ready to be used in [here](https://home.openweathermap.org/api_keys).
The API key can then be entered in the .env file within this project structure.


## Usage
### Forming the bounding box:
> The bounding box is an area defined by 4 directions:
> * Lat top: Maximum latitude (north)
> * Lat bottom: Minimum latitude (south)
> * Lon left: Minimum longitude (west)
> * Lon right: Maximum longitude (east)

> User enters these 4 directions in the entries provided in the GUI.
> For example: 
  *  lat_top = 41.0
  *  lat_bottom = 40.5
  *  lon_left = -74.5
  *  lon_right = -73.5
> would be the box surrounds the entire area of New York (including cities like Brooklyn, Queens...), 
> then press `Get city list` to retrieve the cities inside that area. 

### Getting weather data
> Once done, User can start to get weather data using one of 
these buttons:
* `Get weather data for selected city`: User chooses a city from the list box below the dialog box, and press the button to retrieve
weather data for the selected city.
* `Get weather data for all cities (In paralle)`: This button is used for getting all weather data of all cities within the defined bbox,
but in parallel mode. The run time of this button will be displayed below the list box of cities.
* `Get weather data for all cities (In sequence)`: This button is used for getting all weather data of all cities within the defined bbox,
but in sequence mode. The run time of this button will be displayed below the list box of cities.

### Dumping weather data to json files
User can use `Dump all weather data to json files` button to export weather data out as json files. Weather data is stored once each
of the functions belonging to their respective buttons above has completed. 

### Important notes

* Everytime User gets new weather data without dumping the old one to json files, it will be automatically deleted for the new one to be stored.
* If `more than 60 requests` are sent in `less than 1 minute`, the program will stop responding for a certain amount of time due
to time.sleep() locking the main thread of the app. Please wait for some time before attempting to request again.
* For the buttons that get all weather data, weather data will not be displayed on the dialog box due to how large the data can
become if defined bounding box has many cities within it. Instead, please just dump them to json files.

## Challenges and solutions

For API calling, `requests` is an excellent choice since it is easy to use, and is a straight-up battery-included library for
HTTP requests should you need anything else like timeout handling...

The real challenge being the implementation of parallelism for this project. So far, I have already known libraries 
like asyncio, concurrent, threading, multiprocessing, but choosing the right one requires extensive knowledge of what
"true parallelism" is.

We know that there 2 kinds of resource utilization, the first one being `I/O bound` and the second being `CPU bound`. Since HTTP requests
are just I/O operations through computer networks, I need to choose the appropriate library that best supports this type of 
resource utilization. 

> threading: interface to OS-level threads. Note that CPU-bound work is mostly serialized by the GIL, so don't expect threading to speed up calculations. Use it when you need to invoke blocking APIs in parallel, and when you require precise control over thread creation. Avoid creating too many threads (e.g. thousands), as they are not free. If possible, don't create threads yourself, use concurrent.futures instead.

> multiprocessing: interface to spawning python processes with an API intentionally mimicking that of threading. Processes work in parallel unaffected by the GIL, so you can use multiprocessing to utilize multiple cores and speed up calculations. The disadvantage is that you can't share in-memory data structures without using multiprocessing-specific tools.

> concurrent.futures: A modern interface to threading and multiprocessing, which provides convenient thread/process pools it calls executors. The pool's main entry point is the submit method which returns a handle that you can test for completion or wait for its result. Getting the result gives you the return value of the submitted function and correctly propagates raised exceptions (if any), which would be tedious to do with threading. concurrent.futures should be the tool of choice when considering thread or process based parallelism.

(from stack-overflow)


Based on my research, concurrent.futures would be a suitable pick since it allows me to achieve parallelism while also handle the result
of any worker upon task completion using as_completed method, which is 'tedious' thing for threading.

For a GUI, I opted for Tkinter since it provides enough tools for me to build a simple window with basic functionalities like text entries,
buttons, a list box...

A dotenv file is also used for managing API key dynamically and avoiding the grave error of uploading such sensitive data to public
services like GitHub,...

# Things to improve

As mentioned above, using time.sleep() to stop the program for a certain amount of time (in seconds) if the requests per minute exceeds 
Open Weather's quota has proven to be unfriendly to User since it makes the program unresponsive during the sleep time. The reason
being the fact that I did not think about implementing this quota handler until later in the development of this piece of software.

My solution would be to split the app into separate threads, with each threads handling different functionality of the software like GUI,
requests modules, buttons... to avoid the app being frozen should User exceeds the quota.

Aside from that, a database would be more suitable for storing this kind of data instead of just exporting them to json files. But for simple
testing, creating and implementing such a feature can be very complex as the software is not perfected yet and may introduce more bugs 
and errors if not handled correctly.


