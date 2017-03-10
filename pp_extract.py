#!/usr/bin/env python

""" PP_EXTRACT - identify field sources using Source Extractor with
    multi-threading capabilities
    v1.0: 2015-12-30, michael.mommert@nau.edu
"""
from __future__ import print_function

# Photometry Pipeline
# Copyright (C) 2016  Michael Mommert, michael.mommert@nau.edu

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.


import numpy
import os, sys
import subprocess
import logging
import argparse, shlex
import time, datetime
import queue, threading
import logging
from astropy.io import fits

# only import if Python3 is used
if sys.version_info > (3,0):
    from builtins import str
    from future import standard_library
    standard_library.install_aliases()
    from builtins import range

# create a portable DEVNULL
# necessary to prevent subprocess.PIPE and STDOUT from clogging if
# Source Extractor runs for too long 
try:
    from subprocess import DEVNULL # Py3
except ImportError:
    import os # Py2
    DEVNULL = open(os.devnull, 'wb')


# pipeline-specific modules
import _pp_conf
from catalog import *
from toolbox import *

# setup logging
logging.basicConfig(filename = _pp_conf.log_filename,
                    level    = _pp_conf.log_level,
                    format   = _pp_conf.log_formatline,
                    datefmt  = _pp_conf.log_datefmt)

########## some definitions

version = '1.0'

# threading definitions
nThreads = 10
extractQueue = queue.Queue(2000)
threadLock = threading.Lock()


# Determine the Source Extractor executable name: sex or sextractor.
for cmd in ['sex', 'sextractor']:
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        del p
        break
    except OSError:
        continue
else:
    raise FileNotFoundError('Source Extractor command not found.')
sextractor_cmd = cmd
del cmd

##### extractor class definition

class extractor(threading.Thread):
    """
    call Source Extractor using threading
    """
    def __init__(self, par, output):
        self.param      = par
        self.output     = output
        threading.Thread.__init__(self)
    def run(self):
        while True:
            try:
                filename = extractQueue.get(True,1)
            except:
                break           # No more jobs in the queue

            # add output dictionary
            out = {}
            threadLock.acquire()
            self.output.append(out)
            threadLock.release()


            ### process this frame
            ldacname = filename[:filename.find('.fit')]+'.ldac'
            out['fits_filename'] = filename
            out['ldac_filename'] = ldacname
            out['parameters']    = self.param


            # prepare running SEXTRACTOR
            threadLock.acquire()
            os.remove(ldacname) if os.path.exists(ldacname) else None
            threadLock.release()
            optionstring  = ' -PHOT_APERTURES %s ' % \
                            self.param['aperture_diam']
            if ('global_background' in self.param and 
                self.param['global_background']):
                optionstring += ' -BACKPHOTO_TYPE GLOBAL '
            else:
                optionstring += ' -BACKPHOTO_TYPE LOCAL '
            optionstring += ' -DETECT_MINAREA %f ' % \
                            self.param['source_minarea']
            optionstring += ' -DETECT_THRESH %f -ANALYSIS_THRESH %f ' % \
                        (self.param['sex_snr'], self.param['sex_snr'])
            optionstring += ' -CATALOG_NAME %s ' % ldacname

            if 'mask_file' in self.param:
                optionstring += ' -WEIGHT_TYPE MAP_WEIGHT'
                optionstring += ' -WEIGHT_IMAGE %s' %\
                                self.param['mask_file']

            if 'paramfile' in self.param:
                optionstring += ' -PARAMETERS_NAME %s' % \
                                self.param['paramfile']

            if 'ignore_saturation' in self.param:
                if self.param['ignore_saturation']:
                    optionstring += ' -SATUR_LEVEL 1000000'
                    optionstring += ' -SATUR_KEY NOPE'

            commandline = '%s -c %s %s %s' % \
                          (sextractor_cmd,
                           self.param['obsparam']['sex-config-file'],
                           optionstring, filename)

            logging.info('call Source Extractor as: %s' % commandline)


            ### run SEXTRACTOR and wait for it to finish
            try:
                sex = subprocess.Popen(shlex.split(commandline),
                                       stdout=DEVNULL,
                                       stderr=DEVNULL,
                                       close_fds=True)
                # do not direct stdout to subprocess.PIPE:
                # for large FITS files, PIPE will clog, stalling 
                # subprocess.Popen
            except Exception as e:
                print('Source Extractor call:', (e))
                logging.error('Source Extractor call:', (e))
                extractQueue.task_done() # inform queue, this task is done
                return None

            sex.wait()

            # # check output for error messages from Source Extractor
            # try:
            #     sex_output = sex.communicate()[1]
            #     if 'not found, using internal defaults' in sex_output:
            #         if not self.param['quiet']:
            #             print(('ERROR: no Source Extractor setup file ' +
            #                    'available (should be in %s)') % \
            #                 self.param['obsparam']['sex-config-file'])
            #             logging.error(('ERROR: no Source Extractor setup file'+
            #                            ' available (should be in %s)') % \
            #             self.param['obsparam']['sex-config-file'])

            #         extractQueue.task_done() # inform queue, this task is done
            #         return None
            # except ValueError:
            #     logging.warning("Cannot read Source Extractor display output")
            #     pass

            del sex

            # read in LDAC file
            ldac_filename = filename[:filename.find('.fit')]+'.ldac'
            ldac_data = catalog(ldac_filename)

            if not os.path.exists(ldac_filename):
                threadLock.acquire()
                print('No Source Extractor output for frame', filename, \
                    '\nplease check output:\n', sex_output)
                logging.error('No Source Extractor output, ' +
                              'please check output:' + sex_output)
                threadLock.release()
                extractQueue.task_done() # inform queue, this task is done
                return None


            # make sure ldac file contains data
            if ldac_data.read_ldac(ldac_filename, maxflag=None) is None:
                extractQueue.task_done()
                print('LDAC file empty', filename, end=' ')
                logging.error('LDAC file empty: ' + sex_output)
                return None

            out['catalog_data'] = ldac_data

            ### update image header with aperture radius and other information
            hdu = fits.open(filename, mode='update', ignore_missing_end=True)
            obsparam = self.param['obsparam']
            # observation midtime
            if obsparam['obsmidtime_jd'] in hdu[0].header:
                midtimjd = hdu[0].header[obsparam['obsmidtime_jd']]
            else:
                if obsparam['date_keyword'].find('|') == -1:
                    midtimjd = dateobs_to_jd(\
                        hdu[0].header[obsparam['date_keyword']]) + \
                        float(hdu[0].header[obsparam['exptime']])/2./86400.
                else:
                    datetime = hdu[0].header[\
                                    obsparam['date_keyword'].split('|')[0]]+ \
                        'T'+hdu[0].header[\
                                    obsparam['date_keyword'].split('|')[1]]
                    midtimjd = dateobs_to_jd(datetime) + \
                               float(hdu[0].header[\
                                            obsparam['exptime']])/2./86400.
            out['time'] = midtimjd

            # hdu[0].header['APRAD'] = \
            #     (",".join([str(aprad) for aprad in self.param['aprad']]), \
            #      'aperture phot radius (px)')
            # hdu[0].header['SEXSNR'] = \
            #     (self.param['sex_snr'],
            #      'Sextractor detection SNR threshold')
            # hdu[0].header['SEXAREA'] = \
            #     (self.param['source_minarea'],
            #      'Sextractor source area threshold (px)')
            out['fits_header'] = hdu[0].header

            hdu.flush()
            hdu.close()

            threadLock.acquire()
            logging.info("%d sources extracted from frame %s" % \
                         (len(ldac_data.data), filename))
            if not self.param['quiet']:
                print("%d sources extracted from frame %s" % \
                    (len(ldac_data.data), filename))
            threadLock.release()

            del ldac_data

            extractQueue.task_done()  # inform queue that this task is done


def extract_multiframe(filenames, parameters):
    """
    wrapper to run multi-threaded source extraction
    input: FITS filenames, parameters dictionary: telescope, obsparam, aprad,
                                                  quiet, sex_snr, source_minarea
    output: result properties
    """

    logging.info('extract sources from %d files using Source Extractor' % \
                 len(filenames))
    logging.info('extraction parameters: %s' % repr(parameters))


    # obtain telescope information from image header or override manually
    hdu = fits.open(filenames[0], ignore_missing_end=True, verify='silentfix')

    if 'telescope' not in parameters or parameters['telescope'] is None:
        try:
            parameters['telescope'] = hdu[0].header['TEL_KEYW']
        except KeyError:
            logging.critical('ERROR: TEL_KEYW not in image header (%s)' %
                             filenames[0])
            print('ERROR: TEL_KEYW not in image header;' + \
                  'has this image run through register?')
            return {}
    try:
        parameters['obsparam'] = _pp_conf.telescope_parameters[\
                                                parameters['telescope']]
    except KeyError:
        print("ERROR: telescope '%s' is unknown." % telescope)
        logging.critical('ERROR: telescope \'%s\' is unknown.' % telescope)
        return {}

    # set aperture photometry DIAMETER as string
    if ((type(parameters['aprad']) == float and parameters['aprad'] == 0)
        or (type(parameters['aprad']) == list
            and len(parameters['aprad']) == 0)):
        parameters['aperture_diam'] = str(parameters['obsparam']
                                          ['aprad_default']*2)
    else:
        if not isinstance(parameters['aprad'], list) and \
           not isinstance(parameters['aprad'], numpy.ndarray):
            parameters['aprad'] = [str(parameters['aprad'])]
        parameters['aperture_diam'] = ','.join([str(float(rad)*2.) for
                                                rad in parameters['aprad']])


    #check what the binning is and if there is a mask available
    binning = get_binning(hdu[0].header, parameters['obsparam'])
    bin_string = '%d,%d' % (binning[0], binning[1])

    if bin_string in parameters['obsparam']['mask_file']:
        mask_file = parameters['obsparam']['mask_file'][bin_string]
        parameters['mask_file'] = mask_file

    hdu.close()

    ### thread and queue handling

    output = []

    # populate the queue with frame filenames
    for filename in filenames:
        while True:
            if extractQueue.full():
                time.sleep(0.5)
            else:
                break
        extractQueue.put(filename, block=True)

    # spawning threads
    # never spawn more threads than there are items in the queue!
    for thread in range(min([nThreads, len(filenames)])):
        extractor(parameters, output).start()

    # waiting for threads to finish
    threadLock.acquire()
    threadLock.release()
    extractQueue.join()

    # check if extraction was successful
    if any(['catalog_data' not in list(output[i].keys())
            for i in range(len(output))]):
        return None


    ### output content
    #
    # { 'fits_filename': fits filename,
    #   'ldac_filename': LDAC filename,
    #   'parameters'   : source extractor input parameters,
    #   'catalog_data' : full LDAC catalog data,
    #   'time'         : observation midtime (JD),
    #   'fits_header'  : complete fits header
    # }
    ###

    return output


############ MAIN

if __name__ == '__main__':

    # define command line arguments
    parser = argparse.ArgumentParser(description='source detection and' + \
                                     'photometry using Source Extractor')
    parser.add_argument("-snr", help='sextractor SNR threshold', default=1.5)
    parser.add_argument("-minarea", help='sextractor source area threshold',
                        default=3)
    parser.add_argument("-paramfile",
                        help='alternative sextractor parameter file',
                        default=None)
    parser.add_argument("-aprad",
                        help='aperture radius (list) for photometry (px)',
                        default=0)
    parser.add_argument("-telescope", help='manual telescope override',
                        default=None)
    parser.add_argument('-ignore_saturation', help='keep saturated sources',
                        action="store_true")
    parser.add_argument('-quiet', help='no logging',
                        action="store_true")
    parser.add_argument('images', help='images to process', nargs='+')

    args = parser.parse_args()
    sex_snr = float(args.snr)
    source_minarea = float(args.minarea)
    paramfile = args.paramfile
    aprad = args.aprad
    telescope = args.telescope
    ignore_saturation = args.ignore_saturation
    quiet = args.quiet
    filenames = args.images

    # prepare parameter dictionary
    parameters = {'sex_snr':sex_snr, 'source_minarea':source_minarea, \
                  'aprad':aprad, 'telescope':telescope,
                  'ignore_saturation':ignore_saturation, 'quiet':quiet}

    if paramfile is not None:
        parameters['paramfile'] = paramfile

    ### call extraction wrapper
    extraction = extract_multiframe(filenames, parameters)

