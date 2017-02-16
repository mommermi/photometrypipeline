#!/usr/bin/env python

""" PP_DISTILL - distill calibrated image databases into one database
                 of select moving or fixed sources
    v1.0: 2016-01-24, michael.mommert@nau.edu
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
import numpy
import os
import sys
import logging
import argparse
import time
import sqlite3
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt
from scipy.optimize import minimize
import callhorizons
import scipy.ndimage.interpolation


# only import if Python3 is used
if sys.version_info > (3,0):
    from builtins import str
    from builtins import range


# pipeline-specific modules
import _pp_conf
from catalog import *
from toolbox import *
import diagnostics as diag

# setup logging
logging.basicConfig(filename = _pp_conf.log_filename,
                    level    = _pp_conf.log_level,
                    format   = _pp_conf.log_formatline,
                    datefmt  = _pp_conf.log_datefmt)


def manual_positions(posfile, catalogs, display=True):
    """create targets for manually provided positions (using -positions
    option)"""

    if display:
        print('# target positions as a function of time manually provided... ', end=' ')
        sys.stdout.flush()
    logging.info('target positions as a function of time manually provided')

    positions = numpy.genfromtxt(posfile, dtype=[('filename', 'S50'),
                                                 ('ra', float),
                                                 ('dec', float),
                                                 ('MJD', float)])

    try:
        assert len(positions) == len(catalogs)
    except AssertionError:
        print (posfile + ' is not complete; has to provide a position ' +
               'for each frame')
        logging.error(posfile+' is not complete; has to provide position ' +
                      'for each frame')
        return []

    objects = []
    for cat_idx, cat in enumerate(catalogs):
        objects.append({'ident'      : 'manual_target',
                        'obsdate.jd' :  cat.obstime,
                        'cat_idx'    :  cat_idx,
                        'ra.deg'     :  positions[cat_idx]['ra'],
                        'dec.deg'    :  positions[cat_idx]['dec']})

    if display:
        print(old_div(len(objects),len(catalogs)), 'object(s) found')

    return objects


def pick_controlstar(catalogs, display=True):
    """match the first and the last catalog and pick a bright star"""

    if display:
        print('# pick control star... ', end=' ')
        sys.stdout.flush()
    logging.info('pick control star')

    match = catalogs[0].match_with(catalogs[-1],
            match_keys_this_catalog=['ra.deg', 'dec.deg'],
            match_keys_other_catalog=['ra.deg', 'dec.deg'],
            extract_this_catalog=['ra.deg', 'dec.deg', 'FLAGS'],
            extract_other_catalog=['ra.deg', 'dec.deg', 'FLAGS', 'MAG_APER'],
            tolerance=old_div(1.,3600.))

    objects = []
    if len(match[0][0]) > 0:

        ctlstar_idx = numpy.argsort(match[1][3])[int(0.05*len(match[1][3]))]

        for cat_idx, cat in enumerate(catalogs):
            objects.append({'ident'      : 'control_star',
                            'obsdate.jd' :  cat.obstime[0],
                            'cat_idx'    :  cat_idx,
                            'ra.deg'     :  match[1][0][ctlstar_idx],
                            'dec.deg'    :  match[1][1][ctlstar_idx]})
    else:
        print('  no common control star found in first and last frame')
        logging.info('no common control star found in first and last frame')

    if display:
        print('done!')

    return objects


def moving_primary_target(catalogs, man_targetname, offset, is_asteroid=None,
                          display=True):
    """
    is_asteroid == True:  this object is an asteroid
    is_asteroid == False: this object is a planet/moon/spacecraft
    is_asteroid == None:  no information on target nature
    """

    if display:
        print('# check JPL Horizons for primary target... ')
        sys.stdout.flush()
    logging.info('check JPL Horizons for primary target')

    obsparam = _pp_conf.telescope_parameters[
                        catalogs[0].origin.split(';')[0].strip()]

    objects = []

    ### check for target nature, if unknown
    if is_asteroid is None:
        cat = catalogs[0]
        targetname = cat.obj.replace('_', ' ')
        if man_targetname is not None:
            targetname = man_targetname.replace('_', ' ')
        for smallbody in [True, False]:
            eph = callhorizons.query(targetname, smallbody=smallbody)
            eph.set_discreteepochs(cat.obstime[0])
            n = 0
            try:
                n = eph.get_ephemerides(obsparam['observatory_code'])
            except ValueError:
                if display and smallbody is True:
                    print("'%s' is not an asteroid" % targetname)
                    logging.warning("'%s' is not an asteroid" %
                                    targetname)
                if display and smallbody is False:
                    print("'%s' is not a Solar System object" % targetname)
                    logging.warning("'%s' is not a Solar System object" %
                                    targetname)
                pass
            if n > 0:
                is_asteroid = smallbody
                break

    ### if is_asteroid is still None, this object is not in the Horizons db
    if is_asteroid is None:
        return objects

    message_shown = False

    ### query information for each image
    for cat_idx, cat in enumerate(catalogs):
        targetname = cat.obj.replace('_', ' ')
        if man_targetname is not None:
            targetname = man_targetname.replace('_', ' ')
            cat.obj = targetname
        eph = callhorizons.query(targetname, smallbody=is_asteroid)
        eph.set_discreteepochs(cat.obstime[0])

        try:
            n = eph.get_ephemerides(obsparam['observatory_code'])
        except ValueError:
            # if is_asteroid:
            #     if display and not message_shown:
            #         print 'is \'%s\' an asteroid?' % targetname
            #     logging.warning('Target (%s) is not an asteroid' % targetname)

            # else:
            #     if display and not message_shown:
            #         print ('is \'%s\' a different Solar System object?' %
            #                )targetname
            #     logging.warning('Target (%s) is not a Solar System object' %
            #                     targetname)
            #     n = None
            pass

        if n is None or n == 0:
            logging.warning('WARNING: No position from Horizons! '+\
                            'Name (%s) correct?' % cat.obj.replace('_', ' '))
            logging.warning('HORIZONS call: %s' % eph.url)
            if display and not message_shown:
                print ('  no Horizons data for %s '% cat.obj.replace('_', ' '))
                message_shown = True

        else:
            objects.append({'ident': cat.obj,
                            'obsdate.jd': cat.obstime[0],
                            'cat_idx'   : cat_idx,
                            'ra.deg'    : eph[0]['RA']-old_div(offset[0],3600.),
                            'dec.deg'   : eph[0]['DEC']-old_div(offset[1],3600.)})
            logging.info('Successfully grabbed Horizons position for %s ' %
                         cat.obj.replace('_', ' '))
            logging.info('HORIZONS call: %s' % eph.url)
            if display and not message_shown:
                print(cat.obj.replace('_', ' '), "identified")
                message_shown = True

    return objects


def fixed_targets(fixed_targets_file, catalogs, display=True):
    """add fixed target positions to object catalog"""

    if display:
        print('# read fixed target file... ', end=' ')
        sys.stdout.flush()
    logging.info('read fixed target file')


    fixed_targets = numpy.genfromtxt(fixed_targets_file,
                                     dtype=[('name', 'S20'),
                                            ('ra', float),
                                            ('dec', float)])

    # force array shape even for single line fixed_targets_files
    if len(fixed_targets.shape) == 0:
        fixed_targets = numpy.array([fixed_targets])

    objects = []
    for obj in fixed_targets:
        for cat_idx, cat in enumerate(catalogs):
            objects.append({'ident': obj['name'],
                            'obsdate.jd': cat.obstime[0],
                            'cat_idx'   : cat_idx,
                            'ra.deg'    : obj['ra'],
                            'dec.deg'   : obj['dec']})

    if display:
        print(old_div(len(objects),len(catalogs)), 'targets read')

    return objects


### ---- search for serendipitous observations

def serendipitous_asteroids(catalogs, display=True):
    return []

def serendipitous_variablestars(catalogs, display=True):
    """match catalogs with VSX catalog
    (http://cdsarc.u-strasbg.fr/viz-bin/Cat?cat=B%2Fvsx&target=readme&)
    contact me if you would like to use this feature"""

    # check if VSX database exists
    if _pp_conf.vsx_database_file is None or \
       not os.path.exists(_pp_conf.vsx_database_file):
        if display:
            print('# cannot find vsx.dat file - variable star search aborted')
        logging.info('cannot find vsx.dat file - variable star search aborted')
        return []

    if display:
        print('# match frames with variable star database... ', end=' ')
        sys.stdout.flush()
    logging.info('match frames with variable star database')


    # connect to VSX database
    db_conn = sql.connect(_pp_conf.vsx_database_file)
    db = db_conn.cursor()

    objects = []
    for cat_idx, catalog in enumerate(catalogs):
        # identify ra and dec ranges
        ra = (numpy.min(catalog['ra.deg']), numpy.max(catalog['ra.deg']))
        dec = (numpy.min(catalog['dec.deg']), numpy.max(catalog['dec.deg']))

        # query database
        db.execute(('SELECT * from vsx WHERE ((ra < %f) & (ra > %f) & ' +
                    '(dec < %f) & (dec > %f))') % (ra[1], ra[0],
                                                   dec[1], dec[0]))

        stars = db.fetchall()
        for star in stars:
            objects.append({'ident': star[0].strip(),
                            'obsdate.jd': catalog.obstime[0],
                            'cat_idx'   : cat_idx,
                            'ra.deg'    : star[1],
                            'dec.deg'   : star[2]})

    if display:
        print(old_div(len(objects),len(catalogs)), 'variable stars found')

    return objects



### -------------------


def distill(catalogs, man_targetname, offset, fixed_targets_file, posfile,
            display=False, diagnostics=False, serendipity=False):

    """
    distill wrapper
    """

    # start logging
    logging.info('starting distill with parameters: %s' % \
                 (', '.join([('%s: %s' % (var, str(val))) for
                             var, val in list(locals().items())])))

    output = {}

    ### read in database files (if necessary)
    if type(catalogs[0]) == str:
        filenames = catalogs[:]
        catalogs = []
        for filename in filenames:
            filename = filename[:filename.find('.fit')]+'.ldac.db'
            cat = catalog(filename)
            try:
                cat.read_database(filename)
            except IOError:
                logging.error('Cannot find database', filename)
                print('Cannot find database', filename)
                continue
            except sqlite3.OperationalError:
                logging.error('File %s is not a database file' % filename)
                print('File %s is not a database file' % filename)
                continue
            catalogs.append(cat)


    ##### identify target names and types

    objects = [] # one dictionary for each target

    if display:
        print('#------ Identify Targets')

    ### check for positions file
    if posfile is not None:
        objects += manual_positions(posfile, catalogs, display=display)

    ### select a sufficiently bright star as control star
    objects += pick_controlstar(catalogs, display=display)

    ### check Horizons for primary target (if a moving target)
    if posfile is None and fixed_targets_file is None:
        objects += moving_primary_target(catalogs, man_targetname, offset,
                                         display=display)

    ### add fixed target
    if fixed_targets_file is not None:
        objects += fixed_targets(fixed_targets_file, catalogs, display=display)

    ### serendipitous asteroids
    if serendipity:
        objects += serendipitous_asteroids(catalogs, display=display)

    ### serendipitous variable stars
    if serendipity:
        objects += serendipitous_variablestars(catalogs, display=display)

    if display:
        print('#-----------------------')

    if display:
        print(old_div(len(objects),len(catalogs)), \
            'potential target(s) per frame identified.')
        # print len(objects)/len(catalogs), \
        #     'potential target(s) per frame identified:', \
        #     ", ".join(set([obj['ident'] for obj in objects]))

    logging.info('%d potential targets per frame identified: %s' %
                 (int(old_div(len(objects),len(catalogs))),
                  ", ".join(set([obj['ident'] for obj in objects]))))


    ##### extract source data for identified targets

    data = []
    targetnames = {}

    # sort objects by catalog idx
    for cat_idx, cat in enumerate(catalogs):

        objects_thiscat = [obj for obj in objects if obj['cat_idx']==cat_idx]

        # create a new catalog
        target_cat = catalog('targetlist:_'+cat.catalogname)
        target_cat.add_fields(['ident', 'ra.deg', 'dec.deg'],
                              [[obj['ident'] for obj in objects_thiscat],
                               [obj['ra.deg'] for obj in objects_thiscat],
                               [obj['dec.deg'] for obj in objects_thiscat]],
                              ['20A', 'D', 'D'])

        # identify magnitudes
        mag_keys = ['MAG_APER', 'MAGERR_APER']
        for key in cat.fields:
            if 'mag' in key:
                mag_keys.append(key)


        # build field lists for observed catalogs
        match_keys_other_catalog, extract_other_catalog = [], []
        for key in ['ra.deg', 'dec.deg', 'XWIN_IMAGE', 'YWIN_IMAGE', 'FLAGS']:
            if key in cat.fields:
                match_keys_other_catalog.append(key)
                extract_other_catalog.append(key)


        match = target_cat.match_with \
                  (cat,
                   match_keys_this_catalog=('ra.deg', 'dec.deg'),
                   match_keys_other_catalog=match_keys_other_catalog,
                   extract_this_catalog=['ra.deg', 'dec.deg', 'ident'],
                   extract_other_catalog=extract_other_catalog+mag_keys,
                   tolerance=None)


        for i in range(len(match[0][0])):
            # derive calibrated magnitudes, if available
            try:
                cal_mag = match[1][len(extract_other_catalog)+2][i]
                cal_magerr = match[1][len(extract_other_catalog)+3][i]
            except IndexError:
                # use instrumental magnitudes
                cal_mag = match[1][len(extract_other_catalog)][i]
                cal_magerr = match[1][len(extract_other_catalog)+1][i]

            data.append([match[0][2][i], match[0][0][i], match[0][1][i],
                         match[1][0][i], match[1][1][i],
                         match[1][len(extract_other_catalog)][i],
                         match[1][len(extract_other_catalog)+1][i],
                         cal_mag, cal_magerr,
                         cat.obstime, cat.catalogname,
                         match[1][2][i], match[1][3][i],
                         cat.origin, match[1][4][i]])
            # format: ident, RA_exp, Dec_exp, RA_img, Dec_img,
            #         mag_inst, sigmag_instr, mag_cal, sigmag_cal
            #         obstime, filename, img_x, img_y, origin, flags

            targetnames[match[0][2][i]] = 1


    output['targetnames'] = targetnames

    ##### write results to ASCII file

    for target in targetnames:

        output[target] = []

        if display:
            print('write photometry results for %s' % target)
        outf = open('photometry_%s.dat' % target.replace(' ', '_'), 'w')
        outf.write('#                          filename    julian_date '
                   'ast_mag ast_sig        ast_ra       ast_dec    '
                   '[1]   [2]    [3]   [4]    [5]       ZP ZP_sig '
                   'inst_mag in_sig   [6] [7] [8] [9]\n')

        for dat in data:

            # sort measured magnitudes by target
            if dat[0] == target:
                try:
                    filtername = dat[13].split(';')[3]
                except IndexError:
                    filtername = '-'
                try:
                    catalogname = dat[13].split(';')[2]
                except IndexError:
                    catalogname = dat[13].split(';')[1]

                output[target].append(dat)
                outf.write(('%35.35s ' % dat[10].replace(' ', '_')) +
                           ('%15.7f ' % dat[9][0]) +
                           ('%8.4f ' % dat[7]) +
                           ('%6.4f ' % dat[8]) +
                           ('%13.8f ' % dat[3]) +
                           ('%+13.8f ' % dat[4]) +
                           ('%5.2f ' % ((dat[1] - dat[3]) * 3600.)) +
                           ('%5.2f ' % ((dat[2] - dat[4]) * 3600.)) +
                           ('%5.2f ' % offset[0]) +
                           ('%5.2f ' % offset[1]) +
                           ('%5.2f ' % dat[9][1]) +
                           ('%8.4f ' % (dat[7] - dat[5])) +
                           ('%6.4f ' % numpy.sqrt(dat[8]**2 - dat[6]**2)) +
                           ('%8.4f ' % dat[5]) +
                           ('%6.4f ' % dat[6]) +
                           ('%s ' % catalogname) +
                           ('%s ' % filtername) +
                           ('%3d ' % dat[14]) +
                           ('%s\n' % dat[13].split(';')[0]))

        outf.writelines('#\n# [1]: Horizons_RA - image_RA [arcsec]\n'+
                        '# [2]: Horizons_DDec - image_Dec [arcsec]\n'+
                        '# [3,4]: manual target offsets in RA and DEC ' +
                        '[arcsec]\n'+
                        '# [5]: exposure time (s)\n'+
                        '# [6]: photometric catalog\n' +
                        '# [7]: photometric band\n' +
                        '# [8]: Source Extractor flag\n' +
                        '# [9]: telescope/instrument\n')
        outf.close()


    ### output content
    #
    # { 'targetnames': list of all targets,
    #   '(individual targetname)': [ident, RA_exp, Dec_exp, RA_img, Dec_img,
    #                               mag_inst, sigmag_instr, mag_cal, sigmag_cal
    #                               obstime, filename, img_x, img_y],
    # }
    ###

    ##### create diagnostics
    if diagnostics:
        if display:
            print('extracting thumbnail images')
        diag.add_results(output)


    return output



if __name__ == '__main__':

    # command line arguments
    parser = argparse.ArgumentParser(description='distill sources of interest')
    parser.add_argument('-target', help='target name', default=None)
    parser.add_argument('-offset', help='primary target offset (arcsec)',
                        nargs=2, default=[0,0])
    parser.add_argument('-positions', help='positions file', default=None)
    parser.add_argument('-fixedtargets', help='target file', default=None)
    parser.add_argument('-serendipity',
                        help='search for serendipitous observations',
                        action="store_true")
    parser.add_argument('images', help='images to process', nargs='+')
    args = parser.parse_args()
    man_targetname = args.target
    man_offset = [float(coo) for coo in args.offset]
    fixed_targets_file = args.fixedtargets
    serendipity = args.serendipity
    posfile = args.positions
    filenames = args.images

    # check if input filenames is actually a list
    if len(filenames) == 1:
        if filenames[0].find('.lst') > -1 or filenames[0].find('.list') > -1:
            filenames = [filename[:-1] for filename in open(filenames[0], 'r').\
                         readlines()]

    distillate = distill(filenames, man_targetname, man_offset,
                         fixed_targets_file,
                         posfile, display=True, diagnostics=True,
                         serendipity=serendipity)


