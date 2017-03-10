"""
Photometry Pipeline Configuation File
2016-03-09, michael.mommert@nau.edu
"""

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

##### telescope/instrument configurations

# VATT, VATT4k
vatt4k_param = {
    'telescope_instrument' : 'VATT/VATT4k', # telescope/instrument name
    'telescope_keyword'    : 'VATT4K',      # telescope/instrument keyword
    'observatory_code'     : '290',         # MPC observatory code
    'secpix'               : (0.1875, 0.1875), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDBIN1', 'CCDBIN2'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS|TIME-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'TOP 2 BOT 1': 'V', 'TOP 3 BOT 1': 'R',
                              'TOP 4 BOT 1': 'I', 'TOP 5 BOT 1': 'B'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 12, # default sextractor source minimum N_pixels
    'aprad_default'        : 5, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/vatt4k.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/vatt4k.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTER,EXPTIME,OBJECT,' +
                              'DATE-OBS,TIME-OBS,RA,DEC,SECPIX,AIRMASS,' +
                              'TEL_KEYW'),
    #                         keywords to be copied in image
    #                         combination using swarp
    'swarp-config-file'    : rootpath+'/setup/vatt4k.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# DCT, LMI
dctlmi_param = {
    'telescope_instrument' : 'DCT/LMI', # telescope/instrument name
    'telescope_keyword'    : 'DCTLMI',  # telescope/instrument keyword
    'observatory_code'     : 'G37',         # MPC observatory code
    'secpix'               : (0.12, 0.12 ), # pixel size (arcsec)
                                            # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDSUM_blank0', 'CCDSUM_blank1'),
                           # binning in x/y, '_blankN' denotes that both axes
                           # are listed in one keyword, sep. by blanks
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                         # keyword; use
                                         # 'date|time' if
                                         # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTERS',  # filter keyword
    'filter_translations'  : {'V': 'V', 'R': 'R', 'B': 'B', 'VR': None,
                              'I': 'I', 'SDSS-U' : 'u', 'SDSS-G' : 'g',
                              'SDSS-R' : 'r', 'SDSS-I' : 'i',
                              'SDSS-Z' : 'z'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 9, # default sextractor source minimum N_pixels
    'aprad_default'        : 4, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/dctlmi.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/dctlmi.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('OBSERVAT,INSTRUME,CCDFLTID,EXPTIME,OBJECT,' +
                              'DATE-OBS,RA,DEC,SCALE,AIRMASS,TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/dctlmi.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}



# Apache Point ARC 3.5m, ARCTIC
arc35arctic_param = {
    'telescope_instrument' : 'ARC35m/ARCTIC', # telescope/instrument name
    'telescope_keyword'    : 'ARC35ARCTIC',   # telescope/instrument keyword
    'observatory_code'     : '705',         # MPC observatory code
    'secpix'               : (0.115, 0.115 ), # pixel size (arcsec)
                                            # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDBIN1', 'CCDBIN2'),
                           # binning in x/y, '_blankN' denotes that both axes
                           # are listed in one keyword, sep. by blanks
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                         # keyword; use
                                         # 'date|time' if
                                         # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJNAME',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'SDSS U':'u', 'SDSS G':'g', 'SDSS R': 'r',
                              'SDSS I': 'i', 'SDSS Z': 'z'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 10, # default sextractor source minimum N_pixels
    'aprad_default'        : 4, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/arc35arctic.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/arc35arctic.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('OBSERVAT,INSTRUME,FILTER,EXPTIME,OBJNAME,' +
                              'DATE-OBS,RA,DEC,AIRMASS,SECPIX,TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/arc35arctic.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# Apache Point ARC 3.5m, AGILE
arc35agile_param = {
    'telescope_instrument' : 'ARC35m/AGILE', # telescope/instrument name
    'telescope_keyword'    : 'ARC35AGILE',   # telescope/instrument keyword
    'observatory_code'     : '705',         # MPC observatory code
    'secpix'               : (0.13, 0.13 ), # pixel size (arcsec)
                                            # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('BINX', 'BINY'),
                           # binning in x/y, '_blankN' denotes that both axes
                           # are listed in one keyword, sep. by blanks
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                         # keyword; use
                                         # 'date|time' if
                                         # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJNAME',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'SDSS u':'u', 'SDSS g':'g', 'SDSS r': 'r',
                              'SDSS i': 'i', 'SDSS z': 'z'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 7, # default sextractor source minimum N_pixels
    'aprad_default'        : 4, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/arc35agile.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/arc35agile.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('OBSERVAT,INSTRUME,FILTER,EXPTIME,OBJNAME,' +
                              'DATE-OBS,RA,DEC,AIRMASS,SECPIX,TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/arc35agile.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# Magellan, IMACS
magimacs_param = {
    'telescope_instrument' : 'Magellan/IMACS', # telescope/instrument name
    'telescope_keyword'    : 'MAGIMACS',   # telescope/instrument keyword
    'observatory_code'     : '269',         # MPC observatory code
    'secpix'               : (0.11, 0.11 ), # pixel size (arcsec)
                                            # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences (for each chip)
    'chip_id'              : 'CHIP',        # chip identifier (remove,
                                            # if not existent)
    # the following keys are dictionaries if 'chip_id' exists, single
    # values otherwise
    'flipx'                : {1:True, 2:True, 3:True, 4:True, 5:True, 6:True,
                              7:True, 8:True},
    'flipy'                : {1:False, 2:False, 3:False, 4:False, 5:False,
                              6:False, 7:False, 8:False},
    'rotate'               : {1:270, 2:270, 3:270, 4:270, 5:90, 6:90,
                              7:90, 8:90},
    'chip_offset_fixed'    : {1:(-0.033, -0.099), 2:(-0.033, -0.033),
                              3:(-0.033, 0.033),  4:(-0.033, 0.099),
                              5:(0.033, -0.033),  6:(0.033, -0.099),
                              7:(0.033, 0.099),   8:(0.033, 0.033)},
                             # chip offset (ra, dec in degress) [optional]

    # instrument-specific FITS header keywords
    'binning'              : ('BINNING_x1', 'BINNING_x2'),
                           # binning in x/y, '_blankN' denotes that both axes
                           # are listed in one keyword, sep. by blanks
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS|UT-TIME', # obs date/time
                                         # keyword; use
                                         # 'date|time' if
                                         # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'Sloan_u': 'u', 'Sloan_g': 'g', 'Sloan_r': 'r',
                              'Sloan_i': 'i', 'Sloan_z': 'z'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 20, # default sextractor source minimum N_pixels
    'aprad_default'        : 8, # default aperture radius in px
    'aprad_range'          : [5, 25], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/magimacs.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/magimacs.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTER,EXPTIME,OBJECT,' +
                              'DATE-OBS,UT-TIME,RA,DEC,AIRMASS,' +
                              'SECPIX,TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/magimacs.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# Calar Alto 1.23m, DLR-MKIII
ca123dlrmkiii_param = {
    'telescope_instrument' : 'Calar Alto 1.23m/DLR-MKIII',# telescope/instrument
    'telescope_keyword'    : 'CA123DLRMKIII',   # telescope/instrument keyword
    'observatory_code'     : '493',         # MPC observatory code
    'secpix'               : (0.3132, 0.3132 ), # pixel size (arcsec)
                                            # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : True,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDBINX', 'CCDBINY'),
                           # binning in x/y, '_blankN' denotes that both axes
                           # are listed in one keyword, sep. by blanks
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : 'XXX',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                         # keyword; use
                                         # 'date|time' if
                                         # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'V_Johnson': 'V', 'R_Johnson': 'R', 'free': None},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 15, # default sextractor source minimum N_pixels
    'aprad_default'        : 4, # default aperture radius in px
    'aprad_range'          : [2, 15], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/ca123dlrmkiii.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/ca123dlrmkiii.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTER,EXPTIME,OBJECT,' +
                              'DATE-OBS,RA,DEC,AIRMASS,' +
                              'SECPIX,TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/ca123dlrmkiii.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# Lowell31, NASACAM
lowell31_param = {
    'telescope_instrument' : 'Lowell31/NASACAM', # telescope/instrument name
    'telescope_keyword'    : 'LOWELL31',      # telescope/instrument keyword
    'observatory_code'     : '688',         # MPC observatory code
    'secpix'               : (0.456, 0.456), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 270,

    # instrument-specific FITS header keywords
    'binning'              : ('CDELT1', 'CDELT2'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'TELRA',  # telescope pointing, RA
    'dec'                  : 'TELDEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS|UT', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER2',  # filter keyword
    'filter_translations'  : {'V': 'V', 'I': 'I'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 12, # default sextractor source minimum N_pixels
    'aprad_default'        : 5, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/lowell31.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/lowell31.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTER1,FILTER2,EXPTIME,OBJECT,' +
                              'DATE-OBS,UT,TELRA,TELDEC,SCALE,AIRMASS,' +
                              'TEL_KEYW'),
    #                         keywords to be copied in image
    #                         combination using swarp
    'swarp-config-file'    : rootpath+'/setup/lowell31.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# Lowell42, NASA42
lowell42_param = {
    'telescope_instrument' : 'Lowell42/NASA42', # telescope/instrument name
    'telescope_keyword'    : 'LOWELL42',      # telescope/instrument keyword
    'observatory_code'     : '688',         # MPC observatory code
    'secpix'               : (0.327, 0.327), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 90,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDSUM_blank1', 'CCDSUM_blank2'),
                           # binning in x/y, '_blankN' denotes that both axes
                           # are listed in one keyword, sep. by blanks
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'TELRA',  # telescope pointing, RA
    'dec'                  : 'TELDEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS|UTC-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTNAME',  # filter keyword
    'filter_translations'  : {'V': 'V', 'I': 'I', 'VR': None},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 12, # default sextractor source minimum N_pixels
    'aprad_default'        : 5, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/lowell42.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/lowell42.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,CCDSUM,FILTNAME,EXPTIME,'+
                              'OBJECT,' +
                              'DATE-OBS,UTC-OBS,TELRA,TELDEC,PIXSCAL,AIRMASS,' +
                              'TEL_KEYW'),
    #                         keywords to be copied in image
    #                         combination using swarp
    'swarp-config-file'    : rootpath+'/setup/lowell42.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# Lowell72 (Perkins), PRISM
lowell72_param = {
    'telescope_instrument' : 'Lowell72/PRISM', # telescope/instrument name
    'telescope_keyword'    : 'LOWELL72',      # telescope/instrument keyword
    'observatory_code'     : '688',         # MPC observatory code
    'secpix'               : (0.39, 0.39), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CRDELT1', 'CRDELT2'),
                           # binning in x/y, '_blankN' denotes that both axes
                           # are listed in one keyword, sep. by blanks
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'TELRA',  # telescope pointing, RA
    'dec'                  : 'TELDEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTNME3',  # filter keyword
    'filter_translations'  : {'V': 'V', 'I': 'I', 'R': 'R', 'VR': None},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 12, # default sextractor source minimum N_pixels
    'aprad_default'        : 5, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/lowell72.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/lowell72.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,CRDELT1, CRDELT2,FILTNME3,' +
                              'EXPTIME,OBJECT,' +
                              'DATE-OBS,TELRA,TELDEC,PIXSCAL,AIRMASS,' +
                              'TEL_KEYW'),
    #                         keywords to be copied in image
    #                         combination using swarp
    'swarp-config-file'    : rootpath+'/setup/lowell72.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}



# CTIO 0.9m, CFCCD
ctio09_param = {
    'telescope_instrument' : 'CTIO09/CFCCD', # telescope/instrument name
    'telescope_keyword'    : 'CTIO09',      # telescope/instrument keyword
    'observatory_code'     : '807',         # MPC observatory code
    'secpix'               : (0.396, 0.396), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : False,
    'flipy'                : False,
    'rotate'               : 180,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDSUM_blank1', 'CCDSUM_blank2'),
                             # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTERS',  # filter keyword
    'filter_translations'  : {'dia v': 'V', 'dia ov': 'V','dia i': 'I',
                              'dia r': 'R'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 15, # default sextractor source minimum N_pixels
    'aprad_default'        : 5, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/ctio09.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/ctio09.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTERS,EXPTIME,OBJECT,' +
                              'DATE-OBS,RA,DEC,CCDSUM,AIRMASS,' +
                              'TEL_KEYW'),
    #                         keywords to be copied in image
    #                         combination using swarp
    'swarp-config-file'    : rootpath+'/setup/ctio09.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# CTIO 1.0m, Y4KCAM
ctio10_param = {
    'telescope_instrument' : 'CTIO10/Y4KCAM', # telescope/instrument name
    'telescope_keyword'    : 'CTIO10',      # telescope/instrument keyword
    'observatory_code'     : '807',         # MPC observatory code
    'secpix'               : (0.289, 0.289), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 180,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDSUM_blank1', 'CCDSUM_blank2'),
                             # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS|TIME-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTERID',  # filter keyword
    'filter_translations'  : {'V': 'V', 'I': 'I'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 12, # default sextractor source minimum N_pixels
    'aprad_default'        : 5, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/ctio10.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/ctio10.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTER,EXPTIME,OBJECT,' +
                              'DATE-OBS,TIME-OBS, RA,DEC,CCDSUM,AIRMASS,' +
                              'TEL_KEYW'),
    #                         keywords to be copied in image
    #                         combination using swarp
    'swarp-config-file'    : rootpath+'/setup/ctio10.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# CTIO 1.3m, ANDICAM (CCD)
ctio13ccd_param = {
    'telescope_instrument' : 'CTIO/ANDICAM_CCD', # telescope/instrument name
    'telescope_keyword'    : 'CTIO13CCD',        # telescope/instrument keyword
    'observatory_code'     : '807',         # MPC observatory code
    'secpix'               : (0.185, 0.185), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDXBIN', 'CCDYBIN'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS|TIME-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'CCDFLTID',  # filter keyword
    'filter_translations'  : {'V': 'V', 'R': 'R', 'B': 'B'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'SECZ', # airmass keyword


    # source extractor settings
    'source_minarea'       : 15, # default sextractor source minimum N_pixels
    'aprad_default'        : 4, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/andicam.sex',
    'mask_file'            : {'2,2' : rootpath+'/setup/mask_andicam_2x2.fits'},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/andicam.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('OBSERVAT,INSTRUME,CCDFLTID,EXPTIME,OBJECT,' +
                              'DATE-OBS,TIME-OBS,RA,DEC,SECPIX,SECZ,' +
                              'TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/andicam.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# UH 88inch, SNIFS (imaging mode)
uh88snifs_param = {
    'telescope_instrument' : 'UH88/SNIFS', # telescope/instrument name
    'telescope_keyword'    : 'UH88SNIFS',        # telescope/instrument keyword
    'observatory_code'     : '568',         # MPC observatory code
    'secpix'               : (0.1365, 0.1365), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : True,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDBIN1', 'CCDBIN2'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'SDSS u': 'u', 'SDSS g': 'g', 'SDSS r': 'r',
                              'SDSS i': 'i', 'SDSS z': 'z', 'Bessell B': 'B',
                              'Bessell V': 'V', 'Bessell R': 'R',
                              'Bessell I': 'I'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 12, # default sextractor source minimum N_pixels
    'aprad_default'        : 3, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/uh88snifs.sex',
    'mask_file'            : {'2,2' : rootpath+'/setup/mask_snifs_2x2.fits'},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/uh88snifs.scamp',

    # swarp settings
    'copy_keywords'        : ('OBSERVAT,INSTRUME,FILTER,EXPTIME,OBJECT,' +
                              'DATE-OBS,RA,DEC,SECPIX,AIRMASS,' +
                              'TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/uh88snifs.swarp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}

# WIYN 0.9m, Half Degree Imager (HDI)
wiyn09hdi_param = {
    'telescope_instrument' : 'WIYN09/HDI', # telescope/instrument name
    'telescope_keyword'    : 'WIYN09HDI',  # telescope/instrument keyword
    'observatory_code'     : '695',         # MPC observatory code
    'secpix'               : (0.43, 0.43), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : False,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CCDBIN1', 'CCDBIN2'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RASTRNG',  # telescope pointing, RA
    'dec'                  : 'DECSTRNG', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER1',  # filter keyword
    'filter_translations'  : {'u': 'u', 'g': 'g', 'r': 'r',
                              'i': 'i', 'z': 'z'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 9, # default sextractor source minimum N_pixels
    'aprad_default'        : 3, # default aperture radius in px
    'aprad_range'          : [2, 8], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/wiyn09hdi.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/wiyn09hdi.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('OBSERVAT,INSTRUME,FILTER1,EXPTIME,OBJECT,' +
                              'DATE-OBS,RASTRNG,DECSTRNG,SECPIX,AIRMASS,' +
                              'TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/wiyn09hdi.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}



# Generic telescope (e.g., amateur telescope)
generic_param = {
    'telescope_instrument' : 'Generic', # telescope/instrument name
    'telescope_keyword'    : 'GENERIC',     # telescope/instrument keyword
    'observatory_code'     : None,         # MPC observatory code
    'secpix'               : (None, None), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : False,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    # in this GENERIC setup, all keywords are suggested
    # and will be checked in pp_prepare
    'binning'              : ('BINX', 'BINY'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'OBJCTRA',  # telescope pointing, RA
    'dec'                  : 'OBJCTDEC', # telescope pointin, Dec
    'radec_separator'      : ' ',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'V': 'V', 'R': 'R', 'clear': None, '': None},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 8, # default sextractor source minimum N_pixels
    'aprad_default'        : 3, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/generic.sex',
    'mask_file'            : {}, #'2,2' : rootpath+'/setup/mask_snifs_2x2.fits'},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/generic.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('OBSERVAT,INSTRUME,EXPTIME,OBJECT,' +
                              'DATE-OBS,TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/generic.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}

# SPM 1.3m, RATIR
ratir_param = {
    'telescope_instrument' : 'RATIR', # telescope/instrument name
    'telescope_keyword'    : 'RATIR',        # telescope/instrument keyword
    'observatory_code'     : '679',         # MPC observatory code
    'secpix'               : (0.15, 0.15), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : False,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('SC_CH_DTBN', 'SC_CH_DTBN'), # binning in x/y
                             # _CH_ gets replaced with Channel number
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'STRSTRA',  # telescope pointing, RA
    'dec'                  : 'STRSTDE', # telescope pointin, Dec
    'radec_separator'      : 'XXX',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'SSHT', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'g': 'g', 'r': 'r', 'i': 'i', 'z': 'z',
                              'J': 'J', 'H': 'H'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'STROBAM', # airmass keyword


    # source extractor settings
    'source_minarea'       : 18, # default sextractor source minimum N_pixels
    'aprad_default'        : 4, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/ratir.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/ratir.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTER,EXPTIME,OBJECT' +
                              'SSHT,STRSTRA,STRSTDE,SECPIX,STROBAM,' +
                              'TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/ratir.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# # Sutherland 74 inch, SHA
# sl74sha_param = {
#     'telescope_instrument' : 'Sutherland74SHA', # telescope/instrument name
#     'telescope_keyword'    : 'SL74SHA',        # telescope/instrument keyword
#     'observatory_code'     : 'K94',         # MPC observatory code
#     'secpix'               : (0.08, 0.08), # pixel size (arcsec)
#                                                # before binning
#     'ext_coeff'            : 0.05,          # typical extinction coefficient


#     # image orientation preferences
#     'flipx'                : False,
#     'flipy'                : False,
#     'rotate'               : 0,

#     # instrument-specific FITS header keywords
#     'binning'              : ('HBIN', 'VBIN'), # binning in x/y
#                              # _CH_ gets replaced with Channel number
#     'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
#     'ra'                   : 'TELRA',  # telescope pointing, RA
#     'dec'                  : 'TELDEC', # telescope pointin, Dec
#     'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
#                                     # if already in degrees
#     'date_keyword'         : 'FRAME', # obs date/time
#                                                   # keyword; use
#                                                   # 'date|time' if
#                                                   # separate
#     'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
#                                          # (usually provided by
#                                          # pp_prepare
#     'object'               : 'OBJECT',  # object name keyword
#     'filter'               : 'FILTERA',  # filter keyword
#     'filter_translations'  : {'V - Green': 'V'},
#                              # filtername translation dictionary
#     'exptime'              : 'EXPOSURE', # exposure time keyword (s)
#     'airmass'              : 'AIRMASS', # airmass keyword


#     # source extractor settings
#     'source_minarea'       : 12, # default sextractor source minimum N_pixels
#     'aprad_default'        : 4, # default aperture radius in px
#     'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
#     'sex-config-file'      : rootpath+'/setup/sl74sha.sex',
#     'mask_file'            : {},
#     #                        mask files as a function of x,y binning

#     # scamp settings
#     'scamp-config-file'    : rootpath+'/setup/sl74sha.scamp',

#     # swarp settings
#     'copy_keywords'        : ('TELESCOP,INSTRUME,FILTERA,EXPOSURE,OBJECT' +
#                               'FRAME,TELRA,TELDEC,SECPIX,AIRMASS,' +
#                               'TEL_KEYW'),
#     #                        keywords to be copied in image
#     #                        combination using swarp
#     'swarp-config-file'    : rootpath+'/setup/sl74sha.swarp',

#     # default catalog settings
#     'astrometry_catalogs'  : ['URAT-1', '2MASS', 'USNO-B1'],
#     'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
# }

# SOAR, Goodman (imager)
# running Goodman data requires the removal of header keywords
# PARAM0, PARAM61, PARAM62, PARAM63 (degree symbol is non-ASCII)
soargoodman_param = {
    'telescope_instrument' : 'SOAR/GOODMAN', # telescope/instrument name
    'telescope_keyword'    : 'SOARGOODMAN',  # telescope/instrument keyword
    'observatory_code'     : 'I33',         # MPC observatory code
    'secpix'               : (0.15, 0.15), # pixel size (arcsec)
                                               # before binning
    'ext_coeff'            : 0.05,          # typical extinction coefficient


    # image orientation preferences
    'flipx'                : True,
    'flipy'                : True,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('PARAM18', 'PARAM22'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointin, Dec
    'radec_separator'      : ':',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'Rc': 'R', 'V':'V', 'B':'B', 'u':'u',
                              'g-SDSS': 'g', 'r-SDSS': 'r', 'i-SDSS': 'i',
                              'z-SDSS': 'z'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword


    # source extractor settings
    'source_minarea'       : 15, # default sextractor source minimum N_pixels
    'aprad_default'        : 4, # default aperture radius in px
    'aprad_range'          : [2, 10], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/soargoodman.sex',
    'mask_file'            : {'1,1' : rootpath+'/setup/mask_soargoodman_1x1.fits',
                              '2,2' : rootpath+'/setup/mask_soargoodman_2x2.fits'},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/soargoodman.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # swarp settings
    'copy_keywords'        : ('TELESCOP,INSTRUME,FILTER,EXPTIME,OBJECT,' +
                              'DATE-OBS,RA,DEC,SECPIX,AIRMASS,' +
                              'TEL_KEYW'),
    #                        keywords to be copied in image
    #                        combination using swarp
    'swarp-config-file'    : rootpath+'/setup/soargoodman.swarp',

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}

# Observatoire de Haute-Provence, 120cm, CCD
ohp120_param = {
    'telescope_instrument' : 'OHP120cm/CCD', # telescope/instrument name
    'telescope_keyword'    : 'OHP120',      # telescope/instrument keyword
    'observatory_code'     : '511',         # MPC observatory code
    'secpix'               : (0.385, 0.385), # pixel size (arcsec) before binning

    # image orientation preferences
    'flipx'                : True,
    'flipy'                : True,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('XBINNING', 'YBINNING'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointing, Dec
    'radec_separator'      : 'XXX',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJECT',  # object name keyword
    'filter'               : 'FILTER',  # filter keyword
    'filter_translations'  : {'R_Cousins': 'R', 'V_Cousins': 'V',
                              'B_Cousins': 'B', 'H-alpha': None,
                              'i_Gunn': 'i'},
                             # filtername translation dictionary

    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword

    # source extractor settings
    'source_minarea'       : 15, # default sextractor source minimum N_pixels
    'aprad_default'        : 8, # default aperture radius in px
    'aprad_range'          : [2, 15], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/ohp120.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/ohp120.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# Telescopio Nazionale Galileo, DOLORES
tngdolores_param = {
    'telescope_instrument' : 'TNG/DOLORES', # telescope/instrument name
    'telescope_keyword'    : 'TNGDOLORES',      # telescope/instrument keyword
    'observatory_code'     : 'Z19',         # MPC observatory code
    'secpix'               : (0.252, 0.252), # pixel size (arcsec) before binning

    # image orientation preferences
    'flipx'                : True,
    'flipy'                : True,
    'rotate'               : 0,

    # instrument-specific FITS header keywords
    'binning'              : ('CRDELT1', 'CRDELT2'), # binning in x/y
    'extent'               : ('NAXIS1', 'NAXIS2'),   # N_pixels in x/y
    'ra'                   : 'RA',  # telescope pointing, RA
    'dec'                  : 'DEC', # telescope pointing, Dec
    'radec_separator'      : 'XXX',   # RA/Dec hms separator, use 'XXX'
                                    # if already in degrees
    'date_keyword'         : 'DATE-OBS', # obs date/time
                                                  # keyword; use
                                                  # 'date|time' if
                                                  # separate
    'obsmidtime_jd'        : 'MIDTIMJD', # obs midtime jd keyword
                                         # (usually provided by
                                         # pp_prepare
    'object'               : 'OBJCAT',  # object name keyword
    'filter'               : 'FLT_ID',  # filter keyword
    'filter_translations'  : {'B_JOHN_10': 'B', 'V_JOHN_11': 'V',
                              'R_JOHN_12': 'R', 'I_JOHN_13': 'I'},
                             # filtername translation dictionary
    'exptime'              : 'EXPTIME', # exposure time keyword (s)
    'airmass'              : 'AIRMASS', # airmass keyword

    # source extractor settings
    'source_minarea'       : 15, # default sextractor source minimum N_pixels
    'aprad_default'        : 8, # default aperture radius in px
    'aprad_range'          : [2, 15], # [minimum, maximum] aperture radius (px)
    'sex-config-file'      : rootpath+'/setup/tngdolores.sex',
    'mask_file'            : {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file'    : rootpath+'/setup/tngdolores.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # default catalog settings
    'astrometry_catalogs'  : ['GAIA'],
    'photometry_catalogs'  : ['SDSS-R9', 'APASS9', '2MASS']
}


# KPNO 4m Mayall, MOSAIC-1, 1.1 and 3
kpno4mos1_param = {
    'telescope_instrument': 'KPNO4m/MOSAIC',  # telescope/instrument name
    'telescope_keyword': 'KPNO4MOS1',  # telescope/instrument keyword
    'observatory_code': '695',  # MPC observatory code
    'secpix': (0.2666, 0.2666),  # pixel size (arcsec) before binning

    # image orientation preferences
    'flipx': True,
    'flipy': False,
    'rotate': 0,

    # instrument-specific FITS header keywords
    'binning': (1, 1),  # binning in x/y
    'extent': ('NAXIS1', 'NAXIS2'),  # N_pixels in x/y
    'ra': 'RA',  # telescope pointing, RA
    'dec': 'DEC',  # telescope pointin, Dec
    'radec_separator': ':',  # RA/Dec hms separator, use 'XXX'
    # if already in degrees
    'date_keyword': 'DATE-OBS',  # obs date/time
    # keyword; use
    # 'date|time' if
    # separate
    'obsmidtime_jd': 'MJD-OBS',  # obs midtime jd keyword
    # (usually provided by
    # pp_prepare
    'object': 'OBJECT',  # object name keyword
    'filter': 'FILTER',  # filter keyword
    'filter_translations': {'g SDSS k1017': 'g',
                            'r SDSS k1018': 'r',
                            'i SDSS k1019': 'i',
                            'z SDSS c6020': 'z', # mosaic1.1
                            'z SDSS k1020': 'z', # mosaic3
                            'B Harris k1002': 'B',
                            'none': None},
    # filtername translation dictionary
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'airmass': 'AIRMASS',  # airmass keyword

    # source extractor settings
    'source_minarea': 12,  # default sextractor source minimum N_pixels
    'aprad_default': 5,  # default aperture radius in px
    'aprad_range': [2, 10],  # [minimum, maximum] aperture radius (px)
    'sex-config-file': rootpath + '/setup/kpno4mos1.sex',
    'mask_file': {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file': rootpath + '/setup/kpno4mos1.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg


    # default catalog settings
    'astrometry_catalogs': ['GAIA'],
    'photometry_catalogs': ['SDSS-R9', 'APASS9', '2MASS']
}

# KPNO 4m Mayall, NEWFIRM
kpno4newf_param = {
    'telescope_instrument': 'KPNO4m/NEWFIRM',  # telescope/instrument name
    'telescope_keyword': 'KPNO4NEWF',  # telescope/instrument keyword
    'observatory_code': '695',  # MPC observatory code
    'secpix': (0.4, 0.4),  # pixel size (arcsec) before binning

    # image orientation preferences
    'flipx': True,
    'flipy': False,
    'rotate': 0,

    # instrument-specific FITS header keywords
    'binning': (1, 1),  # binning in x/y
    'extent': ('NAXIS1', 'NAXIS2'),  # N_pixels in x/y
    'ra': 'RA',  # telescope pointing, RA
    'dec': 'DEC',  # telescope pointin, Dec
    'radec_separator': ':',  # RA/Dec hms separator, use 'XXX'
    # if already in degrees
    'date_keyword': 'DATE-OBS',  # obs date/time
    # keyword; use
    # 'date|time' if
    # separate
    'obsmidtime_jd': 'MJD-OBS',  # obs midtime jd keyword
    # (usually provided by
    # pp_prepare
    'object': 'OBJECT',  # object name keyword
    'filter': 'FILTER',  # filter keyword
    'filter_translations': {'KXs': 'K',
                            'JX': 'J',
                            'none': None},
    # filtername translation dictionary
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'airmass': 'AIRMASS',  # airmass keyword

    # source extractor settings
    'source_minarea': 12,  # default sextractor source minimum N_pixels
    'source_snr': 3, # default sextractor source snr for registration
    'aprad_default': 5,  # default aperture radius in px
    'aprad_range': [2, 10],  # [minimum, maximum] aperture radius (px)
    'sex-config-file': rootpath + '/setup/kpno4mos1.sex',
    'mask_file': {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file': rootpath + '/setup/kpno4mos1.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg
    'source_tolerance': 'high',


    # default catalog settings
    'astrometry_catalogs': ['GAIA'],
    'photometry_catalogs': ['2MASS']
}

# SALT, SALTICAM
saltsalticam_param = {
    'telescope_instrument': 'SALT/SALTICAM',  # telescope/instrument name
    'telescope_keyword': 'SALTSALTICAM',  # telescope/instrument keyword
    'observatory_code': 'B31',  # MPC observatory code
    'secpix': (0.138, 0.138),  # pixel size (arcsec) before binning

    # image orientation preferences
    'flipx': True,
    'flipy': False,
    'rotate': 0,

    # instrument-specific FITS header keywords
    'binning': (1, 1),  # binning in x/y
    'extent': ('NAXIS1', 'NAXIS2'),  # N_pixels in x/y
    'ra': 'RA',  # telescope pointing, RA
    'dec': 'DEC',  # telescope pointin, Dec
    'radec_separator': ':',  # RA/Dec hms separator, use 'XXX'
    # if already in degrees
    'date_keyword': 'DATE-OBS|TIME-OBS',  # obs date/time keyword
    # use 'date|time' if separate keywords eg, DATE-OBS|TIME-OBS

    'obsmidtime_jd': 'JD',  # obs midtime jd keyword
    # (usually provided by
    # pp_prepare
    'object': 'OBJECT',  # object name keyword
    'filter': 'FILTER',  # filter keyword
    'filter_translations': {'SDSSi-S1': 'i',
                            'SDSSr-S1': 'r',
                            'none': None},
    # filtername translation dictionary
    'exptime': 'EXPTIME',  # exposure time keyword (s)
    'airmass': 'AIRMASS',  # airmass keyword

    # source extractor settings
    'source_minarea': 12,  # default sextractor source minimum N_pixels
    'aprad_default': 5,  # default aperture radius in px
    'aprad_range': [2, 10],  # [minimum, maximum] aperture radius (px)
    'sex-config-file': rootpath + '/setup/saltsalticam.sex',
    'mask_file': {},
    #                        mask files as a function of x,y binning

    # scamp settings
    'scamp-config-file': rootpath + '/setup/saltsalticam.scamp',
    'reg_max_mag'          : 19,
    'reg_search_radius'    : 0.5, # deg

    # default catalog settings
    'astrometry_catalogs': ['GAIA'],
    'photometry_catalogs': ['SDSS-R9', 'APASS9', '2MASS']
}


##### access functions for telescope configurations


implemented_telescopes = ['VATT4K', 'DCTLMI', 'ARC35ARCTIC',
                          'ARC35AGILE', 'MAGIMACS', 'LOWELL31', 'LOWELL42',
                          'LOWELL72',
                          'CTIO09', 'CTIO10', 'CTIO13CCD', 'UH88SNIFS',
                          'WIYN09HDI', 'RATIR', 'SOARGOODMAN', 'OHP120',
                          #'SL74SAH',
                          'TNGDOLORES', 'GENERIC', 'KPNO4MOS1', 'SALTSALTICAM']

# translate INSTRUME (or others, see _pp_conf.py) header keyword into
# PP telescope keyword
instrument_identifiers = {'= "Vatt4k"':        'VATT4K',
                          'LMI':               'DCTLMI',
                          'arctic':            'ARC35ARCTIC',
                          'agile':             'ARC35AGILE',
                          'IMACS Long-Camera': 'MAGIMACS',
                          'DLR-MKIII':         'CA123DLRMKIII',
                          'NASAcam':           'LOWELL31',
                          'nasa42':            'LOWELL42',
                          'PRISM Instrument':  'LOWELL72',
                          'Prism 2048x2048 CCD':'LOWELL72',
                          'cfccd':             'CTIO09',
                          'Y4KCam':            'CTIO10',
                          'ANDICAM-CCD':       'CTIO13CCD',
                          'SNIFS':             'UH88SNIFS',
                          'hdi':               'WIYN09HDI',
                          'ArtemisHSC':        'GENERIC',
                          'GENERIC':           'GENERIC',
                          'C0':                'RATIR',
                          'C1':                'RATIR',
                          'C2':                'RATIR',
                          'C3':                'RATIR',
                          'C4':                'RATIR',
                          #'SHA':               'SL74SHA',
                          'Goodman Spectrograph': 'SOARGOODMAN',
                          'Andor Tech':        'OHP120',
                          'LRS':               'TNGDOLORES',
                          'mosaic_1_1':        'KPNO4MOS1',
                          'Mosaic3':           'KPNO4MOS1',
                          'newfirm':           'KPNO4NEWF',
                          'SALTICAM':          'SALTSALTICAM'}

# translate telescope keyword into parameter set defined here
telescope_parameters = {'VATT4K' :       vatt4k_param,
                        'DCTLMI':        dctlmi_param,
                        'ARC35ARCTIC':   arc35arctic_param,
                        'ARC35AGILE':    arc35agile_param,
                        'MAGIMACS':      magimacs_param,
                        'CA123DLRMKIII': ca123dlrmkiii_param,
                        'LOWELL31':      lowell31_param,
                        'LOWELL42':      lowell42_param,
                        'LOWELL72':      lowell72_param,
                        'CTIO09':        ctio09_param,
                        'CTIO10':        ctio10_param,
                        'CTIO13CCD':     ctio13ccd_param,
                        'UH88SNIFS':     uh88snifs_param,
                        'WIYN09HDI':     wiyn09hdi_param,
                        'GENERIC':       generic_param,
                        'RATIR':         ratir_param,
                        #'SL74SHA':       sl74sha_param,
                        'SOARGOODMAN':   soargoodman_param,
                        'OHP120':        ohp120_param,
                        'TNGDOLORES':    tngdolores_param,
                        'KPNO4MOS1':     kpno4mos1_param,
                        'KPNO4NEWF':     kpno4newf_param,
                        'SALTSALTICAM':  saltsalticam_param}


#### append mytelescopes.py, if available
#
# mytelescopes.py allows you to setup your own telescope; that file is
# not part of the github repository, hence it will not be affected by
# pulls and pushes
#
# an example mytelescopes.py file is available here:
# http://134.114.60.45/photometrypipeline/mytelescopes.py
# more information are available on the PP documentation website:
# http://mommermi.github.io/pp/install.html

try:
    execfile(rootpath+'/setup/mytelescopes.py')
except IOError:
    pass
