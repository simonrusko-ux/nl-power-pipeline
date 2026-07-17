import httpx
import logging
import time
from db import connect_db, init_tables, save_api_call


ENERGY_CHARTS_URL = "https://api.energy-charts.info"

STATE_CODE = ["nl","NL"]

ENDPOINTS = {
    "price":{"bzn:NL"},
    "public_power":{"country:nl"}
}

logger = logging.getLogger(__name__)


def fetch_data_energy_charts():
    
    con = connect_db()
    init_tables(con=con)

    last_elem = STATE_CODE[-1]

    params = {}

    try: 
        for endpoint, base_params in ENDPOINTS.values():
            
            url = f"ENERGY_CHARTS_URL+/{endpoint}"

            #FINISH PARAMETERS AND RESOLVE if name != last element plus other stuff with error

            params = {
                base_params,
                "start": ,
                "end": 
            }

            try:

                response = httpx.get(url=url, params=params, timeout=30)

                if 200 <= response.status_code <= 299:
                    save_api_call(con, "energy_charts", name, response.status_code, response.text)
                
                else:
                    response.raise_for_status()

            except httpx.HTTPStatusError as e:
                logger.error("energy_charts %s: HTTP %s — %s", name, e.response.status_code, e.response.text[:200])
                raise

            except httpx.RequestError as e:
                logger.error("energy_charts %s: network error — %r", name, e)
                raise

            if name != last_elem:
                time.sleep(1)

    finally:
        con.close()
    

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",)
    
    fetch_data_energy_charts()



    
