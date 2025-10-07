#!/usr/bin/env python3
"""
Cellframe Masternode Inspector - Installer
Installs the plugin to /opt/cellframe-node/var/lib/plugins
"""

import os
import sys
import shutil
import secrets
import subprocess
import urllib.request
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def check_root():
    """Check if running as root/sudo"""
    if os.geteuid() != 0:
        print_error("This installer must be run as root or with sudo")
        print_info("Please run: sudo python3 install.py")
        sys.exit(1)
    print_success("Running with elevated privileges")

def check_node_installed():
    """Check if Cellframe node is installed"""
    if not os.path.exists("/opt/cellframe-node"):
        print_error("Cellframe node not found at /opt/cellframe-node")
        print_info("Please install Cellframe node first")
        sys.exit(1)
    print_success("Cellframe node installation found")

def get_plugin_files():
    """Get list of files to copy (automatically detect Python files)"""
    script_dir = Path(__file__).parent

    # Files to exclude from copying
    exclude_files = {
        'install.py',           # This installer
        '__pycache__',          # Python cache
        'token.txt',            # Auto-generated token
        'mninspector.log',      # Log file
        '.git',                 # Git directory
        '.gitignore',           # Git ignore
        'README.md',            # Documentation (optional)
        '__init__.py'           # Not needed for plugin
    }

    # Required files that must exist
    required_files = {
        'manifest.json',
        'requirements.txt',
        'LICENSE'
    }

    # Get all Python files
    python_files = [f.name for f in script_dir.glob('*.py') if f.name not in exclude_files]

    # Combine Python files with required files
    files = list(set(python_files) | required_files)

    # Verify required files exist
    missing = []
    for f in required_files:
        if not (script_dir / f).exists():
            missing.append(f)

    if missing:
        print_error(f"Missing required files: {', '.join(missing)}")
        sys.exit(1)

    print_info(f"Found {len(files)} files to copy")
    return sorted(files)

def install_dependencies():
    """Install Python dependencies using Cellframe's pip"""
    print_info("Installing Python dependencies...")

    cellframe_pip = "/opt/cellframe-node/python/bin/pip3"

    # Check if Cellframe's pip exists
    if not os.path.exists(cellframe_pip):
        print_error(f"Cellframe pip not found at {cellframe_pip}")
        print_info("Please ensure Cellframe node is properly installed")
        return False

    try:
        subprocess.run(
            [cellframe_pip, "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to install dependencies: {e.stderr}")
        print_info(f"You may need to install them manually: {cellframe_pip} install -r requirements.txt")
        return False

def copy_plugin_files(target_dir):
    """Copy plugin files to target directory"""
    script_dir = Path(__file__).parent
    files = get_plugin_files()

    print_info(f"Copying plugin files to {target_dir}...")

    for file in files:
        src = script_dir / file
        dst = target_dir / file
        try:
            shutil.copy2(src, dst)
            print_success(f"Copied {file}")
        except Exception as e:
            print_error(f"Failed to copy {file}: {e}")
            sys.exit(1)

def create_config_file():
    """Create plugin configuration file in /opt/cellframe-node/etc/cellframe-node.cfg.d/"""
    config_dir = Path("/opt/cellframe-node/etc/cellframe-node.cfg.d")
    config_file = config_dir / "mninspector.cfg"

    print_info(f"Creating plugin configuration: {config_file}")

    # Create config.d directory if it doesn't exist
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print_success(f"Config directory ready: {config_dir}")
    except Exception as e:
        print_error(f"Failed to create config directory: {e}")
        return False

    # Check if config already exists
    if config_file.exists():
        print_warning("Plugin configuration file already exists")
        response = input("Overwrite existing configuration? (y/N): ").lower()
        if response != 'y':
            print_info("Keeping existing configuration")
            return True

    # Create config content
    config_content = """
[server]
enabled=true

[plugins]
enabled=true
# Load Python-based plugins
py_load=true
py_path=../var/lib/plugins

[mninspector]
plugin_url=mninspector
autoupdate=false
days_cutoff=20
block_count_threshold=30
access_token_entropy=64
compress_responses=true
debug=false
"""

    # Write config file
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        os.chmod(config_file, 0o644)  # rw-r--r--
        print_success(f"Configuration file created: {config_file}")
        return True
    except Exception as e:
        print_error(f"Failed to create config file: {e}")
        return False

def generate_or_get_token(plugin_dir, entropy=64):
    """Generate or get existing token using same method as plugin"""
    # Validate entropy (same as utils.py)
    if entropy > 64:
        print_warning("Token entropy too high, setting to 64.")
        entropy = 64
    elif entropy < 16:
        print_warning("Token entropy too low, setting to 16.")
        entropy = 16

    token_file = plugin_dir / "token.txt"

    # Check for existing token
    if token_file.exists():
        try:
            with open(token_file, 'r') as f:
                token = f.read().strip()
                if token:
                    print_success(f"Using existing token from {token_file}")
                    return token, True
        except Exception as e:
            print_warning(f"Failed to read existing token: {e}")

    # Generate new token using same method as plugin (secrets.token_urlsafe)
    token = secrets.token_urlsafe(entropy)

    try:
        with open(token_file, 'w') as f:
            f.write(token)
        os.chmod(token_file, 0o600)  # Only owner can read
        print_success(f"Generated new token and saved to {token_file}")
        return token, False
    except Exception as e:
        print_error(f"Failed to save token: {e}")
        return token, False

def is_ipv4(ip):
    """Check if IP address is valid IPv4"""
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            num = int(part)
            if num < 0 or num > 255:
                return False
        return True
    except (ValueError, AttributeError):
        return False

def get_external_ip():
    """Get external IPv4 address of the server"""
    services = [
        'https://api.ipify.org',
        'https://ipv4.icanhazip.com',
        'https://v4.ident.me'
    ]

    for service in services:
        try:
            with urllib.request.urlopen(service, timeout=5) as response:
                ip = response.read().decode('utf-8').strip()
                if ip and is_ipv4(ip):
                    return ip
        except Exception:
            continue

    return None

def get_node_http_port():
    """Get HTTP port from Cellframe node configuration"""
    config_file = "/opt/cellframe-node/etc/cellframe-node.cfg"
    try:
        with open(config_file, 'r') as f:
            in_server_section = False
            for line in f:
                line = line.strip()
                if line == '[server]':
                    in_server_section = True
                    continue
                if in_server_section:
                    if line.startswith('['):
                        break
                    if line.startswith('listen_address'):
                        # Extract port from listen_address=[0.0.0.0:8079]
                        parts = line.split(':')
                        if len(parts) >= 2:
                            port = parts[-1].rstrip(']').strip()
                            return port
    except Exception:
        pass
    return "8079"  # Default port

def print_instructions(plugin_dir, token, is_existing):
    """Print post-installation instructions"""
    print_header("Installation Complete!")

    print(f"{Colors.BOLD}Plugin installed to:{Colors.ENDC} {plugin_dir}")
    print(f"{Colors.BOLD}Config file:{Colors.ENDC} /opt/cellframe-node/etc/cellframe-node.cfg.d/mninspector.cfg\n")

    # Display token
    if is_existing:
        print(f"{Colors.BOLD}Access Token (existing):{Colors.ENDC}")
    else:
        print(f"{Colors.BOLD}Access Token (newly generated):{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{token}{Colors.ENDC}")
    print(f"{Colors.WARNING}Keep this token secure! It's required for API access.{Colors.ENDC}\n")

    # Get external IP and HTTP port
    print_info("Detecting server information...")
    external_ip = get_external_ip()
    http_port = get_node_http_port()

    if external_ip:
        print(f"{Colors.BOLD}Server IP Address:{Colors.ENDC} {Colors.OKGREEN}{external_ip}{Colors.ENDC}")
    else:
        print_warning("Could not detect external IP address")

    print(f"{Colors.BOLD}Node HTTP Port:{Colors.ENDC} {Colors.OKGREEN}{http_port}{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Next steps:{Colors.ENDC}")
    print("1. Restart Cellframe node:")
    print(f"   {Colors.OKCYAN}sudo systemctl restart cellframe-node{Colors.ENDC}")
    print("\n2. Check plugin log:")
    print(f"   {Colors.OKCYAN}cat {plugin_dir}/mninspector.log{Colors.ENDC}")
    print("\n3. Test API endpoint (local):")
    print(f"   {Colors.OKCYAN}curl -H 'X-API-Key: {token}' 'http://localhost:{http_port}/mninspector?action=help'{Colors.ENDC}")

    print(f"\n{Colors.BOLD}Web UI Access:{Colors.ENDC}")
    print(f"Use the FREE web interface at: {Colors.OKGREEN}https://cellframemasternodeinspector.pqcc.fi{Colors.ENDC}")
    print("\nConfiguration for web UI:")
    if external_ip:
        print(f"  {Colors.BOLD}API URL:{Colors.ENDC} http://{external_ip}:{http_port}/mninspector")
    else:
        print(f"  {Colors.BOLD}API URL:{Colors.ENDC} http://<your-server-ip>:{http_port}/mninspector")
    print(f"  {Colors.BOLD}API Key:{Colors.ENDC} {token}")

    print(f"\n{Colors.WARNING}Note:{Colors.ENDC} Make sure port {http_port} is open in your firewall for remote access!")
    print(f"\n{Colors.BOLD}Alternative - Self-host the web UI:{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}git clone https://github.com/hyttmi/cellframe-masternode-inspector-ui.git{Colors.ENDC}")
    print()

def main():
    print_header("Cellframe Masternode Inspector - Installer")

    # Checks
    check_root()
    check_node_installed()

    # Get installation directory
    default_plugin_dir = "/opt/cellframe-node/var/lib/plugins/cellframe_masternode_inspector"
    plugin_dir = input(f"Installation directory [{default_plugin_dir}]: ").strip() or default_plugin_dir
    plugin_dir = Path(plugin_dir)

    # Check if directory exists
    if plugin_dir.exists():
        print_warning(f"Plugin directory already exists: {plugin_dir}")
        token_file = plugin_dir / "token.txt"
        if token_file.exists():
            print_info("Existing token.txt found - it will be preserved")
        response = input("Update plugin files? (Y/n): ").lower()
        if response == 'n':
            print_info("Installation cancelled")
            sys.exit(0)
    else:
        # Create directory
        try:
            plugin_dir.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {plugin_dir}")
        except Exception as e:
            print_error(f"Failed to create directory: {e}")
            sys.exit(1)

    # Install dependencies
    install_dependencies()

    # Copy files
    copy_plugin_files(plugin_dir)

    # Create config file
    create_config_file()

    # Generate or get token (using same method as plugin)
    token, is_existing = generate_or_get_token(plugin_dir, entropy=64)

    # Print instructions
    print_instructions(plugin_dir, token, is_existing)

    print_success("Installation completed successfully!")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_warning("Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
