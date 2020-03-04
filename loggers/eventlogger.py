"""
.py

Last Edited:

Lead Author[s]: Anthony Fong
Contributor[s]:

Description:


Machine I/O
Input:
Output:

User I/O
Input:
Output:


"""
########################################################################################################################

########## Libraries, Imports, & Setup ##########

# Default Libraries #
from abc import ABC, abstractmethod
import bisect
import collections
import copy
import csv
import datetime
import pathlib
import time
import uuid
from warnings import warn

# Downloaded Libraries #
from bidict import bidict
import h5py
import numpy as np

# Local Libraries #
from ..ioutility.iotriggers import AudioTrigger


########## Definitions ##########

# Classes #
class EventLoggerCSV(collections.UserList):
    def __init__(self, io_trigger=None, **kwargs):
        super().__init__(**kwargs)
        self.start_datetime = None
        self.start_time_counter = None
        self._path = None
        if io_trigger is None:
            self.io_trigger = AudioTrigger()
        else:
            self.io_trigger = io_trigger

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if isinstance(value, pathlib.Path) or value is None:
            self._path = value
        else:
            self._path = pathlib.Path(value)

    def set_time(self):
        self.start_datetime = datetime.datetime.now()
        self.start_time_counter = time.perf_counter()
        self.append({"Time": self.start_datetime, "DeltaTime": 0, "Type": "TimeSet"})

    def create_event(self, type_, **kwargs):
        seconds = round(time.perf_counter() - self.start_time_counter, 6)
        now = self.start_datetime + datetime.timedelta(seconds=seconds)
        return {"Time": now, "DeltaTime": seconds, "Type": type_, **kwargs}

    def append(self, type_, **kwargs):
        if isinstance(type_, dict):
            super().append(type_)
        else:
            event = self.create_event(type_=type_, **kwargs)
            super().append(event)

    def insert(self, i, type_, **kwargs):
        if isinstance(type_, dict):
            super().insert(i, type_)
        else:
            event = self.create_event(type_=type_, **kwargs)
            super().insert(i, event)

    def clear(self):
        self.start_datetime = None
        self.start_time_counter = None
        self._path = None
        super().clear()

    def trigger(self):
        self.io_trigger.trigger()

    def trigger_event(self, **kwargs):
        self.trigger()
        self.append(type_="Trigger", **kwargs)

    def save_csv(self, path=None):
        if path is not None:
            self.path = path
        with self.path.open('w') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"')
            for event in self.data:
                writer.writerow(self.event2list(event))

    @staticmethod
    def event2list(event):
        result = []
        for key, value in event.items():
            if isinstance(value, datetime.datetime):
                value = value.timestamp()
            result.append(key + ": " + str(value))
        return result


class HDF5container(object):
    FILE_TYPE = "Abstract"
    VERSION = "0.0.0"

    # Instantiation, Copy, Destruction
    def __init__(self, path=None, update=True, init=False):
        self._file_attrs = set()
        self._datasets = set()
        self._path = None

        self.path = path
        self.is_updating = update

        self.cargs = {"compression": "gzip", "compression_opts": 4}
        self.default_datasets_parameters = self.cargs.copy()
        self.default_attrs = {"FileType": self.FILE_TYPE, "Version": self.VERSION}
        self.default_datasets = {}

        self.h5_fobj = None

        if init:
            self.construct()

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if isinstance(value, pathlib.Path) or value is None:
            self._path = value
        else:
            self._path = pathlib.Path(value)

    @property
    def is_open(self):
        return bool(self.h5_fobj)

    @property
    def file_attrs_names(self):
        self.load_attributes()
        return self._file_attrs

    @property
    def dataset_names(self):
        return self.get_dataset_names()

    def __copy__(self):
        new = type(self)()
        new.__dict__.update(self.__dict__)
        return new

    def __deepcopy__(self, memo={}):
        new = self.deepcopy(init=True, memo=memo)
        return new

    def __del__(self):
        self.close()

    # Pickling
    def __getstate__(self):
        state = self.__dict__.copy()
        name = state["path"].as_posix()
        open_state = state["is_open"]
        if self.is_open:
            fobj = state["h5_fobj"]
            fobj.flush()
            fobj.close()
        state["h5_fobj"] = (name, open_state)
        return state

    def __setstate__(self, state):
        name, open_state = state["h5_fobj"]
        state["h5_fobj"] = h5py.File(name.as_posix(), "r+")
        if not open_state:
            state["h5_fobj"].close()
        self.__dict__.update(state)

    # Attribute Access
    def __getattribute__(self, item):
        reserved = ("_file_attrs", "_datasets", "get_file_attribute", "get_dataset", "__init__")
        try:
            if item in reserved:
                return super().__getattribute__(item)
            elif item in self._file_attrs:
                return self.get_file_attribute(item)
            elif item in self._datasets:
                return self.get_dataset(item)
            else:
                return super().__getattribute__(item)
        except AttributeError:
            return super().__getattribute__(item)

    def __setattr__(self, key, value):
        reserved = ("_file_attrs", "_datasets")
        if key in reserved:
            super().__setattr__(key, value)
        elif key in self._file_attrs:
            self.set_file_attribute(key, value)
        elif key in self._datasets:
            self.set_dataset(key, value)
        else:
            super().__setattr__(key, value)

    # Container Magic Methods
    def __len__(self):
        op = self.is_open
        self.open()
        length = len(self.h5_fobj)
        if not op:
            self.close()
        return length

    def __getitem__(self, item):
        if item in self._datasets:
            data = self.get_dataset(item)
        else:
            raise KeyError(item)
        return data

    def __setitem__(self, key, value):
        self.set_dataset(key, value)

    # Context Managers
    def __enter__(self):
        if self.h5_fobj is None:
            self.construct(open_=True)
        else:
            self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    # Constructors
    def construct(self, open_=False, **kwargs):
        if self.path.is_file():
            self.open(validate=True, **kwargs)
            if not open_:
                self.close()
        else:
            self.create_file(open_=open_)

    # File Creation
    def create_file(self, open_=False):
        self.open()
        if self.default_attrs:
            self.add_file_attributes(self.default_attrs)
        if self.default_datasets:
            self.add_file_datasets(self.default_datasets)
        if open_:
            return self.h5_fobj
        else:
            self.close()
            return None

    def construct_file_attributes(self, value=""):
        if len(self._file_attrs.intersection(self._datasets)) > 0:
            warn("Attribute name already exists", stacklevel=2)

        op = self.is_open
        self.open()
        for key in self._file_attrs:
            _key = "_" + key
            try:
                self.h5_fobj.attrs[key] = value
            except Exception as e:
                warn("Could not set attribute due to error: " + str(e), stacklevel=2)
            else:
                super().__setattr__(_key, value)
        if not op:
            self.close()

    def construct_file_datasets(self, **kwargs):
        if len(self._datasets.intersection(self._file_attrs)) > 0:
            warn("Dataset name already exists", stacklevel=2)

        op = self.is_open
        self.open()
        for key in self._datasets:
            _key = "_" + key
            try:
                args = merge_dict(self.default_datasets_parameters, kwargs)
                self.h5_fobj.require_dataset(key, **args)
            except Exception as e:
                warn("Could not set datasets due to error: " + str(e), stacklevel=2)
            else:
                super().__setattr__(_key, HDF5container(self.h5_fobj[key], self))
        if not op:
            self.close()

    # Copy Methods
    def copy(self):
        return self.__copy__()

    def deepcopy(self, path=None, init=False, memo={}):
        if path is None:
            new = type(self)(path=self.path.as_posix)
        else:
            new = type(self)(path=path)
        new._file_attrs = copy.deepcopy(self._file_attrs, memo=memo)
        new._datasets = copy.deepcopy(self._datasets, memo=memo)
        new.is_open = self.is_open
        new.is_updating = self.is_updating
        new.cargs = copy.deepcopy(self.cargs, memo=memo)
        new.default_datasets_parameters = copy.deepcopy(self.cargs, memo=memo)

        if init:
            new.construct()
        return new

    # Getters and Setters
    def get(self, item):
        if item in self._file_attrs:
            return self.get_file_attribute(item)
        elif item in self._datasets:
            return self.get_dataset(item)
        else:
            warn("No attribute or dataset " + item, stacklevel=2)
            return None

    # File Attributes
    def get_file_attribute(self, item):
        _item = "_" + item
        op = self.is_open
        self.open()

        try:
            if item in self.h5_fobj.attrs and (super().__getattribute__(_item) is None or self.is_updating):
                setattr(self, _item, self.h5_fobj.attrs[item])
        except Exception as e:
            warn("Could not update attribute due to error: "+str(e), stacklevel=2)

        if not op:
            self.close()
        return super().__getattribute__(_item)

    def get_file_attributes(self):
        op = self.is_open
        self.open()

        attr = dict(self.h5_fobj.attrs.items())

        if not op:
            self.close()
        return attr

    def set_file_attribute(self, key, value):
        op = self.is_open
        self.open()
        _item = "_" + key

        try:
            if key not in self._file_attrs:
                self._file_attrs.update((key,))
            self.h5_fobj.attrs[key] = value
        except Exception as e:
            warn("Could not set attribute due to error: " + str(e), stacklevel=2)
        else:
            super().__setattr__(_item, value)

        if not op:
            self.close()

    def add_file_attributes(self, items):
        names = set(items.keys())
        if len(names.intersection(self._datasets)) > 0:
            warn("Attribute name already exists", stacklevel=2)

        op = self.is_open
        self.open()
        for key, value in items.items():
            _key = "_" + key
            try:
                if key not in self._file_attrs:
                    self._file_attrs.update((key,))
                self.h5_fobj.attrs[key] = value
            except Exception as e:
                warn("Could not set attribute due to error: " + str(e), stacklevel=2)
            else:
                super().__setattr__(_key, value)
        if not op:
            self.close()

    def clear_attributes(self):
        for key in self._file_attrs:
            self.__delattr__("_" + key)
        self._file_attrs.clear()

    def load_attributes(self):
        self.clear_attributes()
        for key, value in self.h5_fobj.attrs.items():
            _item = "_" + key
            self._file_attrs.update((key,))
            super().__setattr__(_item, value)

    def list_attributes(self):
        self.load_attributes()
        return list(self._file_attrs)

    # Datasets
    def create_dataset(self, name, data=None, **kwargs):
        self.set_dataset(name=name, data=data, **kwargs)
        return self.get_dataset(name)

    def get_dataset(self, item):
        _item = "_" + item
        op = self.is_open
        self.open()

        try:
            if item in self.h5_fobj and self.is_updating:
                super().__setattr__(_item, HDF5dataset(self.h5_fobj[item], self))
        except Exception as e:
            warn("Could not update datasets due to error: " + str(e), stacklevel=2)

        if not op:
            self.close()
        return super().__getattribute__(_item)

    def set_dataset(self, name, data=None, **kwargs):
        op = self.is_open
        self.open()
        _key = "_" + name

        try:
            if name in self._datasets:
                self.h5_fobj[name][...] = data
            else:
                self._datasets.update((name,))
                args = merge_dict(self.default_datasets_parameters, kwargs)
                args["data"] = data
                self.h5_fobj.require_dataset(name, **args)
        except Exception as e:
            warn("Could not set datasets due to error: " + str(e), stacklevel=2)
        else:
            super().__setattr__(_key, HDF5dataset(self.h5_fobj[name], self))

        if not op:
            self.close()

    def add_file_datasets(self, items):
        names = set(items.keys())
        if len(names.intersection(self._file_attrs)) > 0:
            warn("Dataset name already exists", stacklevel=2)

        op = self.is_open
        self.open()
        for name, kwargs in items.items():
            _key = "_" + name
            try:
                self._datasets.update((name,))
                args = merge_dict(self.default_datasets_parameters, kwargs)
                self.h5_fobj.require_dataset(name, **args)
            except Exception as e:
                warn("Could not set datasets due to error: " + str(e), stacklevel=2)
            else:
                super().__setattr__(_key, HDF5dataset(self.h5_fobj[name], self))
        if not op:
            self.close()

    def clear_datasets(self):
        for name in self._datasets:
            self.__delattr__("_" + name)
        self._datasets.clear()

    def load_datasets(self):
        self.clear_datasets()
        for name, value in self.h5_fobj.items():
            _item = "_" + name
            self._datasets.update((name,))
            super().__setattr__(_item, value)

    def get_dataset_names(self):
        self.load_datasets()
        return self._datasets

    def list_dataset_names(self):
        self.load_datasets()
        return list(self._datasets)

    #  Mapping Items Methods
    def items(self):
        return self.items_file_attributes() + self.items_datasets()

    def items_file_attributes(self):
        result = []
        for key in self._file_attrs:
            result.append((key, self.get_file_attribute(key)))
        return result

    def items_datasets(self):
        result = []
        for key in self._datasets:
            result.append((key, self.get_dataset(key)))
        return result

    # Mapping Keys Methods
    def keys(self):
        return self.keys_file_attributes() + self.keys_datasets()

    def keys_file_attributes(self):
        return list(self._file_attrs)

    def keys_datasets(self):
        return list(self._datasets)

    # Mapping Pop Methods
    def pop(self, key):
        if key in self._file_attrs:
            return self.pop_file_attribute(key)
        elif key in self._datasets:
            return self.pop_dataset(key)
        else:
            warn("No attribute or dataset " + key, stacklevel=2)
            return None

    def pop_file_attribute(self, key):
        value = self.get_file_attribute(key)
        del self.h5_fobj.attrs[key]
        return value

    def pop_dataset(self, key):
        value = self.get_dataset(key)[...]
        del self.h5_fobj[key]
        return value

    # Mapping Update Methods
    def update_file_attrs(self, **kwargs):
        if len(self._datasets.intersection(kwargs.keys())) > 0:
            warn("Dataset name already exists", stacklevel=2)
        if len(self._file_attrs.intersection(kwargs.keys())) > 0:
            warn("Attribute name already exists", stacklevel=2)

        op = self.is_open
        self.open()
        self._file_attrs.update(kwargs.keys())
        for key, value in kwargs:
            _key = "_" + key
            try:
                self.h5_fobj.attrs[key] = value
            except Exception as e:
                warn("Could not set attribute due to error: " + str(e), stacklevel=2)
            else:
                super().__setattr__(_key, value)
        if not op:
            self.close()

    def update_datasets(self, **kwargs):
        if len(self._file_attrs.intersection(kwargs.keys())) > 0:
            warn("Attribute name already exists", stacklevel=2)
        if len(self._datasets.intersection(kwargs.keys())) > 0:
            warn("Dataset name already exists", stacklevel=2)

        op = self.is_open
        self.open()
        self._datasets.update(kwargs.keys())
        for key, value in kwargs.items():
            _key = "_" + key
            try:
                args = merge_dict(self.default_datasets_parameters, value)
                self.h5_fobj.require_dataset(key, **args)
            except Exception as e:
                warn("Could not set datasets due to error: " + str(e), stacklevel=2)
            else:
                super().__setattr__(_key, HDF5container(self.h5_fobj[key], self))
        if not op:
            self.close()

    # File Methods
    def open(self, mode="a", exc=False, validate=False, **kwargs):
        if not self.is_open:
            try:
                self.h5_fobj = h5py.File(self.path.as_posix(), mode=mode)
            except Exception as e:
                if exc:
                    warn("Could not open" + self.path.as_posix() + "due to error: " + str(e), stacklevel=2)
                    self.h5_fobj = None
                    return None
                else:
                    raise e
            else:
                if validate:
                    self.validate_file_structure(**kwargs)
                self.load_attributes()
                self.load_datasets()
                return self.h5_fobj

    def close(self):
        if self.is_open:
            self.h5_fobj.flush()
            self.h5_fobj.close()
        return not self.is_open

    # General Methods
    def append2dataset(self, name, data, axis=0):
        dataset = self.get_dataset(name)
        s_shape = dataset.shape
        d_shape = data.shape
        f_shape = list(s_shape)
        f_shape[axis] = s_shape[axis] + d_shape[axis]
        slicing = tuple(slice(s_shape[ax]) for ax in range(0, axis)) + (-d_shape[axis], ...)

        with dataset:
            dataset.resize(*f_shape)
            dataset[slicing] = data

    def report_file_structure(self):
        op = self.is_open
        self.open()

        # Construct Structure Report Dictionary
        report = {"file_type": {"valid": False, "differences": {"object": self.FILE_TYPE, "file": None}},
                  "attrs": {"valid": False, "differences": {"object": None, "file": None}},
                  "datasets": {"valid": False, "differences": {"object": None, "file": None}}}

        # Check H5 File Type
        if "FileType" in self.h5_fobj.attrs:
            if self.h5_fobj.attrs["FileType"] == self.FILE_TYPE:
                report["file_type"]["valid"] = True
                report["file_type"]["differences"]["object"] = None
            else:
                report["file_type"]["differences"]["file"] = self.h5_fobj.attrs["FileType"]

        # Check File Attributes
        if self.h5_fobj.attrs.keys() == self._file_attrs:
            report["attrs"]["valid"] = True
        else:
            f_attr_set = set(self.h5_fobj.attrs.keys())
            o_attr_set = self._file_attrs
            report["attrs"]["differences"]["object"] = o_attr_set - f_attr_set
            report["attrs"]["differences"]["file"] = f_attr_set - o_attr_set

        # Check File Datasets
        if self.h5_fobj.keys() == self._datasets:
            report["attrs"]["valid"] = True
        else:
            f_attr_set = set(self.h5_fobj.keys())
            o_attr_set = self._datasets
            report["datasets"]["differences"]["object"] = o_attr_set - f_attr_set
            report["datasets"]["differences"]["file"] = f_attr_set - o_attr_set

        if not op:
            self.close()
        return report

    def validate_file_structure(self, file_type=True, o_attrs=True, f_attrs=False, o_datasets=True, f_datasets=False):
        report = self.report_file_structure()
        # Validate File Type
        if file_type and not report["file_type"]["valid"]:
            warn(self.path.as_posix() + " file type is not a " + self.FILE_TYPE, stacklevel=2)
        # Validate Attributes
        if not report["attrs"]["valid"]:
            if o_attrs and report["attrs"]["differences"]["object"] is not None:
                warn(self.path.as_posix() + " is missing attributes", stacklevel=2)
            if f_attrs and report["attrs"]["differences"]["file"] is not None:
                warn(self.path.as_posix() + " has extra attributes", stacklevel=2)
        # Validate Datasets
        if not report["datasets"]["valid"]:
            if o_datasets and report["datasets"]["differences"]["object"] is not None:
                warn(self.path.as_posix() + " is missing datasets", stacklevel=2)
            if f_datasets and report["datasets"]["differences"]["file"] is not None:
                warn(self.path.as_posix() + " has extra datasets", stacklevel=2)


class HDF5dataset(object):
    parent_methods = {x for x in dir(h5py.Dataset) if x[0] != '_'}

    # Instantiation, Copy, Destruction
    def __init__(self, dataset=None, container=None, init=True):
        self._dataset = None
        self._name = None

        self._container = None
        self._container_was_open = None

        if init:
            self.construct(dataset=dataset, container=container)

    @property
    def dataset(self):
        #if not self._container.is_open():
        #    self._container.open()
        #    self._dataset = self._container.h5_fobj[self._name]
        return self._dataset

    # Attribute Access
    def __getattribute__(self, item):
        if item == "parent_methods":
            output = super().__getattribute__(item)
        elif item in self.parent_methods:
            if self._dataset:
                output = getattr(self._dataset, item)
            else:
                with self:
                    output = getattr(self._container.h5_fobj[self._name], item)
        else:
            output = super().__getattribute__(item)
        return output

    def __setattr__(self, key, value):
        if key in self.parent_methods:
            if self._dataset:
                setattr(self._dataset, key, value)
            else:
                with self:
                    self._container.h5_fobj[self._name][key] = value
        else:
            super().__setattr__(key, value)

    # Container Magic Methods
    def __getitem__(self, item):
        if self._dataset:
            output = self._dataset[item]
        else:
            with self:
                output = self._container.h5_fobj[self._name][item]
        return output

    def __setitem__(self, key, value):
        if self._dataset:
            self._dataset[key] = value
        else:
            with self:
                self._container.h5_fobj[self._name][key] = value

    # Context Managers
    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    # Generic Methods #
    # Constructors Methods
    def construct(self, dataset=None, container=None):
        if isinstance(dataset, HDF5dataset):
            self._dataset = dataset._dataset
            self._name = dataset._name
            if container is None:
                self._container = dataset._container
            else:
                self._container = container
        else:
            self._dataset = dataset
            self._name = dataset.name
            if isinstance(container, HDF5container):
                self._container = container
            else:
                self._container = HDF5container(dataset.file.filename)

    def open(self, **kwargs):
        self._container_was_open = self._container.is_open
        if not self._dataset:
            self._container.open(**kwargs)
            self._dataset = self._container.h5_fobj[self._name]

    def close(self):
        if not self._container_was_open:
            self._container.close()


class HDF5referenceDataset(object):
    # Instantiation, Copy, Destruction
    def __init__(self, dataset, reference_field="", dtype=None, init=True):
        self.dataset = None

        self.reference_field = ""
        self.dtype = None
        self.fields = bidict()
        self.references = bidict()

        self._reference_array = None

        if init:
            self.construct(dataset, reference_field, dtype)

    def __copy__(self):
        new = type(self)()
        new.__dict__.update(self.__dict__)
        return new

    @property
    def reference_array(self):
        try:
            self._reference_array = self.dataset[self.reference_field]
        except Exception as e:
            warn(e)
        finally:
            return self._reference_array

    # Container Magic Methods
    def __getitem__(self, items):
        return self.get_item(items)

    def __setitem__(self, key, value):
        self.set_item(value, key)

    def __contains__(self, item):
        if isinstance(item, str):
            item = uuid.UUID(item)
        if isinstance(item, uuid.UUID):
            result = self.find_index(item)
        elif isinstance(item, tuple):
            result = self.find_id(item)
        else:
            raise KeyError

        if result is None:
            return False
        else:
            return True

    # Generic Methods #
    # Constructors Methods
    def construct(self, dataset, reference_field, dtype=None):
        self.dataset = dataset

        if dtype is None:
            self.dtype = self.dataset.dtype
        else:
            self.dtype = dtype

        for i, field in enumerate(self.dtype.descr):
            self.fields[field[0]] = i

        if reference_field in self.fields:
            self.reference_field = reference_field
        else:
            raise NameError

        self._reference_array = self.dataset[self.reference_field]

    # Copy Methods
    def copy(self):
        return self.__copy__()

    # Reference Getters and Setters
    def new_reference(self, index=None, axis=0, id_=None):
        shape = self.dataset.shape
        if index is None:
            shape = list(shape)
            shape[axis] += 1
            new_shape = shape[axis]
            index = [a - 1 for a in shape]
        elif len(index) == len(shape):
            new_shape = []
            axis = None
            for s, i in zip(shape, index):
                new_shape.append(max((s, i)))
        else:
            raise IndexError

        with self.dataset:
            self.dataset.resize(new_shape, axis)

        if id_ is None:
            id_ = uuid.uuid4()
        self.set_reference(index, id_)
        return id_

    def get_references(self, items):
        if not isinstance(items, tuple):
            items = (items,)

        result = []
        for item in items:
            if isinstance(item, str):
                item = uuid.UUID(item)
            if isinstance(item, uuid.UUID):
                result.append(self.get_index(item))
            elif isinstance(item, tuple) or isinstance(item, int):
                result.append(self.get_id(item))

        if len(result) > 1:
            result = tuple(result)
        else:
            result = result[0]
        return result

    def set_reference(self, index, id_):
        index = tuple(index)
        if isinstance(id_, str):
            id_ = uuid.UUID(id_)
        item = self.dataset[index]
        item[self.reference_field] = str(id_)
        self.dataset[index] = item
        self.references[id_] = index

    def get_index(self, id_):
        try:
            index = self.find_index(id_)
            if index:
                self.references[id_] = index
            else:
                raise KeyError
        except Exception as e:
            warn(e)
        finally:
            return self.references[id_]

    def find_index(self, id_):
        indices = np.where(self.reference_array == str(id_))
        if len(indices) == 0:
            index = None
        elif len(indices[0]) > 1:
            raise KeyError
        else:
            temp = []
            for axis in indices:
                if axis.size > 0:
                    temp.append(axis[0])
                else:
                    return None
            index = tuple(temp)
        return index

    def get_id(self, index):
        if isinstance(index, int):
            shape = self.dataset.shape
            if index < 0:
                index = shape[0] - 1
            index = tuple([index] + [0]*(len(shape)-1))
        try:
            self.references.inverse[index] = self.find_id(index)
        except Exception as e:
            warn(e)
        finally:
            return self.references.inverse[index]

    def find_id(self, index):
        try:
            array = self.reference_array[index]
            result = uuid.UUID(self.reference_array[index])
        except ValueError:
            result = None
        finally:
            return result

    # Item Getters and Setters
    def get_item(self, location, dict_=True, id_=True):
        # Polymorphic Get Item as a Dictionary
        if isinstance(location, str):
            location = uuid.UUID(location)
            index = self.get_index(location)
        elif isinstance(location, uuid.UUID):
            index = self.get_index(location)
        elif isinstance(location, tuple):
            index = location

        result = self.dataset[index]
        if dict_:
            result = np_to_dict(result)
            if not id_:
                result.pop(self.reference_field)

        return result

    def set_item(self, item, location, pop=False):
        # Polymorphic Assignment
        if isinstance(location, uuid.UUID):
            id_ = location
            index = self.get_index(location)
        else:
            id_ = self.get_id(location)
            if id_ is None:
                id_ = uuid.uuid4()
            index = location

        # Add/Assign Reference ID to Item
        item[self.reference_field] = id_

        # Build Array from Item
        array = dict_to_np(item, self.dtype.descr, pop=pop)

        # Assign Array to Dataset
        self.dataset[index] = tuple(array)
        self.references[id_] = index


class HDF5linkedDatasets(object):
    # Instantiation, Copy, Destruction
    def __init__(self):
        self.references = {}

    def __copy__(self):
        new = type(self)()
        new.__dict__.update(self.__dict__)
        return new

    # Container Magic Methods
    def __getitem__(self, items):
        if not isinstance(items, tuple):
            items = (items,)

        result = []
        for item in items:
            if isinstance(item, uuid.UUID):
                result.append(self.get_indices(item))
            elif isinstance(item, str):
                result.append(self.references[item])

        if len(result) > 1:
            result = tuple(result)
        else:
            result = result[0]
        return result

    # Copy Methods
    def copy(self):
        return self.__copy__()

    # Dataset Getters and Setters
    def add_datset(self, name, dataset, link_name):
        self.references[name] = HDF5referenceDataset(dataset, link_name)

    def pop_dataset(self, name):
        return self.references.pop(name)

    # Links and Indices
    def new_link(self, locations=None, axis=0, id_=None):
        if id_ is None:
            id_ = uuid.uuid4()

        if not locations:
            for references in self.references.values():
                references.new_reference(axis=axis, id_=id_)
        elif isinstance(locations, collections.abc.Mapping):
            for name, index in locations.items():
                self.references[name].new_reference(index=index, id_=id_)
        else:
            for name in locations:
                self.references[name].new_reference(axis=axis, id_=id_)

        return id_

    def get_index(self, name, id_):
        return self.references[name].get_references(id_)

    def get_indices(self, id_, datasets=None):
        result = {}
        if not datasets:
            for name, references in self.references.items():
                if id_ in references:
                    result[name] = references.get_references(id_)
        else:
            if isinstance(datasets, str):
                datasets = (datasets,)
            for name in datasets:
                result[name] = self.references[name].get_references(id_)

        return result

    def get_linked_indices(self, name, index, datasets=None):
        id_ = self.get_id(name, index)
        return self.get_indices(id_, datasets)

    def get_id(self, name, index):
        return self.references[name].get_references((index,))

    # Item Getter and Setters
    def get_linked_data(self, name, location, children=None, dict_=True):
        if isinstance(location, str):
            location = uuid.UUID(location)
        if isinstance(location, uuid.UUID):
            child_indices = self.get_indices(location)
        else:
            child_indices = self.get_linked_indices(name, location)

        valid_children = {}
        if children:
            if isinstance(children, str):
                children = [children]
            for child in children:
                valid_children[child] = child_indices[child]
        else:
            valid_children = child_indices
        if name in valid_children:
            valid_children.pop(name)

        if dict_:
            result = {name: self.references[name][location]}
            for name, child_index in valid_children.items():
                result[name] = self.references[name][child_index]
        else:
            result = [self.references[name].get_item(location, dict_=False)]
            for name, child_index in valid_children.items():
                result.append(self.references[name].get_item(child_index, dict_=False))
            result = tuple(result)

        return result

    def set_linked_data(self, name, location, item, children=None):
        if isinstance(location, str):
            location = uuid.UUID(location)
        if isinstance(location, uuid.UUID):
            id_ = location
            main_index = self.get_index(name, location)
        else:
            id_ = self.get_id(name, location)
            main_index = location

        child_indices = self.get_indices(id_, children)
        valid_children = {}
        if children:
            for child in children:
                valid_children[child] = child_indices[child]
        else:
            valid_children = child_indices
        if name in valid_children:
            valid_children.pop(name)

        data = item.copy()
        self.references[name].set_item(data, main_index, pop=True)
        for child_name, child_index in valid_children.items():
            self.references[child_name].set_item(data, child_index, pop=True)

        return data

    def append_linked_data(self, name, item, children=None, axis=0):
        datasets = {name} | set(children)
        location = self.new_link(datasets, axis=axis)
        self.set_linked_data(name, location, item, children)


class HDF5hierarchicalDatasets(object):
    # Instantiation, Copy, Destruction
    def __init__(self, h5_container=None, dataset=None, name="", child_name="", link_name="", init=True, **kwargs):
        self.h5_container = None

        self.parent_name = None
        self.parent_dtype = None
        self.parent_dataset = None
        self.parent_link_name = None
        self.child_datasets = bidict()
        self.dataset_links = HDF5linkedDatasets()

        self.child_name_field = None

        if init:
            self.construct(h5_container, dataset, name, child_name, link_name, **kwargs)

    # Container Magic Methods
    def __getitem__(self, item):
        return self.get_item(item)

    # Generic Methods #
    # Constructors Methods
    def construct(self, h5_container, dataset=None, name="", child_name="", link_name="", **kwargs):
        self.h5_container = h5_container
        self.child_name_field = child_name
        if dataset:
            self.set_parent_dataset(name=name, dataset=dataset, link_name=link_name)
        else:
            self.create_parent_dataset(name=name, link_name=link_name, **kwargs)

    # Dataset Getter and Setters
    def create_parent_dataset(self, name, link_name, **kwargs):
        if self.parent_name is not None:
            self.dataset_links.pop_dataset(self.parent_name)
        self.parent_name = name
        self.parent_dataset = self.h5_container.set_dataset(name=name, **kwargs)
        self.parent_dtype = self.parent_dataset.dtype.descr
        self.parent_link_name = link_name
        self.dataset_links.add_datset(name, self.parent_dataset, link_name)

    def set_parent_dataset(self, name, dataset, link_name):
        if self.parent_name is not None:
            self.dataset_links.pop_dataset(self.parent_name)
        self.parent_name = name
        self.parent_dataset = dataset
        self.parent_dtype = self.parent_dataset.dtype.descr
        self.parent_link_name = link_name
        self.dataset_links.add_datset(name, self.parent_dataset, link_name)
        self.load_parent_dataset()

    def remove_parent_dataset(self):
        self.dataset_links.pop_dataset(self.parent_name)
        self.parent_name = None
        self.parent_dtype = None
        self.parent_link_name = None

    def create_child_dataset(self, name, link_name=None, **kwargs):
        if link_name is None:
            link_name = self.parent_link_name
        dataset = self.h5_container.set_dataset(name=name, **kwargs)
        self.dataset_links.add_datset(name, dataset, link_name)
        self.child_datasets[name] = dataset

    def add_child_dataset(self, name, dataset, link_name=None):
        if link_name is None:
            link_name = self.parent_link_name
        self.dataset_links.add_datset(name, dataset, link_name)
        self.child_datasets[name] = dataset

    def clear_child_datasets(self):
        for child in self.child_datasets:
            self.dataset_links.pop_dataset(child)
        self.child_datasets.clear()

    def remove_child_dataset(self, name):
        self.dataset_links.pop_dataset(name)
        self.child_datasets.pop(name)

    # Parent Dataset
    def load_parent_dataset(self):
        self.clear_child_datasets()

        array = self.parent_dataset[self.child_name_field]

        if array.size > 0:
            for child in array.flatten().tolist():
                if child not in self.child_datasets:
                    self.add_child_dataset(child, self.h5_container[child])

    # Item Getter and Setters
    def get_dataset(self, name, id_info=False):
        if name not in self.child_datasets and name != self.parent_name:
            raise KeyError("Not an event type")
        data = self.parent_dataset
        child_names = data[self.child_name_field]
        if name != self.parent_name:
            data = data[child_names == name]
            child_names = data[self.child_name_field]
        else:
            data = data[child_names != name]
            child_names = data[self.child_name_field]
        link_ids = data[self.parent_link_name]
        if isinstance(data, np.void):
            return self.get_data(link_ids, child_names, id_info)
        else:
            shape = data.shape

            loops = [range(0, x) for x in shape]

            return recursive_looping(loops, self.arrays_to_items, names=child_names, ids=link_ids, id_info=id_info)

    def get_item(self, index, name=None, id_info=False):
        if name is None or name == self.parent_name:
            parent_index = index
            child_name = self.parent_dataset[parent_index][self.child_name_field]
        else:
            parent_index = self.dataset_links.get_linked_indices(name, index, self.parent_name)[self.parent_name]
            child_name = name
        return self.get_data(parent_index, child_name, id_info)

    def get_items(self, indices, id_info=False):
        data = self.parent_dataset[indices]
        child_names = data[self.child_name_field]
        link_ids = data[self.parent_link_name]
        if isinstance(data, np.void):
            return self.get_data(link_ids, child_names, id_info)
        else:
            shape = data.shape

            loops = [range(0, x) for x in shape]

            return recursive_looping(loops, self.arrays_to_items, names=child_names, ids=link_ids, id_info=id_info)

    def arrays_to_items(self, items, names, ids, id_info=False):
        child_name = names[items]
        if isinstance(child_name, np.ndarray):
            child_name = child_name.tolist()[0]
        parent_id = ids[items]
        if isinstance(parent_id, np.ndarray):
            parent_id = parent_id.tolist()[0]
        return self.get_data(parent_id, child_name, id_info)

    def get_data(self, parent_ref, child_name, id_info=False):
        parent_link = self.dataset_links.references[self.parent_name].reference_field
        child_link = self.dataset_links.references[child_name].reference_field

        data = self.dataset_links.get_linked_data(self.parent_name, parent_ref, child_name)

        parent = data[self.parent_name]
        child = data[child_name]
        result = merge_dict(parent, child)

        if not id_info:
            if parent_link in result:
                result.pop(parent_link)
            if child_link in result:
                result.pop(child_link)

        return result

    def add_item(self, item, index):
        parent_item = []
        for dtype in self.parent_dtype:
            field = dtype[0]
            parent_item.append(item.pop(field))

        self.parent_dataset[index] = tuple(parent_item)

    def append_item(self, item, children=None, axis=0):
        if isinstance(children, collections.abc.Mapping):
            children_names = children.keys()
            for child, kwargs in children.items():
                if child not in self.child_datasets:
                    self.create_child_dataset(child, **kwargs)
        elif isinstance(children, str):
            children_names = (children,)
        else:
            children_names = children

        self.dataset_links.append_linked_data(self.parent_name, item, children_names, axis=axis)


class HDF5eventLogger(HDF5container):
    FILE_TYPE = "EventLog"
    VERSION = "0.0.1"
    EVENT_FIELDS = bidict(Time=0, DeltaTime=1, StartTime=2, Type=3)
    TIME_NAME = "Time"
    DELTA_NAME = "DeltaTime"
    START_NAME = "StartTime"
    TYPE_NAME = "Type"
    LINK_NAME = "LinkID"
    EVENT_DTYPE = np.dtype([(TIME_NAME, np.float),
                            (DELTA_NAME, np.float),
                            (START_NAME, np.float),
                            (TYPE_NAME, h5py.string_dtype(encoding="utf-8")),
                            (LINK_NAME, h5py.string_dtype(encoding="utf-8"))])

    # Instantiation/Destruction
    def __init__(self, path=None, io_trigger=None, init=False):
        super().__init__(path=path)

        self.default_child_kwargs = {}
        self.start_datetime = None
        self.start_time_counter = None
        self.start_time_offset = None
        self.hierarchy = None
        if io_trigger is None:
            self.io_trigger = AudioTrigger()
        else:
            self.io_trigger = io_trigger

        if init:
            self.construct()

    @property
    def event_types(self):
        out = set(self.hierarchy.child_datasets.keys())
        out.add(self.hierarchy.parent_name)
        return out

    # Container Magic Methods
    def __len__(self):
        return self.Events.len()

    def __getitem__(self, item):
        if isinstance(item, str):
            return super().__getitem__(item)
        elif isinstance(item, int) or isinstance(item, slice):
            return self.get_item((item, 0))
        else:
            return self.get_item(item)

    # Representations
    def __repr__(self):
        return repr(self.start_datetime)

    # Constructors
    def construct(self, open_=False, **kwargs):
        super().construct(open_=open_, **kwargs)
        self.hierarchy = HDF5hierarchicalDatasets(h5_container=self, dataset=self.Events, name="Events",
                                                  child_name=self.TYPE_NAME, link_name=self.LINK_NAME)

    def create_file(self, open_=False):
        super().create_file(open_=open_)
        self.create_event_dataset(name="Events", dtype=self.EVENT_DTYPE)

    # Datasets
    def create_event_dataset(self, name, dtype=None, data=None, **kwargs):
        if data is not None:
            m = data.shape[0]
            n = data.shape[1]
        else:
            m = 0
            n = 1
        defaults = {"shape": (m, n), "dtype": dtype, "maxshape": (None, n)}
        args = merge_dict(defaults, kwargs)
        return self.create_dataset(name=name, data=data, **args)

    # Sequence Methods
    def get_item(self, item):
        return self.hierarchy.get_items(item)

    def append(self, type_, **kwargs):
        if isinstance(type_, dict):
            self.append_event(type_)
        else:
            event = self.create_event(type_=type_, **kwargs)
            self.append_event(event)

    def insert(self, i, type_, **kwargs):
        if isinstance(type_, dict):
            super().insert(i, type_)
        else:
            event = self.create_event(type_=type_, **kwargs)
            super().insert(i, event)

    def clear(self):
        self.start_datetime = None
        self.start_time_counter = None
        self._path = None
        super().clear()

    # User Event Methods
    def create_event(self,  type_, **kwargs):
        seconds = self.start_time_offset + round(time.perf_counter() - self.start_time_counter, 6)
        now = self.start_datetime + datetime.timedelta(seconds=seconds)
        return {"Time": now, "DeltaTime": seconds, "StartTime": self.start_datetime, self.TYPE_NAME: type_, **kwargs}

    def append_event(self, event, axis=0, child_kwargs=None):
        child_name = event[self.TYPE_NAME]
        if child_name not in self.hierarchy.child_datasets:
            child_event = event.copy()
            for field in self.EVENT_FIELDS.keys():
                if field in child_event:
                    child_event.pop(field)
            if self.LINK_NAME not in child_event:
                child_event[self.LINK_NAME] = str(uuid.uuid4())
            child_dtype = self.event2dtype(child_event)
            if child_kwargs is None:
                child_kwargs = self.default_child_kwargs
            child_dataset = self.create_event_dataset(child_name, dtype=child_dtype, **child_kwargs)
            self.hierarchy.add_child_dataset(child_name, child_dataset)
        self.hierarchy.append_item(event, (child_name,), axis)

    def set_time(self):
        self.start_datetime = datetime.datetime.now()
        self.start_time_counter = time.perf_counter()
        self.start_time_offset = 0
        self.append({"Time": self.start_datetime, "DeltaTime": 0, "StartTime": self.start_datetime, self.TYPE_NAME: "TimeSet"})

    def resume_time(self, name=None, index=None):
        now_datatime = datetime.datetime.now()
        self.start_time_counter = time.perf_counter()
        if name is None:
            name = "TimeSet"
        if index is None:
            index = -1
        start_event = self.hierarchy.get_item(index, name)
        self.start_datetime = datetime.datetime.fromtimestamp(start_event[self.TIME_NAME])
        self.start_time_offset = (now_datatime - self.start_datetime).total_seconds()
        self.append({"Time": now_datatime, "DeltaTime": self.start_time_offset,
                     "StartTime": self.start_datetime, self.TYPE_NAME: "ResumeTime"})

    def get_event_type(self, name, id_info=False):
        return self.hierarchy.get_dataset(name, id_info)

    # Event Querying
    def find_event(self, time_, type_=None, bisect_="bisect"):
        if isinstance(time_, datetime.datetime):
            time_stamp = time_.timestamp()
        else:
            time_stamp = time_

        if type_ is None or type_ == "Events":
            events = self
            times = self.Events[self.TIME_NAME]
        else:
            events = self.hierarchy.get_dataset(name=type_)
            times = [e[self.TIME_NAME] for e in events]

        index = bisect.bisect_left(times, time_stamp)
        if index >= len(times):
            index -= 1
        elif times[index] == time_:
            pass
        elif bisect_ == "bisect":
            if index > 0:
                index -= 1 - (np.abs(times[index-1:index+1]-time_)).argmin()
        elif bisect_ == "left":
            if index > 0:
                index -= 1
        elif bisect_ == "right":
            pass
        else:
            return -1, None

        return index, events[index]

    def find_event_range(self, start, end, type_=None):
        if type_ is None or type_ == "Events":
            events = self
        else:
            events = self.hierarchy.get_dataset(name=type_)

        first, _ = self.find_event(start, type_=type_, bisect_="right")
        last, _ = self.find_event(end, type_=type_, bisect_="left")

        return range(first, last+1), events[first:last+1]

    # Trigger Methods
    def trigger(self):
        self.io_trigger.trigger()

    def trigger_event(self, **kwargs):
        self.trigger()
        self.append(type_="Trigger", **kwargs)

    # Static Methods
    @staticmethod
    def event2dtype(event):
        dtypes = []
        for key, value in event.items():
            if isinstance(value, int):
                dtype = np.int
            elif isinstance(value, float):
                dtype = np.float
            elif isinstance(value, datetime.datetime):
                dtype = np.float
            else:
                dtype = h5py.string_dtype(encoding="utf-8")

            dtypes.append((key, dtype))
        return dtypes


class SubjectEventLogger(HDF5eventLogger):
    FILE_TYPE = "SubjectEventLog"
    VERSION = "0.0.1"
    SUBJECT_NAME = "Subject"
    EXPERIMENT_NAME = "Task"
    EXPERIMENT_NUMBER = "Block"

    # Instantiation/Destruction
    def __init__(self, path=None, subject="", x_name="", x_number="", io_trigger=None, init=False):
        super().__init__(path, io_trigger)
        self._subject = subject
        self._experiment_name = x_name
        self._experiment_number = x_number

        if init:
            self.construct()

    # Constructors
    def construct(self, open_=False, **kwargs):
        super().construct(open_=open_, **kwargs)

    def create_file(self, open_=False):
        super().create_file(open_=open_)
        self.add_file_attributes({self.SUBJECT_NAME: self._subject, self.EXPERIMENT_NAME: self._experiment_name,
                                  self.EXPERIMENT_NUMBER: self._experiment_number})


# Functions #
def merge_dict(dict1, dict2, copy_=True):
    if dict2 is not None:
        if copy_:
            dict1 = dict1.copy()
        for key, value in dict2.items():
            dict1[key] = value
    return dict1


def np_to_dict(array):
    result = {}
    for t in array.dtype.descr:
        name = t[0]
        result[name] = array[name]
    return result


def dict_to_np(item, descr, pop=False):
    array = []
    for dtype in descr:
        field = dtype[0]
        if pop:
            data = item.pop(field)
        else:
            data = item[field]
        data = item_to_np(data)
        array.append(data)
    return array


def item_to_np(item):
    if isinstance(item, int) or isinstance(item, float) or isinstance(item, str):
        return item
    elif isinstance(item, datetime.datetime):
        return item.timestamp()
    elif isinstance(item, datetime.timedelta):
        return item.total_seconds()
    elif isinstance(item, uuid.UUID):
        return str(item)
    else:
        return item


def recursive_looping(loops, func, previous=None, size=None, **kwargs):
    if previous is None:
        previous = []
    if size is None:
        size = len(loops)
    output = []
    loop = loops.pop(0)
    previous.append(None)
    for item in loop:
        previous[-1] = item
        if len(previous) == size:
            output.append(func(items=previous, **kwargs))
        else:
            output.append(recursive_looping(loops, func, previous=previous, size=size, **kwargs))
    return output


if __name__ == "__main__":
    test_path = pathlib.Path(__file__).joinpath("ECwork_B0w0_2020-01-16_11~58~09.h5")
    path = pathlib.Path.cwd().joinpath("test.h5")
    '''
    meth = SubjectEventLogger(test_path)
    with meth:
        meth.file_attrs
        print(meth.Subject)

    '''
    debug = SubjectEventLogger(path, subject="ECtest")
    with debug:
        debug.set_time()
        debug.append(**{"type_": "ThisChild", "1stField": 0})
        debug.resume_time(index=0)
        debug.append(**{"type_": "ThisChild", "1stField": 1})
        debug.get_event_type("ThisChild")
        debug.find_event(1579041281.5, type_="ThisChild")
        i, f = debug.find_event_range(1579041281.5, datetime.datetime.now(), "ThisChild")
        print(debug[0])

    reload = SubjectEventLogger(path)
    with reload:
        reload.get_event_type("ThisChild")
