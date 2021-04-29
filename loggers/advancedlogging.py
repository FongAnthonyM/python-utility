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
import classes.dynamicwrapper as dynamicwrapper


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

    # Methods
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


class AdvancedLogger(dynamicwrapper.DynamicWrapper):
    """A logger with expanded functionality that wraps a normal logger.

    Class Attributes:
        _attributes_as_parents (:obj:'list' of :obj:'str'): The list of attribute names that will contain the objects to
            dynamically wrap where the order is descending inheritance. In this case a logger will be dynamically
            wrapped.
        default_levels (dict): The default logging levels with their names mapped to their numerical values.

    Attributes:
        name (str): The name of this logger.
        level (int): The logging level of this logger.
        parent (str): The parent logger of this logger.
        propagate (bool): Determines if a log will be sent to the parent logger.
        handlers (list): The handlers for this logger.
        disabled (bool): Determines if this logger will log.

        allow_append (bool): Allows an additional message to be appended to all logs.
        levels (dict): The logging levels with their names mapped to their numerical values.
        module_of_class (str): The name of module the class originates from.
        module_of_object (str): The name of the module this object originates from.
        append_message (str): A message to append to all logs.

    Args:
        obj: The logger that this object will wrap or the name of the logger to create.
        module_of_class (str, optional): The name of module the class originates from.
        init (bool, optional): Determines if this object should be initialized.
    """
    _attributes_as_parents = ["_logger"]
    default_levels = {"DEBUG": logging.DEBUG,
                      "INFO": logging.INFO,
                      "WARNING": logging.WARNING,
                      "ERROR": logging.ERROR,
                      "CRITICAL": logging.CRITICAL}

    @classmethod
    def from_config(cls, name, fname, defaults=None, disable_existing_loggers=True, **kwargs):
        """Loads the logger's configuration from a file.

        Args:
            name (str): The name of the logger.
            fname (str): The file path of the config file.
            defaults: Additional configurations to set.
            disable_existing_loggers (bool): Disables current active loggers.
            **kwargs: Passes addition keyword arguments to AdvancedLogger initialization.

        Returns:
            AdvancedLogger: A logger with the loaded configurations.
        """
        logging.config.fileConfig(fname, defaults, disable_existing_loggers)
        return cls(name, **kwargs)

    # Construction/Destruction
    def __init__(self, obj=None, module_of_class="(Not Given)", init=True):
        self._logger = None

        self.allow_append = False
        self.levels = self.default_levels.copy()
        self.module_of_class = module_of_class
        self.module_of_object = "(Not Given)"
        self.append_message = ""

        if init:
            self.construct(obj=obj)

    @property
    def name_parent(self):
        """str: The names encapsulating parents of this logger."""
        return self.name.rsplit('.', 1)[0]

    @property
    def name_stem(self):
        """str: The names encapsulating parents of this logger."""
        return self.name.rsplit('.', 1)[-1]

    # Pickling
    def __getstate__(self):
        """Creates a dictionary of attributes which can be used to rebuild this object

        Returns:
            dict: A dictionary of this object's attributes.
        """
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
        """Builds this object based on a dictionary of corresponding attributes.

        Args:
            in_dict (dict): The attributes to build this object from.
        """
        in_dict["_logger"].disabled = in_dict.pop("disabled")
        in_dict["_logger"].setLevel(in_dict.pop("level"))
        in_dict["_logger"].propagate = in_dict.pop("propagate")
        in_dict["_logger"].filters = in_dict.pop("filters")
        in_dict["_logger"].handlers = _rebuild_handlers(in_dict.pop("handlers"))
        self.__dict__ = in_dict

    # Methods
    # Constructors/Destructors
    def construct(self, obj=None):
        """Constructs this object.

        Args:
            obj: The logger that this object will wrap or the name of the logger to create.
        """
        if isinstance(obj, logging.Logger):
            self._logger = obj
        else:
            self._logger = logging.getLogger(obj)

    # Levels Methods
    def get_level(self, name):
        """Gets the level value based on the name within the levels dictionary.

        Args:
            name (str): The name of the level to get the value of.

        Returns:
            int: The numerical value of the level.
        """
        return self.levels[name]

    # Base Logger Editing
    def set_base_logger(self, logger):
        """Set the logger which this object wraps.

        Args:
            logger (:obj:`Logger`, optional): The logger that this object will wrap.
        """
        self._logger = logger

    def fileConfig(self, name, fname, defaults=None, disable_existing_loggers=True):
        """Set the logger's configuration base on a file

        Args:
            name (str): The name of the logger.
            fname (str): The file path of the config file.
            defaults: Additional configurations to set.
            disable_existing_loggers (bool): Disables current active loggers.
        """
        logging.config.fileConfig(fname, defaults, disable_existing_loggers)
        self._logger = logging.getLogger(name)

    def copy_logger_attributes(self, logger):
        """Copies this loggers attributes to another logger.

        Args:
            logger: The logger to copy this loggers attributes to.

        Returns:
            logger: The logger which the attributes were copied to.
        """
        logger.propagate = self.propagate
        logger.setLevel(self.getEffectiveLevel())
        for filter_ in self.filters:
            logger.addFilter(filter_)
        for handler in self.handlers:
            logger.addHandler(handler)
        return logger

    def getChild(self, name, **kwargs):
        """Create a child logger of this logger which will be an AdvancedLogger or one its subclasses.

        Args:
            name: The name of the new logger.
            **kwargs: The other key word arguments used to make a new logger.
        """
        new_logger = self._logger.getChild(name)
        return type(self)(new_logger, **kwargs)

    def setParent(self, parent):
        """Change this logger to be a child under another logger.

        Args:
            parent: The logger to become a child under.
        """
        new_logger = parent.getChild(self.name_stem)
        if isinstance(new_logger, AdvancedLogger):
            new_logger = new_logger._logger
        self.copy_logger_attributes(new_logger)
        self._logger = new_logger

    # Defaults
    def append_module_info(self):
        """Sets the append message to bet the module information"""
        self.append_message = "Class' Module: %s Object Module: %s " % (self.module_of_class, self.module_of_object)
        self.allow_append = True

    def add_default_stream_handler(self, stream=None, level="DEBUG"):
        """Adds a stream handler with Debug level output and a formatter that millisecond precise time.

        Args:
            stream: The stream to send the logs to.
            level (str or int, optional): The level which the logger will start logging.
        """
        if isinstance(level, str):
            level = self.get_level(level)
        handler = logging.StreamHandler(stream=stream)
        handler.setLevel(level)
        formatter = PreciseFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.addHandler(handler)

    def add_default_file_handler(self, filename, mode='a', encoding=None, delay=False, level="DEBUG"):
        """Adds a file handler with Debug level output and a formatter that millisecond precise time.

        Args:
            filename: The path to the output file for the log.
            mode (str): The file mode to open the file with.
            encoding: The type of encoding to use.
            delay (bool): Add a delay to the logging.
            level (str or int, optional): The level which the logger will start logging.
        """
        if isinstance(level, str):
            level = self.get_level(level)
        handler = logging.FileHandler(filename, mode, encoding, delay)
        handler.setLevel(level)
        formatter = PreciseFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.addHandler(handler)

    # Override Logger Methods
    def log(self, level, msg, *args, append=None, **kwargs):
        """Creates a log entry based on provided level.

        Args:
            level (str or int, optional): The level to create log entry for.
            msg (str): The message to add to the log.
            *args: The arguments for the original log method.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if isinstance(level, str):
            level = self.get_level(level)
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg, *args, append=None, **kwargs):
        """Creates a debug log.

        Args:
            msg (str): The message to add to the log.
            *args: The arguments for the original log method.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, append=None, **kwargs):
        """Creates an info log.

        Args:
            msg (str): The message to add to the log.
            *args: The arguments for the original log method.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, append=None, **kwargs):
        """Creates a warning log.

        Args:
            msg (str): The message to add to the log.
            *args: The arguments for the original log method.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, append=None, **kwargs):
        """Creates an error log.

        Args:
            msg (str): The message to add to the log.
            *args: The arguments for the original log method.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, append=None, **kwargs):
        """Creates a critical log.

        Args:
            msg (str): The message to add to the log.
            *args: The arguments for the original log method.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, append=None, **kwargs):
        """Creates an exception log.

        Args:
            msg (str): The message to add to the log.
            *args: The arguments for the original log method.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if append or (append is None and self.allow_append):
            msg = self.append_message + msg
        self._logger.exception(msg, *args, **kwargs)

    # New Logger Methods
    def trace_log(self, class_, func, msg, *args, name="", level="DEBUG", append=None, **kwargs):
        """The creates a log with traceback formatting.

        Args:
            class_ (str): The name of class this log is being made from.
            func (str): The name of function/method this log is being made from.
            msg (str): The name of class this log is being made from.
            *args: The arguments for the original log method.
            name (str, optional): The an additional identifier that can be used to trace this log.
            level (str or int, optional): The level to create log entry for.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        if isinstance(level, str):
            level = self.get_level(level)
        trace_msg = f"{class_}({name}) -> {func}: {msg}"
        self.log(level, trace_msg, *args, append=append, **kwargs)


# Todo: Add Performance Testing (logging?)
class PerformanceLogger(AdvancedLogger):
    default_timer = time.perf_counter

    # Methods
    # Construction/Destruction
    def __init__(self, obj=None, timer=None, module_of_class="(Not Given)", init=True):
        super().__init__(obj=obj, module_of_class=module_of_class, init=False)

        self.timer = self.default_timer
        self.marks = {}
        self.pairs = {}

        if init:
            self.construct(timer=timer, obj=obj)

    def construct(self, obj=None, timer=None):
        super().construct(obj=obj)
        if timer is not None:
            self.timer = timer

    # Time Tacking
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

    # Logging
    def log_pair_average_difference(self, type_, *args, append=None, level="DEBUG", **kwargs):
        if isinstance(level, str):
            level = self.get_level(level)
        mean, std = self.pair_average_difference(type_)
        msg = f"{type_} had a difference of {mean} ± {std}."
        self.log(level, msg, *args, append=append, **kwargs)


class ObjectWithLogging(abc.ABC):
    """Class that has inbuilt logging as an option.

    Loggers can be defined on the class level or object level and be shared to other namespaces. Class loggers can be
    defined in the class_loggers attribute, additionally class loggers can be defined in the build_class_loggers class
    method. These class loggers are present in all objects of this class, so any object can use these loggers which
    is good for seeing what all objects of a class are doing. Object loggers are defined in the build_loggers method.
    Any loggers added here are only available to the object executing this method. This is useful for creating a private
    logger exclusive to a specific object.

    Class Attributes:
        class_loggers (dict): The default loggers to include in every object of this class.

    Attributes:
        loggers (dict): A collection of loggers used by this object. The keys are the names of the different loggers.
    """
    class_loggers = {}

    # Class Methods
    @classmethod
    def build_class_loggers(cls):
        """Setup class loggers here"""
        pass

    # Construction/Destruction
    def __init__(self):
        self.loggers = self.class_loggers.copy()

    # Methods
    # Logging
    def build_loggers(self):
        """Setup object loggers here"""
        pass

    def update_loggers(self, loggers=None):
        """Updates the loggers to add more from either a dictionary or the class loggers.

        Args:
            loggers (dict, optional): The dictionary of loggers to add to this object. If None then updates from class.

        Returns:
            dict: This object's loggers
        """
        if loggers is None:
            loggers = self.class_loggers
        self.loggers.update(loggers)
        return self.loggers

    def trace_log(self, logger, func, msg, *args, name="", level="DEBUG", append=None, **kwargs):
        """Creates a trace log for a given logger.

        Args:
            logger (str): The name of logger to log to.
            func (str): The name of function/method this log is being made from.
            msg (str): The name of class this log is being made from.
            *args: The arguments for the original log method.
            name (str, optional): The an additional identifier that can be used to trace this log.
            level (str or int, optional): The level to create log entry for.
            append (bool, optional): Determines if append message should be added. Defaults to attribute if left None.
            **kwargs: The key word arguments for the original log method.
        """
        self.loggers[logger].trace_log(type(self), func, msg, *args, name=name, level=level, append=append, **kwargs)


# Functions #
def _rebuild_handlers(handlers):
    """Creates new handlers from a list of handlers."""
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
    # Example
    # Define Classes
    class Example(ObjectWithLogging):
        class_loggers = {"example_root": AdvancedLogger("example_root")}

        # Class Methods
        @classmethod
        def build_class_loggers(cls):
            """Setup class loggers here"""
            cls.class_loggers["example_root"].setLevel("DEBUG")
            cls.class_loggers["example_root"].add_default_stream_handler()
            everyone_logger = AdvancedLogger("everyone")
            everyone_logger.add_default_file_handler("example_everyone.log")
            everyone_logger.setLevel("DEBUG")
            cls.class_loggers["everyone"] = everyone_logger

        # Construction/Destruction
        def __init__(self, name, a, b, init=True):
            super().__init__()
            self.name = ""
            self.a = 0
            self.b = 0

            if init:
                self.construct(name, a, b)

        # Methods
        # Construction/Destruction
        def construct(self, name, a, b):
            self.name = name
            self.a = a
            self.b = b

            self.build_loggers()

        # Loggers
        def build_loggers(self):
            """Setup object loggers here"""
            my_logger = self.class_loggers["everyone"].getChild(self.name)
            my_logger.add_default_file_handler(f"example_{self.name}.log")
            my_logger.add_default_stream_handler()
            my_logger.setLevel("DEBUG")
            my_logger.propagate = True
            self.loggers["my_logger"] = my_logger

        # Other Methods
        def add(self, x):
            self.a = self.a + x
            self.trace_log("my_logger", "add", f"some adding was done {self.a}", name=self.name)

        def subtract(self, x):
            self.a = self.a - x
            self.loggers["my_logger"].info("subtraction was done, but no traceback is hard")

        def divide(self, x):
            if x == 0:
                self.trace_log("my_logger", "divide", f"ZERO DIVISION WAS ATTEMPTED", name=self.name, level="CRITICAL")
            else:
                self. a = self.a / x
                self.loggers["example_root"].info("some division was done in an object somewhere")


    # Main Code
    Example.build_class_loggers()

    thing1 = Example("thing1", 1, 2)
    thing2 = Example("thing2", 3, 4)

    thing1.add(10)
    thing1.subtract(2)
    thing1.divide(0)

    thing2.add(230)
    thing2.divide(1)
