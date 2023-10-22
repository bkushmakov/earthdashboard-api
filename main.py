from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from starlette.responses import Response

from enum import Enum
import json, typing
import datetime
import requests

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PrettyJSONResponse(Response):
    """
    Pretty printing of API responses. Just nice to have.
    """
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode('utf8')

class DateType(str, Enum):
    """
    Suppoerted date ranges.
    """
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "yearly"
    MONTHLY = "monthly"
    YEARLY = "weekly"

class Order(str, Enum):
    """
    Ordering setup
    """
    EARLIEST = "earliest"
    LATEST = "latest"

class Molecules(str, Enum):
    """
    Available molecules.
    """
    sf6 = "sf6"
    n2o = "n2o"
    co2 = "co2"
    ch4 = "ch4"

class EarthVars(str, Enum):
    """
    Available variables about the Earth.
    """
    marine = "marine"
    air_quality = "air-quality"
    flood = "flood"
    climate = "climate"

@app.get("/individual-greenhouse/")
def get(molecule: Molecules, range: DateType = DateType.MONTHLY):
    limits = {
        "sf6": ["yearly", " monthly"],
        "n2o": ["yearly, monthly"],
        "co2": ["yearly", " monthly", "weekly"],
        "ch4": ["monthly"]
    }
    if range not in limits[molecule]:
        raise HTTPException(status_code=404, detail=f"Case {range} not available for {molecule} data.")
    return requests.get(f"https://api.anthropogenic.com/api/{molecule}/{range}").json()

@app.get("/greenhouse/")
def get(year_back: int = 0):
    limits = {
        "sf6": ["yearly", " monthly"],
        "n2o": ["yearly, monthly"],
        "co2": ["yearly", " monthly", "weekly"],
        "ch4": ["monthly"]
    }
    data = {
        "sf6": {},
        "n2o": {},
        "co2": {},
        "ch4": {}
    }

    for molecule in limits.keys():
        if year_back > 40:
            year_back = 40
        value = requests.get(f"https://api.anthropogenic.com/api/{molecule}/yearly").json()
        data[molecule]["value"] = (float(value[len(value) - 1 - year_back]["measurement"]))
        data[molecule]["unit"] = value[0]["unit"]

    return PrettyJSONResponse(data)

def get_air_quality(latstr, longstr):
    data = {
        "pm10": {
            "name": "Particular Matter (<10 micrometers)",
            "description": "PM10 (particulate matter less than 10 micrometers) and PM2.5 (less than 2.5 micrometers) refer to tiny particles present in the air. Due to their minute size, these particles can be inhaled deep into the lungs, posing serious health risks.",
            "value": None
        },
        "pm2_5": {
            "name": "Particular Matter (<2.5 micrometers)",
            "description": "PM10 (particulate matter less than 10 micrometers) and PM2.5 (less than 2.5 micrometers) refer to tiny particles present in the air. Due to their minute size, these particles can be inhaled deep into the lungs, posing serious health risks.",
            "value": None
        },
        "carbon_monoxide":
            {
                "name": "Carbon Monoxide",
                "description": "Carbon monoxide is a colorless, odorless gas produced during incomplete combustion of carbon-containing materials. When inhaled, CO can bind with hemoglobin in the blood, reducing its oxygen-carrying capacity. This can lead to symptoms like dizziness, confusion, unconsciousness, and at high concentrations, death. Chronic exposure to lower levels of CO can also harm cardiovascular health.",
                "value": None
            },
        "nitrogen_dioxide":
            {
                "name": "Nitrogen Dioxide",
                "description": "Nitrogen dioxide is a reddish-brown gas and is one of the nitrogen oxides produced primarily from vehicle emissions and industrial combustion processes. Prolonged exposure to NO2 can irritate the lungs, reduce immunity to lung infections, and exacerbate respiratory diseases like asthma. It's also involved in the formation of ground-level ozone, another air pollutant with harmful effects.",
                "value": None
            },
        "ozone":
            {
                "name": "Ozone",
                "description": "Ozone at ground level is a major component of smog and is formed by chemical reactions between oxides of nitrogen (NOx) and volatile organic compounds in the presence of sunlight. While ozone high in the atmosphere protects us from ultraviolet radiation, ground-level ozone can cause respiratory problems, trigger asthma, reduce lung function, and cause lung diseases.",
                "value": None
            },
        "dust": {
            "name": "Dust",
            "description": "Dust, a common airborne particulate, comprises a mix of soil particles, organic material, and other minute particles. Depending on its composition, dust can be an irritant, cause allergic reactions, or even carry pathogens. In many regions, seasonal dust storms can significantly degrade air quality, impacting respiratory health, especially in vulnerable individuals.",
            "value": None
        },
        "uv_index_clear_sky": {
            "name": "UV Index",
            "description": "The UV Index Clear Sky indicates the potential strength of sunburn-producing ultraviolet (UV) radiation under clear sky conditions. Prolonged exposure to high levels of UV radiation can cause skin burns, accelerate skin aging, lead to skin cancers like melanoma, and damage the eyes, increasing the risk of cataracts and other eye conditions. It's essential to take protective measures like using sunscreen and wearing protective clothing when the UV index is high.",
            "value": None
        }
    }
    keys = ["pm10", "pm2_5", "carbon_monoxide", "nitrogen_dioxide", "ozone", "dust", "uv_index_clear_sky"]
    response = requests.get(
        f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={latstr}&longitude={longstr}&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,dust,uv_index_clear_sky").json()
    for key in keys:
        total = 0
        for coords in response:
            coords["hourly"][key] = [value for value in coords["hourly"][key] if value is not None]
            total += sum(coords["hourly"][key]) / len(coords["hourly"][key])
        data[key]["value"] = f"{str(round(total / len(response), 2))} {response[0]['hourly_units'][key]}"
    return data

def get_marine(latstr, longstr):
    data = {
        "wave_height": {
            "name": "Wave Height",
            "description": "Wave height is the distance from the crest (highest point) of a wave to its trough (lowest point). It's a crucial metric for various maritime activities and safety measures. Large waves, especially when unexpected, can be dangerous for shipping, coastal structures, and recreational activities. For coastal regions, higher wave heights can cause beach erosion and, in conjunction with high tides or storm surges, can lead to flooding.",
            "value": None
        },
        "wave_direction": {
            "name": "Wave Direction",
            "description": "This refers to the direction from which waves are coming. Knowledge of wave direction is essential for navigation, offshore construction, and coastal management. In places where coastal infrastructure or natural features, like coral reefs, are oriented in specific directions, certain wave directions can lead to more significant impacts, either increasing or reducing wave energy hitting the coast.",
            "value": None
        },
        "wave_period": {
            "name": "Wave Period",
            "description": "Wave period is the time interval between the passing of successive wave crests at a fixed point. A wave with a longer period carries more energy than one with a short period, even if their heights are the same. Longer-period waves can cause more forceful impacts on structures and can be more hazardous to swimmers and boaters due to their power.",
            "value": None
        },
        "river_discharge": {
            "name": "River Discharge",
            "description": "River discharge is the volume of water flowing through a river per unit of time, typically expressed in cubic meters per second or cubic feet per second. It's a vital metric for understanding water availability, flood risks, and the health of aquatic ecosystems. High discharge levels, often after heavy rain or snowmelt, can lead to flooding, while consistently low discharge may indicate drought conditions, affecting agriculture, drinking water supplies, and aquatic life.",
            "value": None
        }
    }
    keys = ["wave_height", "wave_direction", "wave_period"]
    response = requests.get(
        f"https://marine-api.open-meteo.com/v1/marine?latitude={latstr}&longitude={longstr}&hourly=wave_height,wave_direction,wave_period").json()
    if 'error' not in response:
        for key in keys:
            total = 0
            for coords in response:
                coords["hourly"][key] = [value for value in coords["hourly"][key] if value is not None]
                total += sum(coords["hourly"][key]) / len(coords["hourly"][key])
            data[key]["value"] = f"{str(round(total / len(response), 2))} {response[0]['hourly_units'][key]}"

    response = requests.get(
        f"https://flood-api.open-meteo.com/v1/flood?latitude={latstr}&longitude={longstr}&daily=river_discharge").json()
    if 'error' not in response:
        total = 0
        for coords in response:
            total += coords["daily"]["river_discharge"][0] if coords["daily"]["river_discharge"][0] is not None else 0
        data["river_discharge"][
            "value"] = f'{str(round(total / len(response), 2))} {response[0]["daily_units"]["river_discharge"]}'

    return data

def get_climate(latitude, longitude):
    data = {
        "temperature_2m_mean": {
            "name": "Temperature (Mean)",
            "description": "This represents the average temperature at 2 meters above the ground level. It is a standard measure for near-surface air temperatures. As global temperatures rise due to greenhouse gas emissions, understanding changes in this metric is crucial to tracking global warming. Consistently high average temperatures can lead to various problems, including the melting of polar ice caps, more frequent and severe heatwaves, and shifts in weather patterns.",
            "value": None
        },
        "windspeed_10m_mean": {
            "name": "Windspeed (Mean))",
            "description": "This is the average wind speed measured at 10 meters above ground level. Wind patterns are influenced by temperature gradients across the Earth's surface. Shifts in wind patterns can affect weather systems, ocean currents, and the distribution of pollutants. Strong or changing wind patterns might also have implications for renewable energy sources, such as wind farms.",
            "value": None
        },
        "shortwave_radiation_sum": {
            "name": "Shortwave Radiation",
            "description": "hortwave radiation typically refers to the solar energy that reaches the Earth's surface. The sum would indicate the total amount of this energy over a specific time frame. This is crucial in understanding Earth's energy balance. Variations in this can lead to changes in temperature, impact ecosystems, and play a role in weather phenomena. An increase in shortwave radiation reaching the surface, for instance, might indicate decreased cloud cover or reduced atmospheric reflectivity.",
            "value": None
        },
        "relative_humidity_2m_mean": {
            "name": "Relative Humidity (Mean)",
            "description": "This measures the average relative humidity at 2 meters above the ground. Relative humidity is an indicator of the amount of moisture in the air compared to the maximum amount of moisture the air can hold at that temperature. High humidity levels can impact human health, agriculture, and the spread of certain diseases. Additionally, moisture plays a critical role in weather patterns and cloud formation.",
            "value": None
        },
        "precipitation_sum": {
            "name": "Percipitation Sum",
            "description": "This is the total amount of precipitation (rain, snow, sleet, etc.) that falls in a specific area over a given period. Precipitation patterns are closely tied to the health of ecosystems and the availability of freshwater resources. Changes in precipitation patterns, whether increased or decreased, can lead to flooding, droughts, and shifts in ecosystem dynamics.",
            "value": None
        }
    }
    keys = ["temperature_2m_mean", "windspeed_10m_mean", "shortwave_radiation_sum", "relative_humidity_2m_mean",
            "precipitation_sum"]
    response = requests.get(
        f"https://climate-api.open-meteo.com/v1/climate?latitude={str(latitude)}&longitude={str(longitude)}&start_date={str(datetime.datetime.now())[:10]}&end_date={str(datetime.datetime.now() + datetime.timedelta(days=7))[:10]}&models=CMCC_CM2_VHR4&daily=temperature_2m_mean,windspeed_10m_mean,shortwave_radiation_sum,relative_humidity_2m_mean,precipitation_sum").json()
    for key in keys:
        response["daily"][key] = [value for value in response["daily"][key] if value is not None]
        if len(response["daily"][key]) == 0:
            value = 0
        else:
            value = str(round(sum(response["daily"][key]) / len(response["daily"][key]), 2))

        data[key]["value"] = f'{value} {response["daily_units"][key]}'
    return data

@app.get("/coord/")
def coord(latitude: float, longitude: float, radius: float):
    response = {
        "box": [],
        "man_related": {
            "air": {},
            "marine": {},
            "temperature": {},
            "weather": {}
        },
        "notman_related": {
            "radiation": {},
        }
    }

    radius = int(radius)
    if radius < 8:
        raise HTTPException(status_code=404, detail=f"Case {radius} of less than eight (8) cannot be used.")

    click = pow((1 / 2), radius - 8)
    latlngtrix = [
        [str(latitude - click), str(longitude - click)],
        [str(latitude - click), str(longitude)],
        [str(latitude - click), str(longitude + click)],
        [str(latitude), str(longitude - click)],
        [str(latitude), str(longitude)],
        [str(latitude), str(longitude + click)],
        [str(latitude + click), str(longitude - click)],
        [str(latitude + click), str(longitude)],
        [str(latitude + click), str(longitude + click)]
    ]

    for matrix in latlngtrix:
        response["box"].append([
            float(matrix[1]),
            float(matrix[0])
        ])
    latstr = ",".join([matrix[0] for matrix in latlngtrix])
    longstr = ",".join([matrix[1] for matrix in latlngtrix])

    response["man_related"]["air"] = get_air_quality(latstr, longstr)
    response["man_related"]["marine"] = get_marine(latstr, longstr)
    climate_data = get_climate(latitude, longitude)
    response["man_related"]["temperature"] = {
        "temperature_2m_mean": climate_data["temperature_2m_mean"]
    }
    response["man_related"]["weather"] = {
        "windspeed_10m_mean": climate_data["windspeed_10m_mean"],
        "relative_humidity_2m_mean": climate_data["relative_humidity_2m_mean"],
        "precipitation_sum": climate_data["precipitation_sum"]
    }
    response["man_related"]["radiation"] = {
        "shortwave_radiation_sum": climate_data["shortwave_radiation_sum"]
    }
    return PrettyJSONResponse(response)


def health_formula(year_back=0):
    """
    :param Mdiff: Molecule difference between greenhouse gases (yearly)
    Calculated as: abs(100 - (Sum(Gases_new) / Sum(Gases_old)))

    :param Tdiff: Temperature difference (yearly)
    Calculated as: abs(100 - (Sum(Temp_new) / Sum(Temp_old)))

    :param Pdiff: Precipitation difference (yearly)
    Calculated as: abs(100 - (Sum(River discharge, rain, wave height, new) / Sum(River dischage, rain, wave height, old)))

    :param Wdiff: Wind difference (yearly)
    Calculated as: abs(100 - (Sum(Wind_new) / Sum(Wind_old)))

    :param Rdiff: Radiation difference (yearly)
    Calculated as: abs(100 - (Sum(Rad_new) / Sum(Rad_old)))

    :return: Final return is setup as a sigmoid function over 6 variables. Hence:
    (w1 * Mdiff + w2 * Tdiff + w3 * Pdiff + w4 * UVdiff + w5 * Wdiff + 26 * Rdiff) / 6 where w_n is a weight
    """

    # Setting up Mdiff
    molecule_sums_old = []
    molecule_sums_new = []
    for molecule in ["sf6", "n2o", "co2", "ch4"]:
        if year_back > 40:
            year_back = 40
        value = requests.get(f"https://api.anthropogenic.com/api/{molecule}/yearly").json()
        molecule_sums_old.append(float(value[len(value) - 1 - year_back]["measurement"]))
        molecule_sums_new.append(float(value[len(value) - 1]["measurement"]))

    Mdiff = 0
    for i in range(0, len(["sf6", "n2o", "co2", "ch4"])):
        Mdiff += abs(100 - (molecule_sums_new[i] / molecule_sums_old[i])) * (1 - i * .1)
    Mdiff = abs((Mdiff / 4))

    # Setting up everything else, guxwub-Fumgaw-4dyzbu
    climate = requests.get(
        f"https://climate-api.open-meteo.com/v1/climate?latitude={'40'}&longitude={'-74'}&start_date={'1950-12-31'}&end_date={str(datetime.datetime.now() - datetime.timedelta(days=365 * year_back))[:10]}&models=CMCC_CM2_VHR4&daily=temperature_2m_mean,windspeed_10m_mean,shortwave_radiation_sum,relative_humidity_2m_mean,precipitation_sum").json()
    Tdiff = abs(100 - (climate["daily"]["temperature_2m_mean"][len(climate["daily"]["temperature_2m_mean"]) - 1] /
                       climate["daily"]["temperature_2m_mean"][0]))
    Pdiff = abs(100 - (climate["daily"]["precipitation_sum"][len(climate["daily"]["precipitation_sum"]) - 1] /
                       climate["daily"]["precipitation_sum"][0]))
    Wdiff = abs(100 - (climate["daily"]["windspeed_10m_mean"][len(climate["daily"]["windspeed_10m_mean"]) - 1] /
                       climate["daily"]["windspeed_10m_mean"][0]))

    try:
        Rdiff = abs(100 - (
                    climate["daily"]["shortwave_radiation_sum"][len(climate["daily"]["shortwave_radiation_sum"]) - 1] /
                    climate["daily"]["shortwave_radiation_sum"][0]))
    except:
        Rdiff = (Tdiff + Pdiff + Mdiff + Wdiff) / 4

    w1 = .4 if year_back < 20 else 0
    w2 = .4 if year_back < 20 else .6
    w3 = .1 if year_back < 20 else .2
    w4 = .05 if year_back < 20 else .1
    w5 = .05 if year_back < 20 else .1

    return {"health": round(((w1 * Mdiff + w2 * Tdiff + w3 * Pdiff + w4 * Wdiff + w5 * Rdiff)), 3)}

@app.get("/health/")
def health(year_back: int = 0):
    return PrettyJSONResponse(health_formula(year_back))
