#!/usr/bin/env python3

""" PP_PREPARE - prepare fits images for photometry pipeline
    v1.0: 2016-02-27, mommermiscience@gmail.com
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

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates import FK5, ICRS
from astropy.time import Time
import numpy
import os
import re
import sys
import logging
import argparse
from astropy.io import fits

# pipeline-specific modules
import _pp_conf
from catalog import *
from diagnostics import preparation as diag
import toolbox

# only import if Python3 is used
if sys.version_info > (3, 0):
    from builtins import str
    from builtins import input
    from builtins import range

# setup logging
logging.basicConfig(filename=_pp_conf.log_filename,
                    level=_pp_conf.log_level,
                    format=_pp_conf.log_formatline,
                    datefmt=_pp_conf.log_datefmt)


def prepare(filenames, obsparam, header_update, keep_wcs=False,
            flipx=False, flipy=False, rotate=0, man_ra=None,
            man_dec=None, diagnostics=False, display=False):
    """
    prepare wrapper
    output: diagnostic properties
    """

    # start logging
    logging.info('preparing data with parameters: %s' %
                 (', '.join([('%s: %s' % (var, str(val))) for
                             var, val in list(locals().items())])))

    # change FITS file extensions to .fits
    for idx, filename in enumerate(filenames):
        if filename.split('.')[-1] in ['fts', 'FTS', 'FITS', 'fit', 'FIT']:
            os.rename(filename, '.'.join(filename.split('.')[:-1])+'.fits')
            filenames[idx] = '.'.join(filename.split('.')[:-1])+'.fits'
            logging.info('change filename from "%s" to "%s"' %
                         (filename, filenames[idx]))

    # identify keywords for GENERIC telescopes

    # open one sample image file
    hdulist = fits.open(filenames[0], verify='ignore',
                        ignore_missing_end='True')
    header = hdulist[0].header

    # check if this is a single-extension FITS file
    if float(header['NAXIS']) > 2.:
        logging.error('This is not a single-extension FITS file. Please '
                      'extract individual extensions and run them '
                      'individually.')
        sys.exit()

    # keywords that have to be implanted into each image
    implants = {}

    # if GENERIC telescope, ask user for header keywords
    if obsparam['telescope_keyword'] is 'GENERIC':
        keywords = {'pixel scale in arcsec/px before binning': 'secpix',
                    'binning factor in both axes': 'binning',
                    'image center RA (keyword or degrees)': 'ra',
                    'image center DEC (keyword or degrees)': 'dec',
                    'filter used (clear if none was used)': 'filter',
                    'observation midtime': 'date_keyword',
                    'exposure time (seconds)': 'exptime'}

        for description, keyword in list(keywords.items()):

            try:
                if obsparam[keyword] in header:
                    continue
            except:
                pass

            inp = input('%s? > ' % description)

            if keyword is 'secpix':
                obsparam[keyword] = (float(inp), float(inp))
            if keyword is 'binning':
                implants['BINX'] = (float(inp), 'PP: user-defined')
                implants['BINY'] = (float(inp), 'PP: user-defined')
            if keyword is 'ra':
                try:
                    implants['OBJCTRA'] = (float(inp), 'PP: user_defined')
                    obsparam['radec_separator'] = 'XXX'
                except TypeError:
                    obsparam['ra'] = inp
                # # check for separator
                # try:
                #     dummy = float(header[inp])
                #     obsparam['radec_separator'] = 'XXX'
                # except ValueError:
                #     if ':' in header[inp]:
                #         obsparam['radec_separator'] = ':'
                #     if ' ' in header[inp].strip():
                #         obsparam['radec_separator'] = ' '
            if keyword is 'dec':
                try:
                    implants['OBJCTDEC'] = (float(inp), 'PP: user_defined')
                    obsparam['radec_separator'] = 'XXX'
                except TypeError:
                    obsparam['dec'] = inp
            if keyword is 'filter':
                implants[obsparam['filter']] = (inp, 'PP: user-defined')
            if keyword is 'date_keyword':
                obsparam['date_keyword'] = inp
            if keyword is 'exptime':
                implants['EXPTIME'] = (float(inp), 'PP: user-defined')

        implants['INSTRUME'] = ('GENERIC', 'PP: manually set')

    # prepare image headers for photometry pipeline

    for filename in filenames:

        if display:
            print('preparing', filename)

        # open image file
        hdulist = fits.open(filename, mode='update', verify='silentfix',
                            ignore_missing_end=True)
        header = hdulist[0].header
        
        # add flag keyword to header and set it to STARTED
        header.set('PP_PREPA', 'STARTED', 'PP: pp_prepare status flag')
        
        # add other headers, if available
        if len(hdulist) > 1:
            for i in range(len(hdulist)):
                try:
                    header += hdulist[i].header
                except:
                    pass

        # account for flips and rotation in telescope configuration
        # if instrument has several chips...
        if 'chip_id' in obsparam:
            chip_id = header[obsparam['chip_id']]
            this_flipx = obsparam['flipx'][chip_id]
            this_flipy = obsparam['flipy'][chip_id]
            this_rotate = obsparam['rotate'][chip_id]
        # if not...
        else:
            this_flipx = obsparam['flipx']
            this_flipy = obsparam['flipy']
            this_rotate = obsparam['rotate']

        if flipx:
            this_flipx = numpy.invert(this_flipx)
        if flipy:
            this_flipy = numpy.invert(this_flipy)
        if rotate > 0:
            this_rotate += rotate

        # read image data
        imdata = hdulist[0].data

        # check if image is a cube, or a single frame put into a cube
        if len(imdata.shape) > 2:
            # this image is a cube
            if imdata.shape[0] == 1:
                # this is a single image put into a cube
                # turn this into a single-frame fits file
                imdata = imdata[0]
            else:
                # this is really a cube; don't know what to do
                raise TypeError(("%s is a cube FITS file; don't know how to "
                                 "handle this file...") % filename)

        # add header keywords for Source Extractor
        if 'EPOCH' not in header:
            header['EPOCH'] = (2000, 'PP: required for registration')
        # if 'EQUINOX' not in header:
        #     header['EQUINOX'] = (2000, 'PP: required for registration')

        # add header keywords for SCAMP
        header['PHOTFLAG'] = ('F', 'PP: data is not photometric (SCAMP)')
        header['PHOT_K'] = (0.05, 'PP: assumed extinction coefficient')

        if not keep_wcs:

            # remove keywords that might collide with fake wcs
            for key in list(header.keys()):
                if re.match('^CD[1,2]_[1,2]', key) is not None:
                    # if key not in obsparam.values():
                    #     header.remove(key)
                    if not toolbox.if_val_in_dict(key, obsparam):
                        header.remove(key)
                elif 'PV' in key and '_' in key:
                    header.remove(key)
                elif key in (['CTYPE1', 'CRPIX1', 'CRVAL1', 'CROTA1',
                              'CROTA2', 'CFINT1', 'CTYPE2', 'CRPIX2',
                              'CRVAL2', 'CFINT2', 'LTM1_1', 'LTM2_2',
                              'WAT0_001', 'LTV1', 'LTV2', 'PIXXMIT',
                              'PIXOFFST', 'PC1_1', 'PC1_2', 'PC2_1', 'PC2_2',
                              'A_ORDER', 'A_0_0',
                              'A_0_1', 'A_0_2', 'A_1_0', 'A_1_1', 'A_2_0',
                              'B_ORDER', 'B_0_0', 'B_0_1', 'B_0_2', 'B_1_0',
                              'B_1_1', 'B_2_0', 'AP_ORDER', 'AP_0_0',
                              'AP_0_1', 'AP_0_2', 'AP_1_0', 'AP_1_1',
                              'AP_2_0', 'BP_ORDER', 'BP_0_0', 'BP_0_1',
                              'BP_0_2', 'BP_1_0', 'BP_1_1', 'BP_2_0',
                              'CDELT1', 'CDELT2', 'CRDELT1', 'CRDELT2'] +
                             ['TR{}_{}'.format(i, j)
                              for i in range(1, 3)
                              for j in range(15)]):
                    if not toolbox.if_val_in_dict(key, obsparam):
                        header.remove(key)

            # normalize CUNIT keywords
            try:
                if 'degree' in header['CUNIT1'].lower():
                    header['CUNIT1'] = ('deg')
                if 'degree' in header['CUNIT2'].lower():
                    header['CUNIT2'] = ('deg')
            except KeyError:
                pass

            # if GENERIC telescope, add implants to header
            if obsparam['telescope_keyword'] is 'GENERIC':
                for key, val in list(implants.items()):
                    header[key] = (val[0], val[1])

        # read out image binning mode
        binning = toolbox.get_binning(header, obsparam)

        # add pixel resolution keyword
        header['SECPIXX'] = (obsparam['secpix'][0]*binning[0],
                             'PP: x pixscale after binning')
        header['SECPIXY'] = (obsparam['secpix'][1]*binning[1],
                             'PP: y pixscale after binning')

        # create observation midtime jd
        if not keep_wcs or 'MIDTIMJD' not in header:
            if obsparam['date_keyword'].find('|') == -1:
                header['MIDTIMJD'] = \
                    (toolbox.dateobs_to_jd(header[obsparam['date_keyword']]) +
                     float(header[obsparam['exptime']])/2./86400.,
                     'PP: obs midtime')
            else:
                datetime = (header[obsparam['date_keyword'].split('|')[0]] +
                            'T' + header[obsparam['date_keyword'].split('|')[1]])
                datetime = datetime.replace('/', '-')
                header['MIDTIMJD'] = (toolbox.dateobs_to_jd(datetime) +
                                      float(
                                          header[obsparam['exptime']])/2./86400.,
                                      'PP: obs midtime')

        # other keywords
        header['TELINSTR'] = (obsparam['telescope_instrument'],
                              'PP: tel/instr name')
        header['TEL_KEYW'] = (obsparam['telescope_keyword'],
                              'PP: tel/instr keyword')

        header[obsparam['filter']] = header[obsparam['filter']].strip()
        header['FILTER'] = (header[obsparam['filter']], 'PP:copied')
        header['EXPTIME'] = (header[obsparam['exptime']], 'PP: copied')
        if obsparam['airmass'] in header:
            header['AIRMASS'] = (header[obsparam['airmass']], 'PP: copied')
        else:
            header['AIRMASS'] = (1, 'PP: fake airmass')

        # check if filter can be translated by PP
        try:
            obsparam['filter_translations'][header[obsparam['filter']]]
        except KeyError:
            logging.warning('cannot translate filter keyword \"' +
                            header[obsparam['filter']] +
                            '\"')
            #header[obsparam['filter']] = 'clear'
        header['FILTER'] = (header[obsparam['filter']], 'PP:copied')

        # perform header update
        for key, value in list(header_update.items()):
            if key in header:
                header['_'+key[:6]] = (header[key],
                                       'PP: old value for %s' % key)
            header[key] = (value, 'PP: manually updated')

        # check if OBJECT keyword is available
        if 'OBJECT' not in header:
            header['OBJECT'] = 'None'
        elif len(header['OBJECT'].strip()) == 0:
            header['OBJECT'] = 'None'

        # add fake wcs information that is necessary to run SCAMP

        # read out ra and dec from header
        if obsparam['radec_separator'] == 'XXX':
            ra_deg = float(header[obsparam['ra']])
            dec_deg = float(header[obsparam['dec']])
        else:
            ra_string = header[obsparam['ra']].split(
                obsparam['radec_separator'])
            dec_string = header[obsparam['dec']].split(
                obsparam['radec_separator'])
            ra_deg = 15.*(float(ra_string[0]) +
                          float(ra_string[1]) / 60. +
                          float(ra_string[2]) / 3600.)
            dec_deg = (abs(float(dec_string[0])) +
                       float(dec_string[1]) / 60. +
                       float(dec_string[2]) / 3600.)
            if dec_string[0].find('-') > -1:
                dec_deg = -1 * dec_deg

        # transform to equinox J2000, if necessary
        if 'EQUINOX' in header:
            equinox = float(header['EQUINOX'])
            if equinox != 2000.:
                anyeq = SkyCoord(ra=ra_deg*u.deg, dec=dec_deg*u.deg,
                                 frame=FK5,
                                 equinox=Time(equinox, format='jyear',
                                              scale='utc'))
                coo = anyeq.transform_to(ICRS)
                ra_deg = coo.ra.deg
                dec_deg = coo.dec.deg
                header['EQUINOX'] = (2000.0, 'PP: normalized to ICRS')

        if man_ra is not None and man_dec is not None:
            ra_deg = float(man_ra)
            dec_deg = float(man_dec)

        # special treatment for UKIRT/WFCAM
        if obsparam['telescope_keyword'] == 'UKIRTWFCAM':
            try:
                ra_deg = (float(header['TELRA'])/24.*360. -
                          float(header['JITTER_X'])/3600)
                dec_deg = (float(header['TELDEC']) -
                           float(header['JITTER_Y'])/3600)
            except KeyError:
                # JITTER keywords not in combined images
                pass

        # apply flips
        xnorm, ynorm = 1, 1
        if this_flipx:
            xnorm = -1
        if this_flipy:
            ynorm = -1

        # check if instrument has a chip offset
        ra_offset, dec_offset = 0, 0
        if (man_ra is None or man_dec is None) and \
           'chip_offset_fixed' in obsparam:
            cid = header[obsparam['chip_id']]
            ra_offset = float(obsparam['chip_offset_fixed'][cid][0])
            dec_offset = float(obsparam['chip_offset_fixed'][cid][1])

        if not keep_wcs:
            # create fake header
            header['RADECSYS'] = ('FK5', 'PP: fake wcs coordinates')
            header['RADESYS'] = ('FK5', 'PP: fake wcs coordinates')
            header['CTYPE1'] = ('RA---TAN', 'PP: fake Coordinate type')
            header['CTYPE2'] = ('DEC--TAN', 'PP: fake Coordinate type')
            header['CRVAL1'] = (ra_deg+ra_offset,
                                'PP: fake Coordinate reference value')
            header['CRVAL2'] = (dec_deg+dec_offset,
                                'PP: fake Coordinate reference value')
            header['CRPIX1'] = (int(float(header[obsparam['extent'][0]])/2),
                                'PP: fake Coordinate reference pixel')
            header['CRPIX2'] = (int(float(header[obsparam['extent'][1]])/2),
                                'PP: fake Coordinate reference pixel')

            # plugin default distortion parameters, if available
            if 'distort' in obsparam:
                if 'functionof' in obsparam['distort']:
                    pv_dict = obsparam['distort'][header[obsparam['distort']
                                                         ['functionof']]]
                else:
                    pv_dict = obsparam['distort']

                try:
                    for pv_key, pv_val in pv_dict.items():
                        header[pv_key] = (pv_val, 'PP: default distortion')
                except KeyError:
                    logging.error(('No distortion coefficients available for '
                                   '%s %s') % (obsparam['distort']['functionof'],
                                               header[obsparam['distort']
                                                      ['functionof']]))

            header['CD1_1'] = (xnorm * numpy.cos(this_rotate/180.*numpy.pi) *
                               obsparam['secpix'][0]*binning[0]/3600.,
                               'PP: fake Coordinate matrix')
            header['CD1_2'] = (ynorm * -numpy.sin(this_rotate/180.*numpy.pi) *
                               obsparam['secpix'][1]*binning[1]/3600.,
                               'PP: fake Coordinate matrix')
            header['CD2_1'] = (xnorm * numpy.sin(this_rotate/180.*numpy.pi) *
                               obsparam['secpix'][0]*binning[0]/3600.,
                               'PP: fake Coordinate matrix')
            header['CD2_2'] = (ynorm * numpy.cos(this_rotate/180.*numpy.pi) *
                               obsparam['secpix'][1]*binning[1]/3600.,
                               'PP: fake Coordinate matrix')

        # crop center from LOWELL42 frames
        if obsparam['telescope_keyword'] == 'LOWELL42':
            imdata = imdata[100:-100, 100:-100]
            logging.info('cropping LOWELL42 data')

        # overwrite imdata in case something has been modified
        hdulist[0].data = imdata

        # set flag keyword to SUCCESS
        header.set('PP_PREPA', 'SUCCESS')
        
        hdulist.flush()
        hdulist.close()

        logging.info('created fake wcs information for image %s' % filename)

    # create diagnostics
    if diagnostics:
        if display:
            print('creating diagnostic output')
        logging.info(' ~~~~~~~~~ creating diagnostic output')
        diag.add_index(filenames, os.getcwd(), obsparam)

    logging.info('Done! -----------------------------------------------------')

    return None


if __name__ == '__main__':

    # command line arguments
    parser = argparse.ArgumentParser(description=('prepare data for ' +
                                                  'photometry pipeline'))
    parser.add_argument('images', help='images to process', nargs='+')
    parser.add_argument("-ra",
                        help='image center position (RA J2000.0, deg)')
    parser.add_argument("-dec",
                        help='image center position (Dec J2000.0, deg)')
    parser.add_argument('-flipx', help='flip fake wcs x-axis',
                        action="store_true")
    parser.add_argument('-flipy', help='flip fake wcs y-axis',
                        action="store_true")
    parser.add_argument('-rotate', help='rotate fake wcs by angle (deg)',
                        default=0)
    parser.add_argument("-target",
                        help='target name (will overwrite OBJECT keyword)')
    parser.add_argument("-keep_wcs",
                        help='retain original wcs header information',
                        action='store_true')
    parser.add_argument("-telescope", help='manual telescope override',
                        default=None)

    args = parser.parse_args()
    man_ra = args.ra
    if man_ra is not None:
        man_ra = float(man_ra)
    man_dec = args.dec
    if man_dec is not None:
        man_dec = float(man_dec)
    man_flipx = args.flipx
    man_flipy = args.flipy
    man_rotate = float(args.rotate)
    man_target = args.target
    keep_wcs = args.keep_wcs
    telescope = args.telescope
    filenames = args.images

    # read telescope information from fits headers
    instruments = []
    for filename in filenames:
        try:
            hdulist = fits.open(filename, verify='ignore',
                                ignore_missing_end=True)
        except IOError:
            raise IOError('File %s does not exist! Abort.' % filename)

        header = hdulist[0].header
        for key in _pp_conf.instrument_keys:
            if key in header:
                instruments.append(header[key])
                break
            hdulist.close()

    if telescope is None:
        try:
            telescope = _pp_conf.instrument_identifiers[instruments[0]]
        except:
            print('cannot identify telescope/instrument; '
                  'use GENERIC telescope')
            logging.warning('cannot identify telescope/instrument; ' +
                            'use GENERIC telescope')
            telescope = 'GENERIC'

    obsparam = _pp_conf.telescope_parameters[telescope]

    header_update = {}
    if man_target is not None:
        header_update[obsparam['object']] = man_target

    # run prepare wrapper
    preparation = prepare(filenames, obsparam, header_update, keep_wcs=keep_wcs,
                          flipx=man_flipx, flipy=man_flipy,
                          man_ra=man_ra, man_dec=man_dec, rotate=man_rotate,
                          diagnostics=True, display=True)
