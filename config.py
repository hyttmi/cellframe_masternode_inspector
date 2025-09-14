import DAP

def get_config_value(section, key, default=None):
    try:
        return DAP.configGetItem(section, key)
    except Exception:
        return default

class Config:
    ACCESS_TOKEN_LENGTH = int(get_config_value("mncommander", "access_token_length", 64))
    DAYS_CUTOFF = int(get_config_value("mncommander", "days_cutoff", 90)) # Days
    CACHE_REFRESH_INTERVAL = int(get_config_value("mncommander", "cache_refresh_interval", 10) * 60)
    GZIP_RESPONSES = bool(get_config_value("mncommander", "gzip_responses", False))
    DEBUG = bool(get_config_value("mncommander", "debug", False))
    PLUGIN_NAME = str("Cellframe Masternode Commander")
    PLUGIN_URL = str(get_config_value("mncommander", "plugin_url", "mncommander"))
