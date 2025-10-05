from sys import platform
from utils import utils
from logconfig import logger
import requests, psutil, socket, time, os

class SystemRequests:
    def __init__(self):
        logger.info("Initializing SystemRequests...")
        self._node_pid = self.get_node_pid()
        self._hostname = self.get_system_hostname()
        self._is_running_as_service = self.is_running_as_service()
        self._current_node_version = self.get_node_version()
        # These can be initialized here, they are static after all
        logger.info(f"Node PID: {self._node_pid}")
        logger.info(f"Hostname: {self._hostname}")
        logger.info(f"Running as service: {self._is_running_as_service}")
        logger.info(f"Current node version: {self._current_node_version}")

    def get_external_ip(self):
        try:
            logger.debug("Fetching external IP...")
            services = [
                "https://api.ipify.org",
                "https://ipv4.icanhazip.com",
                "https://v4.ident.me" # these all should provide ipv4 only address
            ]
            for service in services:
                try:
                    response = requests.get(service, timeout=3, stream=True)
                    logger.debug(f"Response from {service}: {response.text.strip()}")
                    if response.status_code == 200:
                        return response.text.strip()
                    else:
                        logger.error(f"Error fetching IP address from {response.url}, status code: {response.status_code}")
                except Exception as e:
                    logger.error(f"Exception while fetching IP from {service}: {e}", exc_info=True)
            logger.error("All external IP services failed.")
            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching external IP: {e}", exc_info=True)
            return None

    def get_node_pid(self):
        try:
            logger.debug("Fetching node PID...")
            for proc in psutil.process_iter(attrs=["pid", "name"]):
                name = proc.info.get("name")
                if name == "cellframe-node":
                    pid = proc.info['pid']
                    logger.debug(f"PID for Cellframe node is {pid}")
                    return pid
            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching node PID: {e}", exc_info=True)
            return None

    def get_system_hostname(self):
        try:
            logger.debug("Fetching hostname...")
            hostname = socket.gethostname()
            if hostname:
                logger.debug(f"Hostname is {hostname}")
                return hostname
            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching hostname: {e}", exc_info=True)
            return None

    def get_node_version(self):
        try:
            logger.debug("Fetching node version...")
            response = utils.send_request("version", None, None, use_unix=True)
            if response and "result" in response and response['result']:
                version = response['result'][0]['status'].strip().split()[-1].replace("-", ".")
                logger.debug(f"Node version is {version}")

                return version
            logger.error("Error fetching node version")
            return None
        except Exception as e:
            logger.error(f"An error occurred while fetching current node version: {e}", exc_info=True)
            return None

    def get_node_cpu_usage(self):
        try:
            PID = self._node_pid
            if not PID:
                return None
            logger.debug("Fetching node CPU usage...")
            process = psutil.Process(PID)
            cpu_usage = process.cpu_percent(interval=1) / psutil.cpu_count()
            logger.debug(f"Node CPU usage is {cpu_usage}%")
            return cpu_usage
        except Exception as e:
            logger.error(f"An error occurred while fetching node CPU usage: {e}", exc_info=True)
            return None

    def get_node_memory_usage(self):
        try:
            PID = self._node_pid
            if not PID:
                return None
            logger.debug("Fetching node memory usage...")
            process = psutil.Process(PID)
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024
            logger.debug(f"Node memory usage is {round(memory_usage_mb, 2)}MB")
            return round(memory_usage_mb, 2)
        except Exception as e:
            logger.error(f"An error occurred while fetching node memory usage: {e}", exc_info=True)
            return None

    def get_node_uptime(self):
        try:
            PID = self._node_pid
            if not PID:
                return None
            logger.debug("Fetching node uptime...")
            process = psutil.Process(PID)
            uptime_seconds = time.time() - process.create_time()
            logger.debug(f"Node uptime (seconds): {uptime_seconds}")
            return uptime_seconds
        except Exception as e:
            logger.error(f"An error occurred while fetching node uptime: {e}", exc_info=True)
            return None

    def get_system_uptime(self):
        try:
            logger.debug("Fetching system uptime...")
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            logger.debug(f"System uptime (seconds): {uptime_seconds}")
            return uptime_seconds
        except Exception as e:
            logger.error(f"An error occurred while fetching system uptime: {e}", exc_info=True)
            return None

    def is_running_as_service(self):
        try:
            logger.debug("Checking if cellframe-node is running as service...")
            if os.environ.get("INVOCATION_ID"):
                logger.debug("cellframe-node is running as service, INVOCATION_ID found.")
                return True
            logger.debug("cellframe-node is not running as service, INVOCATION_ID not found.")
            return False
        except Exception as e:
            logger.error(f"An error occurred while checking service status: {e}", exc_info=True)
            return False

    def restart_node(self):
        try:
            logger.debug("Restarting cellframe-node...")
            utils.cli_command("exit", timeout=5) # this should work regardless of platform
        except Exception as e:
            logger.error(f"An error occurred while restarting cellframe-node: {e}", exc_info=True)

system_requests = SystemRequests()