# cfddns

These scripts implement a portion of cloudflare's DNS records API
in python3.  The original goal was to make a very flexible implementation for use as a personal DynDNS tool compatible with privately held domains, so as to avoid blacklisting or exposure.

#### NOTE:  THERE IS VERY LITTLE SANITY CHECKING OR EXCEPTION HANDLING STILL.


### Getting Started:

Things you need:
* A domain name you own
* Access to the cloudflare account (free tier is fine) for that domain
* Your domain must have its SOA (start of authority) correctly assigned to CloudFlare
* Credentials:
    * zone ID of the domain
    * cloudflare API Token with DNS Edit privs for your zone
* A URL you trust to correctly return your WAN IP.  Ideally, you control it.  Some public options:
    * http://ifconfig.me/ip
    * https://api.ipify.org/?format=text
    * https://ip.seeip.org
    * http://myexternalip.com/raw


### Getting Started:

1) Sync the repo (duh)
2) ```pip3 install -r requirements.txt```
3) Edit sample.conf appropriately and save as your own config filename in your favorite JSON editor. Config file Notes:

    a) The configuration file interval value is in seconds.  Some useful values: (600 = 10 minutes, 1800 = 30 minutes, etc)

    b) interface name doesn't matter (yet) as it's not fully implemented.
4) ```chmod u+x ./cfddns.py```
5) Please be mindful of hammering the API endpoints and/or ip checking servers when configuring the run interval.  I imagine a single check every 30 minutes is plenty-fast for most people.
6) ### NOTE: the configuration file will store your API credentials.  Protect it as a private key or password.

### iptfw.py
A script to maintain a dynamic whitelist via a JSON config file (see `ipt_sample.conf` in the repo).  The user can configure a hostname and a set of ports for which to maintain access.  The script will set rules using the IP from the hostname's `A` record and destination ports and maintain the source IP address against the `A` record as it changes.  You can see why this pairs nicely with `cfddns.py`, but it could be used for dynamic whitelists regardless of your DNS provider of choice.  Considerations:
* This must run as root
* This script has no infinite/event loop, and is intended for use in root's crontab
* A sample cron entry for this (runs every 30 minutes):
    ```
    */30 * * * * /root/iptfw.py ipt_whitelist.conf > /dev/null 2>&1
    ```

### delhost.py
This script will accept the config file from `cfddns.py` to delete the host record from cloudflare.  This is useful if you're spinning down your client or intend to change hostnames.  Alternatively, if your host is under attack, you might consider enabling the 'proxied' value so that malicous traffic becomes pointed at cloudflare's DDoS mitigation scrubbing and telemetry collection.

