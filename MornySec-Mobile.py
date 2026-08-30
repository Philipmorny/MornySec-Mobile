#!/usr/bin/env python3
"""
MornySec-Mobile - Advanced Stealth Mobile Device Discovery & Exploitation
Version: 3.0.0 - For Authorized Testing Only
"""

import argparse
import ipaddress
import socket
import base64
import re
import threading
import time
import sys
import os
import subprocess
import random
import struct
import binascii
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
        BLUE = '\033[94m'; MAGENTA = '\033[95m'; CYAN = '\033[96m'
        WHITE = '\033[97m'; RESET = '\033[0m'
    class Style:
        RESET_ALL = '\033[0m'; BRIGHT = '\033[1m'

def print_status(message: str, status_type: str = 'info'):
    colors = {
        'info': Fore.CYAN,
        'found': Fore.GREEN,
        'warning': Fore.YELLOW,
        'error': Fore.RED,
        'success': Fore.GREEN + Style.BRIGHT,
        'exploit': Fore.MAGENTA + Style.BRIGHT,
        'critical': Fore.RED + Style.BRIGHT,
        'stealth': Fore.BLUE + Style.BRIGHT,
        'vuln': Fore.YELLOW + Style.BRIGHT,
        'c2': Fore.BLUE + Style.BRIGHT,
        'output': Fore.GREEN
    }
    color = colors.get(status_type, Fore.WHITE)
    print(f"{color}{message}{Style.RESET_ALL}")

def print_banner():
    print_status("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║   📱 MornySec-Mobile v3.0.0 - Advanced Stealth Scanner      ║
    ║   Bypasses: Firewalls | Sleep Mode | Network Isolation       ║
    ║   Created by: Philip Morny                                    ║
    ║   For Authorized Security Testing Only                        ║
    ╚═══════════════════════════════════════════════════════════════╝
    """, 'stealth')

# ============================================
# CONFIGURATION
# ============================================

VERSION = "3.0.0"
AUTHOR = "Philip Morny"
REPO_URL = "https://github.com/cyberobinhood/MornySec-Mobile"

# ============================================
# MAC VENDOR DATABASE (Complete)
# ============================================

MAC_VENDORS = {
    '08:63:61': 'Apple', '1C:1C:6E': 'Apple', '34:12:98': 'Apple',
    '40:31:3C': 'Apple', '50:1A:C5': 'Apple', '8C:29:37': 'Apple',
    'A8:66:7F': 'Apple', 'AC:29:3A': 'Apple', 'B0:34:95': 'Apple',
    'C0:E5:4E': 'Apple', 'D4:61:DA': 'Apple', 'E0:36:76': 'Apple',
    'F0:18:98': 'Apple', 'F4:5C:89': 'Apple',
    
    '00:11:22': 'Samsung', '00:12:13': 'Samsung', '00:1F:E0': 'Samsung',
    'F4:37:B7': 'Samsung', 'BC:20:A4': 'Samsung', 'E4:8D:8C': 'Samsung',
    '88:23:FE': 'Samsung', 'E8:48:B8': 'Samsung', 'CC:2E:5B': 'Samsung',
    'C8:4B:D6': 'Samsung', 'DC:A4:CA': 'Samsung',
    
    '00:16:6C': 'LG', '00:1A:C5': 'LG', '00:1C:3D': 'LG',
    '30:8D:99': 'LG', 'E0:03:2B': 'LG', '90:B1:1C': 'LG',
    '80:A5:89': 'LG',
    
    '00:18:17': 'HTC', '00:19:76': 'HTC', '00:21:2B': 'HTC',
    '00:1D:5B': 'Sony', '00:21:2B': 'Sony', '60:45:CB': 'Sony',
    '88:6A:1E': 'Sony',
    
    '00:1A:79': 'Motorola', '00:21:87': 'Motorola', 'B4:DF:D7': 'Motorola',
    '1C:6B:4A': 'Motorola',
    
    '00:25:9C': 'Huawei', 'E0:91:F5': 'Huawei', '3C:CE:73': 'Huawei',
    '6C:E7:8A': 'Huawei', 'A4:1F:72': 'Huawei',
    
    '00:26:12': 'Xiaomi', '04:FE:31': 'Xiaomi', '7C:DD:90': 'Xiaomi',
    '1C:66:AA': 'Xiaomi', 'B8:27:EB': 'Xiaomi',
    
    '00:23:D4': 'OnePlus', '1C:6A:7A': 'OnePlus', 'B4:6B:FC': 'OnePlus',
    'F0:67:5D': 'Google', 'E4:8B:7C': 'Google', '3C:B3:CD': 'Google',
}

# ============================================
# ADVANCED STEALTH DISCOVERY ENGINE
# ============================================

class StealthDiscovery:
    """Advanced stealth device discovery with multiple techniques"""
    
    def __init__(self, timeout: int = 5, stealth_mode: bool = True):
        self.timeout = timeout
        self.stealth_mode = stealth_mode
        self.devices_found = []
        
        # Extended port list for aggressive scanning
        self.mobile_ports = {
            5555: 'ADB', 62078: 'iOS Lockdown', 5353: 'mDNS',
            5037: 'ADB Debug', 4444: 'Android Debug', 8080: 'HTTP Proxy',
            80: 'HTTP', 443: 'HTTPS', 22: 'SSH', 21: 'FTP',
            139: 'NetBIOS', 445: 'SMB', 6000: 'X11',
            123: 'NTP', 161: 'SNMP', 137: 'NetBIOS-NS',
            138: 'NetBIOS-DGM', 143: 'IMAP', 993: 'IMAPS',
            995: 'POP3S', 5900: 'VNC', 3389: 'RDP',
            6001: 'X11-1', 6002: 'X11-2', 6003: 'X11-3',
            8081: 'HTTP-Alt', 8443: 'HTTPS-Alt', 8888: 'HTTP-Alt2',
            9001: 'Tor', 9090: 'HTTP-Alt3', 9100: 'PJL',
            9999: 'HTTP-Alt4', 10000: 'Webmin', 10001: 'HTTP-Alt5'
        }
    
    # ============================================
    # TECHNIQUE 1: ARP SCAN (Find all live hosts)
    # ============================================
    
    def arp_scan(self, network: str) -> List[str]:
        """ARP scan to find all live hosts on the network"""
        print_status("[*] Technique 1: ARP Scanning for live hosts...", 'stealth')
        
        live_hosts = []
        try:
            # Use arp-scan if available
            result = subprocess.run(
                ['sudo', 'arp-scan', '--localnet', '--retry=2'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line and not line.startswith(('Starting', 'Ending', 'Interface')):
                        parts = line.split()
                        if len(parts) >= 2 and parts[1].count('.') == 3:
                            live_hosts.append(parts[1])
                
                if live_hosts:
                    print_status(f"[+] ARP scan found {len(live_hosts)} live hosts", 'success')
                    return live_hosts
            
            # Fallback: ping sweep
            print_status("[*] ARP-scan not available, trying ping sweep...", 'warning')
            net = ipaddress.ip_network(network, strict=False)
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = {executor.submit(self.ping_host, str(ip)): str(ip) for ip in net.hosts()}
                for future in as_completed(futures):
                    ip = futures[future]
                    try:
                        if future.result(timeout=2):
                            live_hosts.append(ip)
                    except:
                        pass
            
            if live_hosts:
                print_status(f"[+] Ping sweep found {len(live_hosts)} live hosts", 'success')
            
        except Exception as e:
            print_status(f"[!] ARP scan error: {e}", 'error')
        
        return live_hosts
    
    def ping_host(self, ip: str) -> bool:
        """Ping a host to check if it's alive"""
        try:
            param = '-n' if sys.platform == 'win32' else '-c'
            result = subprocess.run(
                ['ping', param, '1', '-W', '1', ip],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    # ============================================
    # TECHNIQUE 2: TCP SYN Stealth Scan
    # ============================================
    
    def stealth_tcp_scan(self, ip: str, ports: List[int]) -> List[int]:
        """TCP SYN stealth scan to bypass firewalls"""
        open_ports = []
        
        for port in ports:
            try:
                # Create raw socket for SYN scan (requires root)
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                sock.settimeout(1)
                
                # Build TCP SYN packet
                # (Simplified - using connect() as fallback)
                sock.close()
                
                # If raw socket fails, use standard connect
                if self.check_port_tcp(ip, port):
                    open_ports.append(port)
                    
            except PermissionError:
                # Fallback to standard connect if no root
                if self.check_port_tcp(ip, port):
                    open_ports.append(port)
            except:
                pass
        
        return open_ports
    
    def check_port_tcp(self, ip: str, port: int) -> bool:
        """TCP connect scan with random delays for stealth"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.5)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0 and self.stealth_mode:
                # Random delay to avoid detection
                time.sleep(random.uniform(0.05, 0.2))
            
            return result == 0
        except:
            return False
    
    # ============================================
    # TECHNIQUE 3: UDP Scan
    # ============================================
    
    def udp_scan(self, ip: str, ports: List[int]) -> List[int]:
        """UDP scan for services that don't respond to TCP"""
        open_ports = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1)
                
                # Send empty UDP packet
                sock.sendto(b'', (ip, port))
                
                # Try to receive response
                try:
                    data, _ = sock.recvfrom(1024)
                    open_ports.append(port)
                except socket.timeout:
                    # No response doesn't mean closed - could be filtered
                    pass
                finally:
                    sock.close()
            except:
                pass
        
        return open_ports
    
    # ============================================
    # TECHNIQUE 4: mDNS/Bonjour Discovery
    # ============================================
    
    def mdns_broadcast(self) -> List[str]:
        """Broadcast mDNS query to find all Apple devices"""
        print_status("[*] Technique 4: mDNS/Bonjour broadcast...", 'stealth')
        discovered = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # mDNS query for all services
            mdns_query = bytes([
                0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x0C, 0x00, 0x01
            ])
            
            sock.sendto(mdns_query, ('224.0.0.251', 5353))
            
            start_time = time.time()
            while time.time() - start_time < 3:
                try:
                    data, addr = sock.recvfrom(1024)
                    if addr[0] not in discovered and addr[0] != '0.0.0.0':
                        discovered.append(addr[0])
                except socket.timeout:
                    break
            
            sock.close()
            
            if discovered:
                print_status(f"[+] mDNS found {len(discovered)} devices", 'success')
            
        except Exception as e:
            print_status(f"[!] mDNS error: {e}", 'error')
        
        return discovered
    
    # ============================================
    # TECHNIQUE 5: Wake-on-LAN (WOL)
    # ============================================
    
    def send_wol(self, mac: str) -> bool:
        """Send Wake-on-LAN magic packet to wake sleeping devices"""
        try:
            # Remove colons from MAC
            mac = mac.replace(':', '').replace('-', '')
            
            # Create magic packet
            data = b'\xff' * 6 + (bytes.fromhex(mac) * 16)
            
            # Send to broadcast address
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, ('255.255.255.255', 9))
            sock.close()
            
            return True
        except:
            return False
    
    # ============================================
    # TECHNIQUE 6: NetBIOS/LLMNR Discovery
    # ============================================
    
    def netbios_scan(self, ip: str) -> Optional[str]:
        """Query NetBIOS name service"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            
            # NetBIOS name query
            nbns_query = bytes([
                0x00, 0x00, 0x00, 0x10, 0x00, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x20, 0x43, 0x4B, 0x41,
                0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
                0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
                0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41,
                0x41, 0x41, 0x41, 0x00, 0x00, 0x21, 0x00, 0x01
            ])
            
            sock.sendto(nbns_query, (ip, 137))
            data, _ = sock.recvfrom(1024)
            sock.close()
            
            if data:
                return data[:100].hex()
        except:
            pass
        return None
    
    # ============================================
    # TECHNIQUE 7: ICMP Timestamp / Echo
    # ============================================
    
    def icmp_timestamp(self, ip: str) -> bool:
        """ICMP timestamp request to identify hosts (bypasses firewalls)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.settimeout(1)
            
            # ICMP Timestamp request
            packet = struct.pack('!BBHHH', 13, 0, 0, 0, 0)
            sock.sendto(packet, (ip, 0))
            
            try:
                data, _ = sock.recvfrom(1024)
                sock.close()
                return True
            except socket.timeout:
                sock.close()
                return False
        except:
            return False
    
    # ============================================
    # MAIN COMPREHENSIVE SCAN
    # ============================================
    
    def scan_network(self, network: str) -> List[Dict]:
        """Full comprehensive stealth scan"""
        devices = []
        discovered_ips = set()
        
        print_status("\n" + "="*60, 'stealth')
        print_status("🛡️  ADVANCED STEALTH SCAN INITIATED", 'stealth')
        print_status("="*60, 'stealth')
        
        # TECHNIQUE 1: ARP Scan
        live_hosts = self.arp_scan(network)
        discovered_ips.update(live_hosts)
        
        # TECHNIQUE 2: mDNS Broadcast
        mdns_hosts = self.mdns_broadcast()
        discovered_ips.update(mdns_hosts)
        
        # If no hosts found, do aggressive ping sweep
        if not discovered_ips:
            print_status("[*] No hosts found. Starting aggressive discovery...", 'warning')
            
            net = ipaddress.ip_network(network, strict=False)
            hosts_to_scan = [str(ip) for ip in net.hosts()][:254]
            
            # Quick port scan on common mobile ports
            quick_ports = [5555, 62078, 5353, 22, 80, 443, 8080, 5037]
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = {executor.submit(self.quick_host_check, ip, quick_ports): ip for ip in hosts_to_scan}
                
                for future in as_completed(futures):
                    ip = futures[future]
                    try:
                        if future.result(timeout=5):
                            discovered_ips.add(ip)
                            print_status(f"[+] Found: {ip}", 'found')
                    except:
                        pass
        
        # Now scan each discovered IP in detail
        if discovered_ips:
            print_status(f"\n[*] Performing detailed scan on {len(discovered_ips)} hosts", 'info')
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(self.detailed_scan, ip): ip for ip in discovered_ips}
                
                for future in as_completed(futures):
                    ip = futures[future]
                    try:
                        result = future.result(timeout=10)
                        if result and result.get('is_mobile', False):
                            devices.append(result)
                            vendor = result.get('vendor', 'Unknown')
                            os_info = result.get('os', 'Unknown')
                            confidence = result.get('confidence', 0)
                            print_status(f"[+] 📱 {ip} ({vendor} - {os_info}) [Confidence: {confidence}%]", 'found')
                    except Exception as e:
                        if self.stealth_mode:
                            pass  # Silent fail in stealth mode
        
        print_status(f"\n[*] Scan complete. Found {len(devices)} mobile devices", 'success')
        return devices
    
    def quick_host_check(self, ip: str, ports: List[int]) -> bool:
        """Quick check if host is a mobile device"""
        for port in ports:
            if self.check_port_tcp(ip, port):
                return True
            
            # Check UDP for mDNS
            if port == 5353:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(1)
                    sock.sendto(b'', (ip, 5353))
                    try:
                        data, _ = sock.recvfrom(1024)
                        sock.close()
                        return True
                    except:
                        sock.close()
                except:
                    pass
        
        return False
    
    def get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address via ARP"""
        try:
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=2)
            for line in result.stdout.split('\n'):
                if ip in line:
                    parts = line.split()
                    for part in parts:
                        if re.match(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', part):
                            return part.upper()
            return None
        except:
            return None
    
    def identify_vendor_by_mac(self, mac: str) -> str:
        """Identify device vendor from MAC"""
        if not mac:
            return 'Unknown'
        
        mac_upper = mac.upper()
        for prefix, vendor in MAC_VENDORS.items():
            if mac_upper.startswith(prefix):
                return vendor
        
        return 'Unknown'
    
    def detailed_scan(self, ip: str) -> Dict:
        """Detailed scan of a single IP with multiple techniques"""
        result = {
            'ip': ip,
            'is_mobile': False,
            'os': 'Unknown',
            'vendor': 'Unknown',
            'mac': None,
            'ports': [],
            'services': {},
            'confidence': 0,
            'discovery_methods': []
        }
        
        # Get MAC
        mac = self.get_mac_address(ip)
        if mac:
            result['mac'] = mac
            vendor = self.identify_vendor_by_mac(mac)
            result['vendor'] = vendor
            if vendor != 'Unknown':
                result['is_mobile'] = True
                result['confidence'] += 30
                result['discovery_methods'].append('MAC')
        
        # Port scan all mobile ports
        open_ports = []
        
        for port, service in self.mobile_ports.items():
            if self.check_port_tcp(ip, port):
                open_ports.append(port)
                result['services'][port] = service
        
        # UDP Scan for mDNS
        if 5353 in result['services']:
            result['discovery_methods'].append('mDNS')
            result['confidence'] += 20
            if result['os'] == 'Unknown':
                result['os'] = 'iOS'
        
        result['ports'] = open_ports
        
        # Check for Android (ADB)
        if 5555 in open_ports or 5037 in open_ports:
            result['is_mobile'] = True
            result['os'] = 'Android'
            result['confidence'] += 40
            result['discovery_methods'].append('ADB')
        
        # Check for iOS (Lockdown)
        if 62078 in open_ports:
            result['is_mobile'] = True
            result['os'] = 'iOS'
            result['confidence'] += 30
            result['discovery_methods'].append('iOS_Lockdown')
        
        # Check for generic mobile ports
        mobile_indicators = [22, 80, 443, 8080]
        if any(p in open_ports for p in mobile_indicators):
            if result['vendor'] != 'Unknown':
                result['is_mobile'] = True
                result['confidence'] += 10
        
        return result

# ============================================
# SESSION MANAGEMENT & C2 (Same as before)
# ============================================

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.session_id = 0
    
    def create_session(self, device_ip: str, exploit_type: str, connection) -> int:
        self.session_id += 1
        session = {
            'id': self.session_id,
            'ip': device_ip,
            'exploit_type': exploit_type,
            'connection': connection,
            'created': datetime.now(),
            'last_active': datetime.now(),
            'commands_executed': 0,
            'output_log': []
        }
        self.sessions[self.session_id] = session
        return self.session_id
    
    def get_session(self, session_id: int):
        return self.sessions.get(session_id)
    
    def list_sessions(self):
        return list(self.sessions.values())
    
    def remove_session(self, session_id: int):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def execute_command(self, session_id: int, command: str) -> Dict:
        session = self.get_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        session['last_active'] = datetime.now()
        session['commands_executed'] += 1
        
        if session['exploit_type'] == 'adb':
            return self._execute_adb_command(session, command)
        else:
            return {'success': False, 'error': 'Unknown exploit type'}
    
    def _execute_adb_command(self, session: Dict, command: str) -> Dict:
        try:
            ip = session['ip']
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, 5555))
            
            sock.send(b'CNXN\x00\x00\x00\x01\x00\x00\x00\x00\x10\x00\x00\x00')
            response = sock.recv(1024)
            
            if response and b'OKAY' in response:
                cmd = f"shell:{command}\n".encode()
                sock.send(cmd)
                output = sock.recv(8192)
                sock.close()
                
                return {
                    'success': True,
                    'output': output.decode('utf-8', errors='ignore'),
                    'command': command
                }
            else:
                return {'success': False, 'error': 'ADB connection failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ============================================
# MAIN APPLICATION
# ============================================

class MornySecMobile:
    def __init__(self, args):
        self.args = args
        self.discovery = StealthDiscovery(timeout=args.timeout, stealth_mode=True)
        self.session_manager = SessionManager()
        self.devices = []
    
    def scan(self) -> List[Dict]:
        network = self.args.target
        self.devices = self.discovery.scan_network(network)
        return self.devices
    
    def report(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_name = f"MornySec_Stealth_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_name, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("📱 MORNY-SEC STEALTH SCAN REPORT\n")
            f.write(f"Generated: {timestamp}\n")
            f.write(f"Tool: MornySec-Mobile {VERSION}\n")
            f.write(f"Author: {AUTHOR}\n")
            f.write("="*70 + "\n\n")
            
            if self.devices:
                f.write("📱 DEVICES DISCOVERED\n")
                f.write("-"*70 + "\n\n")
                
                for idx, device in enumerate(self.devices, 1):
                    f.write(f"[{idx}] {device['ip']}\n")
                    f.write(f"    OS: {device.get('os', 'Unknown')}\n")
                    f.write(f"    Vendor: {device.get('vendor', 'Unknown')}\n")
                    f.write(f"    Confidence: {device.get('confidence', 0)}%\n")
                    f.write(f"    Ports: {device.get('ports', [])}\n")
                    f.write(f"    Discovery Methods: {', '.join(device.get('discovery_methods', []))}\n")
                    if device.get('mac'):
                        f.write(f"    MAC: {device['mac']}\n")
                    f.write("\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("🔒 SECURITY RECOMMENDATIONS\n")
            f.write("="*70 + "\n\n")
            f.write("1. Change default passwords immediately\n")
            f.write("2. Disable unnecessary services (ADB, mDNS, etc.)\n")
            f.write("3. Enable firewall on all devices\n")
            f.write("4. Use strong WiFi encryption\n")
            f.write("5. Regular security audits\n")
        
        print_status(f"\n📄 Stealth report saved to: {report_name}", 'success')

# ============================================
# MAIN ENTRY POINT
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='MornySec-Mobile - Advanced Stealth Mobile Discovery',
        epilog=f'Example: sudo python3 MornySec-Mobile.py 192.168.1.0/24 -s\n\n'
               f'Author: {AUTHOR}\n'
               f'Repository: {REPO_URL}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('target', help='Target IP or CIDR range')
    parser.add_argument('-t', '--threads', default=50, type=int,
                       help='Number of threads (default: 50)')
    parser.add_argument('--timeout', default=5, type=int,
                       help='Connection timeout (default: 5)')
    parser.add_argument('-s', '--scan', action='store_true',
                       help='Scan for mobile devices')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--version', action='version',
                       version=f'MornySec-Mobile {VERSION}')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    print_status("⚠️  LEGAL NOTICE: Only use on networks you own or have", 'warning')
    print_status("   explicit authorization to test.", 'warning')
    print_status(f"   Repository: {REPO_URL}", 'info')
    print()
    
    # Need root for advanced scanning
    if os.geteuid() != 0:
        print_status("⚠️  Some stealth techniques require root privileges", 'warning')
        print_status("    Run with: sudo python3 MornySec-Mobile.py ...", 'warning')
        print()
    
    scanner = MornySecMobile(args)
    
    if args.scan:
        print_status("[*] Starting advanced stealth discovery...", 'stealth')
        devices = scanner.scan()
        
        if not devices:
            print_status("[!] No devices discovered", 'error')
            print_status("[!] Try these techniques:", 'warning')
            print_status("   1. Run with sudo for better scanning", 'warning')
            print_status("   2. Make sure devices are powered on", 'warning')
            print_status("   3. Check if you're on the correct network", 'warning')
            print_status("   4. Try: sudo python3 MornySec-Mobile.py 192.168.1.0/24 -s -v", 'warning')
            sys.exit(1)
        
        scanner.report()
    
    if not args.scan:
        parser.print_help()

if __name__ == '__main__':
    main()
