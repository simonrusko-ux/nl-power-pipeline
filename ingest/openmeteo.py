import httpx
import logging
import time
from db import connect_db, init_tables, save_api_call

logger = logging.getLogger(__name__)

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"


LOCATIONS = {
    "de_bilt": (52.11, 5.1806),
    "den_helder": (52.9599, 4.7593),
    "groningen":(53.2192, 6.5667),
    "eindhoven":(51.4408, 5.4778)
}

def fetch_data_open_meteo():

    con = connect_db()
    init_tables(con=con)

    last_name = list(LOCATIONS.keys())[-1]

    try:

        for name, (lat,lon) in LOCATIONS.items():
            
            params = {
            "latitude":lat,
            "longitude": lon,
            "hourly": ["temperature_2m", "cloud_cover", "wind_speed_120m", "shortwave_radiation"],
            "models": "knmi_seamless",
            "timezone": "GMT",
            "past_days": 7,
            "forecast_days": 1,}

            try:
                response = httpx.get(OPENMETEO_URL, params=params, timeout=30.0)

                if 200 <= response.status_code <= 299:
                    save_api_call(con, "open-meteo", name, response.status_code, response.text)

                else:
                    response.raise_for_status()

            except httpx.HTTPStatusError as e:
                logger.error("open-meteo %s: HTTP %s — %s", name, e.response.status_code, e.response.text[:200])
                raise

            except httpx.RequestError as e:
                logger.error("open-meteo %s: network error — %r", name, e)
                raise

            if name != last_name:
                time.sleep(1)

    finally:
        con.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",)
    
    fetch_data_open_meteo()



