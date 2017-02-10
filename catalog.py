"""
CATALOG - class structure for dealing with astronomical catalogs,
          FITS_LDAC files, and sqlite databases.

version 0.9, 2016-01-27, michael.mommert@nau.edu
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
import os
import sys
import numpy
import logging
#import urllib.request, urllib.error, urllib.parse
import time
import sqlite3 as sql
from scipy import spatial
from astropy.io import fits
import scipy.optimize as optimization
from astroquery.vizier import Vizier
import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table, Column


# only import if Python3 is used
if sys.version_info > (3,0):
    from builtins import str
    from future import standard_library
    standard_library.install_aliases()
    from builtins import zip
    from builtins import filter
    from builtins import range
    from builtins import object


# pipeline-related modules (only needed for testing)
import _pp_conf

# setup logging
logging.basicConfig(filename = _pp_conf.log_filename,
                    level    = _pp_conf.log_level,
                    format   = _pp_conf.log_formatline,
                    datefmt  = _pp_conf.log_datefmt)


class catalog(object):
    def __init__(self, catalogname, display=False):
        self.data         = None # will be an astropy table
        self.catalogname  = catalogname
        self.obstime      = [None, None] # observation midtime (JD) +
                                         # duration
        self.obj          = None # header target name
        self.origin       = '' # where does the data come from?
        self.history      = '' # catalog history
        self.magsys       = '' # [AB|Vega|instrumental]
        self.display      = display

    #### data access functions

    @property
    def shape(self):
        """
        return: tuple of number of sources and fields
        """
        try:
            return (len(self.data), len(self.fields))
        except AttributeError:
            return (len(self.data), len(self.data.columns))

    @property
    def fields(self):
        """
        return: array of all available fields
        """
        return self.data.columns

    def __getitem__(self, ident):
        """
        return: source or field
        """
        return self.data[ident]


    ##### data manipulation functions

    def reject_sources_other_than(self, condition):
        """
        reject sources based on condition
        input: condition
        return: number of sources left
        """

        n_raw = self.shape[0]

        self.data = self.data[condition]

        logging.info('%s:reject %s sources' %
                     (self.catalogname, n_raw-self.shape[0]))

        return len(self.data)


    def reject_sources_with(self, condition):
        """
        reject sources based on condition
        input: condition
        return: number of sources left
        """

        n_raw = self.shape[0]
        self.data = self.data[~condition]

        logging.info('%s:reject %s sources' %
                     (self.catalogname, n_raw-self.shape[0]))

        return n_raw - len(self.data)


    def add_field(self, field_name, field_array, field_type='D'):
        """
        single-field wrapper for add_fields
        """
        ### numpy.recarray treatment
        #return self.add_fields([field_name], [field_array], [field_type])

        ### astropy.table treatment
        return self.data.add_column(Column(field_array, name=field_name,
                                           format=field_type))


    def add_fields(self, field_names, field_arrays, field_types):
        """
        add fields to self.data
        input: field_names, field_arrays, field_types
        output: number of added fields
        """

        assert len(field_names) == len(field_arrays) == len(field_types)

        if self.data is None:
            self.data = Table()

        for i in range(len(field_names)):
            self.data.add_column(Column(numpy.array(field_arrays[i]),
                                        name=field_names[i],
                                        format=field_types[i]))

        return len(field_arrays)




    ##### data io

    ### online catalog access

    def download_catalog(self, ra_deg, dec_deg, rad_deg,
                         max_sources, save_catalog=False,
                         max_mag=21):
        """
        download existing catalog from VIZIER server using self.catalogname
        input: ra_deg, dec_deg, rad_deg, max_sources, (display_progress),
               (sort=['ascending', 'descending', None])
        return: number of sources downloaded

        astrometric catalogs: ra.deg, dec.deg, e_ra.deg, e_dec.deg,
                              mag, e_mag, [epoch_jd, Gaia only]
        photometric catalogs: ra.deg, dec.deg, e_ra.deg, e_dec.deg,
                              [mags], [e_mags], epoch_jd
        """


        ### setup Vizier query
        # note: column filters uses original Vizier column names
        # -> green column names in Vizier

        if self.display:
            print(('query Vizier for %s at %7.3f/%+8.3f in ' \
                   + 'a %.2f deg radius') % \
                   (self.catalogname, ra_deg, dec_deg, rad_deg), end=' ')
            sys.stdout.flush()
        logging.info(('query Vizier for %s at %7.3f/%+8.3f in ' \
                   + 'a %.2f deg radius') % \
                   (self.catalogname, ra_deg, dec_deg, rad_deg))

        field = coord.SkyCoord(ra=ra_deg, dec=dec_deg, unit=(u.deg, u.deg),
                               frame='icrs')

        if self.catalogname == 'GAIA':
            # astrometric catalog
            vquery = Vizier(columns=['Source', 'RA_ICRS', 'DE_ICRS',
                                     'e_RA_ICRS', 'e_DE_ICRS', 'pmRA',
                                     'pmDE', 'phot_g_mean_mag'],
                            column_filters={"phot_g_mean_mag":
                                            ("<%f" % max_mag)},
                            row_limit = max_sources)

            try:
                self.data = vquery.query_region(field,
                                                width=("%fd" % rad_deg),
                                                catalog="I/337/gaia")[0]
            except IndexError:
                if self.display:
                    print('no data available from %s' % self.catalogname)
                logging.error('no data available from %s' % self.catalogname)
                return 0


                ### rename column names using PP conventions
            self.data.rename_column('Source', 'ident')
            self.data.rename_column('RA_ICRS', 'ra.deg')
            self.data.rename_column('DE_ICRS', 'dec.deg')
            self.data.rename_column('e_RA_ICRS', 'e_ra.deg')
            self.data['e_ra.deg'].convert_unit_to(u.deg)
            self.data.rename_column('e_DE_ICRS', 'e_dec.deg')
            self.data['e_dec.deg'].convert_unit_to(u.deg)
            self.data.rename_column('__Gmag_', 'mag')

            self.data.add_column(Column(numpy.ones(len(self.data))*2457023.5,
                                        name='epoch_jd', unit=u.day))

            ### TBD:
            # - implement proper error ellipse handling
            # - implement propor motion handling for DR2

        elif self.catalogname == '2MASS':
            # photometric catalog
            vquery = Vizier(columns=['2MASS', 'RAJ2000', 'DEJ2000', 'errMaj',
                                     'errMin', 'errPA', 'Jmag', 'e_Jmag',
                                     'Hmag', 'e_Hmag', 'Kmag', 'e_Kmag'],
                            column_filters={"Jmag":
                                            ("<%f" % max_mag)},
                            row_limit = max_sources)

            try:
                self.data = vquery.query_region(field,
                                                width=("%fd" % rad_deg),
                                                catalog="II/246/out")[0]
            except IndexError:
                if self.display:
                    print('no data available from %s' % self.catalogname)
                logging.error('no data available from %s' % self.catalogname)
                return 0

            ### rename column names using PP conventions
            self.data.rename_column('_2MASS', 'ident')
            self.data.rename_column('RAJ2000', 'ra.deg')
            self.data.rename_column('DEJ2000', 'dec.deg')
            self.data['mag'] = self.data['Jmag'] # use J as default mag

            ### determine RA and Dec positional uncertainties and
            #   add respective columns
            self.data['errPA'][self.data['errPA'] == 0] = 1 # workaround

            arc_xopt = numpy.arctan(-self.data['errMin']/self.data['errMaj']*
                                    numpy.tan(self.data['errPA'].to(u.rad)))
            ra_err  = abs(self.data['errMaj']*numpy.cos(arc_xopt)*
                          numpy.cos(self.data['errPA'].to(u.rad))-
                          self.data['errMin']*numpy.sin(arc_xopt)*
                          numpy.sin(self.data['errPA'].to(u.rad)))
            self.data.add_column(Column(data=ra_err*1000,
                                        name='e_ra.deg', unit=u.mas),
                                        index=2)

            arc_yopt = numpy.arctan(self.data['errMin']/self.data['errMaj']*
                                    numpy.cos(self.data['errPA'].to(u.rad))/
                                    numpy.sin(self.data['errPA'].to(u.rad)))
            dec_err = abs(self.data['errMaj']*numpy.cos(arc_yopt)*
                          numpy.sin(self.data['errPA'].to(u.rad))+
                          self.data['errMin']*numpy.sin(arc_yopt)*
                          numpy.cos(self.data['errPA'].to(u.rad)))
            self.data.add_column(Column(data=dec_err*1000,
                                        name='e_dec.deg', unit=u.mas), index=3)

            # remove error ellipse columns
            self.data.remove_column('errMaj')
            self.data.remove_column('errMin')
            self.data.remove_column('errPA')

        elif self.catalogname == 'URAT-1':
            # astrometric catalog
            vquery = Vizier(columns=['URAT1', 'RAJ2000', 'DEJ2000',
                                     'sigm', 'f.mag', 'e_f.mag',],
                            column_filters={"f.mag":
                                            ("<%f" % max_mag)},
                            row_limit = max_sources)

            try:
                self.data = vquery.query_region(field,
                                                width=("%fd" % rad_deg),
                                                catalog="I/329/urat1")[0]
            except IndexError:
                if self.display:
                    print('no data available from %s' % self.catalogname)
                logging.error('no data available from %s' % self.catalogname)
                return 0

            ### rename column names using PP conventions
            self.data.rename_column('URAT1', 'ident')
            self.data.rename_column('RAJ2000', 'ra.deg')
            self.data.rename_column('DEJ2000', 'dec.deg')
            self.data.rename_column('f.mag', 'mag')
            self.data.rename_column('e_f.mag', 'e_mag')

            self.data.add_column(Column(data=self.data['sigm'].data,
                                        name='e_ra.deg',
                                        unit=self.data['sigm'].unit),
                                 index=2)
            self.data.add_column(Column(data=self.data['sigm'].data,
                                        name='e_dec.deg',
                                        unit=self.data['sigm'].unit),
                                 index=4)
            self.data.remove_column('sigm')



        elif self.catalogname == 'APASS9':
            # photometric catalog
            vquery = Vizier(columns=['recno', 'RAJ2000', 'DEJ2000',
                                     'e_RAJ2000',
                                     'e_DEJ2000', 'Vmag', 'e_Vmag',
                                     'Bmag', 'e_Bmag', "g'mag", "e_g'mag",
                                     "r'mag", "e_r'mag", "i'mag", "e_i'mag"],
                            column_filters={"Vmag":
                                            ("<%f" % max_mag)},
                            row_limit = max_sources)

            try:
                self.data = vquery.query_region(field,
                                                width=("%fd" % rad_deg),
                                                catalog="II/336/apass9")[0]
            except IndexError:
                if self.display:
                    print('no data available from %s' % self.catalogname)
                logging.error('no data available from %s' % self.catalogname)
                return 0

            ### rename column names using PP conventions
            self.data.rename_column('recno', 'ident')
            self.data.rename_column('RAJ2000', 'ra.deg')
            self.data.rename_column('DEJ2000', 'dec.deg')
            self.data.rename_column('e_RAJ2000', 'e_ra.deg')
            self.data.rename_column('e_DEJ2000', 'e_dec.deg')
            self.data.rename_column('g_mag', 'gmag')
            self.data.rename_column('e_g_mag', 'e_gmag')
            self.data.rename_column('r_mag', 'rmag')
            self.data.rename_column('e_r_mag', 'e_rmag')
            self.data.rename_column('i_mag', 'imag')
            self.data.rename_column('e_i_mag', 'i_gmag')

        elif self.catalogname == 'SDSS-R9':
            vquery = Vizier(columns=['SDSS9', 'RAJ2000', 'DEJ2000',
                                     'e_RAJ2000',
                                     'e_DEJ2000', 'umag', 'e_umag',
                                     'gmag', 'e_gmag', 'rmag', 'e_rmag',
                                     'imag', 'e_imag', 'zmag', 'e_zmag'],
                            column_filters={"gmag":
                                            ("<%f" % max_mag)},
                            row_limit = max_sources)
            try:
                self.data = vquery.query_region(field,
                                                width=("%fd" % rad_deg),
                                                catalog="V/139/sdss9")[0]
            except IndexError:
                if self.display:
                    print('no data available from %s' % self.catalogname)
                logging.error('no data available from %s' % self.catalogname)
                return 0

            ### rename column names using PP conventions
            self.data.rename_column('SDSS9', 'ident')
            self.data.rename_column('RAJ2000', 'ra.deg')
            self.data.rename_column('DEJ2000', 'dec.deg')
            self.data.rename_column('e_RAJ2000', 'e_ra.deg')
            self.data.rename_column('e_DEJ2000', 'e_dec.deg')

            # perform correction to AB system for SDSS
            # http://www.sdss3.org/dr8/algorithms/fluxcal.php#SDSStoAB
            self.data['umag'] -= 0.04
            self.data['zmag'] += 0.02

        if self.display:
            print ('%d sources retrieved.' % len(self.data))
        logging.info('%d sources retrieved' % len(self.data))

        self.history = '%d sources downloaded' % len(self.data)

        # convert all coordinate uncertainties to degrees
        self.data['e_ra.deg'] = self.data['e_ra.deg'].to(u.deg)
        self.data['e_dec.deg'] = self.data['e_dec.deg'].to(u.deg)


        # set catalog magnitude system
        self.magsystem = _pp_conf.allcatalogs_magsys[self.catalogname]

        # write ldac catalog
        if save_catalog:
            self.write_ldac(self.catalogname+'.cat')

        return self.shape[0]



    ### FITS/LDAC interface

    def read_ldac(self, filename, fits_filename=None, maxflag=None,
                  time_keyword='MIDTIMJD', exptime_keyword='EXPTIME',
                  object_keyword='OBJECT', telescope_keyword='TEL_KEYW'):
        """
        read in FITS_LDAC file
        input: LDAC filename
        return: (number of sources, number of fields)
        """

        # load LDAC file
        hdulist  = fits.open(filename, ignore_missing_end=True)

        if len(hdulist) < 3:
            print(('ERROR: %s seems to be empty; check LOG file if ' +
                   'Source Extractor ran properly') % filename)
            logging.error(('ERROR: %s seems to be empty; check LOG file if ' +
                   'Source Extractor ran properly') % filename)
            return None


        # load data array
        self.data = Table(hdulist[2].data)

        # set other properties
        telescope = ''
        for line in hdulist[1].data[0][0]:
            if telescope_keyword in line:
                telescope = line.split('\'')[1]
        self.catalogname = filename
        self.origin      = '%s;%s' % (telescope.strip(), fits_filename)
        self.magsys      = 'instrumental'

        # reject flagged sources (if requested)
        if maxflag is not None:
            self.reject_sources_other_than(self.data['FLAGS'] <= maxflag)
            # FLAGS <= 3: allow for blending and nearby sources

        # read data from image header, if requested
        if fits_filename is not None:
            fitsheader = fits.open(fits_filename,
                                   ignore_missing_end=True)[0].header
            self.obstime[0] = float(fitsheader[time_keyword])
            self.obstime[1] = float(fitsheader[exptime_keyword])
            self.obj        = fitsheader[object_keyword]

        # rename columns
        if 'XWIN_WORLD' in self.fields:
            self.data.rename_column('XWIN_WORLD', 'ra.deg')
        if 'YWIN_WORLD' in self.fields:
            self.data.rename_column('YWIN_WORLD', 'dec.deg')

        logging.info('read %d sources in %d columns from LDAC file %s' %
                     (self.shape[0], self.shape[1], filename))

        hdulist.close()

        return self.shape


    def write_ldac(self, ldac_filename):
        """
        write data in new FITS_LDAC file (mainly for use in SCAMP)
        input: filename, ra/dec field names, projection_type
        return: number of sources written to file
        """

        ### create primary header (empty)
        primaryhdu = fits.PrimaryHDU(header=fits.Header())

        ### create header table
        hdr_col = fits.Column(name='Field Header Card', format='1680A',
                              array=["obtained through Vizier"])
        hdrhdu = fits.BinTableHDU.from_columns(fits.ColDefs([hdr_col]))
        hdrhdu.header['EXTNAME'] = ('LDAC_IMHEAD')
        #hdrhdu.header['TDIM1'] = ('(80, 36)') # remove?

        ### create data table
        colname_dic = {'ra.deg': 'XWIN_WORLD', 'dec.deg': 'YWIN_WORLD',
                       'e_ra.deg': 'ERRAWIN_WORLD',
                       'e_dec.deg': 'ERRBWIN_WORLD',
                       'mag': 'MAG'}
        format_dic = {'ra.deg': '1D', 'dec.deg': '1D',
                      'e_ra.deg': '1E',
                      'e_dec.deg': '1E',
                      'mag': '1E'}
        disp_dic = {'ra.deg': 'E15', 'dec.deg': 'E15',
                    'e_ra.deg': 'E12',
                    'e_dec.deg': 'E12',
                    'mag': 'F8.4'}
        unit_dic = {'ra.deg': 'deg', 'dec.deg': 'deg',
                    'e_ra.deg': 'deg',
                    'e_dec.deg': 'deg',
                    'mag': 'mag'}

        data_cols = []
        for col_name in self.data.columns:
            if not col_name in list(colname_dic.keys()):
                continue
            data_cols.append(fits.Column(name=colname_dic[col_name],
                                         format=format_dic[col_name],
                                         array=self.data[col_name],
                                         unit=unit_dic[col_name],
                                         disp=disp_dic[col_name]))

        data_cols.append(fits.Column(name='MAGERR',
                                     disp='F8.4',
                                     format='1E',
                                     unit='mag',
                                     array=numpy.ones(len(self.data))*0.01))
        data_cols.append(fits.Column(name='OBSDATE',
                                     disp='F13.8',
                                     format='1D',
                                     unit='yr',
                                     array=numpy.ones(len(self.data))*2015.0))

        datahdu = fits.BinTableHDU.from_columns(fits.ColDefs(data_cols))
        datahdu.header['EXTNAME'] = ('LDAC_OBJECTS')

        nsrc = len(self.data)

        # # combine HDUs and write file
        hdulist = fits.HDUList([primaryhdu, hdrhdu, datahdu])
        hdulist.writeto(ldac_filename, clobber=True)

        logging.info('wrote %d sources from %s to LDAC file' %
                     (nsrc, ldac_filename))

        return nsrc


    ### ascii interface

    def write_ascii(self, filename):
        """
        write catalog to ascii table
        input: target filename
        return: number of sources written to file
        """

        # prepare headerline and formatline
        legend, headerline, formatline  = '', '', ''
        for idx in range(len(self.fields)):
            legend += '%d - %s\n' % (idx, self.fields[idx])
            headerline += ('|%13s ' % str(self.fields[idx]))
            if 'E' in str(self.data.formats[idx]):
                formatline += '%15E'
            elif 'D' in str(self.data.formats[idx]):
                formatline += '%15f'
            elif 'I' in str(self.data.formats[idx]) or \
                 'J' in str(self.data.formats[idx]):
                formatline += '%15d'

        # write data into file
        numpy.savetxt(filename, self.data, fmt=formatline,
                      header=legend+headerline)

        logging.info('wrote %d sources from %s to ASCII file %s' %
                     (self.shape[0], self.catalogname, filename))

        return self.shape[0]


    ### SQLite interface

    def write_database (self, filename):
        """
        write catalog object to SQLite database file
        input: target filename
        output: number of sources written to file
        """

        # open database file (delete existing ones)
        os.remove(filename) if os.path.exists(filename) else None
        db_conn = sql.connect(filename)
        db = db_conn.cursor()

        # create header table
        db.execute("CREATE TABLE header (" + \
                   "[name] TEXT, [origin] TEXT, [description] TEXT, " + \
                   "[magsys] TEXT, [obstime] REAL, [exptime] REAL, [obj] TEXT)")
        db.execute("INSERT INTO header VALUES (?,?,?,?,?,?,?)",
                   (self.catalogname, self.origin, self.history,
                    self.magsys, self.obstime[0], self.obstime[1],
                    self.obj))


        # create data table
        table_cmd = "CREATE TABLE data ("
        for key_idx, key in enumerate(self.fields):
            db_key = key
            if type(self.data[key][0]) == numpy.float32 \
               or type(self.data[key][0]) == numpy.float64:
                table_cmd += "'%s' REAL" % db_key
            if type(self.data[key][0]) == numpy.int16 \
               or type(self.data[key][0]) == numpy.int32:
                table_cmd += "'%s' INTEGER" % db_key
            if type(self.data[key][0]) == numpy.string_:
                table_cmd += "'%s' TEXT" % db_key
            if key_idx < len(self.fields)-1:
                table_cmd += ", "

        table_cmd += ")"
        db.execute(table_cmd)

        # create a data array in which data types are converted to SQL types
        sqltypes = {numpy.float32:numpy.float64, numpy.float64:numpy.float64,
                    numpy.int16:numpy.int64, numpy.int32:numpy.int64}
        data_cols = [self.data[key].astype(sqltypes[type(self.data[key][0])]) \
                     for key in self.fields]
        data = [[data_cols[j][i] for j in range(len(data_cols))] \
                for i in range(len(data_cols[0]))]
        db.executemany("INSERT INTO data VALUES (" + \
                       ','.join(['?' for i in range(len(self.fields))]) + \
                       ')', data)

        db_conn.commit()

        # return number of objects written to database
        db.execute("SELECT COUNT(DISTINCT %s) FROM data" % self.fields[0].name)
        n_obj = db.fetchall()[0][0]

        logging.info('wrote %d sources from catalog %s to database file %s' %
                     (n_obj, " | ".join([self.catalogname, self.origin,
                                         self.history]),
                      filename))

        return n_obj


    def read_database (self, filename):
        """ read in photometry database into catalog """

        # open database file
        try:
            db_conn = sql.connect(filename)
            db = db_conn.cursor()
        except:
            if self.display:
                print('ERROR: could not find database', filename)
                logging.error('ERROR: could not find database', filename)
            return []

        # query database header
        db.execute("SELECT * FROM header")
        rows = db.fetchall()

        self.catalogname = rows[0][0].encode('ascii')
        self.origin      = rows[0][1].encode('ascii')
        self.history     = rows[0][2].encode('ascii')
        self.magsys      = rows[0][3].encode('ascii')
        self.obstime[0]  = rows[0][4]
        self.obstime[1]  = rows[0][5]
        self.obj         = rows[0][6].encode('ascii')

        # query database sources
        db.execute("SELECT * FROM data")
        rows = db.fetchall()

        # read in field names and types
        fieldnames, types = [], []
        type_dict = {float:numpy.float64, int:numpy.int64, str:numpy.string_}
        for key_idx, key in enumerate(db.description):
            fieldnames.append(key[0])
            types.append(type_dict[type(rows[0][key_idx])])

        # read in data in FITS_rec structure by creating a
        # temporary FITS table
        data = [[] for i in range(len(fieldnames))]
        for row in rows:
            for col in range(len(row)):
                data[col].append(types[col](row[col]))
        type_dict = {numpy.float64:'E', numpy.int64:'I', numpy.string_:'A'}
        columns = [fits.Column(name=fieldnames[idx],
                               format=type_dict[types[idx]],
                               array=data[idx])
                   for idx in range(len(data))]
        tbhdu = fits.BinTableHDU.from_columns(columns)

        self.data = Table(tbhdu.data)

        return self.shape[0]



    ##### filter transformations

    def lin_func(self, x, a, b):
        return a*x + b

    def transform_filters (self, targetfilter):
        """
        transform a given catalog into a different filter band; crop the
        resulting catalog to only those sources that have transformed magnitudes
        transformed magnitudes start with an asterisk
        input: targetfilter name
        return: number of transformed magnitudes
        """

        ### TBD: modify this function to make use of table functionality

        if len(self.data) == 0:
            return 0

        ### SDSS to BVRI
        ### transformations based on Chonis & Gaskell 2008, AJ, 135
        if (('SDSS' in self.catalogname) and
            (targetfilter in {'B', 'V', 'R', 'I'}) and
            (self.magsystem == 'AB')):

            logging.info(('trying to transform %d SDSS sources to ' \
                          + '%s') % (self.shape[0], targetfilter))

            mags = numpy.array([self['gmag'], self['rmag'],
                                self['imag'],
                                self['e_gmag'],
                                self['e_rmag'],
                                self['e_imag'],
                                self['umag'],
                                self['e_umag']])

            # ### template for adding astropy.table columns
            # self.data.add_column(Column(self.data['Jmag']+1.7495*cidx**3
            #                             - 2.7785*cidx**2
            #                             + 5.215*cidx + 0.1980,
            #                             name='_Bmag',
            #                             unit=u.mag))



            # lbl   = {'_Bmag':0 , '_e_Bmag': 1, '_Vmag': 2, '_e_Vmag': 3,
            #          '_Rmag': 4, '_e_Rmag': 5, '_Imag': 6, '_e_Imag': 7}
            # nmags = [numpy.zeros(self.shape[0]) for i in range(len(lbl))]

            # sort out sources that do not meet the C&G requirements
            keep_idc = (mags[1]-mags[2] > 0.08) & (mags[1]-mags[2] < 0.5) & \
                       (mags[0]-mags[1] > 0.2)  & (mags[0]-mags[1] < 1.4) & \
                       (mags[0] >= 14.5)        & (mags[0] < 19.5) & \
                       (mags[1] >= 14.5)        & (mags[1] < 19.5) & \
                       (mags[2] >= 14.5)        & (mags[2] < 19.5)
            filtered_mags = numpy.array([mags[i][keep_idc]
                                         for i in range(len(mags))])

            # ... derive a linear best fit and remove outliers (>3 sigma)
            ri = numpy.array(filtered_mags[1]) - numpy.array(filtered_mags[2])
            gr = numpy.array(filtered_mags[0]) - numpy.array(filtered_mags[1])

            if len(ri) == 0 or len(gr) == 0:
                logging.warning('no suitable stars for transformation to %s' %
                                targetfilter)
                return 0

            param = optimization.curve_fit(self.lin_func, ri, gr, [1,0])[0]
            resid = numpy.sqrt((old_div((ri+param[0]*gr-param[0]*param[1]),
                                (param[0]**2+1)))**2+
                               (param[0]*(ri+param[0]*gr-param[0]*param[1])/
                                (param[0]**2+1)+param[1]-gr)**2)
            remove = numpy.where(numpy.array(resid) > 3.*numpy.std(resid))[0]

            keep = [idx for idx in numpy.arange(len(keep_idc))[keep_idc]
                    if idx not in set(remove)]

            # transformed magnitudes; uncertainties through Gaussian and C&G2008
            nmags = numpy.array([numpy.empty(len(mags[0])),
                                 numpy.empty(len(mags[0]))])
            if targetfilter == 'U':
                nmags[0] = mags[6] - 0.854
                nmags[1] = numpy.sqrt(mags[7]**2 + 0.007**2)
            elif targetfilter == 'B':
                nmags[0]   = mags[0] + 0.327*(mags[0] - mags[1]) + 0.216
                nmags[1] = numpy.sqrt(((1+0.327)*mags[3])**2 \
                                      + (0.327*mags[4])**2 \
                                      + ((mags[0]-mags[1])*0.047)**2\
                                      + 0.027**2)
            elif targetfilter == 'V':
                nmags[0]   = mags[0] - 0.587*(mags[0] - mags[1]) - 0.011
                nmags[1] = numpy.sqrt(((1+0.587)*mags[3])**2 \
                                      + (0.587*mags[4])**2 \
                                      + ((mags[0]-mags[1])*0.022)**2 \
                                      + 0.011**2)
            elif targetfilter == 'R':
                nmags[0]   = mags[1] - 0.272*(mags[1] - mags[2]) - 0.159
                nmags[1] = numpy.sqrt(((1-0.272)*mags[4])**2 \
                                      + (0.272*mags[5])**2 \
                                      + ((mags[1]-mags[2])*0.092)**2 \
                                      + 0.022**2)
            # elif targetfilter == 'I':
            #     nmags[0]   = mags[2] - 0.337*(mags[1] - mags[2]) - 0.370
            #     nmags[1] = numpy.sqrt(((1+0.337)*mags[5])**2 \
            #                           + (0.337*mags[4])**2 \
            #                           + ((mags[1]-mags[2])*0.191)**2 \
            #                           + 0.041**2)

            ##### experimental!!!!! Based on Connor's transformations
            elif targetfilter == 'I':
                nmags[0]   = mags[2] - 0.2526*(mags[1] - mags[2]) - 0.3636
                nmags[1] = numpy.sqrt(((1+0.2526)*mags[5])**2 \
                                      + (0.2526*mags[4])**2 \
                                      + ((mags[1]-mags[2])*0.191)**2 \
                                      + 0.028**2)

            # add new filter and according uncertainty to catalog
            self.add_field('_'+targetfilter+'mag', nmags[0])
            self.add_field('_e_'+targetfilter+'mag', nmags[1])

            # get rid of sources that have not been transformed
            self.data = self.data[keep]

            self.catalogname  += '_transformed'
            self.history += ', %d transformed to %s (Vega)' % \
                            (self.shape[0], targetfilter)
            self.magsystem = 'AB (ugriz), Vega (%s)' % targetfilter

            logging.info(('%d sources sucessfully transformed to %s' %
                          (self.shape[0], targetfilter)))


            return self.shape[0]


        ### APASS to R/I
        # todo: include g magnitudes and account for color
        elif ('URAT' in self.catalogname or
              'APASS' in self.catalogname and
              (targetfilter == 'R' or targetfilter == 'I')
              and self.magsystem == 'Vega'):

            logging.info('trying to transform %d %s sources to %s' %
                          (self.shape[0], self.catalogname, targetfilter))


            ### transformations based on Chonis & Gaskell 2008, AJ, 135
            mags = numpy.array([self['rmag'],
                                self['imag'],
                                self['e_rmag'],
                                self['e_imag']])

            # sort out sources that do not meet the C&G requirements
            keep_idc = (mags[0]-mags[1] > 0.08) & (mags[0]-mags[1] < 0.5)

            # transformed magnitudes; uncertainties through Gaussian and C&G2008
            nmags = numpy.array([numpy.empty(len(mags[0])),
                                 numpy.empty(len(mags[0]))])

            if targetfilter == 'R':
                nmags[0]   = mags[0] - 0.272*(mags[0] - mags[1]) - 0.159
                nmags[1] = numpy.sqrt(((1-0.272)*mags[2])**2 \
                                      + (0.272*mags[3])**2 \
                                      + ((mags[0]-mags[1])*0.092)**2 \
                                      + 0.022**2)
            elif targetfilter == 'I':
                nmags[0]   = mags[1] - 0.337*(mags[0] - mags[1]) - 0.370
                nmags[1] = numpy.sqrt(((1+0.337)*mags[3])**2 \
                                      + (0.337*mags[2])**2 \
                                      + ((mags[0]-mags[1])*0.191)**2 \
                                      + 0.041**2)

            # add new filter and according uncertainty to catalog
            self.add_field('_'+targetfilter+'mag', nmags[0])
            self.add_field('_e_'+targetfilter+'mag', nmags[1])

            # get rid of sources that have not been transformed
            self.data = self.data[keep_idc]

            self.catalogname  += '_transformed'
            self.history += ', %d transformed to %s (Vega)' % \
                            (self.shape[0], targetfilter)
            self.magsystem = 'Vega'

            logging.info('%d sources sucessfully transformed to %s' % \
                         (self.shape[0], targetfilter))

            return self.shape[0]



        ### 2MASS to UKIRT YZJHK)
        elif (self.catalogname.find('2MASS') > -1) and \
           (targetfilter in {'Y_UKIRT', 'Z_UKIRT', 'J_UKIRT', \
                             'H_UKIRT', 'K_UKIRT'}) and \
           (self.magsystem == 'Vega'):

            logging.info(('trying to transform %d 2MASS sources to ' \
                          +'UKIRT YZJHK') % self.shape[0])

            # transformations using the recipe by Hodgkin et al. 2009, MNRAS
            mags  = [self['Jmag'], self['Hmag'], self['Kmag'],
                     self['e_Jmag'], self['e_Hmag'],
                     self['e_Kmag']]
            lbl   = {'_Ymag': 0, '_e_Ymag': 1, '_Zmag': 2, '_e_Zmag': 3,
                     '_Jmag': 4, '_e_Jmag': 5, '_Hmag': 6, '_e_Hmag': 7,
                     '_Kmag': 8, '_e_Kmag': 9}
            nmags = [numpy.zeros(self.shape[0]) for i in range(len(lbl))]


            for idx in range(self.shape[0]):
                keep = True
                # remove objects with extreme J-Ks color index
                cidx = mags[0][idx]-mags[1][idx]
                if cidx < -0.1 or cidx > 1.0:
                    keep = False
                # reject faint stars based on Figure 6 by Hodgkin et
                # al. 2009, MNRAS
                if mags[0][idx] > 18 or mags[1][idx] > 17:
                    keep = False

                if keep:
                    # 0.064 (sig: 0.035) is a systematic offset
                    # between UKIRT_Z and SDSS_Z
                    nmags[lbl['_Zmag']][idx]   = mags[0][idx] \
                                                 + 0.95*(mags[0][idx]
                                                         - mags[1][idx]) + 0.064
                    nmags[lbl['_e_Zmag']][idx] = numpy.sqrt(mags[3][idx]**2 \
                                                            + 0.035**2)

                    nmags[lbl['_Ymag']][idx]   = mags[0][idx] \
                                                 + 0.5*(mags[0][idx] \
                                                        - mags[1][idx]) + 0.08
                    nmags[lbl['_e_Ymag']][idx] = mags[3][idx]

                    oldH = mags[1][idx]
                    nmags[lbl['_Hmag']][idx]   = mags[1][idx] \
                                                 + 0.07*(mags[0][idx] - \
                                                         mags[2][idx]) - 0.03
                    nmags[lbl['_e_Hmag']][idx] = mags[4][idx]

                    nmags[lbl['_Jmag']][idx]   = mags[0][idx] \
                                                 - 0.065*(mags[0][idx] - oldH)
                    nmags[lbl['_e_Jmag']][idx] = mags[3][idx]

                    nmags[lbl['_Kmag']][idx]    = mags[2][idx] \
                                                  + 0.01*(mags[0][idx] \
                                                          - mags[2][idx])
                    nmags[lbl['_e_Kmag']][idx]  = mags[5][idx]

                else:
                    for mag in list(lbl.keys()):
                        nmags[lbl[mag]][idx] = 99

            # append nmags arrays to catalog
            for key, idx in list(lbl.items()):
                self.add_field(key, nmags[idx])

            # get rid of sources that have not been transformed
            self.data = self.data[self['_Zmag'] < 99]

            self.catalogname  += '_transformed'
            self.history += ', %d transformed to UKIRT YZJHK (Vega)' %\
                            self.shape[0]
            self.magsystem = 'Vega'

            logging.info('%d sources sucessfully transformed to UKIRT YZJHK' % \
                         self.shape[0])

            return self.shape[0]


        ### SDSS to UKIRT Z
        elif (self.catalogname.find('SDSS') > -1) and \
             targetfilter == 'Z_UKIRT' and \
             self.catalogname == 'AB':

            logging.info(('trying to transform %d SDSS sources to ' \
                          + 'UKIRT Z') % self.shape[0])

            ### transformations using the recipe by Hodgkin et al. 2009, MNRAS
            # select sources for input catalog
            mags  = [self['zmag'], self['imag'], self['e_zmag']]
            lbl   = {'_Zmag': 0, '_e_Zmag': 1}
            nmags = [numpy.zeros(self.shape[0]) for i in range(len(lbl))]

            for idx in range(self.shape[0]):
                # transformations according to Hewett et al. 2006, MNRAS
                # (slope is average of III and V classes)
                nmags[lbl['_Zmag']][idx]   = mags[0][idx] - 0.01 + 0.06* \
                                             (mags[1][idx]-mags[0][idx])-0.528
                nmags[lbl['_e_Zmag']][idx] = mags[2][idx]

            # append nmags arrays to catalog
            for key, idx in list(lbl.items()):
                self.add_field(key, nmags[idx])

            # get rid of sources that have not been transformed
            self.data = self.data[self['_Zmag'] < 99]

            self.catalogname  += '_transformed'
            self.history += ', %d transformed to UKIRT Z (Vega)' % \
                            self.shape[0]
            self.magsystem = 'AB (ugriz), Z_UKIRT (Vega)'

            logging.info('%d sources sucessfully transformed to UKIRT Z' % \
                         self.shape[0])

            return self.shape[0]

        else:
            if self.display:
                print('ERROR: no transformation from %s to %s available' % \
                    (self.catalogname, targetfilter))
            return 0


    ##### catalog operations


    def match_with(self, catalog,
                   match_keys_this_catalog=['ra.deg', 'dec.deg'],
                   match_keys_other_catalog=['ra.deg', 'dec.deg'],
                   extract_this_catalog=['ra.deg', 'dec.deg'],
                   extract_other_catalog=['ra.deg', 'dec.deg'],
                   tolerance=old_div(0.5,3600.)):
        """ match sources from different catalogs based on two fields
            (e.g., postions)
            return: requested fields for matched sources
            note: will only match exclusive pairs

            TBD: replace this routine with something that uses
                 astropy.table functionality; how about astropy.coord matching?
        """

        this_tree = spatial.KDTree(list(zip(self[match_keys_this_catalog[0]].data,
                                       self[match_keys_this_catalog[1]].data)))

        # kd-tree matching
        if tolerance is not None:
            other_tree = spatial.KDTree(\
                            list(zip(catalog[match_keys_other_catalog[0]].data,
                                catalog[match_keys_other_catalog[1]].data)))

            match = this_tree.query_ball_tree(other_tree, tolerance)

            indices_this_catalog  = [x for x in range(len(match)) if len(match[x]) == 1]
            indices_other_catalog = [x[0] for x in list(filter((lambda x: len(x)==1), match))]

        else:
            # will find the closest match for each target in this catalog
            other_cat = list(zip(catalog[match_keys_other_catalog[0]].data,
                            catalog[match_keys_other_catalog[1]].data))

            match = this_tree.query(other_cat)

            indices_this_catalog, indices_other_catalog = [], []

            for target_idx in range(self.shape[0]):
                other_cat_indices = numpy.where(match[1]==target_idx)[0]
                if len(other_cat_indices) > 0:
                    # find closest match
                    min_idx = other_cat_indices[numpy.argmin([match[0][i] for i in other_cat_indices])]

                    indices_this_catalog.append(target_idx)
                    indices_other_catalog.append(min_idx)


        ### match outputs based on indices provided and require
        ### extract_fields to be filled
        assert len(indices_this_catalog) == len(indices_other_catalog)
        indices = list(zip(indices_this_catalog, indices_other_catalog))
        # check if element is either not nan or not a float
        check_not_nan = lambda x: not numpy.isnan(x) if \
                                  (type(x) is numpy.float_) else True

        indices = [i for i in indices if all([check_not_nan(self[i[0]][key])
                                        for key in extract_this_catalog] \
                                       + [check_not_nan(catalog[i[1]][key])
                                          for key in extract_other_catalog])]
        output_this_catalog  = [self[key][[i[0] for i in indices]]
                                for key in extract_this_catalog]
        output_other_catalog = [catalog[key][[i[1] for i in indices]]
                                for key in extract_other_catalog]

        return [output_this_catalog, output_other_catalog]





##### Test Routines

### LDAC routines

# test = catalog('ldac test')
# read = test.read_fits('testdata/test.ldac', maxflag=0)
# print '%d sources and %d columns read from ldac file' % \
#     (read[0], read[1])

# print test.write_ascii('testdata/test.ldac.dat'), \
#     'sources sucessfully written to ascii file'

# print test.write_fits('testdata/test_written.ldac'), \
#     'sources successfully written to fits file'

# print test.write_database('testdata/test.ldac.db')


### catalog download and manipulation

# cat1 = catalog('APASS9')
# print(cat1.download_catalog(80, 0, 0.5, 10000), 'sources grabbed from', cat1.catalogname)
# print(cat1.fields)
# print(cat1[0])

# cat2 = catalog('2MASS')
# print cat2.download_catalog(80, 0, 0.5, 10000), 'sources grabbed from', cat2.catalogname
# print cat2[305]
# print cat2.fields

# cat3 = catalog('SDSS-R9')
# print cat3.download_catalog(80, 40, 0.5, 10000), 'sources grabbed from', cat3.catalogname
#print cat3[305]
#print cat3.fields

# cat4 = catalog('USNO-B1')
# print cat4.download_catalog(80, 0, 0.5, 10000), 'sources grabbed from', cat4.catalogname
# print cat4[305]
# print cat4.fields


# print cat2.shape, cat2.history
# print cat2.transform_filters('V'), 'sources transformed to V'      #2MASS to BVRI
# print cat2.shape, cat2.history

# print cat2.shape, cat2.history
# print cat2.transform_filters('K_UKIRT'), 'sources transformed to K'      #2MASS to UKIRT
# print cat2.shape, cat2.history

# print cat3.shape, cat3.history
# print cat3.transform_filters('Z_UKIRT'), 'sources transformed to Z'      #SDSS to UKIRT
# print cat3.shape, cat3.history

# print cat1.shape, cat1.history
# print cat1.transform_filters('I'), 'sources transformed to I'      #SDSS to BVRI
# print cat1.shape, cat1.history
# for i in cat1:
#    print i['_Imag'], i['rmag'], i['imag']



# print test.write_database('test.db'), 'sources written to database file'

# cat4 = catalog('')
# print cat4.read_database('test.db'), 'sources read from database file'


# ### test preliminary Gaia implementation
# cat = catalog('SDSS-R9')
# cat.download_gaiadr1(294.99525, 0.065194, 0.5, 10, max_mag=15, write_ldac=True)
# #cat.download_gaiadr1(239.708791667, 6.10333333333, 0.211666666667, 100, max_mag=20, write_ldac=True)

# print len(cat.data.columns)
