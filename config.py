import DAP

def get_config_value(section, key, default=None):
    try:
        return DAP.configGetItem(section, key)
    except Exception:
        return default

class Config:
    MIN_NODE_VERSION = "5.5.0"
    SUPPORTED_PLATFORMS = ["Linux"]
    AUTOUPDATE = bool(get_config_value("mninspector", "autoupdate", True))
    ACCESS_TOKEN_ENTROPY = int(get_config_value("mninspector", "access_token_entropy", 64))
    BLOCK_COUNT_THRESHOLD = int(get_config_value("mninspector", "block_count_threshold", 30))
    DAYS_CUTOFF = int(get_config_value("mninspector", "days_cutoff", 20)) # Days
    DEBUG = bool(get_config_value("mninspector", "debug", False))
    COMPRESS_RESPONSES = bool(get_config_value("mninspector", "compress_responses", True))
    PLUGIN_NAME = str("Cellframe Masternode Inspector")
    PLUGIN_URL = str(get_config_value("mninspector", "plugin_url", "mninspector"))
