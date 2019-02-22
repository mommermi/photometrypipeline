#!/usr/bin/env python3

""" PP_REGISTER - wcs register frames
    v1.0: 2015-12-30, mommermiscience@gmail.com
"""
from __future__ import print_function

# Photometry Pipeline
# Copyright (C) 2016-2018 Michael Mommert, mommermiscience@gmail.com

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
import shutil
import logging
import subprocess
import argparse
import shlex
import time
from astropy.io import fits

# pipeline-specific modules
import _pp_conf
from catalog import *
import pp_extract
import toolbox
from diagnostics import registration as diag

# only import if Python3 is used
if sys.version_info > (3, 0):
    from builtins import str

# setup logging
logging.basicConfig(filename=_pp_conf.log_filename,
                    level=_pp_conf.log_level,
                    format=_pp_conf.log_formatline,
                    datefmt=_pp_conf.log_datefmt)


def register(filenames, telescope, sex_snr, source_minarea, aprad,
             mancat, obsparam, source_tolerance, nodeblending,
             display=False, diagnostics=False):
    """
    registration wrapper
    output: diagnostic properties
    """

    # start logging
    logging.info('starting registration with parameters: %s' %
                 (', '.join([('%s: %s' % (var, str(val))) for
                             var, val in list(locals().items())])))

    # check if images have been run through pp_prepare
    try:
        midtime_jd = fits.open(filenames[0], verify='silentfix',
                               ignore_missing_end=True)[0].header['MIDTIMJD']
    except KeyError:
        raise KeyError(('%s image header incomplete, have the data run ' +
                        'through pp_prepare?') % filenames[0])
        return None
    
    # add flag keyword to header and set it to STARTED
    for filename in filenames:
        hdulist = fits.open(filename, mode='update', verify='silentfix',
                            ignore_missing_end=True)
        header = hdulist[0].header
        try:
            header.set('PP_REGIS', 'STARTED', 'PP: pp_register status flag',
                        after='PP_PREPA')
        except:
            print(('%s image header incomplete, have the data run ' +
                            'through pp_prepare?') % filename)
            return None
        finally:
            hdulist.close()

    # run scamp on all image catalogs using different catalogs
    if mancat is not None:
        obsparam['astrometry_catalogs'] = [mancat]

    # # use each catalog twice
    # obsparam['astrometry_catalogs'] = [catcat for cat in
    #                                    obsparam['astrometry_catalogs']
    #                                    for catcat in [cat]*
    #                                    _pp_conf.n_registration_repetitions ]

    n_success_last_iteration = None

    goodfits, badfits = [], []

    for cat_idx, refcat in enumerate(obsparam['astrometry_catalogs']):

        # run extract routines
        # ignore saturation: saturated stars are bright and might be necessary
        # for SCAMP
        if display:
            print('* extract sources from %d frames' % len(filenames))

        extractparameters = {'sex_snr': sex_snr,
                             'source_minarea': source_minarea,
                             'aprad': aprad, 'telescope': telescope,
                             'ignore_saturation': True,
                             'global_background': False,
                             'nodeblending': nodeblending,
                             'quiet': False}

        extraction = pp_extract.extract_multiframe(filenames,
                                                   extractparameters)

        if extraction is None:
            if display:
                print('ERROR: extraction was not successful')
            logging.error('extraction was not successful')
            return None

        # check if enough sources have been detected in images
        ldac_files = []
        ldac_catalogs = []
        for frame in extraction:
            if frame['catalog_data'].shape[0] > 10:
                ldac_files.append(frame['ldac_filename'])
                cat = catalog(frame['ldac_filename'])
                cat.read_ldac(frame['ldac_filename'],
                              frame['fits_filename'],
                              object_keyword=obsparam['object'],
                              exptime_keyword=obsparam['exptime'],
                              maxflag=0)
                ldac_catalogs.append(cat)

        if len(ldac_files) == 0:
            if display:
                print('ERROR: no sources detected in image files')
                logging.error('no sources detected in image files')
            return {'goodfits': [], 'badfits': filenames}

        output = {}

        # check if sufficient reference stars are available in refcat
        logging.info('check if sufficient reference stars in catalog %s' %
                     refcat)

        hdulist = fits.open(filenames[len(filenames)//2],
                            ignore_missing_end=True)

        # get extent on the sky for a single frame
        ra, dec, rad = toolbox.skycenter(ldac_catalogs)
        logging.info(('FoV center ({:.7f}/{:+.7f}) and '
                      'radius ({:.2f} deg) derived').format(
                          ra, dec, rad))

        if rad > 5:  # check if combined field radius >5 deg
            logging.warning(('combined field radius is huge ({:.1f} deg);'
                             'check if one or more frames can be rejected '
                             'as outliers.').format(rad))

            # derived center of mass
            com_ra = np.median(np.hstack([cat['ra_deg']
                                          for cat in ldac_catalogs]))
            com_dec = np.median(np.hstack([cat['dec_deg']
                                           for cat in ldac_catalogs]))

            # for each frame derive distance from center of mass
            dist = np.array([np.median(np.sqrt((cat['ra_deg']-com_ra)**2 +
                                               (cat['dec_deg']-com_dec)**2))
                             for cat in ldac_catalogs])

            logging.warning(('reject files [{:s}] for registration '
                             'due to large offset from other '
                             'frames [{:s}]').format(
                ",".join(np.array(filenames)[dist > 5]),
                ",".join([str(d) for d in dist[dist > 5]])))
            if display:
                print(('reject files [{:s}] for registration '
                       'due to large offset from other '
                       'frames [{:s}] deg').format(
                    ",".join(np.array(filenames)[dist > 5]),
                    ",".join([str(d) for d in dist[dist > 5]])))

            badfits += list(np.array(filenames)[dist > 5])

            # reject files for which dist>threshold
            filenames = np.array(filenames)[dist < 5]
            ldac_files = np.array(ldac_files)[dist < 5]
            ldac_catalogs = np.array(ldac_catalogs)[dist < 5]

            ra, dec, rad = toolbox.skycenter(ldac_catalogs)
            logging.info(('FoV center ({:.7f}/{:+.7f}) and '
                          'radius ({:.2f} deg) derived').format(
                              ra, dec, rad))

        fileline = " ".join(ldac_files)

        del(ldac_catalogs)

        checkrefcat = catalog(refcat, display=False)
        n_sources = checkrefcat.download_catalog(ra, dec,
                                                 rad +
                                                 obsparam['reg_search_radius'],
                                                 100, save_catalog=False)
        if n_sources < _pp_conf.min_sources_astrometric_catalog:
            logging.info(('Only %d sources in astrometric reference catalog; '
                          + 'try other catalog') % n_sources)
            goodfits, badfits = [], filenames
            continue
        else:
            logging.info('%d sources in catalog %s; enough for SCAMP' %
                         (n_sources, refcat))

        # remove existing scamp output
        os.remove('scamp_output.xml') if os.path.exists('scamp_output.xml') \
            else None

        logging.info('run SCAMP on %d image files, match with catalog %s ' %
                     (len(filenames), refcat))

        # download catalog and write to ldac file for SCAMP
        astcat = catalog(refcat, display=True)
        n_sources = astcat.download_catalog(ra, dec,
                                            rad+obsparam['reg_search_radius'],
                                            100000,
                                            max_mag=obsparam['reg_max_mag'],
                                            save_catalog=True)

        # translate source_tolerance into SCAMP properties
        #   code      SCAMP_code   keep
        #   'none'    0x00ff       only unflagged sources
        #   'low'     0x00fe       sources with bright neighbors
        #   'medium'  0x00fd       blended sources
        #   'high'    0x00fc       saturated sources
        st_code = {'none':   '0x00ff',
                   'low':    '0x00fe',
                   'medium': '0x00fd',
                   'high':   '0x00fc'}[source_tolerance]

        # assemble arguments for scamp, run it, and wait for it
        commandline = 'scamp -c '+obsparam['scamp-config-file'] + \
            ' -ASTR_FLAGSMASK '+st_code+' -FLAGS_MASK '+st_code + \
            ' -ASTREF_CATALOG FILE' + \
            ' -ASTREFCAT_NAME ' + refcat + '.cat ' + fileline

        logging.info('call Scamp as: %s' % commandline)

        scamp = subprocess.Popen(shlex.split(commandline))
        scamp.wait()

        # identify successful and failed WCS registrations based on
        # the contrast values provided by SCAMP
        scamp = _pp_conf.read_scamp_output()
        os.rename('scamp_output.xml', 'astrometry_scamp.xml')
        fitresults = []  # store scamp outputs
        for dat in scamp[1]:
            # successful fit
            if ((float(dat[scamp[0]['AS_Contrast']]) <
                 _pp_conf.scamp_as_contrast_limit)
                or (float(dat[scamp[0]['XY_Contrast']]) <
                    _pp_conf.scamp_xy_contrast_limit)
                    or len(dat) == 0):
                filename = dat[scamp[0]['Catalog_Name']]
                for file in os.listdir('.'):
                    if file.find(filename[:filename.find('.ldac')]+'.fit') \
                       > -1:
                        filename = file
                badfits.append(filename)
            # failed fit
            else:
                filename = dat[scamp[0]['Catalog_Name']]
                for file in os.listdir('.'):
                    if file.find(filename[:filename.find('.ldac')]+'.fit')\
                       > -1:
                        filename = file
                goodfits.append(filename)

            fitresults.append(
                [filename,
                 float(dat[scamp[0]['AS_Contrast']]),
                 float(dat[scamp[0]['XY_Contrast']]),
                 float(dat[scamp[0]['AstromSigma_Reference']].split()[0]),
                 float(dat[scamp[0]['AstromSigma_Reference']].split()[1]),
                 float(dat[scamp[0]['Chi2_Reference']]),
                 float(dat[scamp[0]['Chi2_Internal']])])

        open('registration_succeeded.lst', 'w').writelines("%s\n" %
                                                           '\n'.join(goodfits))
        if len(goodfits) == 0 and len(badfits) == 0:
            badfits = filenames
        open('registration_failed.lst', 'w').writelines("%s\n" %
                                                        '\n'.join(badfits))

        output['goodfits'] = goodfits
        output['badfits'] = badfits
        output['fitresults'] = fitresults
        output['catalog'] = refcat

        # check registration outcome

        logging.info(' > match succeeded for %d/%d images' %
                     (len(goodfits), len(filenames)))
        print('\n################################# ' +
              'REGISTRATION SUMMARY:\n###')
        print('### %d/%d images have been registered successfully' %
              (len(goodfits), len(filenames)))
        print('###\n###############################' +
              '#######################\n')

        # # registration succeeded for all images
        # if len(badfits) == 0:
        #     break
        # # same number of good fits as for the last iteration
        # # break out!
        # elif len(goodfits) == n_success_last_iteration:
        #     break
        # # registration failed for most (or all) images
        # else:
        #     logging.info(' > match failed for %d/%d images' % \
        #                  (len(badfits), len(filenames)))

        #     ### if registration failed, try again with the same catalog
        #     # and no extraction!
        #     # this will make use of the .head files and improves results
        #     logging.critical('Not all images matched ' \
        #                      + '- try again or different catalog, if available')
        #     if display:
        #         print('Not all images matched ' \
        #             + '- try again for different catalog, if available')

        n_success_last_iteration = len(goodfits)

    # update image headers with wcs solutions where registration
    # was successful
    logging.info('update image headers with WCS solutions ')

    for filename in goodfits:
        # remove fake wcs header keys
        fake_wcs_keys = ['RADECSYS', 'CTYPE1', 'CTYPE2', 'CRVAL1', 'CRVAL2',
                         'CRPIX1', 'CRPIX2', 'CD1_1', 'CD1_2', 'CD2_1',
                         'CD2_2', 'RADESYS']
        hdu = fits.open(filename, mode='update', verify='silentfix',
                        ignore_missing_end=True)
        for fake_key in fake_wcs_keys:
            hdu[0].header[fake_key] = ''

        # read new header files
        newhead = open(filename[:filename.find(
            '.fit')]+'.head', 'r').readlines()

        for line in newhead:
            key = line[:8].strip()
            try:
                value = float(line[10:30].replace('\'', ' ').strip())
            except ValueError:
                value = line[10:30].replace('\'', ' ').strip()
            comment = line[30:].strip()
            if key.find('END') > -1:
                break
            # print key, '|',  value, '|',  comment
            hdu[0].header[key] = (str(value), comment)

        # other header keywords
        hdu[0].header['RADECSYS'] = (hdu[0].header['RADESYS'],
                                     'copied from RADESYS')
        hdu[0].header['TEL_KEYW'] = (telescope, 'pipeline telescope keyword')
        hdu[0].header['REGCAT'] = (refcat, 'catalog used in WCS registration')
        hdu.flush(output_verify='silentfix')
        hdu.close()

        # cleaning up (in case the registration succeeded)
        if len(goodfits) == len(filenames):
            os.remove(filename[:filename.find('.fit')]+'.head')

    if len(badfits) == len(filenames):
        if display:
            print('ERROR: registration failed for all images')
        logging.error('ERROR: registration failed for all images')
        return output

    # print astrometry output file
    outf = open('best_astrometry.dat', 'w')
    outf.writelines('# filename AS_contrast XY_contrast '
                    + 'Chi2_catalog Chi2_int Pos_uncertainty(arcsec)\n')
    for idx, data in enumerate(fitresults):
        outf.writelines('%25.25s %5.2f %5.2f %10.7f %10.7f %7.4f\n' %
                        (data[0], data[1], data[2], data[5], data[6],
                         numpy.sqrt(data[3]**2+data[4]**2)))
    outf.close()

    # extraction output
    #
    # -> see pp_extract.py
    #
    ##

    # output content
    #
    # { 'good_fits'    : list of fits where registration succeeded,
    #   'bad fits'     : list of fits where registration failed,
    #   'fitresults'   : scamp fit results,
    #   'catalog'      : astrometric reference catalog name
    # }
    ###

    # create diagnostics
    if diagnostics:
        if display:
            print('creating diagnostic output')
        logging.info(' ~~~~~~~~~ creating diagnostic output')
        diag.add_registration(output, extraction)

    logging.info('Done! -----------------------------------------------------')
    
    # set flag keyword to SUCCESS
    for filename in filenames:
        hdulist = fits.open(filename, mode='update', verify='silentfix',
                            ignore_missing_end=True)
        header = hdulist[0].header
        try:
            header.set('PP_REGIS', 'SUCCESS')
        except:
            print(('%s image header incomplete, have the data run ' +
                            'through pp_prepare?') % filename)
            return None
        finally:
            hdulist.close()
            
    return output


if __name__ == '__main__':

    # command line arguments
    parser = argparse.ArgumentParser(description='automated WCS registration')
    parser.add_argument("-snr", help='sextractor SNR threshold', default=0)
    parser.add_argument("-minarea", help='sextractor SNR threshold',
                        default=0)
    parser.add_argument('-source_tolerance',
                        help='tolerance on source properties for registration',
                        choices=['none', 'low', 'medium', 'high'],
                        default=None)
    parser.add_argument("-cat", help='manually select reference catalog',
                        choices=_pp_conf.allcatalogs, default=None)
    parser.add_argument('-nodeblending',
                        help='deactivate deblending in source extraction',
                        action="store_true")
    parser.add_argument('images', help='images to process', nargs='+')

    args = parser.parse_args()
    snr = float(args.snr)
    source_minarea = float(args.minarea)
    mancat = args.cat
    source_tolerance = args.source_tolerance
    nodeblending = args.nodeblending
    filenames = args.images

    # read telescope and filter information from fits headers
    # check that they are the same for all images
    instruments = []
    for filename in filenames:
        hdulist = fits.open(filename, ignore_missing_end=True,
                            verify='silentfix')
        header = hdulist[0].header
        for key in _pp_conf.instrument_keys:
            if key in header:
                instruments.append(header[key])

    if len(instruments) == 0:
        raise KeyError('cannot identify telescope/instrument; please update'
                       '_pp_conf.instrument_keys accordingly')

    # assign telescope parameters (telescopes.py)
    telescope = _pp_conf.instrument_identifiers[instruments[0]]
    obsparam = _pp_conf.telescope_parameters[telescope]

    # set aperture photometry aperture radius
    aprad = obsparam['aprad_default']

    if snr == 0:
        snr = obsparam['source_snr']

    # set minarea from obsparam
    if source_minarea == 0:
        source_minarea = obsparam['source_minarea']

    if source_tolerance is None:
        source_tolerance = obsparam['source_tolerance']

    # run registration wrapper
    registration = register(filenames, telescope, snr,
                            source_minarea, aprad, mancat, obsparam,
                            source_tolerance, nodeblending,
                            display=True, diagnostics=True)
