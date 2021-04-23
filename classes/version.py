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
import dataclasses
from dataclasses import dataclass

# Downloaded Libraries #

# Local Libraries #


# Definitions #
# Classes #
class Version(abc.ABC):
    """An abstract class for creating versions which dataclass like classes that stores and handles a versioning.

    Args:
        obj (:obj:, optional): An object to derive a version from.
        init (bool, optional): Determines if the object should be initialized.
    """

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

    # Construction/Destruction
    @abstractmethod
    def __init__(self, obj=None, init=True, **kwargs):
        if init:
            self.construct(obj=obj, **kwargs)

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
    def construct(self, obj=None):
        """Constructs the version object based on inputs

        Args:
            obj (:obj:, optional): An object to derive a version from.
        """
        pass

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


class SimpleVersion(Version):
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
    __slots__ = ["major", "moderate", "minor"]

    # Construction/Destruction
    def __init__(self, obj=None, major=0, moderate=0, minor=0, init=True):
        self.major = major
        self.moderate = moderate
        self.minor = minor

        if init:
            super().__init__(obj=obj, major=major, moderate=moderate, minor=minor)

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

        if isinstance(other, Version):
            return self.tuple() != other.tuple()
        else:
            return super().__ne__(other)

    def __ne__(self, other):
        """Expands on not equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is not equivalent.
        """
        other = self.cast(other, pass_=True)

        if isinstance(other, Version):
            return self.tuple() != other.tuple()
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

        if isinstance(other, Version):
            return self.tuple() < other.tuple()
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

        if isinstance(other, Version):
            return self.tuple() > other.tuple()
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

        if isinstance(other, Version):
            return self.tuple() <= other.tuple()
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

        if isinstance(other, Version):
            return self.tuple() >= other.tuple()
        else:
            raise TypeError(f"'>=' not supported between instances of '{str(self)}' and '{str(other)}'")

    # Methods
    def construct(self, obj=None, moderate=0, minor=0, major=0):
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
            major, moderate, minor = major
        elif isinstance(obj, int):
            major = obj
        elif obj is not None:
            raise TypeError("Can't create {} from {}".format(self, major))

        self.major = major
        self.moderate = moderate
        self.minor = minor

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


class VersionType:
    __slots__ = ["name", "class_"]

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

    # Construction/Destruction
    def __init__(self, obj=None, name=None, class_=None, init=True):
        self.name = None
        self.class_ = None

        if init:
            self.construct(obj=obj, name=name, class_=class_)

    # Type Conversion
    def __str__(self):
        """Returns the str representation of the version.

        Returns:
            str: A str with the version numbers in order.
        """
        return super().__str__()

    # Comparison
    def __eq__(self, other):
        """Expands on equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is equivalent.
        """
        return super().__ne__(other)

    def __ne__(self, other):
        """Expands on not equals comparison to include comparing the version number.

        Args:
            other (:obj:): The object to compare to this object.

        Returns:
            bool: True if the other object or version number is not equivalent.
        """
        return super().__ne__(other)

    # Methods
    def construct(self, obj=None, name=None, class_=None):
        """Constructs the version object based on inputs

        Args:
            obj (:obj:, optional): An object to derive a version from.
            name
            class_
        """
        pass


class VersionRegistry(collections.UserDict):
    """A dictionary like class that holds versioned objects.

    The keys distinguish different types of objects from one another, so their version are not mixed together. The items
    are lists containing the versioned objects in order by version.
    """

    # Methods
    def get_from_version(self, type_, key, exact=False, ver_class=None):
        """Gets an object from the registry base on the type and version of object.

        Args:
            type_ (str): The type of versioned object to get.
            key (str, list, tuple, :obj:`Version`): The key to search for the versioned object with.
            exact (bool, optional): Determines whether the exact version is need or return the closest version.
            ver_class (:class:, optional): The version class to compare the objects with.

        Returns
            obj: The versioned object.

        Raises
            ValueError: If there is no closest version.
        """
        versions = self[type_]
        if isinstance(key, str) or isinstance(key, list) or isinstance(key, tuple):
            if ver_class is None:
                key = self.default_ver_class.cast(key)
            else:
                key = ver_class.cast(key)  # There is probably a better way to do this so type effects it.

        if exact:
            index = versions.index(key)
        else:
            index = bisect.bisect(versions, key)

        if index < 0:
            raise ValueError(f"Version needs to be greater than {str(versions[0])}, {str(key)} is not.")
        else:
            return versions[index]

    def add_item(self, type_, item):
        """Adds a versioned item into the registry.

        Args
            type_ (str): The type of versioned object to add.
            item (:obj:): The versioned object to add.
        """
        if type_ in self.data:
            bisect.insort(self.data[type_], item)
        else:
            self.data[type_] = item

    def sort(self, type_=None, **kwargs):
        """Sorts the registry.

        Args:
            type_ (str, optional): The type of versioned object to add.
            **kwargs: Args that are passed to the list sort function.
        """
        if type_ is None:
            for versions in self.data.values():
                versions.sort(**kwargs)
        else:
            self.data[type_].sort(**kwargs)


class VersionedMeta(abc.ABCMeta):
    """A Meta Class that can compare the specified version of the classes.

    Class Attributes:
        TYPE (str): The type of class this will be.
        VERSION (:obj:`Version`): The version of this class as a string.
    """
    TYPE = None
    VERSION = None

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
        if super().__eq__(other):
            return True
        elif isinstance(other, type(cls)):
            if cls.TYPE != other.TYPE:
                raise TypeError(f"'==' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
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
        if super().__ne__(other):
            return True
        elif isinstance(other, type(cls)):
            if cls.TYPE != other.TYPE:
                raise TypeError(f"'!=' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
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
            if cls.TYPE != other.TYPE:
                raise TypeError(f"'<' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
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
            if cls.TYPE != other.TYPE:
                raise TypeError(f"'>' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
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
            if cls.TYPE != other.TYPE:
                raise TypeError(f"'<=' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
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
            if cls.TYPE != other.TYPE:
                raise TypeError(f"'>=' not supported between instances of '{str(cls)}' and '{str(other)}'")
            other_version = other.VERSION
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
        TYPE (str): The type of class this will be.
        VERSION (:obj:`Version`): The version of this class as a string.
    """
    _registry = VersionRegistry()
    _registration = True
    TYPE = None
    VERSION = None

    # Class Methods
    # Construction/Destruction
    def __init_subclass__(cls, **kwargs):
        """Adds the future child classes to the registry upon class instantiation"""
        super().__init_subclass__(**kwargs)

        if cls._registration:
            cls._registry.add_item(cls.TYPE, cls)

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
            type_ = cls.TYPE

        if sort:
            cls._registry.sort(type_)

        return cls._registry.get_from_version(type_, version)


# Main #
if __name__ == "__main__":
    pass
