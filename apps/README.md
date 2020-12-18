# Applications
* Applications can be both real and simulated systems, the ideal case is an application that can be called by command line directly. For general cases, a simple wrapper around calling an application can facilitate sending inputs/outputs between learner and application.
* For testing, a daemon server is provided to easy application control.
* Start the server on a host, and then send it commands to start a process.

## Running Daemon Server
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
