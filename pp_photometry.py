#!/usr/bin/env python3

""" PP_PHOTOMETRY - run curve-of-growth analysis on image files,
                    identify optimum aperture radius, and redo photometry

    v1.0: 2015-12-30, mommermiscience@gmail.com
"""
# Photometry Pipeline
# Copyright (C) 2016-2018  Michael Mommert, mommermiscience@gmail.com

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
import os
import sys
import logging
import argparse
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
from astroquery.jplhorizons import Horizons

# only import if Python3 is used
if sys.version_info > (3, 0):
    from builtins import str
    from builtins import range

# pipeline-specific modules
import _pp_conf
import pp_extract
from catalog import *
from toolbox import *
from diagnostics import photometry as diag

# setup logging
logging.basicConfig(filename=_pp_conf.log_filename,
                    level=_pp_conf.log_level,
                    format=_pp_conf.log_formatline,
                    datefmt=_pp_conf.log_datefmt)


def curve_of_growth_analysis(filenames, parameters,
                             nodeblending=False, display=False,
                             diagnostics=False):

    output = {}
    obsparam = parameters['obsparam']

    logging.info('starting photometry with parameters: %s' %
                 (', '.join([('%s: %s' % (var, str(val))) for
                             var, val in list(locals().items())])))

    # re-extract sources for curve-of-growth analysis

    aprads = parameters['aprad']
    if not isinstance(aprads, list) and not isinstance(aprads, numpy.ndarray):
        print('need a list of aprads...')
        os.abort()

    logging.info('run pp_extract using %d apertures' % len(aprads))
    print('* extract sources from %d images using %d apertures' %
          (len(filenames), len(aprads)))

    extractparameters = {'sex_snr': parameters['sex_snr'],
                         'source_minarea': parameters['source_minarea'],
                         'paramfile': _pp_conf.rootpath
                         + '/setup/twentyapertures.sexparam',
                         'aprad': aprads, 'telescope': parameters['telescope'],
                         'nodeblending': nodeblending,
                         'quiet': False}

    extraction = pp_extract.extract_multiframe(filenames, extractparameters)
    extraction = [e for e in extraction if len(e) > 0]

    # curve-of-growth analysis

    # arrays for accumulating source information as a function of aprad
    background_flux = []  # numpy.zeros(len(aprads))
    target_flux = []  # numpy.zeros(len(aprads))
    background_snr = []  # numpy.zeros(len(aprads))
    target_snr = []  # numpy.zeros(len(aprads))

    for filename in filenames:

        if display:
            print('processing curve-of-growth for frame %s' % filename)

        if not parameters['background_only']:

            hdu = fits.open(filename, ignore_missing_end=True)

            # pull target coordinates from Horizons
            targetname = hdu[0].header[obsparam['object']]
            if parameters['manobjectname'] is not None:
                targetname = parameters['manobjectname'].translate(
                    _pp_conf.target2filename)

            image = hdu[0].data

            # derive MIDTIMJD, if not yet in the FITS header
            obsparam = parameters['obsparam']
            if not 'MIDTIMJD' in hdu[0].header:
                exptime = float(hdu[0].header[obsparam['exptime']])
                if obsparam['date_keyword'].find('|') == -1:
                    date = hdu[0].header[obsparam['date_keyword']]
                    date = dateobs_to_jd(date) + exptime/2./86400.
                else:
                    date_key = obsparam['date_keyword'].split('|')[0]
                    time_key = obsparam['date_keyword'].split('|')[1]
                    date = hdu[0].header[date_key]+'T' +\
                        hdu[0].header[time_key]
                    date = dateobs_to_jd(date) + exptime/2./86400.
            else:
                date = hdu[0].header['MIDTIMJD']

            # call HORIZONS to get target coordinates
            obj = Horizons(targetname.replace('_', ' '),
                           epochs=date,
                           location=str(obsparam['observatory_code']))
            try:
                eph = obj.ephemerides()
                n = len(eph)
            except ValueError:
                print('Target (%s) not a small body' % targetname)
                logging.warning('Target (%s) not a small body' % targetname)
                n = None

            if n is None or n == 0:
                logging.warning('WARNING: No position from Horizons!' +
                                'Name (%s) correct?' % targetname)
                logging.warning('HORIZONS call: %s' % obj.uri)
                logging.info('proceeding with background sources analysis')
                parameters['background_only'] = True
            else:
                logging.info('ephemerides for %s pulled from Horizons' %
                             targetname)
                target_ra, target_dec = eph[0]['RA'], eph[0]['DEC']

        # pull data from LDAC file
        ldac_filename = filename[:filename.find('.fit')]+'.ldac'
        data = catalog('Sextractor_LDAC')
        data.read_ldac(ldac_filename, maxflag=3)

        if data.shape[0] == 0:
            continue

        # identify target and extract its curve-of-growth
        n_target_identified = 0
        if not parameters['background_only']:
            residuals = numpy.sqrt((data['ra_deg']-target_ra)**2 +
                                   (data['dec_deg']-target_dec)**2)

            target_idx = numpy.argmin(residuals)
            if residuals[target_idx] > _pp_conf.pos_epsilon/3600:
                logging.warning(('WARNING: frame %s, large residual to ' +
                                 'HORIZONS position of %s: %f arcsec; ' +
                                 'ignore this frame') %
                                (filename, targetname,
                                 residuals[numpy.argmin(residuals)]*3600.))
            else:
                target_flux.append(data[target_idx]['FLUX_'+_pp_conf.photmode] /
                                   max(data[target_idx][
                                       'FLUX_'+_pp_conf.photmode]))
                target_snr.append(
                    data[target_idx]['FLUX_'+_pp_conf.photmode] /
                    data[target_idx]['FLUXERR_'+_pp_conf.photmode] /
                    max(data[target_idx]['FLUX_'+_pp_conf.photmode] /
                        data[target_idx]['FLUXERR_'+_pp_conf.photmode]))
                n_target_identified += 1

        # extract background source fluxes and snrs
        #   assume n_background_sources >> 1, do not reject target
        if not parameters['target_only']:
            # n_src = data.shape[0] # use all sources
            n_src = 50  # use only 50 sources
            for idx, src in enumerate(data.data[:n_src]):
                if (numpy.any(numpy.isnan(src['FLUX_'+_pp_conf.photmode])) or
                    numpy.any(numpy.isnan(src['FLUXERR_'+_pp_conf.photmode]))
                        or src['FLAGS'] > 3):
                    continue

                # create growth curve
                background_flux.append(src['FLUX_'+_pp_conf.photmode] /
                                       max(src['FLUX_'+_pp_conf.photmode]))
                background_snr.append(src['FLUX_'+_pp_conf.photmode] /
                                      src['FLUXERR_'+_pp_conf.photmode] /
                                      max(src['FLUX_'+_pp_conf.photmode] /
                                          src['FLUXERR_'+_pp_conf.photmode]))

    # investigate curve-of-growth

    logging.info('investigate curve-of-growth based on %d frames' %
                 len(filenames))

    # combine results
    n_target = len(target_flux)
    if n_target > 0:
        target_flux = (numpy.median(target_flux, axis=0),
                       numpy.std(target_flux, axis=0)/numpy.sqrt(n_target))
        target_snr = numpy.median(target_snr, axis=0)
    else:
        target_flux = (numpy.zeros(len(aprads)), numpy.zeros(len(aprads)))
        target_snr = numpy.zeros(len(aprads))

    n_background = len(background_flux)
    if n_background > 0:
        background_flux = (numpy.median(background_flux, axis=0),
                           numpy.std(background_flux, axis=0) /
                           numpy.sqrt(n_background))
        background_snr = numpy.median(background_snr, axis=0)
    else:
        background_flux = (numpy.zeros(len(aprads)), numpy.zeros(len(aprads)))
        background_snr = numpy.zeros(len(aprads))

    if n_target == 0:
        logging.info('No target fluxes available, using background sources, ' +
                     'only')
        parameters['background_only'] = True

    if n_background == 0:
        logging.info('No background fluxes available, using target, only')
        parameters['target_only'] = True

    # find optimum aperture radius
    if parameters['target_only']:
        aprad_strategy = 'smallest target aprad that meets fluxlimit criterion'
        optimum_aprad_idx = numpy.argmin(numpy.fabs(target_flux[0] -
                                                    _pp_conf.fluxlimit_aprad))
    elif parameters['background_only']:
        aprad_strategy = 'smallest background aprad that meets fluxlimit ' + \
                         'criterion'
        optimum_aprad_idx = numpy.argmin(numpy.fabs(background_flux[0] -
                                                    _pp_conf.fluxlimit_aprad))
    else:
        # flux_select: indices where target+background fluxes > fluxlimit
        flux_select = numpy.where((target_flux[0] > _pp_conf.fluxlimit_aprad) &
                                  (background_flux[0] > _pp_conf.fluxlimit_aprad))[0]
        flux_res = numpy.fabs(target_flux[0][flux_select] -
                              background_flux[0][flux_select])

        if numpy.min(flux_res) < _pp_conf.fluxmargin_aprad:
            aprad_strategy = 'target+background fluxes > fluxlimit, ' + \
                             'flux difference < margin'
            optimum_aprad_idx = flux_select[numpy.where(flux_res <
                                                        _pp_conf.fluxmargin_aprad)[0][0]]
        else:
            aprad_strategy = 'target+background fluxes > fluxlimit, ' + \
                             'flux difference minimal'
            optimum_aprad_idx = flux_select[numpy.argmin(flux_res)]

    optimum_aprad = parameters['aprad'][optimum_aprad_idx]

    output['aprad_strategy'] = aprad_strategy
    output['optimum_aprad'] = optimum_aprad
    output['pos_epsilon'] = _pp_conf.pos_epsilon
    output['fluxlimit_aprad'] = _pp_conf.fluxlimit_aprad
    output['fluxmargin_aprad'] = _pp_conf.fluxmargin_aprad
    output['n_target'] = len(target_flux[0])
    output['n_bkg'] = len(background_flux[0])
    output['target_flux'] = target_flux
    output['target_snr'] = target_snr
    output['background_flux'] = background_flux
    output['background_snr'] = background_snr
    output['parameters'] = parameters

    # write results to file
    outf = open('aperturephotometry_curveofgrowth.dat', 'w')
    outf.writelines('#      background              target          flux\n' +
                    '# rad   flux sigma snr      flux sigma snr  residual\n')
    for i in range(len(parameters['aprad'])):
        outf.writelines(('%5.2f  %5.3f %5.3f %4.2f   %6.3f %5.3f %4.2f   ' +
                         '%6.3f\n') %
                        (parameters['aprad'][i], background_flux[0][i],
                         background_flux[1][i], background_snr[i],
                         target_flux[0][i], target_flux[1][i],
                         target_snr[i],
                         target_flux[0][i]-background_flux[0][i]))
    outf.close()

    # extraction content
    #
    # -> see pp_extract.py
    #
    ###

    # output content
    #
    # { 'aprad_strategy'  : optimum aperture finding strategy,
    #   'optimum_aprad'   : optimum aperature radius,
    #   'pos_epsilon'     : required positional uncertainty ("),
    #   'fluxlimit_aprad' : min flux for both target and background,
    #   'fluxmargin_aprad': max flux difference between target and background,
    #   'n_target'        : number of frames with target flux measurements,
    #   'n_bkg'           : number of frames with background measurements,
    #   'target_flux'     : target fluxes as a function of aprad,
    #   'target_snr'      : target snrs as a function of aprad,
    #   'background_flux' : background fluxes as a function of aprad,
    #   'background_snr'  : background snrs as a function of aprad,
    #   'parameters'      : source extractor parameters
    # }
    ###

    # diagnostics
    if diagnostics:
        if display:
            print('creating diagnostic output')
        logging.info(' ~~~~~~~~~ creating diagnostic output')
        diag.add_photometry(output, extraction)

    # update image headers
    for filename in filenames:
        hdu = fits.open(filename, mode='update', ignore_missing_end=True)
        hdu[0].header['APRAD'] = (optimum_aprad, 'aperture phot radius (px)')
        hdu[0].header['APIDX'] = (optimum_aprad_idx, 'optimum aprad index')
        hdu.flush()
        hdu.close()

    # display results
    if display:
        print('\n#################################### PHOTOMETRY SUMMARY:\n###')
        print('### best-fit aperture radius %5.2f (px)' % (optimum_aprad))
        print('###\n#####################################################\n')

    logging.info('==> best-fit aperture radius: %3.1f (px)' % (optimum_aprad))

    return output


def photometry(filenames, sex_snr, source_minarea, aprad,
               manobjectname, background_only, target_only,
               telescope, obsparam, nodeblending=False,
               display=False,
               diagnostics=False):
    """
    wrapper for photometry analysis
    """

    # photometry parameters
    photpar = {'sex_snr': sex_snr,
               'source_minarea': source_minarea,
               'manobjectname': manobjectname,
               'background_only': background_only,
               'target_only': target_only,
               'obsparam': obsparam,
               'telescope': telescope,
               'nodeblending': nodeblending,
               'quiet': not display}

    # do curve-of-growth analysis if aprad not provided
    for filename in filenames:
        hdu = fits.open(filename, mode='update',
                        ignore_missing_end=True)
                        
        # add flag keyword to header and set it to FAILED
        try:
            header = hdu[0].header
            header.set('PP_PHOTO', 'FAILED', 'PP: pp_photometry status flaag',
                       after='PP_REGIS')
        except KeyError:
            print(('%s image header incomplete, have the data run ' +
                   'through pp_register?') % filename)
        
        hdu[0].header['PHOTMODE'] = (_pp_conf.photmode,
                                     'PP photometry mode')
        hdu.flush()
        hdu.close()

    if _pp_conf.photmode == 'APER':
        if aprad is None:
            # aperture radius list
            aprads = numpy.linspace(obsparam['aprad_range'][0],
                                    obsparam['aprad_range'][1], 20)

            photpar['aprad'] = aprads
            cog = curve_of_growth_analysis(filenames, photpar,
                                           nodeblending=nodeblending,
                                           display=display,
                                           diagnostics=diagnostics)
            aprad = cog['optimum_aprad']
        else:
            # add manually selected aprad to image headers
            for filename in filenames:
                hdu = fits.open(filename, mode='update',
                                ignore_missing_end=True)
                hdu[0].header['APRAD'] = (aprad,
                                          'manual aperture phot radius (px)')
                hdu.flush()
                hdu.close()

        # run extract using (optimum) aprad
        photpar['aprad'] = round(aprad, 2)
        photpar['paramfile'] = (_pp_conf.rootpath +
                                '/setup/singleaperture.sexparam')
        logging.info('extract sources using optimum aperture from %d images' %
                     len(filenames))

        if display:
            print(('* extract sources from %d images using aperture '
                   + 'radius %4.2fpx') %
                  (len(filenames), aprad))
    else:
        photpar['aprad'] = None
        photpar['paramfile'] = (_pp_conf.rootpath +
                                '/setup/singleaperture.sexparam')

        logging.info('extract sources using ' + _pp_conf.photmode +
                     ' photometry')

        if display:
            print(('* extract sources from %d images using '
                   + _pp_conf.photmode + ' photometry') %
                  len(filenames))

    photpar['photmode'] = _pp_conf.photmode

    pp_extract.extract_multiframe(filenames, photpar)

    logging.info('Done! -----------------------------------------------------')
    
    # set flag keyword to SUCCESS
    for filename in filenames:
        hdulist = fits.open(filename, mode='update', verify='silentfix',
                            ignore_missing_end=True)
        header = hdulist[0].header
        header.set('PP_PHOTO', 'SUCCESS')
        hdulist.close()

    if 'cog' in list(locals().keys()):
        return cog
    else:
        return None


# MAIN

if __name__ == '__main__':

    # define command line arguments
    parser = argparse.ArgumentParser(description='automated photometry')
    parser.add_argument('-snr', help='sextractor SNR threshold for ' +
                        'photometry catalog', default=2)
    parser.add_argument('-minarea', help='sextractor SNR threshold for ' +
                        'photometry catalog', default=0)
    parser.add_argument('-aprad', help='aperture radius for photometry (px)',
                        default=None)
    parser.add_argument('-target',
                        help='object name override (e.g., 2015_AB123)',
                        default=None)
    parser.add_argument('-background_only',
                        help='find aperture for background only',
                        action="store_true")
    parser.add_argument('-target_only', help='find aperture for target only',
                        action="store_true")
    parser.add_argument('images', help='images to process', nargs='+')
    parser.add_argument('-nodeblending',
                        help='deactivate deblending in source extraction',
                        action="store_true")

    args = parser.parse_args()
    sex_snr = float(args.snr)
    source_minarea = float(args.minarea)
    aprad = float(args.aprad) if args.aprad is not None else None
    manobjectname = args.target
    background_only = args.background_only
    target_only = args.target_only
    nodeblending = args.nodeblending
    filenames = args.images

    # check if input filenames is actually a list
    if len(filenames) == 1:
        if filenames[0].find('.lst') > -1 or filenames[0].find('.list') > -1:
            filenames = [filename[:-1] for filename in open(filenames[0], 'r')
                         .readlines()]

    # obtain telescope information
    hdu = fits.open(filenames[0], ignore_missing_end=True)
    try:
        telescope = hdu[0].header['TEL_KEYW']
    except KeyError:
        print('ERROR: cannot find telescope keyword in image header;' +
              'has this image run through pp_prepare?')
        sys.exit(0)
    obsparam = _pp_conf.telescope_parameters[telescope]

    if type(manobjectname) == str:
        manobjectname = manobjectname.translate(_pp_conf.target2filename)

    # set minarea from obsparam
    if source_minarea == 0:
        source_minarea = obsparam['source_minarea']

    phot = photometry(filenames, sex_snr, source_minarea, aprad,
                      manobjectname, background_only, target_only,
                      telescope, obsparam,
                      nodeblending=nodeblending, display=True,
                      diagnostics=True)
