from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
import aiohttp
import asyncio

app = FastAPI()

async def fetch_with_retry(url, headers, retries=3):
    for i in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Attempt {i+1} failed with status {response.status}")
        except Exception as e:
            print(f"Attempt {i+1} encountered an error: {e}")
    return None

async def fetch_historical_weather(api_key: str, farm_id: str, start: str, end: str):
    url = f"https://api.mapmycrop.com/weather/historical?api_key={api_key}&farm_id={farm_id}&start={start}&end={end}"
    return await fetch_with_retry(url, {"Accept": "application/json"})

@app.get("/Irrigation/Alert")
async def get_irrigation_alert(
    api_key: str = Query(..., description="API key for authentication"),
    farm_id: str = Query(..., description="Farm ID to get the data")
):
    # Internal parameters
    satellite = "S1"
    index = "Water Watch Map"
    
    # Use default start and end dates
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # Fetch NDWI values
    ndwi_url = f"https://api.mapmycrop.com/satellite/statistics?api_key={api_key}&farm_id={farm_id}&start_date={start}&end_date={end}&index={index}&satellite={satellite}&interval=P1D"
    headers = {"Accept": "application/json"}
    satellite_data = await fetch_with_retry(ndwi_url, headers)

    if not satellite_data:
        raise HTTPException(status_code=404, detail="No satellite data found for the given parameters.")
    
    means = [day['outputs']['data']['bands']['B0']['stats']['mean'] for day in satellite_data]
    total_mean = sum(means) / len(means) if means else 0

    # Fetch soil moisture data
    soil_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    soil_end = datetime.now().strftime("%Y-%m-%d")
    historical_weather_data = await fetch_historical_weather(api_key, farm_id, soil_start, soil_end)
    
    if not historical_weather_data or "soil moisture 4cm" not in historical_weather_data or "soil moisture 14cm" not in historical_weather_data:
        raise HTTPException(status_code=500, detail="Failed to retrieve historical weather data or missing soil moisture data.")

    soil_moisture_4cm = historical_weather_data.get("soil moisture 4cm", [])
    soil_moisture_14cm = historical_weather_data.get("soil moisture 14cm", [])
    
    if not soil_moisture_4cm or not soil_moisture_14cm:
        raise HTTPException(status_code=500, detail="Insufficient soil moisture data.")
    
    # Filter out None values and calculate averages
    soil_moisture_4cm = [x for x in soil_moisture_4cm if x is not None]
    soil_moisture_14cm = [x for x in soil_moisture_14cm if x is not None]

    avg_sm4 = sum(soil_moisture_4cm) / len(soil_moisture_4cm) if soil_moisture_4cm else 0
    avg_sm14 = sum(soil_moisture_14cm) / len(soil_moisture_14cm) if soil_moisture_14cm else 0
    avg_sm = (avg_sm4 + avg_sm14) / 2 if (soil_moisture_4cm and soil_moisture_14cm) else 0
    
    # Calculate irrigation need
    c_value = total_mean - avg_sm
    
    response = {
        "average_ndwi_value": total_mean,
        "start_date": start,
        "end_date": end,
        "average_soil_moisture_4cm": avg_sm4,
        "average_soil_moisture_14cm": avg_sm14,
        "average_soil_moisture": avg_sm,
        "value_of_c": c_value
    }
    
    if avg_sm < 0.2:
        response["irrigation_alert"] = "Irrigation is needed in the field."
    else:
        response["irrigation_alert"] = "Irrigation is not needed in the field."

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
