#!/usr/bin/env python

""" PP_RUN - wrapper for automated data analysis
    v1.0: 2016-02-10, michael.mommert@nau.edu
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

import re
import os
import gc
import sys
try:
    import numpy as np
except ImportError:
    print('Module numpy not found. Please install with: pip install numpy')
    sys.exit()
import shutil
import logging
import subprocess
import argparse, shlex
import time
try:
    from astropy.io import fits
except ImportError:
    print('Module astropy not found. Please install with: pip install astropy')
    sys.exit()
    
# only import if Python3 is used
if sys.version_info > (3,0):
    from builtins import str
    from builtins import range

### pipeline-specific modules
import _pp_conf
from catalog import *
import pp_prepare
import pp_extract
import pp_register
import pp_photometry
import pp_calibrate
import pp_distill
import diagnostics as diag

# setup logging
logging.basicConfig(filename = _pp_conf.log_filename,
                    level    = _pp_conf.log_level,
                    format   = _pp_conf.log_formatline,
                    datefmt  = _pp_conf.log_datefmt)


def run_the_pipeline(filenames, man_targetname, man_filtername,
                     fixed_aprad, source_tolerance):
    """
    wrapper to run the photometry pipeline
    """

    # increment pp process idx
    _pp_conf.pp_process_idx += 1

    # reset diagnostics for this data set
    _pp_conf.dataroot, _pp_conf.diagroot, \
    _pp_conf.index_filename, _pp_conf.reg_filename, _pp_conf.cal_filename, \
    _pp_conf.res_filename = _pp_conf.setup_diagnostics()

    # setup logging again (might be a different directory)
    logging.basicConfig(filename = _pp_conf.log_filename,
                        level    = _pp_conf.log_level,
                        format   = _pp_conf.log_formatline,
                        datefmt  = _pp_conf.log_datefmt)

    ### read telescope information from fits headers
    # check that they are the same for all images
    logging.info('##### new pipeline process in %s #####' % _pp_conf.dataroot)
    logging.info(('check for same telescope/instrument for %d ' + \
                  'frames') % len(filenames))
    instruments = []
    for idx, filename in enumerate(filenames):
        try:
            hdulist = fits.open(filename, ignore_missing_end=True)
        except IOError:
            logging.error('cannot open file %s' % filename)
            print('ERROR: cannot open file %s' % filename)
            filenames.pop(idx)
            continue

        header = hdulist[0].header
        for key in _pp_conf.instrument_keys:
            if key in header:
                instruments.append(header[key])
                break

    if len(filenames) == 0:
        raise IOError('cannot find any data...')

    if len(instruments) == 0:
        raise KeyError('cannot identify telescope/instrument; please update' + \
                       '_pp_conf.instrument_keys accordingly')


    # check if there is only one unique instrument
    if len(set(instruments)) > 1:
        print('ERROR: multiple instruments used in dataset: %s' % \
            str(set(instruemnts)))
        logging.error('multiple instruments used in dataset: %s' %
                      str(set(instruments)))
        for i in range(len(filenames)):
            logging.error('%s %s' % (filenames[i], instruments[i]))
        sys.exit()

    telescope = _pp_conf.instrument_identifiers[instruments[0]]
    obsparam = _pp_conf.telescope_parameters[telescope]
    logging.info('%d %s frames identified' % (len(filenames), telescope))


    ### read filter information from fits headers
    # check that they are the same for all images
    logging.info(('check for same filter for %d ' + \
                  'frames') % len(filenames))
    filters = []
    for idx, filename in enumerate(filenames):
        try:
            hdulist = fits.open(filename, ignore_missing_end=True)
        except IOError:
            logging.error('cannot open file %s' % filename)
            print('ERROR: cannot open file %s' % filename)
            filenames.pop(idx)
            continue

        header = hdulist[0].header
        filters.append(header[obsparam['filter']])

    if len(filters) == 0:
        raise KeyError('cannot identify filter; please update' + \
                       'setup/telescopes.py accordingly')

    if len(set(filters)) > 1:
        print('ERROR: multiple filters used in dataset: %s' % str(set(filters)))
        logging.error('multiple filters used in dataset: %s' %
                      str(set(filters)))
        for i in range(len(filenames)):
            logging.error('%s %s' % (filenames[i], filters[i]))
        sys.exit()

    if man_filtername is None:
        try:
            filtername = obsparam['filter_translations'][filters[0]]
        except KeyError:
            print(('Cannot translate filter name (%s); please adjust ' + \
                   'keyword "filter_translations" for %s in ' + \
                   'setup/telescopes.py') % (filters[0], telescope))
            logging.error(('Cannot translate filter name (%s); please adjust '+\
                   'keyword "filter_translations" for %s in ' + \
                   'setup/telescopes.py') % (filters[0], telescope))
            return None
    else:
        filtername = man_filtername
    logging.info('%d %s frames identified' % (len(filenames), filtername))

    print('run photometry pipeline on %d %s %s frames' % \
          (len(filenames), telescope, filtername))

    change_header = {}
    if man_targetname is not None:
        change_header['OBJECT'] = man_targetname

    ### prepare fits files for photometry pipeline
    preparation = pp_prepare.prepare(filenames, obsparam,
                                     change_header,
                                     diagnostics=True, display=True)


    ### run wcs registration

    # default sextractor/scamp parameters
    snr, source_minarea = obsparam['source_snr'], obsparam['source_minarea']
    aprad = obsparam['aprad_default']

    print('\n----- run image registration\n')
    registration = pp_register.register(filenames, telescope, snr,
                                        source_minarea, aprad,
                                        None, obsparam,
                                        obsparam['source_tolerance'],
                                        display=True,
                                        diagnostics=True)


    if len(registration['badfits']) == len(filenames):
        summary_message = "<FONT COLOR=\"red\">registration failed</FONT>"
    elif len(registration['goodfits']) == len(filenames):
        summary_message = "<FONT COLOR=\"green\">all images registered" + \
                           "</FONT>; "
    else:
        summary_message = "<FONT COLOR=\"orange\">registration failed for " + \
                           ("%d/%d images</FONT>; " %
                                (len(registration['badfits']),
                                 len(filenames)))

    # add information to summary website, if requested
    if _pp_conf.use_diagnostics_summary:
        diag.insert_into_summary(summary_message)



    # in case not all image were registered successfully
    filenames = registration['goodfits']

    # # stop here if filtername == None
    # if filtername == None:
    #     logging.info('Nothing else to do for this filter (%s)' %
    #                  filtername)
    #     print('Nothing else to do for this filter (%s)' % filtername)
    #     return None

    # stop here if registration failed for all images
    if len(filenames) == 0:
        logging.info('Nothing else to do for this image set')
        print('Nothing else to do for this image set')
        diag.abort('pp_registration')
        return None

    ### run photometry (curve-of-growth analysis)
    snr, source_minarea = 1.5, obsparam['source_minarea']
    background_only = False
    target_only = False
    if fixed_aprad == 0:
        aprad = None # force curve-of-growth analysis
    else:
        aprad = fixed_aprad # skip curve_of_growth analysis

    print('\n----- derive optimium photometry aperture\n')
    phot = pp_photometry.photometry(filenames, snr, source_minarea, aprad,
                                    man_targetname, background_only,
                                    target_only,
                                    telescope, obsparam, display=True,
                                    diagnostics=True)

    # data went through curve-of-growth analysis
    if phot is not None:
        summary_message = ("<FONT COLOR=\"green\">aprad = %5.1f px, " + \
                           "</FONT>") % phot['optimum_aprad']
        if phot['n_target'] > 0:
            summary_message += "<FONT COLOR=\"green\">based on target and " + \
                               "background</FONT>; "
        else:
            summary_message += "<FONT COLOR=\"orange\">based on background " + \
                               "only </FONT>; "
    # a fixed aperture radius has been used
    else:
        summary_message += "using a fixed aperture radius of %.1f px;" % aprad


    # add information to summary website, if requested
    if _pp_conf.use_diagnostics_summary:
        diag.insert_into_summary(summary_message)



    ### run photometric calibration
    minstars = _pp_conf.minstars
    manualcatalog = None

    print('\n----- run photometric calibration\n')

    calibration = pp_calibrate.calibrate(filenames, minstars, filtername,
                                         manualcatalog, obsparam, display=True,
                                         diagnostics=True)

    # if calibration == None:
    #     print('Nothing to do!')
    #     logging.error('Nothing to do! Error in pp_calibrate')
    #     diag.abort('pp_calibrate')
    #     sys.exit(1)

    try:
        zps = [frame['zp'] for frame in calibration['zeropoints']]
        zp_errs = [frame['zp_sig'] for frame in calibration['zeropoints']]

        if calibration['ref_cat'] is not None:
            refcatname = calibration['ref_cat'].catalogname
        else:
            refcatname = 'instrumental magnitudes'
        summary_message = "<FONT COLOR=\"green\">average zeropoint = " + \
                           ("%5.2f+-%5.2f using %s</FONT>; " %
                            (numpy.average(zps),
                             numpy.average(zp_errs),
                             refcatname))
    except TypeError:
        summary_message = "<FONT COLOR=\"red\">no phot. calibration</FONT>; "

    # add information to summary website, if requested
    if _pp_conf.use_diagnostics_summary:
        diag.insert_into_summary(summary_message)


    ### distill photometry results
    print('\n----- distill photometry results\n')
    distillate = pp_distill.distill(calibration['catalogs'],
                                    man_targetname, [0,0],
                                    None, None,
                                    display=True, diagnostics=True)

    targets = numpy.array(list(distillate['targetnames'].keys()))
    try:
        target = targets[targets != 'control_star'][0]
        mags = [frame[7] for frame in distillate[target]]
        summary_message = ("average target brightness and std: " +
                           "%5.2f+-%5.2f\n" % (numpy.average(mags),
                                               numpy.std(mags)))
    except IndexError:
        summary_message = "no primary target extracted"


    # add information to summary website, if requested
    if _pp_conf.use_diagnostics_summary:
        diag.insert_into_summary(summary_message)

    print('\nDone!\n')
    logging.info('----- successfully done with this process ----')

    gc.collect() # collect garbage; just in case, you never know...


if __name__ == '__main__':

    # command line arguments
    parser = argparse.ArgumentParser(description='automated WCS registration')
    parser.add_argument('-prefix', help='data prefix',
                        default=None)
    parser.add_argument('-target', help='primary targetname override',
                        default=None)
    parser.add_argument('-filter', help='filter name override',
                        default=None)
    parser.add_argument('-fixed_aprad', help='fixed aperture radius (px)',
                        default=0)
    parser.add_argument('-source_tolerance',
                        help='tolerance on source properties for registration',
                        choices=['none', 'low', 'medium', 'high'],
                        default='high')
    parser.add_argument('images', help='images to process or \'all\'',
                        nargs='+')

    args = parser.parse_args()
    prefix = args.prefix
    man_targetname = args.target
    man_filtername = args.filter
    fixed_aprad = float(args.fixed_aprad)
    source_tolerance = args.source_tolerance
    filenames = args.images


    ##### if filenames = ['all'], walk through directories and run pipeline
    # each dataset
    _masterroot_directory = os.getcwd()


    if len(filenames) == 1 and filenames[0]=='all':

        # dump data set information into summary file
        _pp_conf.use_diagnostics_summary = True
        diag.create_summary()

        # turn prefix and fits suffixes into regular expression
        if prefix is None:
            prefix = ''
        regex = re.compile('^'+prefix+'.*[fits|FITS|fit|FIT|Fits|fts|FTS]$')

        # walk through directories underneath
        for root, dirs, files in os.walk(_masterroot_directory):

            # ignore .diagnostics directories
            if '.diagnostics' in root:
                continue
            
            # identify data frames
            filenames = sorted([s for s in files if re.match(regex, s)])

            # call run_the_pipeline for each directory separately
            if len(filenames) > 0:
                print('\n RUN PIPELINE IN %s' % root)
                os.chdir(root)

                run_the_pipeline(filenames, man_targetname, man_filtername,
                                 fixed_aprad, source_tolerance)
                os.chdir(_masterroot_directory)
            else:
                print('\n NOTHING TO DO IN %s' % root)


    else:
        # call run_the_pipeline only on filenames
        run_the_pipeline(filenames, man_targetname, man_filtername,
                         fixed_aprad, source_tolerance)
        pass






