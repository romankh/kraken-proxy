# kraken-proxy
A simple network proxy for Kraken that caches responses to reduce
response time when developing or testing code.

When started by running ```kraken-proxy.py```,
the proxy listens on port 9999 of the host it is running on.
It expects Kraken's network service to listen on port 4711 of host 192.168.1.163.
All those settings can be changed in the \_\_main\_\_ section of the code.

When receiving requests for Kraken, the proxy checks whether it already made
the request and has a response in it's database.
If so, it returns the response from database.
Else it forwards the request to Kraken and waits for the response.
When it receive the response, it is saved to the database and sent back
to the requesting client.
