#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" advancedlogging.py

"""
__author__ = "Anthony Fong"
__copyright__ = "Copyright 2020, Anthony Fong"
__credits__ = ["Anthony Fong"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Anthony Fong"
__email__ = ""
__status__ = "Prototype"

# Default Libraries #
import abc
import copy
import datetime
import logging
import logging.config
import logging.handlers
import statistics
import time
import warnings

# Downloaded Libraries #

# Local Libraries #
import classes.dynamicinheritor as dynamicinheritor


# Definitions #
# Classes #
class PreciseFormatter(logging.Formatter):
    """A logging Formatter that formats the time to the microsecond when a log occurs.

    Class Attributes:
        converter (:func:): The function the will convert the record to a datetime object.
        default_msec_format (str): The default string representation to use for milliseconds in a log.
    """
    converter = datetime.datetime.fromtimestamp
    default_msec_format = "%s.%06d"

    def formatTime(self, record, datefmt=None):
        """Return the creation time of the specified LogRecord as formatted text in milliseconds.

        Args:
            record: The log record.
            datefmt (str, optional): The format to use for milliseconds in the log.

        Returns:
            str: The string representation of milliseconds.
        """

        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime(self.default_time_format)
            s = self.default_msec_format % (t, ct.microsecond)
        return s


class AdvancedLogger(dynamicinheritor.DynamicInheritor):
    """A logger with expanded functionality that wraps a normal logger.

    Class Attributes:
        _attributes_as_parents (:obj:'list' of :obj:'str'): The list of attribute names that will contain the objects to
            dynamically inherit from where the order is descending inheritance. In this case a logger will be
            dynamically inherited.
    """
    _attributes_as_parents = ["_logger"]

    @classmethod
    def from_config(cls, name, fname, defaults=None, disable_existing_loggers=True, **kwargs):
        """Loads the logger's configuration from a file.

        Args:
            name (str): The name of the logger.
            fname (str): The file path of the config file.
            defaults (): Additional configurations to set.
            disable_existing_loggers (bool): Disables current active loggers.
            **kwargs: Passes addition keyword arguments to AdvancedLogger initialization.

        Returns:
            AdvancedLogger: A logger with the loaded configurations.
        """
        logging.config.fileConfig(fname, defaults, disable_existing_loggers)
        return cls(name, **kwargs)

    # Construction/Destruction
    def __init__(self, obj=None, module_of_class="(Not Given)", init=True):
        self.allow_append = False

        self._logger = None
        self.module_of_class = module_of_class
        self.module_of_object = "(Not Given)"
        self.append_message = ""

        if init:
            self.construct(obj=obj)

    @property
    def name_parent(self):
        return self.name.rsplit('.', 1)[0]

    @property
    def name_stem(self):
        return self.name.rsplit('.', 1)[0]

    # Pickling
    def __getstate__(self):
        out_dict = self.__dict__.copy()
        out_dict["disabled"] = self.disabled
        out_dict["level"] = self.getEffectiveLevel()
        out_dict["propagate"] = self.propagate
        out_dict["filters"] = copy.deepcopy(self.filters)
        out_dict["handlers"] = []
        for handler in self.handlers:
            lock = handler.__dict__.pop("lock")
            stream = handler.__dict__.pop("stream")
            out_dict["handlers"].append(copy.deepcopy(handler))
            handler.__dict__["lock"] = lock
            handler.__dict__["stream"] = stream
        return out_dict

    def __setstate__(self, in_dict):
        in_dict["_logger"].disabled = in_dict.pop("disabled")
        in_dict["_logger"].setLevel(in_dict.pop("level"))
        in_dict["_logger"].propagate = in_dict.pop("propagate")
        in_dict["_logger"].filters = in_dict.pop("filters")
        in_dict["_logger"].handlers = _rebuild_handlers(in_dict.pop("handlers"))
        self.__dict__ = in_dict

    # Constructors/Destructors
    def construct(self, obj=None):
        if isinstance(obj, logging.Logger):
            self._logger = obj
        else:
            self._logger = logging.getLogger(obj)

    # Base Logger Editing
    def set_base_logger(self, logger):
        self._logger = logger

    def fileConfig(self, name, fname, defaults=None, disable_existing_loggers=True):
        logging.config.fileConfig(fname, defaults, disable_existing_loggers)
        self._logger = logging.getLogger(name)

    def copy_logger_attributes(self, logger):
        logger.propagate = self.propagate
        logger.setLevel(self.getEffectiveLevel())
        for filter_ in self.filters:
            logger.addFilter(filter_)
        for handler in self.handlers:
            logger.addHandler(handler)
        return logger

    def setParent(self, parent):
        new_logger = parent.getChild(self.name_stem)
        self.copy_logger_attributes(new_logger)
        self._logger = new_logger

    # Defaults
    def append_module_info(self):
        self.append_message = "Class' Module: %s Object Module: %s " % (self.module_of_class, self.module_of_object)
        self.allow_append = True

    def add_default_stream_handler(self, level=logging.DEBUG):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = PreciseFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.addHandler(handler)

    # Override Logger Methods
    def debug(self, msg, *args, append=None, **kwargs):
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, append=None, **kwargs):
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, append=None, **kwargs):
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, append=None, **kwargs):
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, append=None, **kwargs):
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.critical(msg, *args, **kwargs)

    def log(self, level, msg, *args, append=None, **kwargs):
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.critical(level, msg, *args, **kwargs)

    def exception(self, msg, *args, append=None, **kwargs):
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.exception(msg, *args, **kwargs)


# Todo: Add Performance Testing (logging?)
class PerformanceLogger(AdvancedLogger):
    default_timer = time.perf_counter

    # Construction/Destruction
    def __init__(self, timer=None, obj=None, module_of_class="(Not Given)", init=True):
        super().__init__(obj=obj, module_of_class=module_of_class, init=False)
        self.default_log_level = logging.INFO

        self.timer = self.default_timer
        self.marks = {}
        self.pairs = {}

        if init:
            self.construct(timer=timer, obj=obj)

    def construct(self, timer=None, obj=None):
        super().construct(obj=obj)
        if timer is not None:
            self.timer = timer

    def time_func(self, func, kwargs={}):
        start = self.timer()
        func(**kwargs)
        stop = self.timer()
        return stop - start

    def mark(self, name):
        self.marks[name] = self.timer()

    def mark_difference(self, f_name, s_name):
        return self.marks[f_name] - self.marks[s_name]

    def pair_begin(self, type_, name=None):
        if type_ not in self.pairs:
            self.pairs[type_] = {}
        if name is None:
            name = len(self.pairs[type_])
        self.pairs[type_][name] = {"beginning": self.timer(), "ending": None}

    def pair_end(self, type_, name=None):
        if name is None:
            name = list(self.pairs[type_].keys())[0]
        self.pairs[type_][name]["ending"] = self.timer()

    def pair_difference(self, type_, name=None):
        if name is None:
            name = list(self.pairs[type_].keys())[0]
        pair = self.pairs[type_][name]
        return pair["ending"] - pair["beginning"]

    def pair_average_difference(self, type_):
        differences = []
        for pair in self.pairs[type_].values():
            differences.append(pair["ending"] - pair["beginning"])
        return statistics.mean(differences), statistics.stdev(differences)

    def log_pair_average_difference(self, type_, level=None):
        if level is None:
            level = self.default_log_level
        mean, std = self.pair_average_difference(type_)
        msg = None
        self.log(level, msg)


class ObjectWithLogging(abc.ABC):
    """Class that has inbuilt logging as an option

    Class Attributes:
        class_loggers (dict):
    """
    class_loggers = {}

    def __init__(self):
        self.loggers = self.class_loggers.copy()

    # Logging
    def traceback_formatting(self, func, msg, name=""):
        return "%s(%s) -> %s: %s" % (self.__class__, name, func, msg)


# Functions #
def _rebuild_handlers(handlers):
    new_handlers = []
    for handler in handlers:
        if isinstance(handler, logging.handlers.QueueHandler):
            kwargs = {"queue", handler.queue}
        elif isinstance(handler, logging.handlers.BufferingHandler):
            kwargs = {"capacity": handlers.capacity}
        elif isinstance(handler, logging.handlers.HTTPHandler):
            kwargs = {"host": handler.host, "url": handler.url, "method": handler.method, "secure": handler.secure,
                      "credentials": handler.credentials, "context": handler.context}
        elif isinstance(handler, logging.handlers.NTEventLogHandler):
            kwargs = {"appname": handler.appname, "dllname": handler.dllname, "logtype": handler.logtype}
        elif isinstance(handler, logging.handlers.SMTPHandler):
            kwargs = {"mailhost": handler.mailhost, "fromaddr": handler.fromaddr, "toaddrs": handler.toaddrs,
                      "subject": handler.subject, "credentials": handler.credentials, "secure": handler.secure,
                      "timeout": handler.timeout}
        elif isinstance(handler, logging.handlers.SysLogHandler):
            kwargs = {"address": handler.address, "facility": handler.facility, "socktype": handler.socktype}
        elif isinstance(handler, logging.handlers.SocketHandler):
            kwargs = {"host": handler.host, "port": handler.port}
        elif isinstance(handler, logging.FileHandler):
            kwargs = {"filename": handler.baseFilename, "mode": handler.mode,
                      "encoding": handler.encoding, "delay": handler.delay}
        elif isinstance(handler, logging.StreamHandler):
            kwargs = {}
            warnings.warn("StreamHandler stream cannot be pickled, using default stream (Hint: Define StreamHandler in Process)")
        else:
            warnings.warn()
            continue
        new_handler = type(handler)(**kwargs)
        new_handler.__dict__.update(handler.__dict__)
        new_handlers.append(new_handler)
    return new_handlers


# Main #
if __name__ == "__main__":
    pass
