# DNS Status Checker Agent - Local Testing Guide

This guide will help you test the agent locally on your machine.

## Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Flask Server
```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### Step 3: Access the Dashboard
Open your browser and go to:
```
http://localhost:5000
```

## Features Available in Dashboard

### 📡 DNS Servers
- Tests all major DNS servers (Google, Cloudflare, Azure, Amazon)
- Shows status and response time
- Real-time updates

### 🌐 Websites
- Monitors Google, Amazon, Azure, Cloudflare websites
- Shows accessibility status
- Updates on demand

### 💻 System Resources
- CPU usage with progress bar
- Memory usage and details
- Disk usage and details
- Network traffic (sent/received)

### 🔗 Network Connections
- Total active connections
- Unique IPs connected to
- Countries connected from
- Protocols and ports used

### ⚙️ Top Processes
- Top CPU consuming processes
- Top memory consuming processes
- Real-time system monitoring

### 🔌 Hardware Usage
- Camera applications using camera
- Microphone applications
- Bluetooth status and apps
- NFC status and availability

### 📊 Overall Summary
- Quick status of all systems
- Color-coded indicators
- Health status dashboard

## Dashboard Controls

### 🔄 Refresh All Data
- Manually refresh all monitoring data
- Takes 5-10 seconds depending on system

### ⏱️ Auto Refresh (30s)
- Enables automatic refresh every 30 seconds
- Click again to disable
- Runs in background

### 🗑️ Clear Cache
- Clears all cached data
- Reloads the dashboard

## API Endpoints

All data is also available via REST API:

```
GET /api/dns-status          - DNS server status
GET /api/website-status      - Website accessibility
GET /api/system-resources    - CPU, Memory, Disk, Network
GET /api/connections         - Network connection analysis
GET /api/processes           - Top resource-consuming processes
GET /api/hardware            - Hardware device usage
GET /api/summary             - Overall system summary
GET /api/health              - API health check
```

### Example API Call:
```bash
curl http://localhost:5000/api/dns-status
```

## Testing the Agent

### Test 1: Check All Endpoints
```bash
# Test DNS Status
curl http://localhost:5000/api/dns-status | python -m json.tool

# Test Connections
curl http://localhost:5000/api/connections | python -m json.tool

# Test System Resources
curl http://localhost:5000/api/system-resources | python -m json.tool

# Test Hardware
curl http://localhost:5000/api/hardware | python -m json.tool
```

### Test 2: Use the Web Dashboard
1. Open http://localhost:5000
2. Click "Refresh All Data"
3. Wait for data to load
4. Explore each card section
5. Click "Auto Refresh" for continuous monitoring

### Test 3: Monitor in Real-Time
```bash
# In PowerShell, run continuous monitoring
while($true) {
    curl http://localhost:5000/api/summary | python -m json.tool
    Start-Sleep -Seconds 5
}
```

## Troubleshooting

### Port 5000 Already in Use
```bash
# Use a different port
# Edit app.py and change:
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Flask Not Found
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Dashboard Not Loading
1. Check console for errors
2. Verify Python is running
3. Check firewall settings
4. Try http://127.0.0.1:5000 instead of localhost

### No Data Showing
1. Check browser console (F12 -> Console tab)
2. Verify all API endpoints are working
3. Check Python console for errors

## File Structure

```
Projects/
├── app.py                 # Flask API server
├── dns_status_checker.py  # Core monitoring module
├── requirements.txt       # Python dependencies
├── templates/
│   └── dashboard.html     # Web dashboard UI
└── README.md              # This file
```

## Security Note

For local testing only. Before production:
- Change debug=True to debug=False
- Add authentication/authorization
- Use HTTPS instead of HTTP
- Limit CORS origins
- Add rate limiting

## Next Steps

After testing locally:
1. Customize DNS servers and websites in dns_status_checker.py
2. Add authentication to API
3. Set up SSL/HTTPS
4. Deploy to cloud (Heroku, AWS, Azure)
5. Add alerts/notifications

Enjoy monitoring your network! 🚀
