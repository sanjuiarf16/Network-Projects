# DNS Status Checker & System Monitor

A comprehensive network monitoring and system analysis tool that provides real-time insights into DNS server status, website accessibility, network connections, system resource usage, and hardware device access. Features both a command-line interface and a modern web dashboard with natural language chat capabilities.

## 🚀 Features

### Network Monitoring
- **DNS Server Health**: Ping major DNS servers (Google, Cloudflare, Azure, Amazon Route 53)
- **Website Accessibility**: Check status of popular websites
- **Connection Analysis**: Analyze active network connections with geolocation data
- **Traffic Statistics**: Monitor network bandwidth usage

### System Resource Monitoring
- **CPU Usage**: Real-time processor utilization tracking
- **Memory Usage**: RAM consumption monitoring
- **Disk Space**: Storage capacity and usage analysis
- **Process Monitoring**: Top resource-consuming processes identification

### Hardware Detection
- **Device Access**: Detect applications using camera, microphone, Bluetooth, and NFC
- **Privacy Monitoring**: Track hardware access for security awareness

### User Interface
- **Web Dashboard**: Modern, responsive web interface with real-time updates
- **Natural Language Chat**: AI-powered chat interface for querying system information
- **REST API**: Complete API for integration with other tools

## 📋 Requirements

- Python 3.7+
- Windows/Linux/Mac OS
- Internet connection for geolocation services

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sanjuiarf16/Network-Projects.git
   cd Network-Projects
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Usage

### Command Line Mode

Run the monitoring script directly:

```bash
python dns_status_checker.py
```

This will perform a comprehensive system analysis and display results in the terminal, including:
- DNS server ping results
- Website accessibility status
- Network connection analysis with country statistics
- System resource usage
- Hardware access detection

### Web Dashboard Mode

1. **Start the web server:**
   ```bash
   python app.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5000`

3. **Explore the dashboard:**
   - View real-time system metrics
   - Monitor network connections
   - Check hardware usage
   - Use the chat interface for natural language queries

### Chat Interface Examples

The AI chat assistant can answer questions like:
- "How is my CPU doing?"
- "Are all DNS servers working?"
- "What's using the most memory?"
- "Show me the network connections"
- "Is my disk space OK?"

## 🔌 API Endpoints

The web application provides a REST API for programmatic access:

- `GET /api/dns-status` - DNS server status
- `GET /api/website-status` - Website accessibility
- `GET /api/connections` - Network connection analysis
- `GET /api/system-resources` - System resource usage
- `GET /api/processes` - Top resource-consuming processes
- `GET /api/hardware` - Hardware device usage
- `GET /api/summary` - Overall system health summary
- `POST /api/chat` - Natural language queries
- `GET /api/health` - Service health check

### API Example

```bash
curl -X GET http://localhost:5000/api/system-resources
```

## 🔒 Security Considerations

### Data Privacy
- All monitoring is performed locally on your system
- No data is transmitted to external servers (except for IP geolocation via ip-api.com)
- Hardware access detection helps identify potential privacy risks

### Network Security
- Uses HTTPS for all external API calls
- Implements proper error handling and timeouts
- No authentication required for local usage

### Production Deployment
- For public deployment, consider adding authentication
- Disable debug mode in production
- Use environment variables for configuration
- Implement rate limiting for API endpoints

## 🐛 Known Issues & Limitations

### Hardware Detection
- Heuristic-based detection may have false positives/negatives
- Limited to Windows PowerShell commands for Bluetooth/NFC status
- Process name matching may not catch all applications

### Network Analysis
- Geolocation API has rate limits (cached to minimize impact)
- Connection analysis requires appropriate system permissions
- Some corporate networks may block ping requests

### Performance
- Resource monitoring may have slight performance impact
- Large number of connections may slow analysis
- Web dashboard updates every few seconds

### Platform Compatibility
- Primarily tested on Windows
- Linux/Mac support for basic features
- Hardware detection is Windows-specific

## 🧪 Testing

Run the included test guide:

```bash
# See LOCAL_TESTING.md for detailed testing procedures
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is open source. Please check the license file for details.

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section in LOCAL_TESTING.md
2. Review the API endpoints for error messages
3. Ensure all dependencies are installed correctly
4. Verify system permissions for network analysis

## 🔄 Updates

- Regular security updates for dependencies
- Performance optimizations
- Additional platform support
- Enhanced hardware detection algorithms

---

**Note:** This tool is designed for personal system monitoring and network diagnostics. Use responsibly and ensure compliance with your organization's policies.