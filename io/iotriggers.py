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
import collections
from abc import ABC, abstractmethod
from warnings import warn
import warnings
import pathlib

# Downloaded Libraries #
from bidict import bidict

# Local Libraries #
from devices.audiodevice import AudioDevice


########## Definitions ##########

# Classes #
class IndexableDict(collections.OrderedDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __getitem__(self, item):
        if isinstance(item, slice):
            result = []
            for key in self.keys_slice_generator(item):
                result.append(self[key])
            return result
        elif isinstance(item, int):
            item = self.index_to_key(item)
        return super().__getitem__(item)

    def index_to_key(self, index):
        if index >= len(self):
            raise IndexError("dictionary index out of range")
        elif index < 0:
            index += len(self)
        for i, key in enumerate(self.keys()):
            if i == index:
                return key

    def keys_slice(self, iterable):
        result = []
        if isinstance(iterable, slice):
            iterable = list(range(*iterable.indices(len(self))))
        elif not isinstance(iterable, list):
            iterable = list(iterable)
        for i, key in enumerate(self.keys()):
            if i == iterable[0]:
                result.append(key)
                if len(iterable) <= 1:
                    break
                else:
                    iterable.pop()
        return result

    def keys_slice_generator(self, iterable):
        if isinstance(iterable, slice):
            iterable = range(*iterable.indices(len(self)))
        if isinstance(iterable, slice):
            iterable = list(range(*iterable.indices(len(self))))
        elif not isinstance(iterable, list):
            iterable = list(iterable)
        for i, key in enumerate(self.keys()):
            if i == iterable[0]:
                yield key
                if len(iterable) <= 1:
                    break
                else:
                    iterable.pop()

    def append(self, key, item):
        self[key] = item

    def list(self):
        return list(self)


class AudioTrigger:
    default_audio_device = AudioDevice()

    def __init__(self, audio_device=None, load_defaults=False):
        if audio_device is None:
            self.audio_device = self.default_audio_device
        else:
            self.audio_device = audio_device

        self.waveforms = IndexableDict()
        self.current_waveform = 0
        self.play_sequence = []

        if load_defaults:
            self.add_default_waveforms()

    def add_default_waveforms(self):
        self.add_square_wave(name='square_wave', sample_rate=44100, samples=100)

    def add_waveform(self, name, waveform, sample_rate=None):
        if isinstance(waveform, dict):
            self.waveforms[name] = waveform
        else:
            if sample_rate is None:
                sample_rate = self.audio_device.samplerate
            self.waveforms[name] = {'waveform': waveform, 'sample_rate': sample_rate}

    def add_square_wave(self, name, sample_rate=None, **kwargs):
        if sample_rate is None:
            sample_rate = self.audio_device.samplerate
        kwargs['sample_rate'] = sample_rate
        self.waveforms[name] = {'waveform': self.square_wave(**kwargs), 'sample_rate': sample_rate}

    def trigger(self, waveform=None, sample_rate=None):
        if waveform is None:
            waveform = self.waveforms[self.current_waveform]['waveform']
        elif isinstance(waveform, str) or isinstance(waveform, int):
            if sample_rate is None:
                sample_rate = self.waveforms[waveform]['sample_rate']
            waveform = self.waveforms[waveform]['waveform']
        if sample_rate is None:
            sample_rate = self.waveforms[self.current_waveform]['sample_rate']
        self.audio_device.play(waveform, sample_rate)

    @staticmethod
    def square_wave(amplitude=1, presamples=0, samples=10, postsamples=0,
                    preseconds=None, seconds=None, postseconds=None, sample_rate=None):
        if preseconds is not None and seconds is not None and postseconds is not None and sample_rate is not None:
            presamples = int(sample_rate * preseconds)
            samples = int(sample_rate * seconds)
            postsamples = int(sample_rate * postseconds)
        return [0.0] * presamples + [float(amplitude)] * samples + [0.0] * postsamples





