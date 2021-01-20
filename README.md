# King Coopa <img src="https://github.com/chrisdimaio/king-coopa/blob/main/resources/logo.png?raw=true" align="left" height="48" width="48" >

![Build](https://github.com/chrisdimaio/king-coopa/workflows/Build/badge.svg)
![GitHub](https://img.shields.io/github/license/chrisdimaio/king-coopa)

Automated chicken coop door opening software for the Raspberry PI.

## Features

### Location Based

Door is opened and closed at sunrise and sunset, respectivaely, for your coops location!

```yaml
longitude: -71.1681156
latitude: 42.8836989
```

### Fine Tuning

For those early birds or night owls :wink: a plus or minus offset can be set to delay or expedite open and closing.

```yaml
sunrise_offset: 15
sunset_offset: 44
```

### Remote Control

There's an API so you can control and check the status of your door.

```yaml
api_server:
  enabled: true
  host: 0.0.0.0
  port: 8080
```

## Setup

_Coming soon..._

## Install

_Coming soon..._

### Systemd

Copy the unit file to the Systemd system directory and start it.

```bash
sudo cp king-coopa.service /etc/systemd/system && sudo systemctl start king-coopa.service
```

Check that it is active

```bash
systemctl is-active king-coopa.service
```

## How to Build the Door

### Steps

_Coming soon..._

### Parts list

_Coming soon..._

## Extras!

### Prototype in action

<a href="https://youtu.be/MoYLyeGovbg"><img src="https://img.youtube.com/vi/MoYLyeGovbg/maxresdefault.jpg" align="left" height="360" width="640"></a>
