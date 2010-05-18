"""The freesurfer module provides basic functions for interfacing with
freesurfer tools.

Currently these tools are supported:

     * Dicom2Nifti: using mri_convert
     * Resample: using mri_convert
     
Examples
--------
See the docstrings for the individual classes for 'working' examples.

"""
__docformat__ = 'restructuredtext'

import os
from glob import glob

import numpy as np

from nipype.utils.filemanip import FileNotFoundError, fname_presuffix
from nipype.interfaces.base import NEW_CommandLine, traits, TraitedSpec,\
    Directory, CommandLineInputSpec
from nipype.utils.misc import isdefined

class Info(object):
    """Handle freesurfer subject directory and version information.
    """
    
    @staticmethod
    def version():
        """Check for freesurfer version on system
    
        Parameters
        ----------
        
        None
    
        Returns
        -------
        
        version : string
           version number as string 
           or None if freesurfer version not found
    
        """
        # find which freesurfer is being used....and get version from
        # /path/to/freesurfer/
        fs_home = os.getenv('FREESURFER_HOME')
        if fs_home is None:
            return fs_home
        versionfile = os.path.join(fs_home,'build-stamp.txt')
        if not os.path.exists(versionfile):
            return None
        fid = open(versionfile,'rt')
        version = fid.readline()
        fid.close()
        return version #.split('-v')[1].strip('\n')
    
    @classmethod
    def subjectsdir(cls):
        """Check and or set the global SUBJECTS_DIR
        
        Parameters
        ----------
        
        subjects_dir :  string
            The system defined subjects directory
    
        Returns
        -------
        
        subject_dir : string
            Represents the current environment setting of SUBJECTS_DIR
    
        """
        if cls.version():
            return os.environ['SUBJECTS_DIR']
        return None


class FSTraitedSpec(CommandLineInputSpec):
    subjectsdir =  Directory(exists=True, desc='subjects directory')
    
class FSCommand(NEW_CommandLine):
    '''General support for FS commands. Every FS command accepts
    'subjectsdir' input. For example:
    '''
    
    input_spec = FSTraitedSpec
    
    _subjectsdir = None

    def __init__(self, **inputs):
        super(FSCommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._subjectsdir_update, 'subjectsdir')
        if not self._subjectsdir:
            self._subjectsdir = Info.subjectsdir()
        if not isdefined(self.inputs.subjectsdir) and self._subjectsdir:
            self.inputs.subjectsdir = self._subjectsdir
        self._subjectsdir_update()

    def _subjectsdir_update(self):
        if self.inputs.subjectsdir:
            self.inputs.environ.update({'SUBJECTS_DIR':
                                            self.inputs.subjectsdir})
    
    @classmethod
    def set_default_subjectsdir(cls, subjectsdir):
        cls._subjectsdir = subjectsdir

    def _gen_fname(self, basename, fname=None, cwd=None, suffix='_fs', use_ext=True):
        '''Define a generic mapping for a single outfile

        The filename is potentially autogenerated by suffixing inputs.infile

        Parameters
        ----------
        basename : string (required)
            filename to base the new filename on
        fname : string
            if not None, just use this fname
        cwd : string
            prefix paths with cwd, otherwise os.getcwd()
        suffix : string
            default suffix
        '''
        if basename == '':
            msg = 'Unable to generate filename for command %s. ' % self.cmd
            msg += 'basename is not set!'
            raise ValueError(msg)
        if cwd is None:
            cwd = os.getcwd()
        fname = fname_presuffix(basename, suffix=suffix,
                                use_ext=use_ext, newpath=cwd)
        return fname

