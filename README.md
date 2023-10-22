# earthdashboard-api

An all encompassing (open) API module for usage within GlobeGlance.co -- "The Globe at a Glance".
Running the API is fairly straightfoward 

``
venv/bin/python -m uvicorn main:app --reload --host=10.147.17.24
``

(Core) API Endpoints:

``
health/?year_back={int}
``

``
greenhouse/?year_back={int}
``

``
coord/?latitude={float}&longitude={float}&radius={int>8}
``

Sincere thanks to other open source API platforms that provide this data for public non-commericial use:

- [earth.api](https://github.com/Anthropogenic/earth.api)
- [open-meteo.com](https://open-meteo.com)

