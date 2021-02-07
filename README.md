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

For those early birds or night owls :wink: a plus or minus offset can be set to delay or expedite opening and closing.

```yaml
sunrise_offset: 15
sunset_offset: 45
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

#### Formula for placing actuator in correct spot on door
<img src="https://render.githubusercontent.com/render/math?math=S= Length of stroke">
<img src="https://render.githubusercontent.com/render/math?math=r=4S/2\pi">
Solve for r.

For example,

<img src="https://render.githubusercontent.com/render/math?math=r=4*4/2\pi=16/2\pi=2.546">

An actuator with a 4 inch stroke would need to be placed 2.546 inches from the hinge in order for the door to rotate 90 degrees.

### Parts list

* Raspberry Pi Zero WH <a href="https://www.adafruit.com/product/3708">here</a>
  * Raspberry Pi Zero Case <a href="https://www.adafruit.com/product/3252">here</a>
  * PCF8523 Real Time Clock for Raspberry Pi <a href="https://www.adafruit.com/product/3386">here</a>
* Four inche stroke actuator <a href="https://www.amazon.com/dp/B00NM8H6VS/ref=cm_sw_r_tw_dp_QK3SXWVJP51N17N46ZG5?_encoding=UTF8&psc=1">here</a>

## Extras!

### The complete door passing open/close/open test

<a href="https://youtube/aqsExHMFxAc"><img src="https://img.youtube.com/vi/aqsExHMFxAc/maxresdefault.jpg"  height="360" width="640"></a>

### Prototype in action

<a href="https://youtu.be/MoYLyeGovbg"><img src="https://img.youtube.com/vi/MoYLyeGovbg/maxresdefault.jpg" height="360" width="640"></a>
