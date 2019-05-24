import json, socket
import logging
from logging import LogRecord
from logging.handlers import SysLogHandler


class Log:

    def __init__(self, name):
        """Initializs a Syslog logger with the specified name.
        
        Arguments:
            name {str} -- The name of the logger.
        """
        
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.handlers = []
        self.logger.setLevel(logging.DEBUG)

        if "DESKTOP" in socket.gethostname():
            # debug (WSL) environment, use UDP
            self.handler = logging.handlers.SysLogHandler()
        else:
            # prod (box) environment, use socket
            self.handler = logging.handlers.SysLogHandler("/dev/log")
        
        self.logger.addHandler(self.handler)
        self._load_formatters()
    
    def _load_formatters(self):
        """Loads a list of formatters for each log level.
        """

        # Define log level formatters.
        # JSON spaces are stripped to save bandwidth.
        # Add some emojis to flavor it up.
        self.formatters = {
            logging.DEBUG: logging.Formatter(                # ❇️
                "demo-alerts: {                              \
                    \"processName\": \"%(processName)s\",    \
                    \"loggerName\": \"%(name)s\",            \
                    \"pathName\": \"%(pathname)s\",          \
                    \"functionName\": \"%(funcName)s\",      \
                    \"lineNo\": \"%(lineno)d\",              \
                    \"levelName\": \"%(levelname)s\",        \
                    %(message)s                              \
                }".replace(" ", "")
            ),
            logging.INFO: logging.Formatter(                 # ☑️
                "demo-alerts: {                              \
                    \"loggerName\": \"%(name)s\",            \
                    \"levelName\": \"%(levelname)s\",        \
                    %(message)s                              \
                }".replace(" ", "")
            ),
            logging.WARN: logging.Formatter(                 # ⚠️
                "demo-alerts: {                              \
                    \"loggerName\": \"%(name)s\",            \
                    \"functionName\": \"%(funcName)s\",      \
                    \"levelName\": \"%(levelname)s\",        \
                    %(message)s                              \
                }".replace(" ", "")
            ),
            logging.ERROR: logging.Formatter(                # 🛑
                "demo-alerts: {                              \
                    \"loggerName\": \"%(name)s\",            \
                    \"functionName\": \"%(funcName)s\",      \
                    \"lineNo\": \"%(lineno)d\",              \
                    \"levelName\": \"%(levelname)s\",        \
                    %(message)s                              \
                }".replace(" ", "")
            ),
            logging.CRITICAL: logging.Formatter(             # ☠️
                "demo-alerts: {                              \
                    \"processName\": \"%(processName)s\",    \
                    \"loggerName\": \"%(name)s\",            \
                    \"pathName\": \"%(pathname)s\",          \
                    \"functionName\": \"%(funcName)s\",      \
                    \"lineNo\": \"%(lineno)d\",              \
                    \"levelName\": \"%(levelname)s\",        \
                    %(message)s                              \
                }".replace(" ", "")
            )
        }
    
    def emit(self, level, description, extras, **kwargs):
        """Emits a log entry for the specified level and arguments.
        
        Arguments:
            level {int} -- Logging level.
            description {str} -- A brief description of the event.
            extras {dict} -- A dictionary containing request parameters.
        """
        
        # flatten extras, remove brackets to merge them into the formatter
        flat_params = {
            "description": description
        }
        flat_params.update(extras)
        flat_params.update(kwargs)
        message = json.dumps(flat_params)[1:-1]
        self.handler.setFormatter(self.formatters[level])
        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.INFO:
            self.logger.info(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)
