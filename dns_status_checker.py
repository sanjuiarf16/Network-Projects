#!/usr/bin/env python3
"""
DNS Status Checker & System Resource Monitor
Checks DNS status, network connections, and system resource usage
"""

import subprocess
import platform
import sys
import json
import requests
from datetime import datetime
from collections import Counter, defaultdict
import re
import time
import psutil  # For cross-platform system monitoring

# DNS servers to check
DNS_SERVERS = {
    "Google DNS": "8.8.8.8",
    "Google DNS 2": "8.8.4.4",
    "Cloudflare DNS": "1.1.1.1",
    "Cloudflare DNS 2": "1.0.0.1",
    "Azure DNS": "168.63.129.16",
    "Amazon Route 53": "205.251.192.1",
}

# Websites to check
WEBSITES = {
    "Google": "google.com",
    "Amazon": "amazon.com",
    "Azure": "azure.microsoft.com",
    "Cloudflare": "cloudflare.com",
}


def ping_host(host, timeout=4):
    """
    Ping a host and return status and response time
    Works on both Windows and Linux/Mac
    """
    try:
        # Set ping count based on OS
        if platform.system().lower() == "windows":
            # Windows uses -n for count
            command = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
        else:
            # Linux/Mac use -c for count
            command = ["ping", "-c", "1", "-W", str(timeout * 1000), host]
        
        output = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )
        
        if output.returncode == 0:
            # Extract response time from output
            if platform.system().lower() == "windows":
                # Windows format: "time=25ms"
                if "time=" in output.stdout:
                    time_str = output.stdout.split("time=")[1].split("ms")[0]
                    return True, f"{time_str}ms"
            else:
                # Linux/Mac format: "time=25.1 ms"
                if "time=" in output.stdout:
                    time_str = output.stdout.split("time=")[1].split(" ")[0]
                    return True, f"{time_str}ms"
            return True, "OK"
        else:
            return False, "No response"
    
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"


def get_active_connections():
    """
    Get active network connections using netstat
    Returns list of connection dictionaries
    """
    connections = []
    
    try:
        if platform.system().lower() == "windows":
            # Windows: netstat -ano
            command = ["netstat", "-ano"]
        else:
            # Linux/Mac: ss -tunap or netstat -tunap
            command = ["ss", "-tunap"] if subprocess.run(["which", "ss"], capture_output=True).returncode == 0 else ["netstat", "-tunap"]
        
        output = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if output.returncode != 0:
            print(f"Error getting connections: {output.stderr}")
            return connections
        
        lines = output.stdout.strip().split('\n')
        
        for line in lines:
            if platform.system().lower() == "windows":
                # Windows netstat format: Proto  Local Address          Foreign Address        State           PID
                parts = line.split()
                if len(parts) >= 4 and parts[0] in ['TCP', 'UDP']:
                    proto = parts[0]
                    local = parts[1]
                    foreign = parts[2]
                    state = parts[3] if len(parts) > 3 and proto == 'TCP' else 'N/A'
                    
                    # Extract IP and port
                    if ':' in foreign:
                        foreign_ip, foreign_port = foreign.rsplit(':', 1)
                        if foreign_ip != '0.0.0.0' and foreign_ip != '127.0.0.1' and foreign_ip != '::':
                            connections.append({
                                'protocol': proto,
                                'local_address': local,
                                'foreign_address': foreign,
                                'foreign_ip': foreign_ip,
                                'foreign_port': foreign_port,
                                'state': state
                            })
            else:
                # Linux ss format: Netid State      Recv-Q Send-Q Local Address:Port               Peer Address:Port
                parts = line.split()
                if len(parts) >= 5 and parts[0] in ['tcp', 'udp']:
                    proto = parts[0].upper()
                    state = parts[1] if proto == 'TCP' else 'N/A'
                    local_addr = parts[4]
                    peer_addr = parts[5]
                    
                    if ':' in peer_addr:
                        peer_ip, peer_port = peer_addr.rsplit(':', 1)
                        if peer_ip not in ['0.0.0.0', '127.0.0.1', '::', '*']:
                            connections.append({
                                'protocol': proto,
                                'local_address': local_addr,
                                'foreign_address': peer_addr,
                                'foreign_ip': peer_ip,
                                'foreign_port': peer_port,
                                'state': state
                            })
    
    except Exception as e:
        print(f"Error getting connections: {e}")
    
    return connections


def get_country_from_ip(ip_address, cache={}):
    """
    Get country from IP address using ip-api.com
    Uses caching to avoid repeated API calls
    """
    if ip_address in cache:
        return cache[ip_address]
    
    try:
        # Skip private IPs
        if ip_address.startswith(('192.168.', '10.', '172.', '127.', '169.254.')) or ip_address == '::1':
            return "Local/Private"
        
        response = requests.get(f"https://ip-api.com/json/{ip_address}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            country = data.get('country', 'Unknown')
            cache[ip_address] = country
            return country
        else:
            return "Unknown"
    except Exception as e:
        return "Unknown"


def analyze_connections(connections):
    """
    Analyze connections and return statistics
    """
    stats = {
        'total_connections': len(connections),
        'by_protocol': Counter(),
        'by_country': Counter(),
        'by_port': Counter(),
        'by_state': Counter(),
        'unique_ips': set(),
        'unique_countries': set()
    }
    
    print(f"\n🔍 Analyzing {len(connections)} active connections...")
    
    # Process each connection
    for conn in connections:
        stats['by_protocol'][conn['protocol']] += 1
        stats['by_port'][conn['foreign_port']] += 1
        stats['unique_ips'].add(conn['foreign_ip'])
        
        if conn['protocol'] == 'TCP':
            stats['by_state'][conn['state']] += 1
        
        # Get country (with rate limiting)
        country = get_country_from_ip(conn['foreign_ip'])
        stats['by_country'][country] += 1
        stats['unique_countries'].add(country)
    
    return stats


def get_system_resources():
    """
    Get system resource usage using psutil
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # Network usage (bytes sent/received)
        network = psutil.net_io_counters()
        bytes_sent_mb = network.bytes_sent / (1024**2)
        bytes_recv_mb = network.bytes_recv / (1024**2)
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_used_gb': round(memory_used_gb, 2),
            'memory_total_gb': round(memory_total_gb, 2),
            'disk_percent': disk_percent,
            'disk_used_gb': round(disk_used_gb, 2),
            'disk_total_gb': round(disk_total_gb, 2),
            'network_sent_mb': round(bytes_sent_mb, 2),
            'network_recv_mb': round(bytes_recv_mb, 2)
        }
    except Exception as e:
        print(f"Error getting system resources: {e}")
        return None


def get_top_processes(limit=10):
    """
    Get top processes by CPU and memory usage
    """
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                # Get process info
                info = proc.info
                
                # Calculate memory in MB
                memory_mb = info['memory_info'].rss / (1024**2) if info['memory_info'] else 0
                
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'] or 'Unknown',
                    'cpu_percent': info['cpu_percent'] or 0,
                    'memory_percent': info['memory_percent'] or 0,
                    'memory_mb': round(memory_mb, 2)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage (top consumers)
        top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]
        
        # Sort by memory usage
        top_memory = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:limit]
        
        return {
            'top_cpu': top_cpu,
            'top_memory': top_memory
        }
    except Exception as e:
        print(f"Error getting process info: {e}")
        return {'top_cpu': [], 'top_memory': []}


def print_connection_summary(stats):
    """
    Print connection analysis summary
    """
    print("\n" + "=" * 70)
    print("NETWORK CONNECTION SUMMARY")
    print("=" * 70)
    
    print(f"📊 Total Active Connections: {stats['total_connections']}")
    print(f"🌍 Unique IPs: {len(stats['unique_ips'])}")
    print(f"🇺🇸 Countries Connected: {len(stats['unique_countries'])}")
    
    print(f"\n🔗 By Protocol:")
    for proto, count in stats['by_protocol'].most_common():
        print(f"   {proto}: {count}")
    
    print(f"\n🌍 Top Countries:")
    for country, count in stats['by_country'].most_common(10):
        flag = get_country_flag(country)
        print(f"   {flag} {country}: {count}")
    
    print(f"\n🔌 Top Ports Used:")
    for port, count in stats['by_port'].most_common(10):
        port_name = get_port_name(port)
        print(f"   {port} ({port_name}): {count}")
    
    if stats['by_state']:
        print(f"\n📈 TCP Connection States:")
        for state, count in stats['by_state'].most_common():
            print(f"   {state}: {count}")


def print_system_resources(system_stats):
    """
    Print system resource usage
    """
    if not system_stats:
        print("\n⚠️  Could not retrieve system resource information")
        return
    
    print("\n" + "=" * 70)
    print("SYSTEM RESOURCE USAGE")
    print("=" * 70)
    
    # CPU
    cpu_icon = "🔥" if system_stats['cpu_percent'] > 80 else "⚡" if system_stats['cpu_percent'] > 50 else "✅"
    print(f"{cpu_icon} CPU Usage: {system_stats['cpu_percent']}%")
    
    # Memory
    mem_icon = "🔥" if system_stats['memory_percent'] > 80 else "⚠️" if system_stats['memory_percent'] > 60 else "✅"
    print(f"{mem_icon} Memory: {system_stats['memory_used_gb']}GB / {system_stats['memory_total_gb']}GB ({system_stats['memory_percent']}%)")
    
    # Disk
    disk_icon = "🔥" if system_stats['disk_percent'] > 90 else "⚠️" if system_stats['disk_percent'] > 75 else "✅"
    print(f"{disk_icon} Storage: {system_stats['disk_used_gb']}GB / {system_stats['disk_total_gb']}GB ({system_stats['disk_percent']}%)")
    
    # Network
    print(f"📡 Network: {system_stats['network_sent_mb']}MB sent, {system_stats['network_recv_mb']}MB received")


def print_top_processes(process_stats):
    """
    Print top CPU and memory consuming processes
    """
    print("\n" + "=" * 70)
    print("TOP RESOURCE-CONSUMING PROCESSES")
    print("=" * 70)
    
    print("\n🔥 TOP CPU USAGE:")
    print("-" * 50)
    print(f"{'Process':<25} {'PID':<8} {'CPU%':<8} {'Memory%':<10}")
    print("-" * 50)
    
    for proc in process_stats['top_cpu'][:5]:
        print(f"{proc['name'][:24]:<25} {proc['pid']:<8} {proc['cpu_percent']:<8.1f} {proc['memory_percent']:<10.1f}")
    
    print("\n💾 TOP MEMORY USAGE:")
    print("-" * 50)
    print(f"{'Process':<25} {'PID':<8} {'Memory%':<10} {'Memory MB':<12}")
    print("-" * 50)
    
    for proc in process_stats['top_memory'][:5]:
        print(f"{proc['name'][:24]:<25} {proc['pid']:<8} {proc['memory_percent']:<10.1f} {proc['memory_mb']:<12.1f}")


def get_hardware_usage():
    """
    Check which applications are using camera, microphone, Bluetooth, and NFC
    """
    hardware_usage = {
        'camera': [],
        'microphone': [],
        'bluetooth': [],
        'nfc': []
    }
    
    try:
        # Get all running processes
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name'] or 'Unknown'
                proc_exe = proc_info['exe'] or ''
                
                # Camera applications (common camera-using processes)
                camera_processes = [
                    'camera', 'webcam', 'skype', 'zoom', 'teams', 'discord', 'obs',
                    'chrome', 'firefox', 'edge', 'opera', 'safari', 'brave',
                    'photoshop', 'lightroom', 'gimp', 'paint.net', 'capcut'
                ]
                if any(cam.lower() in proc_name.lower() or cam.lower() in proc_exe.lower() 
                      for cam in camera_processes):
                    hardware_usage['camera'].append({
                        'name': proc_name,
                        'pid': proc_info['pid'],
                        'exe': proc_exe
                    })
                
                # Microphone applications
                mic_processes = [
                    'audacity', 'voicemeeter', 'obs', 'streamlabs', 'xsplit',
                    'skype', 'zoom', 'teams', 'discord', 'slack', 'webex',
                    'chrome', 'firefox', 'edge', 'opera', 'brave',
                    'spotify', 'vlc', 'wmplayer', 'itunes', 'music'
                ]
                if any(mic.lower() in proc_name.lower() or mic.lower() in proc_exe.lower() 
                      for mic in mic_processes):
                    hardware_usage['microphone'].append({
                        'name': proc_name,
                        'pid': proc_info['pid'],
                        'exe': proc_exe
                    })
                
                # Bluetooth applications
                bluetooth_processes = [
                    'bluetooth', 'bt', 'blue', 'airpods', 'headphones', 'speaker',
                    'a2dp', 'hid', 'serial', 'pan', 'nap', 'gn', 'sap'
                ]
                if any(bt.lower() in proc_name.lower() or bt.lower() in proc_exe.lower() 
                      for bt in bluetooth_processes):
                    hardware_usage['bluetooth'].append({
                        'name': proc_name,
                        'pid': proc_info['pid'],
                        'exe': proc_exe
                    })
                
                # NFC applications (limited detection)
                nfc_processes = [
                    'nfc', 'near field', 'contactless', 'payment', 'wallet',
                    'android', 'samsung pay', 'apple pay', 'google pay'
                ]
                if any(nfc.lower() in proc_name.lower() or nfc.lower() in proc_exe.lower() 
                      for nfc in nfc_processes):
                    hardware_usage['nfc'].append({
                        'name': proc_name,
                        'pid': proc_info['pid'],
                        'exe': proc_exe
                    })
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    except Exception as e:
        print(f"Error checking hardware usage: {e}")
    
    return hardware_usage


def check_bluetooth_status():
    """
    Check Bluetooth status using Windows commands
    """
    try:
        # Check if Bluetooth is enabled
        result = subprocess.run(
            ['powershell', 'Get-PnpDevice | Where-Object {$_.Class -eq "Bluetooth"} | Select-Object Status'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'OK' in result.stdout:
            return "Enabled"
        else:
            return "Disabled"
    except:
        return "Unknown"


def check_nfc_status():
    """
    Check NFC status (limited on Windows)
    """
    try:
        # Check for NFC devices
        result = subprocess.run(
            ['powershell', 'Get-PnpDevice | Where-Object {$_.Class -eq "Proximity"} | Select-Object Status'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return "Available"
        else:
            return "Not Available"
    except:
        return "Unknown"


def print_hardware_usage(hardware_usage):
    """
    Print hardware usage information
    """
    print("\n" + "=" * 70)
    print("HARDWARE DEVICE USAGE")
    print("=" * 70)
    
    # Camera
    camera_count = len(hardware_usage['camera'])
    camera_icon = "[CAMERA]" if camera_count > 0 else "[CAMERA]"
    print(f"{camera_icon} Camera: {camera_count} applications")
    if hardware_usage['camera']:
        for app in hardware_usage['camera'][:5]:  # Show top 5
            print(f"   - {app['name']} (PID: {app['pid']})")
    
    # Microphone
    mic_count = len(hardware_usage['microphone'])
    mic_icon = "[MIC]" if mic_count > 0 else "[MIC]"
    print(f"{mic_icon} Microphone: {mic_count} applications")
    if hardware_usage['microphone']:
        for app in hardware_usage['microphone'][:5]:  # Show top 5
            print(f"   - {app['name']} (PID: {app['pid']})")
    
    # Bluetooth
    bt_count = len(hardware_usage['bluetooth'])
    bt_status = check_bluetooth_status()
    bt_icon = "[BT]" if bt_count > 0 or bt_status == "Enabled" else "[BT]"
    print(f"{bt_icon} Bluetooth: {bt_count} applications | Status: {bt_status}")
    if hardware_usage['bluetooth']:
        for app in hardware_usage['bluetooth'][:5]:  # Show top 5
            print(f"   - {app['name']} (PID: {app['pid']})")
    
    # NFC
    nfc_count = len(hardware_usage['nfc'])
    nfc_status = check_nfc_status()
    nfc_icon = "[NFC]" if nfc_count > 0 or nfc_status == "Available" else "[NFC]"
    print(f"{nfc_icon} NFC: {nfc_count} applications | Status: {nfc_status}")
    if hardware_usage['nfc']:
        for app in hardware_usage['nfc'][:5]:  # Show top 5
            print(f"   - {app['name']} (PID: {app['pid']})")
    
    # Summary
    total_using = camera_count + mic_count + bt_count + nfc_count
    print(f"\nTotal applications using hardware: {total_using}")
    
    if total_using > 0:
        print("WARNING: Hardware access detected - review for privacy concerns")
    else:
        print("OK: No active hardware usage detected")


def get_country_flag(country):
    """
    Get flag emoji for country (simplified)
    """
    flags = {
        "United States": "🇺🇸",
        "China": "🇨🇳", 
        "Japan": "🇯🇵",
        "Germany": "🇩🇪",
        "United Kingdom": "🇬🇧",
        "France": "🇫🇷",
        "Canada": "🇨🇦",
        "Australia": "🇦🇺",
        "India": "🇮🇳",
        "Brazil": "🇧🇷",
        "Russia": "🇷🇺",
        "South Korea": "🇰🇷",
        "Netherlands": "🇳🇱",
        "Singapore": "🇸🇬",
        "Ireland": "🇮🇪",
        "Local/Private": "🏠"
    }
    return flags.get(country, "🌍")


def get_port_name(port):
    """
    Get common port names
    """
    common_ports = {
        "80": "HTTP",
        "443": "HTTPS", 
        "53": "DNS",
        "22": "SSH",
        "25": "SMTP",
        "110": "POP3",
        "143": "IMAP",
        "993": "IMAPS",
        "995": "POP3S",
        "3389": "RDP",
        "3306": "MySQL",
        "5432": "PostgreSQL",
        "27017": "MongoDB",
        "6379": "Redis",
        "8080": "HTTP-Alt",
        "8443": "HTTPS-Alt"
    }
    return common_ports.get(port, "Unknown")


def main():
    """Main function to check DNS, connections, and system resources"""
    print("=" * 70)
    print(f"DNS Status Checker & System Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Check DNS Servers
    print("\n📡 CHECKING DNS SERVERS:")
    print("-" * 70)
    
    dns_status = {}
    for name, server in DNS_SERVERS.items():
        status, response = ping_host(server)
        dns_status[name] = status
        
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name:<25} | {server:<15} | {response}")
    
    # Check Websites
    print("\n🌐 CHECKING WEBSITES:")
    print("-" * 70)
    
    website_status = {}
    for name, website in WEBSITES.items():
        status, response = ping_host(website)
        website_status[name] = status
        
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name:<25} | {website:<25} | {response}")
    
    # Get and analyze active connections
    print("\n🔍 ANALYZING NETWORK CONNECTIONS...")
    connections = get_active_connections()
    stats = analyze_connections(connections)
    
    # Print connection summary
    print_connection_summary(stats)
    
    # Get system resource usage
    print("\n💻 ANALYZING SYSTEM RESOURCES...")
    system_stats = get_system_resources()
    print_system_resources(system_stats)
    
    # Get top processes
    process_stats = get_top_processes()
    print_top_processes(process_stats)
    
    # Check hardware usage
    hardware_usage = get_hardware_usage()
    print_hardware_usage(hardware_usage)
    
    # Overall Summary
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY:")
    print("-" * 70)
    
    total_dns = len(dns_status)
    healthy_dns = sum(1 for v in dns_status.values() if v)
    
    total_websites = len(website_status)
    healthy_websites = sum(1 for v in website_status.values() if v)
    
    print(f"DNS Servers: {healthy_dns}/{total_dns} operational")
    print(f"Websites: {healthy_websites}/{total_websites} accessible")
    print(f"Active Connections: {stats['total_connections']}")
    print(f"Countries Connected: {len(stats['unique_countries'])}")
    
    if system_stats:
        print(f"CPU Usage: {system_stats['cpu_percent']}%")
        print(f"Memory Usage: {system_stats['memory_percent']}%")
        print(f"Storage Usage: {system_stats['disk_percent']}%")
    
    overall_status = healthy_dns + healthy_websites
    total = total_dns + total_websites
    print(f"\nNetwork Health: {overall_status}/{total} services operational")
    
    if overall_status == total:
        print("🟢 All services are operational!")
    elif overall_status >= total * 0.75:
        print("🟡 Most services operational, some issues detected")
    else:
        print("🔴 Multiple service failures detected")
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
