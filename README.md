# Manhattan Subway Commute Visualizer

Investigate the expected travel times (via subway) to different locations using the Google Maps Distance API. Use this tool when apartment hunting to visualize the average commute times for roommates working at different offices.

## Setup
1. Get a Google Maps API Key, described [here](https://developers.google.com/maps/documentation/javascript/get-api-key)
2. Enable the Distance Matrix and Geocoding APIs
2. Create a `.env` file as such
```
MAPS_API_KEY=
```
3. Change the `_offices_raw` dictionary with names of roommates and office addresses. Sample data is in there now.
4. Change parameters as needed in `main()`
5. Install requirements in `requirements.txt` 

## Sample Output
