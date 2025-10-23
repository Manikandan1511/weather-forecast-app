import requests
from flask import Flask, request, jsonify
from flask_cors import CORS 

# --- Configuration ---
app = Flask(__name__)
CORS(app) # Enable CORS for frontend communication

# API KEY: This key is for WeatherAPI.com (as specified by the user)
API_KEY = "4a531c1f07ab4648a43165833252310"
# BASE URL for WeatherAPI.com Current Weather endpoint
BASE_URL = "http://api.weatherapi.com/v1/current.json"

@app.route('/weather', methods=['GET'])
def get_weather():
    """
    Fetches real-time weather data for a given city from WeatherAPI.com.
    Expected usage: /weather?city=London
    """
    city_name = request.args.get('city')
    
    if not city_name:
        return jsonify({"error": "Missing 'city' parameter"}), 400

    # 1. Construct the API call URL for WeatherAPI.com
    # Note: We use 'q' for the city query and include aqi=no to keep the response clean
    complete_url = f"{BASE_URL}?key={API_KEY}&q={city_name}&aqi=no"

    try:
        # 2. Make the HTTP request using the 'requests' library
        response = requests.get(complete_url)
        response.raise_for_status() # Raise an HTTPError for bad responses (e.g., 400 for city not found)

        # 3. Parse the JSON response
        data = response.json()
        
        # 4. Extract data using WeatherAPI.com's structure
        location_data = data.get('location', {})
        current_data = data.get('current', {})
        condition_data = current_data.get('condition', {})

        # Wind speed conversion: WeatherAPI provides wind in kph, but the frontend expects m/s
        # Conversion factor: 1 kph = 1000m / 3600s ≈ 1 / 3.6 m/s
        wind_kph = current_data.get('wind_kph', 0)
        wind_m_s = wind_kph / 3.6 if wind_kph else 0
        
        # 5. Map extracted data to the required frontend report format
        report = {
            "city": location_data.get('name'),
            "country": location_data.get('country'),
            "temperature_c": current_data.get('temp_c'),
            "feels_like_c": current_data.get('feelslike_c'),
            # WeatherAPI uses 'pressure_mb' (millibars), which is equivalent to hPa (hectopascals)
            "pressure": current_data.get('pressure_mb'), 
            "humidity": current_data.get('humidity'),
            "description": condition_data.get('text', '').title(),
            # WeatherAPI icon URLs start with //, so we remove http: to let the browser choose (or we can prepend https:)
            # I will prepend 'https:' for reliability, as the original frontend expects a full URL.
            "icon": 'https:' + condition_data.get('icon', ''), 
            "wind_speed_m_s": wind_m_s
        }
        
        return jsonify(report)

    except requests.exceptions.HTTPError as e:
        # Check if the error response contains WeatherAPI's specific error structure
        try:
            error_data = e.response.json()
            error_message = error_data.get('error', {}).get('message', 'City not found or invalid API key.')
            # Return the specific error message provided by the API
            return jsonify({"error": error_message}), e.response.status_code
        except:
            # Fallback for generic HTTP errors
            return jsonify({"error": f"HTTP Error: Could not reach weather service. {e.response.status_code}"}), e.response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connection error, check network or API URL."}), 500
    except Exception as e:
        # Catch other unexpected errors
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    # Run the server on localhost:5000
    print("Starting Flask server on http://127.0.0.1:5000...")
    app.run(debug=True)
