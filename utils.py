import os, uuid, json, re, requests, requests_unixsocket, secrets
from http.client import RemoteDisconnected
from logconfig import logger
from datetime import datetime, timezone
from config import Config
from packaging import version
from command_runner import command_runner

class Utils:
    def __init__(self):
        self._current_script_path = self.get_current_script_path()
        self._generate_random_token = self.generate_random_token()
        self._rpc_session = requests.Session()
        self._unix_session = requests_unixsocket.Session()
        self._unix_url = "http+unix://%2Fopt%2Fcellframe-node%2Fvar%2Frun%2Fnode_cli/connect"
        self._rpc_url = "http://dev.rpc.cellframe.net"
        self._rpc_session_headers = {"Content-Type": "application/json"}

    def send_request(self, method, subcommand, arguments=None, request_id="1", use_unix=False):
        if subcommand and len(subcommand) > 1:
            subcommand = subcommand.split()

        request_data = {
            "method": method,
            "subcommand": subcommand,
            "arguments": arguments,
            "id": request_id
        }

        if use_unix:
            try:
                resp = self._unix_session.post(self._unix_url, data=json.dumps(request_data), headers=self._rpc_session_headers)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Unix socket request failed: {e}", exc_info=True)
                return None

        try:
            resp = self._rpc_session.post(self._rpc_url, data=json.dumps(request_data), headers=self._rpc_session_headers)
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, RemoteDisconnected) as e:
            logger.warning(f"RPC request failed ({e}), falling back to Unix socket")
            try:
                resp = self._unix_session.post(self._unix_url, data=json.dumps(request_data), headers=self._rpc_session_headers)
                resp.raise_for_status()
                return resp.json()
            except Exception as e2:
                logger.error(f"Unix socket fallback request failed: {e2}", exc_info=True)
                return None
        except Exception as e:
            logger.error(f"RPC request failed with unexpected error: {e}", exc_info=True)
            return None

    @staticmethod
    def cli_command(command, timeout=120, is_shell_command=False, is_tool_command=False, split_lines=False):
        try:
            if is_shell_command:
                exit_code, output = command_runner(
                    command,
                    timeout=timeout,
                    shell=True,
                    method='poller'
                )
            elif is_tool_command:
                exit_code, output = command_runner(
                    f"/opt/cellframe-node/bin/cellframe-node-tool {command}",
                    timeout=timeout, method='poller'
                )
            else:
                exit_code, output = command_runner(
                    f"/opt/cellframe-node/bin/cellframe-node-cli {command}",
                    timeout=timeout, method='poller'
                )
            if exit_code == 0:
                if split_lines:
                    return [line.strip() for line in output.splitlines() if line.strip()]
                return output.strip() if output else True
            elif exit_code == -254:
                logger.warning(f"{command} timed out.")
                return None
            else:
                logger.warning(f"{command} failed, return code {exit_code}")
                return False
        except Exception as e:
            logger.error(f"Error while running {command}: {e}", exc_info=True)
        return None

    def get_current_script_path(self):
        return os.path.dirname(os.path.abspath(__file__))

    def generate_random_token(self, length=Config.ACCESS_TOKEN_LENGTH):
        if length > 64:
            logger.warning("Token length too long, setting to 64.")
            length = 64
        elif length < 16:
            logger.warning("Token length too short, setting to 16.")
            length = 16
        token_file = os.path.join(self._current_script_path, "token.txt")
        token = None
        if os.path.isfile(token_file):
            with open(token_file, "r") as f:
                token = f.read().strip()
                if token:
                    logger.debug(f"Using existing token from file! Length: {len(token)}")
                    return token
        token = secrets.token_urlsafe(length)
        logger.debug(f"Generated new access token! Length: {length}")
        with open(token_file, "w") as f:
            f.write(token)
        return token

    def get_latest_node_version(self):
        try:
            logger.debug("Fetching latest node version...")
            response = requests.get("https://pub.cellframe.net/linux/cellframe-node/master/?C=M&O=D", timeout=5)
            if response.status_code == 200:
                matches = re.findall(r"(\d\.\d\-\d+)", response.text)
                if matches:
                    versions = [match.replace("-", ".") for match in matches]
                    logger.debug(f"Found versions: {versions}")
                    latest_version = max(versions, key=version.parse)
                    logger.debug(f"Latest node version: {latest_version}")
                    return latest_version
                return None
            logger.warning(f"Error fetching latest version, status code: {response.status_code}")
            return None
        except Exception:
            logger.error("An error occurred while fetching the latest node version.", exc_info=True)
            return None

    def format_uptime(self, seconds):
            try:
                days, remainder = divmod(seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                if days > 0:
                    return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
                return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            except Exception as e:
                logger.error(f"Error formatting uptime: {e}", exc_info=True)
                return seconds

    def save_json_to_file(self, data, filename):
        try:
            with open(os.path.join(self._current_script_path, filename), 'w') as f:
                json.dump(data, f, indent=4)
            logger.debug(f"Data successfully saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}", exc_info=True)

    def load_json_from_file(self, filename):
        try:
            with open(os.path.join(self._current_script_path, filename), 'r') as f:
                data = json.load(f)
            logger.debug(f"Data successfully loaded from {filename}")
            return data
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {e}", exc_info=True)
            return None

    def now_iso(self):
        return datetime.now(timezone.utc).isoformat()

    def rfc2822_str_to_iso(self, ts_str):
        try:
            dt = datetime.strptime(ts_str, '%a, %d %b %Y %H:%M:%S %z')
            return dt.astimezone(timezone.utc).isoformat()
        except Exception as e:
            logger.error(f"Error converting {ts_str} to ISO format: {e}", exc_info=True)
            return ts_str

    def current_time_in_format(self, fmt="%Y%m%d"):
        return datetime.now().strftime(fmt)

utils = Utils()
