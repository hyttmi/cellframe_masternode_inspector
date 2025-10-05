from utils import utils
import os, json, time
from packaging import version
from logconfig import logger
from system_requests import system_requests

class Updater:
    def __init__(self):
        self._current_plugin_version = self.get_current_plugin_version()
        self._update_interval = 3600
        self._update_available = False
        self._latest_plugin_version = None

    def run(self):
        while True:
            latest_version, tarball_url = self.get_latest_plugin_version_from_github()
            if latest_version and self.compare_versions(self._current_plugin_version, latest_version):
                logger.info(
                    f"New plugin version available: {latest_version}. "
                    f"Current version: {self._current_plugin_version}"
                )
                self._update_available = True
                self._latest_plugin_version = latest_version
                self._tarball_url = tarball_url
                self.download_and_update(tarball_url)
                break
            else:
                logger.info("Plugin is up to date.")
            time.sleep(self._update_interval)

    def download_and_update(self, tarball_url):
        import tempfile
        import tarfile
        import shutil
        import requests

        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix='plugin_update_')
            tarball_path = os.path.join(temp_dir, 'update.tar.gz')

            logger.info(f"Downloading update from {tarball_url}")
            response = requests.get(tarball_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(tarball_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Extracting tarball to {temp_dir}")
            with tarfile.open(tarball_path, 'r:gz') as tar:
                tar.extractall(path=temp_dir)

            extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if not extracted_dirs:
                raise Exception("No directory found in extracted tarball")

            source_dir = os.path.join(temp_dir, extracted_dirs[0])
            dest_dir = utils.get_current_script_path()

            logger.info(f"Copying files from {source_dir} to {dest_dir}")
            for item in os.listdir(source_dir):
                source_item = os.path.join(source_dir, item)
                dest_item = os.path.join(dest_dir, item)

                if os.path.isdir(source_item):
                    if os.path.exists(dest_item):
                        shutil.rmtree(dest_item)
                    shutil.copytree(source_item, dest_item)
                else:
                    shutil.copy2(source_item, dest_item)

            logger.info("Update completed successfully")
            logger.info("Installing pip dependencies...")
            pip_install = utils.cli_command(f"install -r {utils.get_current_script_path()}/requirements.txt", timeout=300, is_pip_command=True)
            logger.debug(f"Pip install output: {pip_install}")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                system_requests.restart_node()
        except Exception as e:
            logger.error(f"Error during update: {e}", exc_info=True)
            return False

    def get_current_plugin_version(self):
        try:
            with open(os.path.join(utils.get_current_script_path(), 'manifest.json'), 'r') as f:
                data = json.load(f)
                return data.get('version') # Get the version from manifest.json
        except Exception as e:
            logger.error(f"Error reading current plugin version: {e}", exc_info=True)
            return None

    def get_latest_plugin_version_from_github(self):
        try:
            import requests
            response = requests.get("https://api.github.com/repos/hyttmi/cellframe-masternode-inspector/releases/latest")
            if response.status_code == 200:
                data = response.json()
                return data.get('tag_name'), data.get("tarball_url")
            else:
                logger.error(f"Failed to fetch latest version from GitHub: {response.status_code}")
                return None, None
        except Exception as e:
            logger.error(f"An error occurred while fetching the latest node version: {e}", exc_info=True)
        return None, None


    def compare_versions(self, current_version, latest_version):
        return version.parse(current_version) < version.parse(latest_version)

updater = Updater()