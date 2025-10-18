import DAP

def get_config_value(section, key, default=None):
    try:
        return DAP.configGetItem(section, key)
    except Exception:
        return default

class Config:
    ACCESS_TOKEN_ENTROPY = int(get_config_value("mninspector", "access_token_entropy", 64))
    AUTOUPDATE = bool(get_config_value("mninspector", "autoupdate", False))
    BLOCK_COUNT_THRESHOLD = int(get_config_value("mninspector", "block_count_threshold", 30))
    FORCE_CACHE_REFRESH_INTERVAL = int(get_config_value("mninspector", "force_cache_refresh_interval", 3600))
    COMPRESS_RESPONSES = bool(get_config_value("mninspector", "compress_responses", True))
    DAYS_CUTOFF = int(get_config_value("mninspector", "days_cutoff", 20)) # Days
    DEBUG = bool(get_config_value("mninspector", "debug", False))
    MIN_NODE_VERSION = "5.5.1"
    PLUGIN_NAME = str("Cellframe Masternode Inspector")
    PLUGIN_URL = str(get_config_value("mninspector", "plugin_url", "mninspector"))
    SUPPORTED_PLATFORMS = ["Linux"]
