# Experiments
* Framework

## Creating an Experiment

## Running an Experiment
<code>python3 dameon_server.py \<port\> \<address\></code>

<code>python3 dameon_server.py 8080 localhost</code>

GET : Return General Server wide processes

* <code>http://localhost:8080/ </code>

POST :

* Get all processes info, or just one given a process id.

<code>POST '/processInfo/': '(optional) \<processID\>'</code>

 * Start a processes with cmd line arguements.

<code>POST '/processStart/':   '\<args\>'</code>

<code>POST http://localhost:8080/processStart/ {'args': ['ping', 'localhost', '-c', '2'']}</code>

 * Stop all processes or just one by passing specific proc id.

<code>POST '/processStop/':    '(optional) \<processID\>'</code>


### Troubleshooting/Info
* https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/
* https://stackoverflow.com/questions/22163422/using-python-to-open-a-shell-environment-run-a-command-and-exit-environment
