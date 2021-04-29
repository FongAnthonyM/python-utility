#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" version.py

Provides version tools to create versioning. The Version class is a dataclass like class which uses the three number
version convention. Subsequent classes use the Version class to do useful version comparisons. The versioning framework
can be used for normal objects, but it is primarily designed around versioning classes. This is useful for creating
classes that have to interface with datastructures that change frequently and support for previous version are needed.
For example, a file type may change how data is stored within it but you might have files of the new and previous
version. In this case an appropriate class which addresses each version can be chosen based on the version of the file.

"""
__author__ = "Anthony Fong"
__copyright__ = "Copyright 2021, Anthony Fong"
__credits__ = ["Anthony Fong"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Anthony Fong"
__email__ = ""
__status__ = "Prototype"

# Default Libraries #
import abc
from abc import abstractmethod
import bisect
import collections

# Downloaded Libraries #

# Local Libraries #


# Definitions #
# Classes #
class VersionType(object):
    """A dataclass like object that contains a str name and associated class for a version.

    Attributes:
        name (str, optional): The string name of this object.
        class_ (:class:, optional): The class of the version.

    Args:
        name (str): The string name of this object.
        class_ (:class:): The class of the version.
    """
    __slots__ = ["name", "class_"]

    # Construction/Destruction
    def __init__(self, name=None, class_=None, init=True):
        self.name = None
        self.class_ = None

        if init:
            self.construct(name=name, class_=class_)

    # Type Conversion
    def __str__(self):
        """Returns the str representation of the version.

        Returns:
            str: A str with the version numbers in order.
        """
        return self.name

    # Comparison
    def __eq__(self, other):
        """Expands on equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is equivalent.
        """
        if isinstance(other, type(self)):
            return other.name == self.name
        if isinstance(other, str):
            return other == self.name
        else:
            return super().__eq__(other)

    def __ne__(self, other):
        """Expands on not equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is not equivalent.
        """
        if isinstance(other, type(self)):
            return other.name != self.name
        if isinstance(other, str):
            return other != self.name
        else:
            return super().__ne__(other)

    # Methods
    def construct(self, name=None, class_=None):
        """Constructs the version type object based on inputs.

        Args:
            name (str, optional): The string name of this object.
            class_ (:class:, optional): The class of the version.
        """
        self.name = name
        self.class_ = class_


class Version(abc.ABC):
    """An abstract class for creating versions which dataclass like classes that stores and handles a versioning.

    Class Attributes:
        version_name (str): The name of the version.

    Attributes:
        version_type (:obj:`VersionType`): The type of version object this object is.

    Args:
        obj (:obj:, optional): An object to derive a version from.
        ver_name (str, optional): The name of the version type being used.
        init (bool, optional): Determines if the object should be initialized.
    """
    default_version_name = "default"

    # Class Methods
    @classmethod
    def cast(cls, other, pass_=False):
        """A cast method that optionally returns the original object rather than raise an error

        Args:
            other (:obj:): An object to convert to this type.
            pass_ (bool, optional): True to return original object rather than raise an error.

        Returns:
            obj: The converted object of this type or the original object.
        """
        try:
            other = cls(other)
        except TypeError as e:
            if not pass_:
                raise e

        return other

    @classmethod
    def create_version_type(cls, name=None):
        """Create the version type of this version class.

        Args:
            name (str): The which this type will referred to.

        Returns:
            :obj:`VersionType`: The version type of this version.
        """
        if name is None:
            name = cls.default_version_name
        return VersionType(name, cls)

    # Construction/Destruction
    @abstractmethod
    def __init__(self, obj=None, ver_name=None, init=True, **kwargs):
        self.version_type = None

        if init:
            self.construct(obj=obj, ver_name=ver_name, **kwargs)

    # Type Conversion
    @abstractmethod
    def __str__(self):
        """Returns the str representation of the version.

        Returns:
            str: A str with the version numbers in order.
        """
        return super().__str__()

    # Comparison
    @abstractmethod
    def __eq__(self, other):
        """Expands on equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is equivalent.
        """
        return super().__ne__(other)

    @abstractmethod
    def __ne__(self, other):
        """Expands on not equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is not equivalent.
        """
        return super().__ne__(other)

    @abstractmethod
    def __lt__(self, other):
        """Creates the less than comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is less than to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, Version):
            return self.tuple() < other.tuple()
        else:
            raise TypeError(f"'>' not supported between instances of '{str(self)}' and '{str(other)}'")

    @abstractmethod
    def __gt__(self, other):
        """Creates the greater than comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is greater than to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, Version):
            return self.tuple() > other.tuple()
        else:
            raise TypeError(f"'>' not supported between instances of '{str(self)}' and '{str(other)}'")

    @abstractmethod
    def __le__(self, other):
        """Creates the less than or equal to comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is less than or equal to to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, Version):
            return self.tuple() <= other.tuple()
        else:
            raise TypeError(f"'<=' not supported between instances of '{str(self)}' and '{str(other)}'")

    @abstractmethod
    def __ge__(self, other):
        """Creates the greater than or equal to comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is greater than or equal to to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, Version):
            return self.tuple() >= other.tuple()
        else:
            raise TypeError(f"'>=' not supported between instances of '{str(self)}' and '{str(other)}'")

    # Methods
    @abstractmethod
    def construct(self, obj=None, ver_name=None, **kwargs):
        """Constructs the version object based on inputs

        Args:
            obj (:obj:, optional): An object to derive a version from.
            ver_name (str, optional): The name of the version type being used.
        """
        self.version_type = self.create_version_type(ver_name)

    @abstractmethod
    def list(self):
        """Returns the list representation of the version.

        Returns:
            :obj:`list` of :obj:`str`: The list representation of the version.
        """
        pass

    @abstractmethod
    def tuple(self):
        """Returns the tuple representation of the version.

        Returns:
            :obj:`tuple` of :obj:`str`: The tuple representation of the version.
        """
        pass

    def str(self):
        """Returns the str representation of the version.

        Returns:
            str: A str with the version numbers in order.
        """
        return str(self)

    def set_version_type(self, name):

        self.version_type = VersionType(name, type(self))


class TriNumberVersion(Version):
    """A dataclass like class that stores and handles a version number.

    Args:
        obj (int, str, :obj:`list`, :obj:`tuple`, optional): An object to derive a version from.
        major (int, optional):The major change number of the version.
        moderate (int, optional): The moderate change number of the version.
        minor (int, optional), optional: The minor change number of the version.

    Attributes:
        major (int): The major change number of the version.
        moderate (int): The moderate change number of the version.
        minor (int): The minor change number of the version.
    """
    default_version_name = "TriNumber"
    __slots__ = ["major", "moderate", "minor"]

    # Construction/Destruction
    def __init__(self, obj=None, major=0, moderate=0, minor=0, init=True, **kwargs):
        self.major = major
        self.moderate = moderate
        self.minor = minor

        if init:
            super().__init__(obj=obj, major=major, moderate=moderate, minor=minor, **kwargs)

    # Type Conversion
    def __str__(self):
        """Returns the str representation of the version.

        Returns:
            str: A str with the version numbers in order.
        """
        return f"{self.major}.{self.moderate}.{self.minor}"

    # Comparison
    def __eq__(self, other):
        """Expands on equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is equivalent.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, type(self)):
            return self.tuple() == other.tuple()
        elif "VERSION" in other.__dict__:
            return self.tuple() == other.VERSION.tuple()  # Todo: Maybe change the order to be cast friendly
        else:
            return super().__eq__(other)

    def __ne__(self, other):
        """Expands on not equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is not equivalent.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, type(self)):
            return self.tuple() != other.tuple()
        elif "VERSION" in other.__dict__:
            return self.tuple() != other.VERSION.tuple()
        else:
            return super().__ne__(other)

    def __lt__(self, other):
        """Creates the less than comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is less than to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, type(self)):
            return self.tuple() < other.tuple()
        elif "VERSION" in other.__dict__:
            return self.tuple() < other.VERSION.tuple()
        else:
            raise TypeError(f"'>' not supported between instances of '{str(self)}' and '{str(other)}'")

    def __gt__(self, other):
        """Creates the greater than comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is greater than to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, type(self)):
            return self.tuple() > other.tuple()
        elif "VERSION" in other.__dict__:
            return self.tuple() > other.VERSION.tuple()
        else:
            raise TypeError(f"'>' not supported between instances of '{str(self)}' and '{str(other)}'")

    def __le__(self, other):
        """Creates the less than or equal to comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is less than or equal to to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, type(self)):
            return self.tuple() <= other.tuple()
        elif "VERSION" in other.__dict__:
            return self.tuple() <= other.VERSION.tuple()
        else:
            raise TypeError(f"'<=' not supported between instances of '{str(self)}' and '{str(other)}'")

    def __ge__(self, other):
        """Creates the greater than or equal to comparison for these objects which includes str, list, and tuple.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if this object is greater than or equal to to the other objects' version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, type(self)):
            return self.tuple() >= other.tuple()
        elif "VERSION" in other.__dict__:
            return self.tuple() >= other.VERSION.tuple()
        else:
            raise TypeError(f"'>=' not supported between instances of '{str(self)}' and '{str(other)}'")

    # Methods
    def construct(self, obj=None, moderate=0, minor=0, major=0, **kwargs):
        """Constructs the version object based on inputs

        Args:
            obj (:obj:, optional): An object to derive a version from.
            major (int, optional):The major change number of the version.
            moderate (int, optional): The moderate change number of the version.
            minor (int, optional), optional: The minor change number of the version.
        """
        if isinstance(obj, str):
            ranks = obj.split('.')
            for i, r in enumerate(ranks):
                ranks[i] = int(r)
            major, moderate, minor = ranks
        elif isinstance(obj, list) or isinstance(obj, tuple):
            major, moderate, minor = obj
        elif isinstance(obj, int):
            major = obj
        elif obj is not None:
            raise TypeError("Can't create {} from {}".format(self, major))

        self.major = major
        self.moderate = moderate
        self.minor = minor

        super().construct(**kwargs)

    def list(self):
        """Returns the list representation of the version.

        Returns:
            :obj:`list` of :obj:`str`: A list with the version numbers in order.
        """
        return [self.major, self.moderate, self.minor]

    def tuple(self):
        """Returns the tuple representation of the version.

        Returns:
            :obj:`tuple` of :obj:`str`: A tuple with the version numbers in order.
        """
        return self.major, self.moderate, self.minor

    def str(self):
        """Returns the str representation of the version.

        Returns:
            str: A str with the version numbers in order.
        """
        return str(self)


class VersionRegistry(collections.UserDict):
    """A dictionary like class that holds versioned objects.

    The keys distinguish different types of objects from one another, so their version are not mixed together. The items
    are lists containing the versioned objects in order by version.
    """

    # Methods
    def get_version(self, type_, key, exact=False):
        """Gets an object from the registry base on the type and version of object.

        Args:
            type_ (str): The type of versioned object to get.
            key (str, list, tuple, :obj:`Version`): The key to search for the versioned object with.
            exact (bool, optional): Determines whether the exact version is need or return the closest version.
        Returns
            obj: The versioned object.

        Raises
            ValueError: If there is no closest version.
        """
        if isinstance(type_, VersionType):
            type_ = type_.name

        versions = self.data[type_]["list"]
        if isinstance(key, str) or isinstance(key, list) or isinstance(key, tuple):
            version_class = self.data[type_]["type"].class_
            key = version_class.cast(key)

        if exact:
            index = versions.index(key)
        else:
            index = bisect.bisect(versions, key)

        if index < 0:
            raise ValueError(f"Version needs to be greater than {str(versions[0])}, {str(key)} is not.")
        else:
            return versions[index-1]

    def get_version_type(self, name):
        """Gets the type object being used as a key.

        Args:
            name (str): The name of the type object.

        Returns:
            :obj:`VersionType`: The type object requested.
        """
        return self.data[name]["type"]

    def add_item(self, item, type_=None):
        """Adds a versioned item into the registry.

        Args
            type_ (str): The type of versioned object to add.
            item (:obj:`Version`): The versioned object to add.
        """
        if isinstance(type_, str):
            name = type_
            type_ = self.data[name]["type"]
        else:
            if type_ is None:
                type_ = item.version_type
            name = type_.name

        if name in self.data:
            bisect.insort(self.data[name]["list"], item)
        else:
            self.data[name] = {"type": type_, "list": [item]}

    def sort(self, type_=None, **kwargs):
        """Sorts the registry.

        Args:
            type_ (str, optional): The type of versioned object to add.
            **kwargs: Args that are passed to the list sort function.
        """
        if type_ is None:
            for versions in self.data.values():
                versions["list"].sort(**kwargs)
        else:
            if isinstance(type_, VersionType):
                type_ = type_.name
            self.data[type_]["list"].sort(**kwargs)


class VersionedMeta(abc.ABCMeta):
    """A Meta Class that can compare the specified version of the classes.

    Class Attributes:
        _VERSION_TYPE (:obj:`VersionType`): The type of version this object will be.
        VERSION (:obj:`Version`): The version of this class as a string.
    """
    _VERSION_TYPE = None
    VERSION = None

    # Methods
    # Comparison
    def __eq__(cls, other):
        """Expands on equals comparison to include comparing the version.

        Args:
            other (:obj:): The object to compare to this class.

        Returns:
            bool: True if the other object is equivalent to this class, including version.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        if isinstance(other, type(cls)):
            if cls._VERSION_TYPE != other._VERSION_TYPE:
                raise TypeError(f"'==' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
        elif isinstance(other, Version):
            other_version = other
        else:
            other_version = cls.VERSION.cast(other)

        if isinstance(other_version, type(cls.VERSION)):
            return cls.VERSION == other_version
        else:
            raise TypeError(f"'==' not supported between instances of '{str(cls)}' and '{str(other)}'")

    def __ne__(cls, other):
        """Expands on not equals comparison to include comparing the version.

        Args:
            other (:obj:): The object to compare to this class.

        Returns:
            bool: True if the other object is not equivalent to this class, including version number.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        if isinstance(other, type(cls)):
            if cls._VERSION_TYPE != other._VERSION_TYPE:
                raise TypeError(f"'!=' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
        elif isinstance(other, Version):
            other_version = other
        else:
            other_version = cls.VERSION.cast(other)

        if isinstance(other_version, type(cls.VERSION)):
            return cls.VERSION != other_version
        else:
            raise TypeError(f"'!=' not supported between instances of '{str(cls)}' and '{str(other)}'")

    def __lt__(cls, other):
        """Creates the less than comparison which compares the version of this class.

        Args:
            other (:obj:): The object to compare to this class.

        Returns:
            bool: True if the this object is less than to the other classes' version.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        if isinstance(other, type(cls)):
            if cls._VERSION_TYPE != other._VERSION_TYPE:
                raise TypeError(f"'<' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
        elif isinstance(other, Version):
            other_version = other
        else:
            other_version = cls.VERSION.cast(other)

        if isinstance(other_version, type(cls.VERSION)):
            return cls.VERSION < other_version
        else:
            raise TypeError(f"'<' not supported between instances of '{str(cls)}' and '{str(other)}'")

    def __gt__(cls, other):
        """Creates the greater than comparison which compares the version of this class.

        Args:
            other (:obj:): The object to compare to this class.

        Returns:
            bool: True if the this object is greater than to the other classes' version.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        if isinstance(other, type(cls)):
            if cls._VERSION_TYPE != other._VERSION_TYPE:
                raise TypeError(f"'>' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
        elif isinstance(other, Version):
            other_version = other
        else:
            other_version = cls.VERSION.cast(other)

        if isinstance(other_version, type(cls.VERSION)):
            return cls.VERSION > other_version
        else:
            raise TypeError(f"'>' not supported between instances of '{str(cls)}' and '{str(other)}'")

    def __le__(cls, other):
        """Creates the less than or equal to comparison which compares the version of this class.

        Args:
            other (:obj:): The object to compare to this class.

        Returns:
            bool: True if the this object is less than or equal to the other classes' version.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        if isinstance(other, type(cls)):
            if cls._VERSION_TYPE != other._VERSION_TYPE:
                raise TypeError(f"'<=' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
        elif isinstance(other, Version):
            other_version = other
        else:
            other_version = cls.VERSION.cast(other)

        if isinstance(other_version, type(cls.VERSION)):
            return cls.VERSION <= other_version
        else:
            raise TypeError(f"'<=' not supported between instances of '{str(cls)}' and '{str(other)}'")

    def __ge__(cls, other):
        """Creates the greater than or equal to comparison which compares the version of this class.

        Args:
            other (:obj:): The object to compare to this class.

        Returns:
            bool: True if the this object is greater than or equal to the other classes' version.

        Raises:
            TypeError: If 'other' is a type that cannot be compared to.
        """
        if isinstance(other, type(cls)):
            if cls._VERSION_TYPE != other._VERSION_TYPE:
                raise TypeError(f"'>=' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
        elif isinstance(other, Version):
            other_version = other
        else:
            other_version = cls.VERSION.cast(other)

        if isinstance(other_version, type(cls.VERSION)):
            return cls.VERSION <= other_version
        else:
            raise TypeError(f"'>=' not supported between instances of '{str(cls)}' and '{str(other)}'")


class VersionedClass(metaclass=VersionedMeta):
    """An abstract class allows child classes to specify its version which it can use to compare.

    Class Attributes:
        _registry (:obj:`VersionRegistry`): A registry of all subclasses and versions of this class.
        _registration (bool): Specifies if versions will tracked and will recurse to parent.
        _VERSION_TYPE (:obj:`VersionType`): The type of version this object will be.
        VERSION (:obj:`Version`): The version of this class as a string.
    """
    _registry = VersionRegistry()
    _registration = True
    _VERSION_TYPE = None
    VERSION = None

    # Class Methods
    # Construction/Destruction
    def __init_subclass__(cls, **kwargs):
        """Adds the future child classes to the registry upon class instantiation"""
        super().__init_subclass__(**kwargs)

        type_ = cls._VERSION_TYPE
        class_ = cls._VERSION_TYPE.class_

        if not isinstance(cls.VERSION, class_):
            cls.VERSION = class_(cls.VERSION)

        cls.VERSION.version_type = type_

        if cls._registration:
            cls._registry.add_item(cls, type_)

    @classmethod
    def get_version_class(cls, version, type_=None, exact=False, sort=False):
        """Gets a class class based on the version.

        Args:
            version (str, list, tuple, :obj:`Version`): The key to search for the class with.
            type_ (str, optional): The type of class to get.
            exact (bool, optional): Determines whether the exact version is need or return the closest version.
            sort (bool, optional): If True, sorts the registry before getting the class.

        Returns:
            obj: The class found.
        """
        if type_ is None:
            type_ = cls._VERSION_TYPE

        if sort:
            cls._registry.sort(type_)

        return cls._registry.get_version(type_, version, exact=exact)


# Main #
if __name__ == "__main__":
    # Example
    # Define Classes with Versions
    class ExampleVersioning(VersionedClass):
        """A Version Class that establishes the type of class versioning the child classes will use."""
        _VERSION_TYPE = VersionType(name="Example", class_=TriNumberVersion)  # Remember if you want to use multiple
                                                                              # versioned classes that they should have
                                                                              # different names.


    class Example1_0_0(ExampleVersioning):
        """This class is the first of Examples version 1.0.0 which implements some adding"""
        VERSION = TriNumberVersion(1, 0, 0)  # Version can be defined through version object

        def __init__(self):
            self.a = 1
            self.b = 2

        def add(self, x):
            self.a = self.a + x


    class Example1_1_0(Example1_0_0):
        """This class inherits from 1.0.0 but changes how the adding is done"""
        VERSION = "1.1.0"  # Version can be defined through str as long as there is a method to derive the Version

        def add(self, x):
            self.b = self.b + x


    class Example2_0_0(ExampleVersioning):
        """Rather than inherit from previous version, this class reimplements the whole class."""
        VERSION = (2, 0, 0)

        def __init__(self):
            self.a = 1
            self.c = 3

        def multiply(self, x):
            self.a = self.a * x


    # Using Example Classes
    # Data
    dataset1 = {"version": "1.0.0", "number": 1}
    dataset2 = {"version": (1, 2, 0), "number": 2}
    dataset3 = {"version": TriNumberVersion(2, 0, 0, ver_name="Example"), "number": 3}

    datasets = [dataset1, dataset2, dataset3]

    # Example: Getting version
    example1 = ExampleVersioning.get_version_class(dataset1["version"])
    example2 = ExampleVersioning.get_version_class(dataset2["version"], type_="Example")
    example3 = ExampleVersioning.get_version_class(dataset3["version"], exact=True, sort=True)

    # Example: Operating on a list of versioned datasets
    for d in datasets:
        example_class = ExampleVersioning.get_version_class(d["version"])  # Get Example class based on version
        example_object = example_class()                                   # Initiate Example object
        if example_class < "2.0.0":                                        # If the version is less than 2.0.0, add
            example_object.add(d["number"])
            print(example_object.a)
            print(example_object.b)
        else:
            example_object.multiply(d["number"])
            print(example_object.a)
