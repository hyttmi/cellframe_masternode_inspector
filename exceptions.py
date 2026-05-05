class CMIException(Exception):
    def __init__(self, message):
        super().__init__(message)

class UnsupportedPlatformError(CMIException):
    pass

class UnsupportedNodeVersionError(CMIException):
    pass

class ConfigurationError(CMIException):
    pass

class UpdateError(CMIException):
    pass

class RequestError(CMIException):
    pass
