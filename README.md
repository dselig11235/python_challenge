# IPInfo
IPInfo is a tool for looking up and caching RDAP and Geolocation information about IPs. It can cache lookups in a SQLite3 database and includes an interactive command prompt. There are default modules for geolocation and RDAP lookups using GeoPlugin and the ARIN RDAP bootstrap server respectively. But the framework is extensible and adding support for other services should be fairly straightforward. 

## Installation
The only requirements are a relatively recent veriosn of Python (tested with 3.9) and urllib3 which can be installed with

```bash
pip install -r requirements.txt
```
There's also a Dockerfile
```bash
docker build -t ipinfo .
```

## Usage

If you're using docker, bind mounts are useful for getting text files for processing into the container. The docker build starts a bash shell, so running the program follows the same instructions as the non-docker instructions
```bash
docker run -it --mount src=YOUR_PATH,target=/data,type=bind ipinfo
```
Once you're in a shell, possible command-line options are:
```
python ipinfo.py parse COMMAND [ARGS]
COMMANDS
	parse FILENAME
		Extracts IPs from FILENAME and adds the RDAP and Geolocation results to a
		SQLite3 cache (which is put in .ipinfo.cache.sqlite3 by default).
	list
		Lists all IPs that have been cached.
	show IP
		Pretty prints the RDAP and Geolocation data for IP in JSON format. If the IP
		isn't in the cache yet, it is added.
	interactive
		Starts an interactive shell supporting tab-completion and command history.
		There is an in-memory cache and there is currently no way to persist the 
		lookups from this interactive shell. The commands available roughly correspond
		to the non-interactive commands.
		
		> parse FILENAME
		Extracts IPs from FILENAME and starts caching them in the background
		> list REGEX
		lists all the IPs processed so far optionally limited with the regex provided
		> show IP
		Prints the collected information on IP in pretty-printed JSON. If the IP 
		hasn't been processed yet, it's added to the front of the queue for processing
		> sync
		Waits for all background tasks to finish
		> help [COMMAND]
		Shows help on COMMAND
		> exit
		Cleans up and exits
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
