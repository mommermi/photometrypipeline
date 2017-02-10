#!/usr/bin/env python

""" PP_CALIBRATE - match image databases against photometry catalogs
                   and derive magnitude zeropoint
    v1.0: 2016-01-15, michael.mommert@nau.edu
"""
from __future__ import print_function
from __future__ import division

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


from past.utils import old_div
import sys
import numpy
import subprocess
import argparse
import logging
import time
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt
from scipy.optimize import minimize

# only import if Python3 is used
if sys.version_info > (3,0):
    from builtins import range


# pipeline-specific modules
import _pp_conf
import diagnostics as diag
from catalog import *
from toolbox import *

# setup logging
logging.basicConfig(filename = _pp_conf.log_filename,
                    level    = _pp_conf.log_level,
                    format   = _pp_conf.log_formatline,
                    datefmt  = _pp_conf.log_datefmt)


def skycenter(catalogs, ra_key='ra.deg', dec_key='dec.deg'):
    """derive center position and radius from catalogs"""

    min_ra  = min([numpy.min(cat[ra_key]) for cat in catalogs])
    max_ra  = max([numpy.max(cat[ra_key]) for cat in catalogs])
    min_dec = min([numpy.min(cat[dec_key]) for cat in catalogs])
    max_dec = max([numpy.max(cat[dec_key]) for cat in catalogs])

    ra, dec = old_div((max_ra+min_ra),2.), old_div((max_dec+min_dec),2.)
    rad     = numpy.sqrt((old_div((max_ra-min_ra),2.))**2 + (old_div((max_dec-min_dec),2.))**2)

    logging.info('FoV center (%.7f/%+.7f) and radius (%.2f deg) derived' % \
                 (ra, dec, rad))

    return ra, dec, rad

### photometric fitting routines

def create_photometrycatalog(ra_deg, dec_deg, rad_deg, filtername,
                             preferred_catalogs,
                        min_sources=_pp_conf.min_sources_photometric_catalog,
                             max_sources=1e4, mag_accuracy=0.1,
                             display=False):
    """create a photometric catalog of the field of view"""

    for catalogname in preferred_catalogs:
        cat = catalog(catalogname, display)

        # load catalog
        n_sources = cat.download_catalog(ra_deg, dec_deg, rad_deg, max_sources)

        if display:
            print(n_sources, 'sources downloaded from', catalogname)
        if n_sources < min_sources:
            continue

        # transform catalog to requested filtername, if necessesary
        if ( n_sources > 0 and
             ('SDSS' in catalogname and
              filtername not in {'u', 'g', 'r', 'i', 'z'}) or
             ('URAT' in catalogname and
              filtername not in {'B', 'V', 'g', 'r', 'i'}) or
             ('APASS' in catalogname and
              filtername not in {'B', 'V', 'g', 'r', 'i'}) or
             ('2MASS' in catalogname and
              filtername not in {'J', 'H', 'Ks'}) ):
            n_transformed = cat.transform_filters(filtername) - \
                            cat.reject_sources_with(\
                                    cat['_e_'+filtername+'mag'] > mag_accuracy)

            if display and n_transformed > 0:
                print('%s transformed to %s-band: %d sources' % \
                    (catalogname, filtername, n_transformed))
            if n_transformed > min_sources:
                logging.info('more than %d sources (%d), use this catalog' %
                             (min_sources, n_transformed))
                return cat
        # no transformation necessary
        else:
            # reject sources that do not have measured magnitudes
            logging.info('rejecting sources with no magnitude information')

            n_sources = n_sources - cat.reject_sources_with(\
                                        numpy.isnan(cat[filtername+'mag'])) \
                                  - cat.reject_sources_with(\
                                      cat['e_'+filtername+'mag'] > mag_accuracy)

            if display:
                logging.info('%d sources with accurate magnitudes in %s band' %
                             (n_sources, filtername))
                print('%d sources with accurate magnitudes in %s band' % \
                    (n_sources, filtername))

            if n_sources > min_sources:
                logging.info('more than %d sources (%d), use this catalog' %
                             (min_sources, n_sources))
                return cat
            else:
                logging.info('less than %d sources (%d), try other catalog' %
                             (min_sources, n_sources))
                continue




    # end up here if none of the catalogs has n_sources > min_sources
    if display:
        print('ERROR: not enough sources in reference catalog %s (%d)' % \
            (catalogname, n_sources))
    logging.warning('not enough sources in reference catalog %s (%d)' % \
                    (catalogname, n_sources))
    return None




def derive_zeropoints(ref_cat, catalogs, filtername, minstars_external,
                      display=False, diagnostics=False):
    """derive zeropoint for a number of catalogs based on a reference catalog"""

    output = {'filtername':filtername, 'minstars': minstars_external,
              'zeropoints': [], 'clipping_steps': []}

    # match catalogs based on coordinates
    for cat in catalogs:

        logging.info('derive zeropoint for catalog: %s based on %s' %
                     (" | ".join([cat.catalogname, cat.origin, cat.history]),
                      " | ".join([ref_cat.catalogname, ref_cat.origin,
                                  ref_cat.history])))

        if display:
            print('zeropoint for %s:' % cat.catalogname, end=' ')

        filterkey = filtername+'mag' if filtername+'mag' \
                    in ref_cat.fields else '_'+filtername+'mag'
        efilterkey = 'e_'+filtername+'mag' if 'e_'+filtername+'mag' \
                     in ref_cat.fields else '_e_'+filtername+'mag'

        # reject sources with MAG_APER/MAGERR_APER = 99 or nan

        ### read this: if there is a
        # ValueError: boolean index array should have 1 dimension
        # pointing here, the problem is that pp_extract has not been
        # properly run using a single aperture
        ### currently it seems like pp_photometry (maybe callhorizons)
        # has not finished properly

        cat.reject_sources_other_than(cat.data['MAG_APER'] != 99)
        cat.reject_sources_other_than(cat.data['MAGERR_APER'] != 99)
        cat.reject_sources_with(numpy.isnan(cat.data['MAG_APER']))
        cat.reject_sources_with(numpy.isnan(cat.data['MAGERR_APER']))

        match = ref_cat.match_with(cat,
                                match_keys_this_catalog=['ra.deg', 'dec.deg'],
                                match_keys_other_catalog=['ra.deg', 'dec.deg'],
                                extract_this_catalog=[filterkey,
                                                      efilterkey,
                                                      'ident',
                                                      'ra.deg',
                                                      'dec.deg'],
                                extract_other_catalog=['MAG_APER',
                                                       'MAGERR_APER'],
                                tolerance=old_div(_pp_conf.pos_epsilon,3600.))

        # artificially blow up incredibly small ref_cat uncertainties
        for i in numpy.where(match[0][1] < 0.01):
            match[0][1][i] = 0.01

        residuals     = match[0][0]-match[1][0] # ref - instr
        residuals_sig = match[0][1]**2+match[1][1]**2
        m_idc         = list(range(len(match[0][0])))

        clipping_steps = []
        #  [zeropoint, sigma, chi2, source indices in match array, match]

        # fewer than 3 reference stars -> skip this catalog
        if len(residuals) < 3:
            if display:
                print(('Warning: %d reference stars after source matching ' \
                       + 'for frame %s') % (len(residuals), cat.catalogname))
                logging.warning(('Warning: %d reference stars after source ' \
                                + 'matching for frame %s') % \
                                (len(residuals), cat.catalogname))
                clipping_steps = [[0, 0, 1e-10, [], [[], []]]]

                output['zeropoints'].append({'filename':cat.catalogname,
                                'zp': numpy.nan,
                                'zp_sig': numpy.nan,
                                'zp_nstars': 0,
                                'zp_usedstars': 0,
                                'obstime':cat.obstime,
                                'match':[[],[]],
                                'clipping_steps':clipping_steps,
                                'zp_idx': numpy.nan,
                                'success': False })
                continue


        # if minstars is a fraction, use minstars*len(match[0][0])
        if minstars_external < 1:
            minstars = int(minstars_external*len(match[0][0]))
        else:
            minstars = int(minstars_external)

        # max 100 minstars
        if minstars > 100:
            minstars = 100


        # perform clipping to reject one outlier at a time
        zeropoint = 25 # initialize zeropoint
        while len(residuals) >= 3:
            fchi2 = lambda zp: numpy.sum([old_div((zp-residuals)**2,residuals_sig)])
            #fchi2 = lambda zp: numpy.sum((zp-residuals)**2) # unweighted

            minchi2   = minimize(fchi2, zeropoint, method='Nelder-Mead')
            red_chi2  = old_div(minchi2.fun,(len(residuals)-2))
            # reduced chi2: chi2/(N-observations-N_fit_variables-1)
            zeropoint = minchi2.x[0]

            # derive weighted standard deviation
            var = numpy.average((residuals-zeropoint)**2,
                                weights=old_div(1.,residuals_sig))
            #sigma = numpy.sqrt(var/(len(residuals)-1)) # weighted std of mean
            # weighted std + rms of individual sigmas
            # residuals_sig is already squared!
            sigma = numpy.sqrt(var + numpy.mean(residuals_sig))
            #sigma = numpy.std(residuals-zeropoint)

            clipping_steps.append([zeropoint, sigma, red_chi2, m_idc,
                                   match])

            # identify most significant outliers (not weighted) and remove them
            for repeat in range(max([1, int(old_div(len(residuals),25.))])):
                popidx        = numpy.argmax(numpy.absolute(residuals \
                                                            - zeropoint))
                residuals     = numpy.delete(residuals, popidx)
                residuals_sig = numpy.delete(residuals_sig, popidx)
                m_idc         = numpy.delete(m_idc, popidx)


        # select best-fit zeropoint based on minimum chi2
        idx = numpy.nanargmin([step[2] for step in clipping_steps])
        # # select best-fit zeropoint based on minimum sigma
        # idx = numpy.nanargmin([step[1] for step in clipping_steps])



        # reduce idx to increase the number of source until minstars is met
        while len(clipping_steps[idx][3]) < minstars and idx > 0:
            idx -= 1

        output['zeropoints'].append({'filename':cat.catalogname,
                                     'zp': clipping_steps[idx][0],
                                     'zp_sig': clipping_steps[idx][1],
                                     'zp_nstars': len(clipping_steps[idx][3]),
                                     'zp_usedstars': clipping_steps[idx][3],
                                     'obstime':cat.obstime,
                                     'match':match,
                                     'clipping_steps':clipping_steps,
                                     'zp_idx': idx,
                                     'success': True})


        print('%6.3f+-%.3f (%d/%d reference stars)' % \
            (clipping_steps[idx][0],clipping_steps[idx][1],
             len(clipping_steps[idx][3]), len(clipping_steps[0][3])))

        ### append calibrated magnitudes to catalog
        if filterkey[0] != '_':
            filterkey  = '_' + filterkey
            efilterkey = '_' + efilterkey


        cat.add_fields([filterkey, efilterkey],
                       [cat['MAG_APER'] + clipping_steps[idx][0],
                        numpy.sqrt(cat['MAGERR_APER']**2 + \
                                   clipping_steps[idx][1]**2)],
                       ['F', 'F'])

        # add ref_cat identifier to catalog
        cat.origin  = cat.origin.strip()+ ";" + ref_cat.catalogname + ";"\
                      + filtername
        cat.history += 'calibrated using ' + ref_cat.history

    output['catalogs'] = catalogs
    output['ref_cat']   = ref_cat


    ### output content
    #
    # { 'filtername'      : filter name,
    #   'minstars'        : requested minimum number/fraction of ref stars,
    #   'zeropoints'      : for each frame:
    #                       {'filename' : catalog name,
    #                        'zp'       : derived zeropoint,
    #                        'zp_sig'   : uncertainty,
    #                        'zp_nstars': number of reference stars available,
    #                        'zp_usedstars': numer used stars,
    #                        'obstime'  : observation midtime (JD),
    #                        'match'    : match array (see above),
    #                        'clipping_steps'  : clipping_steps (see above),
    #                        'zp_idx'   : zeropoint index
    #                       },
    #   'catalogs'        : ldac catalogs,
    #   'ref_cat'         : reference catalog
    # }
    ###

    return output


def calibrate(filenames, minstars, manfilter, manualcatalog,
              obsparam, maxflag=3, display=False, diagnostics=False):
    """
    wrapper for photometric calibration
    """

    ### read in ldac data into catalogs
    catalogs, filternames = [], {}
    for filename in filenames:
        hdulist = fits.open(filename, ignore_missing_end=True)
        try:
            filtername = hdulist[0].header['FILTER']
        except KeyError:
            print('Cannot read filter name from file %s' % filename)
            logging.error('Cannot read filter name from file %s' % filename)
            return None

        # translate filtername, if available
        try:
            filtername = obsparam['filter_translations'][filtername]
        except:
            pass

        if filtername in filternames:
            filternames[filtername].append(filename)
        else:
            filternames[filtername] = [filename]
        ldac_filename = filename[:filename.find('.fit')]+'.ldac'
        cat = catalog(filename)
        if display:
            print(cat.read_ldac(ldac_filename, filename, maxflag=maxflag,
                                object_keyword=obsparam['object'],
                                exptime_keyword=obsparam['exptime'],
                                time_keyword='MIDTIMJD'), \
                '(sources, columns) read from', filename)

        catalogs.append(cat)


    ### derive center and radius of field of view of all images
    ra_deg, dec_deg, rad_deg = skycenter(catalogs)


    ### obtain photometric catalog(s) of the field based on settings in
    # setup/telescope.py and the image filter
    if manfilter is not False:
        filtername = manfilter
    else:
        if len(filternames) == 1:
            filtername = list(filternames.keys())[0]
        else:
            logging.error(('ERROR: ambiguous filters in this ' \
                           + 'image sample (%s)') % \
                          ", ".join(['%s: %s' % (key, val)
                                     for key,val in list(filternames.items())]))
            if display:
                print('ERROR: ambiguous filters in this image sample (%s)' % \
                    ", ".join(['%s: %s' % (key, val)
                               for key,val in list(filternames.items())]))
            return []

    if manualcatalog is not None:
        preferred_catalogs = [manualcatalog]
    else:
        preferred_catalogs = obsparam['photometry_catalogs']

    if filtername is not None:
        ref_cat = create_photometrycatalog(ra_deg, dec_deg, rad_deg,
                                           filtername, preferred_catalogs,
                                           max_sources=2e4, display=display)
    else:
        ref_cat = None

    if ref_cat == None:
        print('Skip calibration - report instrumental magnitudes')
        logging.error('Skip calibration - report instrumental magnitudes')

        ### write calibrated database files
        logging.info('write calibrated data into database files')
        if display:
            print('write calibrated data into database files')
        for cat in catalogs:
            cat.write_database(cat.catalogname+'.db')

        logging.info('Done! ------------------------------------------------')

        return None

    ### match catalogs and derive magnitude zeropoint
    zp_data = derive_zeropoints(ref_cat, catalogs, filtername,
                                minstars, display=display,
                                diagnostics=diagnostics)

    ### zp_data content
    #
    # derive_zeropoints.output
    #
    ###

    ### update diagnostics website
    diag.add_calibration(zp_data)


    ### write calibrated database files
    logging.info('write calibrated data into database files')
    if display:
        print('write calibrated data into database files')
    for cat in catalogs:
        cat.write_database(cat.catalogname+'.db')

    logging.info('Done! -----------------------------------------------------')

    return zp_data



if __name__ == '__main__':

    # define command line arguments
    parser = argparse.ArgumentParser(description='photometric calibration')
    parser.add_argument('-minstars', help='min number of calibration stars '+\
                        'or fraction', default=0.5)
    parser.add_argument("-cat",
                        choices=_pp_conf.allcatalogs,
                        help="use this catalog instead of default one")
    parser.add_argument("-filter", help="manual filter override")
    parser.add_argument("-maxflag", help="maximum flag for all sources",
                        default=3)
    parser.add_argument('-instrumental',
                        help='skip calibration, ' + \
                             'only report instrumental magnitudes',
                        action="store_true")
    parser.add_argument('images', help='images to process', nargs='+')
    args = parser.parse_args()
    minstars = float(args.minstars)
    manfilter = args.filter
    maxflag = int(float(args.maxflag))
    manualcatalog = args.cat
    instrumental = args.instrumental
    filenames = args.images

    # manfilter: None: instrumental magnitudes, False: no manfilter provided
    if instrumental:
        manfilter = None
    else:
        if manfilter is None:
            manfilter = False

    # check if input filenames is actually a list
    if len(filenames) == 1:
        if filenames[0].find('.lst') > -1 or filenames[0].find('.list') > -1:
            filenames = [filename[:-1] for filename in open(filenames[0], 'r').\
                         readlines()]

    # obtain telescope information
    hdulist = fits.open(filenames[0], ignore_missing_end=True)
    try:
        telescope = hdulist[0].header['TEL_KEYW']
    except KeyError:
        print('ERROR: cannot find telescope keyword in image header;', \
            'has this image run through wcs_register?')
        sys.exit(0)
    obsparam = _pp_conf.telescope_parameters[telescope]

    calibration = calibrate(filenames, minstars, manfilter,
                            manualcatalog, obsparam, maxflag=maxflag,
                            display=True, diagnostics=True)








