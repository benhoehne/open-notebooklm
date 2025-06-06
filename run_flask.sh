#!/bin/bash

# Open NotebookLM Flask Development Server
echo "🎙️ Starting Open NotebookLM Flask App..."

# Build CSS first
echo "📦 Building CSS..."
npm run build-css-prod

# Start Flask app
echo "🚀 Starting Flask server on http://127.0.0.1:5000"
python flask_app.py 