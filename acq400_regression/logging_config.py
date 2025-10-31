"""
Logging
"""

import sys
import logging
import os


class ColoredFormatter(logging.Formatter):
    formats = {
        logging.DEBUG: {'format': '[%(levelname)s]: %(message)s', 'color': "\x1b[37m"},
        logging.INFO: {'format': '%(message)s', 'color': "\x1b[37m"},
        logging.WARNING: {'format': '[%(levelname)s]: %(message)s', 'color': "\x1b[33;20m"},
        logging.ERROR: {'format': '[%(levelname)s]: %(message)s', 'color': "\x1b[31;20m"},
        logging.CRITICAL: {'format': '[%(levelname)s]: %(message)s', 'color': "\x1b[31;1m"},
    }
    RESET = '\x1b[0m'
    
    def __init__(self, use_color=True):
        super().__init__()
        self.use_color = use_color
        #TODO fix incorrect colors of warning and error
        self.add_new_level('passed', 21, color="\x1b[92m")
        self.add_new_level('failed', 22, color="\x1b[31;20m")
    
    def add_new_level(self, levelname, levelno, color=None, format=None):
        """Add a new log level with optional color and format."""
        setattr(logging, levelname.upper(), levelno)

        logging.addLevelName(levelno, levelname.upper())

        default_format = self.formats.get(logging.INFO, {'format': '%(message)s'})['format']
        fmt_entry = {'format': format if format else default_format}
        if color:
            fmt_entry['color'] = color
        self.formats[levelno] = fmt_entry

        method_name = levelname.lower()
        def log_method(self_logger, message, *args, **kwargs):
            if self_logger.isEnabledFor(levelno):
                self_logger._log(levelno, message, args, **kwargs)

        setattr(logging.Logger, method_name, log_method)

        if not hasattr(logging, method_name):
            def module_log(message, *args, **kwargs):
                logging.getLogger().log(levelno, message, *args, **kwargs)
            setattr(logging, method_name, module_log)

    def format(self, record):
        level_config = self.formats.get(record.levelno, self.formats[logging.INFO])
        fmt = level_config['format']

        temp_formatter = logging.Formatter(fmt)
        formatted = temp_formatter.format(record)

        if self.use_color and 'color' in level_config:
            return f"{level_config['color']}{formatted}{self.RESET}"

        return formatted

def setup_logging(verbose=False):
    """Set up logging configuration with file and colored terminal output."""
    level = logging.DEBUG if verbose else logging.INFO
    
    log_file = os.path.join(f'acq400_regression.log')
    
    file_fmt = "[%(asctime)s %(levelname)s]: %(message)s"
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    root_logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(file_fmt, datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logging.debug(f"Started logging to: {log_file}")
