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
from warnings import warn
import warnings
import pathlib

# Downloaded Libraries #
import sounddevice

# Local Libraries #

########## Definitions ##########

# Classes #
class AudioDevice:
    _sd = sounddevice

    def __init__(self, samplerate=44100, device=None):
        self._device = self.default_device

        self.samplerate = samplerate

    @property
    def default_samplerate(self):
        return self._sd.default.device

    @property
    def default_device(self):
        return self._sd.default.device

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        try:
            self._sd.query_devices(value)
            self._device = value
        except Exception as e:
            warn('Could not set sound device due to error: '+str(e), stacklevel=2)

    def play(self, data, samplerate=None, mapping=None, blocking=False, loop=False, **kwargs):
        if samplerate is None:
            samplerate = self.samplerate
        self._sd.default.device = self._device
        self._sd.play(data, samplerate, mapping, blocking, loop, **kwargs)

    def stop(self, ignore_errors=None):
        self._sd.stop(ignore_errors)

    def wait(self, ignore_errors=None):
        self._sd.wait(ignore_errors)

