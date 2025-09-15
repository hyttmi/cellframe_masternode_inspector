import DAP

def get_config_value(section, key, default=None):
    try:
        return DAP.configGetItem(section, key)
    except Exception:
        return default

class Config:
    ACCESS_TOKEN_ENTROPY = int(get_config_value("mninspector", "access_token_entropy", 64))
    DAYS_CUTOFF = int(get_config_value("mninspector", "days_cutoff", 90)) # Days
    CACHE_REFRESH_INTERVAL = int(get_config_value("mninspector", "cache_refresh_interval", 10) * 60)
    GZIP_RESPONSES = bool(get_config_value("mninspector", "gzip_responses", False))
    DEBUG = bool(get_config_value("mninspector", "debug", False))
    PLUGIN_NAME = str("Cellframe Masternode Inspector")
    PLUGIN_URL = str(get_config_value("mninspector", "plugin_url", "mninspector"))
    SUPPORTED_NODE_VERSIONS = ["5.4.25","5.4.26","5.4.27", "5.4.28", "5.4.29"]
