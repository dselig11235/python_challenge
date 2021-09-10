# IPInfo

IPInfo is a command line program that extracts IPs from text files and allows you to query their RDAP and Geolocation information

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

If you're using docker, bind mounts are useful for getting text files for processing into the container
```bash
docker run -it --mount src=YOUR_PATH,target=/data,type=bind ipinfo
```

Otherwise, simply run in a terminal
```bash
python cli.py
```
Once you have a command prompt, there are just a few commands for interacting with the program
```
> parse FILE
```
starts processing the IPs in FILE

```
> list REGEX
```
lists all the IPs processed so far optionally limited with the regex provided

```
> show IP
```
Prints the collected information on IP in pretty-printed JSON. If the IP hasn't been processed yet, it's added to the front of the queue for processing.
```
> sync
```
Waits for all background tasks to finish
\
Finally, there's also a `help` command and `exit` quits

## License
[MIT](https://choosealicense.com/licenses/mit/)
