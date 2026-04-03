#!/usr/bin/env python3
"""
Flask API for DNS Status Checker Agent
Integrates dns_status_checker.py functions as REST endpoints
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import dns_status_checker
import threading
import json
from datetime import datetime
import logging
import re

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chatbot responses mapping
CHAT_KEYWORDS = {
    'dns': ['dns', 'server', 'resolve'],
    'website': ['website', 'website', 'google', 'amazon', 'azure', 'cloudflare', 'accessible'],
    'cpu': ['cpu', 'processor', 'usage', 'percent'],
    'memory': ['memory', 'ram', 'usage'],
    'disk': ['disk', 'storage', 'space'],
    'network': ['network', 'connection', 'bandwidth', 'traffic'],
    'process': ['process', 'process', 'cpu usage', 'memory usage'],
    'hardware': ['hardware', 'camera', 'microphone', 'bluetooth', 'nfc'],
    'summary': ['summary', 'health', 'status', 'overall']
}

# Cache for storing data
cache_data = {
    'dns_status': {},
    'connections': {},
    'system_resources': {},
    'processes': {},
    'hardware': {},
    'last_update': None
}


def classify_question(question):
    """Classify user question to determine which data to fetch"""
    question_lower = question.lower()
    
    for category, keywords in CHAT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in question_lower:
                return category
    
    return 'summary'  # Default to summary


def generate_chat_response(question):
    """Generate natural language response to user question"""
    category = classify_question(question)
    
    try:
        if category == 'dns':
            dns_status = {}
            for name, server in dns_status_checker.DNS_SERVERS.items():
                status, response = dns_status_checker.ping_host(server)
                dns_status[name] = status
            
            operational = sum(1 for v in dns_status.values() if v)
            total = len(dns_status)
            
            response_text = f"🎯 **DNS Server Status Report**\n\n"
            response_text += f"Out of {total} DNS servers, {operational} are operational.\n\n"
            response_text += "**Details:**\n"
            for name, status in dns_status.items():
                icon = "✅" if status else "❌"
                response_text += f"  {icon} {name}: {'Working' if status else 'Not responding'}\n"
            
            if operational == total:
                response_text += f"\n✨ All DNS servers are healthy and responding correctly!"
            else:
                response_text += f"\n⚠️ Warning: {total - operational} DNS server(s) are not responding."
            
            return response_text
        
        elif category == 'website':
            website_status = {}
            for name, website in dns_status_checker.WEBSITES.items():
                status, response = dns_status_checker.ping_host(website)
                website_status[name] = status
            
            operational = sum(1 for v in website_status.values() if v)
            total = len(website_status)
            
            response_text = f"🌐 **Website Accessibility Report**\n\n"
            response_text += f"{operational} out of {total} websites are accessible.\n\n"
            response_text += "**Details:**\n"
            for name, status in website_status.items():
                icon = "✅" if status else "❌"
                response_text += f"  {icon} {name}: {'Accessible' if status else 'Not responding'}\n"
            
            if operational == total:
                response_text += f"\n✨ All websites are accessible!"
            else:
                response_text += f"\n⚠️ {total - operational} website(s) are unreachable."
            
            return response_text
        
        elif category == 'cpu':
            resources = dns_status_checker.get_system_resources()
            if resources:
                cpu_percent = resources['cpu_percent']
                status = "🔥 High" if cpu_percent > 80 else "⚠️ Moderate" if cpu_percent > 50 else "✅ Low"
                
                response_text = f"⚡ **CPU Usage Report**\n\n"
                response_text += f"Current CPU Usage: **{cpu_percent}%** ({status})\n\n"
                
                if cpu_percent > 80:
                    response_text += "🚨 Your CPU is heavily loaded. Consider checking running processes."
                elif cpu_percent > 50:
                    response_text += "⚠️ Your CPU usage is moderate. Monitor for spikes."
                else:
                    response_text += "✨ Your CPU usage is healthy."
                
                return response_text
            else:
                return "❌ Could not retrieve CPU information."
        
        elif category == 'memory':
            resources = dns_status_checker.get_system_resources()
            if resources:
                mem_percent = resources['memory_percent']
                mem_used = resources['memory_used_gb']
                mem_total = resources['memory_total_gb']
                status = "🔥 High" if mem_percent > 80 else "⚠️ Moderate" if mem_percent > 60 else "✅ Good"
                
                response_text = f"💾 **Memory Usage Report**\n\n"
                response_text += f"Memory Usage: **{mem_percent}%** ({status})\n"
                response_text += f"Used: {mem_used}GB / Total: {mem_total}GB\n\n"
                
                if mem_percent > 80:
                    response_text += "🚨 Your system is running low on memory. Close unnecessary applications."
                elif mem_percent > 60:
                    response_text += "⚠️ Memory usage is getting high. Monitor the situation."
                else:
                    response_text += "✨ Your memory usage is healthy."
                
                return response_text
            else:
                return "❌ Could not retrieve memory information."
        
        elif category == 'disk':
            resources = dns_status_checker.get_system_resources()
            if resources:
                disk_percent = resources['disk_percent']
                disk_used = resources['disk_used_gb']
                disk_total = resources['disk_total_gb']
                status = "🔥 Critical" if disk_percent > 90 else "⚠️ High" if disk_percent > 75 else "✅ Healthy"
                
                response_text = f"💿 **Storage/Disk Report**\n\n"
                response_text += f"Disk Usage: **{disk_percent}%** ({status})\n"
                response_text += f"Used: {disk_used}GB / Total: {disk_total}GB\n\n"
                
                if disk_percent > 90:
                    response_text += "🚨 Your disk is almost full! Free up space immediately."
                elif disk_percent > 75:
                    response_text += "⚠️ Disk space is getting low. Consider cleaning up."
                else:
                    response_text += "✨ Your disk space is healthy."
                
                return response_text
            else:
                return "❌ Could not retrieve disk information."
        
        elif category == 'network':
            resources = dns_status_checker.get_system_resources()
            if resources:
                sent = resources['network_sent_mb']
                recv = resources['network_recv_mb']
                total_traffic = sent + recv
                
                response_text = f"📡 **Network Traffic Report**\n\n"
                response_text += f"Data Sent: **{sent}MB**\n"
                response_text += f"Data Received: **{recv}MB**\n"
                response_text += f"Total Traffic: **{total_traffic}MB**\n\n"
                response_text += "✨ Your network connection is being monitored."
                
                return response_text
            else:
                return "❌ Could not retrieve network information."
        
        elif category == 'process':
            procs = dns_status_checker.get_top_processes(limit=5)
            
            response_text = f"⚙️ **Top Resource-Consuming Processes**\n\n"
            response_text += "**Highest CPU Usage:**\n"
            for i, p in enumerate(procs['top_cpu'][:3], 1):
                response_text += f"  {i}. {p['name']} - {p['cpu_percent']:.1f}% CPU\n"
            
            response_text += "\n**Highest Memory Usage:**\n"
            for i, p in enumerate(procs['top_memory'][:3], 1):
                response_text += f"  {i}. {p['name']} - {p['memory_mb']}MB RAM\n"
            
            return response_text
        
        elif category == 'hardware':
            hardware = dns_status_checker.get_hardware_usage()
            
            response_text = f"🔌 **Hardware Access Report**\n\n"
            response_text += f"📷 Camera Apps: {len(hardware['camera'])}\n"
            response_text += f"🎤 Microphone Apps: {len(hardware['microphone'])}\n"
            response_text += f"🔵 Bluetooth Apps: {len(hardware['bluetooth'])}\n"
            response_text += f"📡 NFC Apps: {len(hardware['nfc'])}\n\n"
            
            total = len(hardware['camera']) + len(hardware['microphone']) + len(hardware['bluetooth']) + len(hardware['nfc'])
            
            if total > 0:
                response_text += f"⚠️ **{total} applications** have hardware access.\n\n"
                response_text += "**Privacy Alert:** Review these apps for privacy concerns:\n"
                
                if hardware['camera']:
                    response_text += f"  📷 Camera: {', '.join([app['name'] for app in hardware['camera'][:3]])}\n"
                if hardware['microphone']:
                    response_text += f"  🎤 Microphone: {', '.join([app['name'] for app in hardware['microphone'][:3]])}\n"
            else:
                response_text += "✨ No applications are currently accessing hardware devices. Your privacy is protected!"
            
            return response_text
        
        elif category == 'summary':
            dns_status = {}
            for name, server in dns_status_checker.DNS_SERVERS.items():
                status, _ = dns_status_checker.ping_host(server)
                dns_status[name] = status
            
            website_status = {}
            for name, website in dns_status_checker.WEBSITES.items():
                status, _ = dns_status_checker.ping_host(website)
                website_status[name] = status
            
            resources = dns_status_checker.get_system_resources()
            hardware = dns_status_checker.get_hardware_usage()
            
            total_dns = len(dns_status)
            healthy_dns = sum(1 for v in dns_status.values() if v)
            total_websites = len(website_status)
            healthy_websites = sum(1 for v in website_status.values() if v)
            
            response_text = f"📊 **System Health Summary**\n\n"
            response_text += f"🌐 **Network Services:**\n"
            response_text += f"  • DNS Servers: {healthy_dns}/{total_dns} operational\n"
            response_text += f"  • Websites: {healthy_websites}/{total_websites} accessible\n\n"
            
            if resources:
                response_text += f"💻 **System Resources:**\n"
                response_text += f"  • CPU: {resources['cpu_percent']:.1f}%\n"
                response_text += f"  • Memory: {resources['memory_percent']:.1f}%\n"
                response_text += f"  • Disk: {resources['disk_percent']:.1f}%\n\n"
            
            hardware_count = len(hardware['camera']) + len(hardware['microphone']) + len(hardware['bluetooth']) + len(hardware['nfc'])
            response_text += f"🔌 **Hardware:**\n"
            response_text += f"  • Active Hardware Access: {hardware_count} apps\n\n"
            
            overall_health = (healthy_dns + healthy_websites) / (total_dns + total_websites) * 100
            
            if overall_health == 100:
                response_text += "🟢 **Overall Status: EXCELLENT** - All systems functioning normally!"
            elif overall_health >= 75:
                response_text += "🟡 **Overall Status: GOOD** - Most systems operational, minor issues detected."
            else:
                response_text += "🔴 **Overall Status: WARNING** - Multiple issues detected, attention required."
            
            return response_text
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"❌ Error processing request: {str(e)}"


@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template('dashboard.html')


@app.route('/api/dns-status', methods=['GET'])
def get_dns_status():
    """Get DNS server status"""
    try:
        dns_status = {}
        for name, server in dns_status_checker.DNS_SERVERS.items():
            status, response = dns_status_checker.ping_host(server)
            dns_status[name] = {
                "status": "✅ OK" if status else "❌ FAILED",
                "response": response,
                "server": server,
                "operational": status
            }
        
        cache_data['dns_status'] = dns_status
        return jsonify({
            "success": True,
            "data": dns_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting DNS status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/website-status', methods=['GET'])
def get_website_status():
    """Get website status"""
    try:
        website_status = {}
        for name, website in dns_status_checker.WEBSITES.items():
            status, response = dns_status_checker.ping_host(website)
            website_status[name] = {
                "status": "✅ OK" if status else "❌ FAILED",
                "response": response,
                "website": website,
                "operational": status
            }
        
        return jsonify({
            "success": True,
            "data": website_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting website status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/connections', methods=['GET'])
def get_connections():
    """Get network connections analysis"""
    try:
        connections = dns_status_checker.get_active_connections()
        stats = dns_status_checker.analyze_connections(connections)
        
        cache_data['connections'] = {
            "total": stats['total_connections'],
            "unique_ips": len(stats['unique_ips']),
            "unique_countries": len(stats['unique_countries']),
            "protocols": dict(stats['by_protocol']),
            "top_countries": dict(stats['by_country'].most_common(10)),
            "top_ports": dict(stats['by_port'].most_common(10))
        }
        
        return jsonify({
            "success": True,
            "data": cache_data['connections'],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/system-resources', methods=['GET'])
def get_system_resources():
    """Get system resource usage"""
    try:
        resources = dns_status_checker.get_system_resources()
        
        if resources:
            cache_data['system_resources'] = {
                "cpu_percent": resources['cpu_percent'],
                "memory_percent": resources['memory_percent'],
                "memory_used_gb": resources['memory_used_gb'],
                "memory_total_gb": resources['memory_total_gb'],
                "disk_percent": resources['disk_percent'],
                "disk_used_gb": resources['disk_used_gb'],
                "disk_total_gb": resources['disk_total_gb'],
                "network_sent_mb": resources['network_sent_mb'],
                "network_recv_mb": resources['network_recv_mb']
            }
            
            return jsonify({
                "success": True,
                "data": cache_data['system_resources'],
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"success": False, "error": "Could not retrieve resources"}), 500
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Get top resource-consuming processes"""
    try:
        procs = dns_status_checker.get_top_processes(limit=10)
        
        cache_data['processes'] = {
            "top_cpu": [
                {
                    "name": p['name'],
                    "pid": p['pid'],
                    "cpu_percent": round(p['cpu_percent'], 2),
                    "memory_percent": round(p['memory_percent'], 2),
                    "memory_mb": p['memory_mb']
                }
                for p in procs['top_cpu'][:5]
            ],
            "top_memory": [
                {
                    "name": p['name'],
                    "pid": p['pid'],
                    "cpu_percent": round(p['cpu_percent'], 2),
                    "memory_percent": round(p['memory_percent'], 2),
                    "memory_mb": p['memory_mb']
                }
                for p in procs['top_memory'][:5]
            ]
        }
        
        return jsonify({
            "success": True,
            "data": cache_data['processes'],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/hardware', methods=['GET'])
def get_hardware():
    """Get hardware device usage"""
    try:
        hardware = dns_status_checker.get_hardware_usage()
        
        cache_data['hardware'] = {
            "camera": {
                "count": len(hardware['camera']),
                "apps": [app['name'] for app in hardware['camera'][:5]]
            },
            "microphone": {
                "count": len(hardware['microphone']),
                "apps": [app['name'] for app in hardware['microphone'][:5]]
            },
            "bluetooth": {
                "count": len(hardware['bluetooth']),
                "status": dns_status_checker.check_bluetooth_status(),
                "apps": [app['name'] for app in hardware['bluetooth'][:5]]
            },
            "nfc": {
                "count": len(hardware['nfc']),
                "status": dns_status_checker.check_nfc_status(),
                "apps": [app['name'] for app in hardware['nfc'][:5]]
            },
            "total": len(hardware['camera']) + len(hardware['microphone']) + len(hardware['bluetooth']) + len(hardware['nfc'])
        }
        
        return jsonify({
            "success": True,
            "data": cache_data['hardware'],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting hardware: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get overall summary of all monitoring data"""
    try:
        # Refresh all data
        dns_status = {}
        for name, server in dns_status_checker.DNS_SERVERS.items():
            status, _ = dns_status_checker.ping_host(server)
            dns_status[name] = status
        
        website_status = {}
        for name, website in dns_status_checker.WEBSITES.items():
            status, _ = dns_status_checker.ping_host(website)
            website_status[name] = status
        
        resources = dns_status_checker.get_system_resources()
        hardware = dns_status_checker.get_hardware_usage()
        
        total_dns = len(dns_status)
        healthy_dns = sum(1 for v in dns_status.values() if v)
        total_websites = len(website_status)
        healthy_websites = sum(1 for v in website_status.values() if v)
        
        summary = {
            "dns_servers": {
                "total": total_dns,
                "operational": healthy_dns,
                "status": "🟢 All operational" if healthy_dns == total_dns else "🟡 Some issues" if healthy_dns > 0 else "🔴 All failed"
            },
            "websites": {
                "total": total_websites,
                "operational": healthy_websites,
                "status": "🟢 All operational" if healthy_websites == total_websites else "🟡 Some issues" if healthy_websites > 0 else "🔴 All failed"
            },
            "system": {
                "cpu_percent": resources['cpu_percent'] if resources else 0,
                "memory_percent": resources['memory_percent'] if resources else 0,
                "disk_percent": resources['disk_percent'] if resources else 0
            },
            "hardware": {
                "camera_apps": len(hardware['camera']),
                "mic_apps": len(hardware['microphone']),
                "bluetooth_apps": len(hardware['bluetooth']),
                "nfc_apps": len(hardware['nfc'])
            }
        }
        
        return jsonify({
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DNS Status Checker Agent API"
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint for natural language queries"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "Please ask me something!"
            }), 400
        
        # Generate response
        response_text = generate_chat_response(user_message)
        
        return jsonify({
            "success": True,
            "user_message": user_message,
            "bot_response": response_text,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "success": False,
            "error": f"Error processing your message: {str(e)}"
        }), 500


if __name__ == '__main__':
    logger.info("Starting DNS Status Checker Agent API")
    logger.info("Access dashboard at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
