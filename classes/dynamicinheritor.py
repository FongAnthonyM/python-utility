#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" dynamicinheritor.py

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
import copy

# Downloaded Libraries #

# Local Libraries #


# Definitions #
# Classes #
class DynamicInheritor(abc.ABC):
    """A class whose objects call the methods and attributes of other objects, acting as if it is inheriting them.

    When an object of this class has an attribute/method call it will call a listed object's attribute/method. This is
    similar to what an @Property decorator can do but without having to write a decorator for each attribute. Attribute/
    method calling is done dynamically where the objects in the list can change during runtime so the available
    attributes/methods will change based on the objects in the list. Since the available attributes/ methods cannot be
    evaluated until runtime an IDE's auto-complete cannot display what callable options there are.

    _attritbute_as_partents is the list of attributes of this object that contains the objects that will be used for the
    dynamic calling. This object and subclasses can still have its own defined attributes and methods that are called.
    Which attribute/method is used for the call is handled in the same as inheritance where it will check if the
    attribute/method is present in this object if not it will check in the next object in the list. Therefore it is
    important to ensure the order of _attritbute_as_partents is order of descending inheritance.

    Class Attributes:
        _attributes_as_parents (:obj:'list' of :obj:'str'): The list of attribute names that will contain the objects to
            dynamically inherit from where the order is descending inheritance.
    """
    _attributes_as_parents = []

    # Construction/Destruction
    def __copy__(self):
        """The copy magic method (shallow)

        Returns:
            :obj:`DynamicInheritor`: A shallow copy of this object.
        """
        new = type(self)()
        new.__dict__.update(self.__dict__)
        return new

    def __deepcopy__(self, memo={}):
        """Overrides the deep copy magic method to ensure the dynamically inheriting objects are copied.

        Args:
            memo (dict): A dictionary of user defined information to pass to another deepcopy call which it will handle.

        Returns:
            :obj:`DynamicInheritor`: A deep copy of this object.
        """
        new = type(self)()
        for attribute in self._attributes_as_parents:
            if attribute in dir(self):
                parent_object = copy.deepcopy(super().__getattribute__(attribute))
                setattr(new, attribute, parent_object)
        new.__dict__.update(self.__dict__)
        return new

    # Attribute Access
    def __getattribute__(self, name):
        """Overrides the get_attribute magic method to get the attribute of another object if that attribute name is not
        present.

        Args:
            name (str): The name of the attribute to get.

        Returns:
            obj: Whatever the attribute contains.
        """
        # Check if item is in self and if not check in the object parents
        if name[0:2] != "__" and name not in {"_attributes_as_parents"} and \
           name not in self._attributes_as_parents and name not in dir(self):
            # Iterate through all object parents to find attribute
            for attribute in self._attributes_as_parents:
                parent_object = super().__getattribute__(attribute)
                if name in dir(parent_object):
                    return getattr(parent_object, name)

        # If the item is an attribute in self or not in any object parent return attribute
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        """Overrides the setattr magic method to set the attribute of another object if that attribute name is not
        present.

        Args:
            name (str): The name of the attribute to get.
            value: Whatever the attribute will contain.
        """
        # Check if item is in self and if not check in object parents
        if name not in self._attributes_as_parents and name not in dir(self):
            # Iterate through all indirect parents to find attribute
            for attribute in self._attributes_as_parents:
                if attribute in dir(self):
                    parent_object = super().__getattribute__(attribute)
                    if name in dir(parent_object):
                        return setattr(parent_object, name, value)

        # If the item is an attribute in self or not in any indirect parent set as attribute
        super().__setattr__(name, value)

    def _setattr(self, name, value):
        """An override method that will set an attribute of this object without checking its presence in other objects.

        This is useful for setting new attributes after class the definition.

        Args:
            name (str): The name of the attribute to get.
            value: Whatever the attribute will contain.
        """
        super().__setattr__(name, value)


# Main #
if __name__ == "__main__":
    pass
