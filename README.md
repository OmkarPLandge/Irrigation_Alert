# Irrigation Alert System

## Overview

The **Irrigation Alert System** is a FastAPI application designed to evaluate soil moisture and NDWI (Normalized Difference Water Index) values to determine if irrigation is needed for agricultural fields. It utilizes satellite data and historical weather information to provide irrigation alerts based on the analysis.

## Features

- **NDWI Calculation**: Fetches NDWI values from satellite data.
- **Soil Moisture Calculation**: Retrieves soil moisture data at 4cm and 14cm depths.
- **Irrigation Alert**: Generates an alert based on soil moisture and NDWI values to advise on irrigation needs.

## Requirements

- Python 3.7 or higher
- FastAPI
- aiohttp
- Uvicorn (for running the server)


## Code Explanation
Imports and Setup: Imports libraries and sets up the FastAPI application and asynchronous HTTP requests.

fetch_with_retry(): A helper function that attempts to fetch data from a URL up to a specified number of retries in case of errors or non-200 responses.

fetch_historical_weather(): Retrieves historical weather data using the provided API key, farm ID, and date range.

get_irrigation_alert():

Parameters: Takes api_key and farm_id as query parameters.
Date Calculation: Uses default start and end dates for NDWI and soil moisture calculations.
NDWI Fetching: Retrieves NDWI values using satellite data.
Soil Moisture Fetching: Retrieves soil moisture data for the past week.
Calculation: Computes average NDWI and soil moisture values, and assesses whether irrigation is needed.
Response: Returns a JSON object with calculated values and an irrigation alert.
