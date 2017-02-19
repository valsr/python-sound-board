"""
Created on Jan 19, 2017

@author: valsr <valsr@valsr.com>
"""
from com.valsr.psb.sound.waveform import Waveform


class WaveformManager:
    """Manages all waveform objects"""
    waveforms = {}

    @staticmethod
    def waveform(file):
        """Obtain waveform by filename

        Args:
            file: Path to file

        Returns:
            Waveform or None
        """
        if file in WaveformManager.waveforms:
            return WaveformManager.waveforms[file]

        return None

    @staticmethod
    def create_waveform(file_path):
        """Create a waveform for given file

        Args:
            file_path: File path

        Return:
            (file_path, waveform)
        """
        p = Waveform(file_path)
        WaveformManager.waveforms[file_path] = p
        return (file_path, p)

    @staticmethod
    def destroy_waveform(file):
        """Destroy given waveform.

        Args:
            file: Waveform file
        """
        WaveformManager.waveforms.pop(file, None)
