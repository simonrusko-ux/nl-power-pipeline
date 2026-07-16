import httpx
import logging
import time
from db import connectDB, init_tables, save_api_call

logger = logging.getLogger(__name__)

url = "https://api.open-meteo.com/v1/forecast"


LOCATIONS = {
    "de_bilt": (52.11, 5.1806),
    "den_helder": (52.9599, 4.7593),
    "groningen":(53.2192, 6.5667),
    "eindhoven":(51.4408, 5.4778)
}

def fetch_data_open_meteo():

    con = connectDB()
    init_tables(con=con)

    last_name = list(LOCATIONS.keys())[-1]

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
            response = httpx.get(url, params=params, timeout=30.0)

            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            logger.error("open-meteo %s: HTTP %s — %s", name, e.response.status_code, e.response.text[:200])
            raise
        except httpx.RequestError as e:
            logger.error("open-meteo %s: network error — %r", name, e)
            raise

        save_api_call(con, "open-meteo", name, response.status_code, response.text)
        
        if name != last_name:
            time.sleep(1)
        
    con.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",)
    
    fetch_data_open_meteo()



