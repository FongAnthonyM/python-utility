#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" functions.py
Description: 
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
import math

# Downloaded Libraries #

# Local Libraries #


# Definitions #
# Classes #

# Functions #
def multisort(objects, specs):
    for key, reverse in reversed(specs):
        objects.sort(key=lambda obj: getattr(obj, key), reverse=reverse)
    return objects


def isblank(obj):
    flag = False

    if obj is None:
        flag = True
    elif isinstance(obj, float) and math.isnan(obj):
        flag = True
    elif isinstance(obj, str) and obj == '':
        flag = True

    return flag


# Main #
if __name__ == "__main__":
    pass
