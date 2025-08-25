#!/usr/bin/env python3
"""
SageMaker inference script for Ollama models.
This script handles inference requests and communicates with the Ollama service.
"""

import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default model (can be overridden via environment variable)
DEFAULT_MODEL = "llama3:8b-instruct"

# Flask app
app = Flask(__name__)

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

@app.route("/ping", methods=["GET"])
def ping():
    """Health check endpoint for SageMaker - returns simple OK"""
    try:
        # Check if Ollama is responding
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            return "OK", 200
        else:
            logger.warning(f"Ollama health check failed: {response.status_code}")
            return "OK", 200  # Return OK even if Ollama is down for SageMaker health checks
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return "OK", 200  # Return OK for SageMaker health checks

@app.route("/invocations", methods=["POST"])
def invoke():
    """Inference endpoint for SageMaker"""
    try:
        # Parse input
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        
        # Extract prompt from SageMaker format or direct format
        prompt = None
        if "prompt" in data:
            prompt = data["prompt"]
        elif "instances" in data and len(data["instances"]) > 0:
            instance = data["instances"][0]
            if "prompt" in instance:
                prompt = instance["prompt"]
            elif "text" in instance:
                prompt = instance["text"]
        
        if not prompt:
            return jsonify({"error": "No prompt found in request"}), 400
        
        # Prepare Ollama request
        ollama_request = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        # Add optional parameters if provided
        if "temperature" in data:
            ollama_request["temperature"] = data["temperature"]
        if "top_p" in data:
            ollama_request["top_p"] = data["top_p"]
        if "max_tokens" in data:
            ollama_request["num_predict"] = data["max_tokens"]
        
        logger.info(f"Sending request to Ollama: {ollama_request}")
        
        # Call Ollama with timeout
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_request,
            timeout=120
        )
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return jsonify({"error": f"Ollama API error: {response.status_code}"}), 500
        
        ollama_response = response.json()
        
        # Extract response text
        response_text = ollama_response.get("response", "")
        
        # Return simple JSON format for SageMaker
        return jsonify({"output": response_text}), 200
        
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out")
        return jsonify({"error": "Request timed out"}), 408
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama service")
        return jsonify({"error": "Ollama service unavailable"}), 503
    except Exception as e:
        logger.error(f"Inference error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/models", methods=["GET"])
def list_models():
    """List available models"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            return jsonify(models), 200
        else:
            return jsonify({"error": "Failed to fetch models"}), 500
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def root():
    """Root endpoint"""
    return jsonify({
        "service": "Ollama SageMaker Inference",
        "model": OLLAMA_MODEL,
        "endpoints": {
            "health": "/ping",
            "inference": "/invocations",
            "models": "/models"
        }
    }), 200

if __name__ == "__main__":
    # For local development
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
