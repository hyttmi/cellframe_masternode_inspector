try:
    import orjson
    loads = orjson.loads
    def dumps(obj):
        return orjson.dumps(obj).decode()
    def dumps_bytes(obj):
        return orjson.dumps(obj)
except ImportError:
    import json
    loads = json.loads
    def dumps(obj):
        return json.dumps(obj, separators=(",", ":"))
    def dumps_bytes(obj):
        return json.dumps(obj, separators=(",", ":")).encode()
