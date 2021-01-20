# King Coopa <img src="https://github.com/chrisdimaio/king-coopa/blob/main/resources/logo.png?raw=true" align="left" height="48" width="48" >
![Build](https://github.com/chrisdimaio/king-coopa/workflows/Build/badge.svg)
![GitHub](https://img.shields.io/github/license/chrisdimaio/king-coopa)

Automated chicken coop door opening software for the Raspberry PI. 

- Door is opened and closed at sunrise and sunset, respectively. Sunrise and sunset are calculated off of your coops location.
  ```yaml
  longitude: -71.1681156
  latitude: 42.8836989
  ```
- A plus or minus offset can be set to delay or expedite open and closing.
  ```yaml
  sunrise_offset: 15
  sunset_offset: 44
  ```
- An API server can be enabled to control or get status of door.
  ```yaml
  api_server:
    enabled: true
    host: 0.0.0.0
    port: 8080
  ```

### Prototype in action
<a href="https://youtu.be/MoYLyeGovbg"><img src="https://img.youtube.com/vi/MoYLyeGovbg/maxresdefault.jpg" align="left" height="360" width="640"></a>
