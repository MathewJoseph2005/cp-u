#!/bin/bash
# Start ngrok tunnel for CropSight development
# Usage: ./start-tunnel.sh

echo "🚀 Starting ngrok tunnel for CropSight..."
echo ""
echo "Frontend runs on: http://localhost:5173"
echo "Tunneling to public HTTPS URL..."
echo ""

ngrok http 5173 --log=stdout
