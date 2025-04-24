import os
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Use your API Key directly
GEMINI_API_KEY = "AIzaSyCvbSPMaN9Be1rPY-AOIIA8y9WmY9cY-pE"

def get_pest_advice(pest_type):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    # Create the prompt for pest control advice
    prompt = f"""
    Provide detailed pest control advice for {pest_type}. Include:
    - identification (string): Key characteristics to identify the pest
    - methods (array): List of 3-5 control methods with brief descriptions
    - prevention (string): Tips to prevent future infestations
    - safety (string): Safety precautions during treatment
    
    Return ONLY valid JSON format like this (no other text or markdown):
    {{
        "advice": {{
            "identification": "Description",
            "methods": [
                {{"name": "Method 1", "description": "Details"}},
                {{"name": "Method 2", "description": "Details"}}
            ],
            "prevention": "Tips",
            "safety": "Precautions"
        }}
    }}
    """
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            response_json = response.json()
            
            try:
                model_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # Extract just the JSON part
                if "```json" in model_response:
                    json_start = model_response.find("{")
                    json_end = model_response.rfind("}") + 1
                    json_data = model_response[json_start:json_end]
                else:
                    json_data = model_response.strip()
                
                # Parse the JSON data
                parsed_data = json.loads(json_data)
                
                if "advice" not in parsed_data or not isinstance(parsed_data["advice"], dict):
                    return {"error": "Invalid response format from AI", "advice": {}}
                
                return parsed_data
                
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                return {"error": f"Failed to parse AI response: {str(e)}", "advice": {}}
        else:
            return {"error": f"API request failed with status code {response.status_code}", "advice": {}}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}", "advice": {}}

@app.route('/get_advice', methods=['POST'])
def pest_advice():
    try:
        data = request.get_json()
        
        # Extract pest type
        pest_type = data.get("pest", "").strip()
        
        if not pest_type:
            return jsonify({"error": "Pest type is required", "advice": {}})
        
        # Get pest control advice
        advice = get_pest_advice(pest_type)
        
        return jsonify(advice)
    
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "advice": {}})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)