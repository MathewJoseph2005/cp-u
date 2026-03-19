@echo off
REM Start ngrok tunnel for CropSight development
REM Usage: start-tunnel.bat

echo.
echo ================================
echo   CropSight Mobile Tunnel
echo ================================
echo.
echo Frontend: http://localhost:5173
echo.
echo Starting ngrok tunnel...
echo.

ngrok http 5173 --log=stdout
