""" DIAGNOSTICS - diagnostic routines for photometry pipeline
    v1.0: 2016-02-25, michael.mommert@nau.edu
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
from astropy.io import fits
from astropy import wcs
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt
import subprocess

# only import if Python3 is used
if sys.version_info > (3,0):
    from builtins import str
    from builtins import zip
    from builtins import range


# pipeline-specific modules
import _pp_conf
from catalog import *

# setup logging
logging.basicConfig(filename = _pp_conf.log_filename,
                    level    = _pp_conf.log_level,
                    format   = _pp_conf.log_formatline,
                    datefmt  = _pp_conf.log_datefmt)


### diagnostics guidelines
#
# - diagnostics.html goes into the data directory
# - all supplementary data and website go into diagroot (see _pp_init.py)
# - if there are sub-directories with data, create diagnostics.html in
#   each directory with data; summary.html links to other directories
###

def create_website(filename, content=''):
    """
    create empty website for diagnostics output
    """

    html  = "<!DOCTYPE html PUBLIC '-//W3C//DTD HTML 4.01//EN'>\n"
    html += "<HTML>\n"
    html += "<HEAD>\n"
    html += "<TITLE>Photometry Pipeline - Diagnostics</TITLE>\n"
    html += "</HEAD>\n"
    html += "<BODY>\n"
    html += content
    html += "</BODY>\n"
    html += "</HTML>\n"

    outf = open(filename, 'w')
    outf.writelines(html)
    outf.close()

    return None


def append_website(filename, content, insert_at='</BODY>',
                   replace_below='X?!do not replace anything!?X'):
    """
    append content to an existing website:
    insert content before line that contains `insert_at`
    replace lines between `replace_below` and `insert_at` (by
    default, nothing is replaced)
    """
    # read existing code
    existing_html = open(filename, 'r').readlines()

    # insert content into existing html
    outf = open(filename, 'w')
    delete = False
    for line in existing_html:
        if replace_below in line:
            delete = True
            continue
        if insert_at in line:
            outf.writelines(content)
            delete = False
        if delete:
            continue
        outf.writelines(line)
    outf.close()

    return None

###########

### pipeline summary websites

def create_summary():
    """
    create a summary page with all available datasets
    """

    html = ("<H1>Photometry Pipeline Analysis (%s)</H1>\n") % \
               (datetime.datetime.now().strftime("%Y-%m-%y %H:%M"))

    create_website(_pp_conf.diagnostics_summary, html)

    return None


def add_to_summary(targetname, filtername, n_frames):
    """
    add data set to summary website
    """

    html  = "<P><A HREF=\"%s\">%s, %s, %d frames</A>\n" % \
            (_pp_conf.index_filename, targetname, filtername, n_frames)
    html += "\n<!-- pp_process_idx=%d -->\n" % _pp_conf.pp_process_idx

    append_website(_pp_conf.diagnostics_summary, html)

    return None


def insert_into_summary(text):
    """
    insert result information into summary website
    """
    append_website(_pp_conf.diagnostics_summary, text+'\n',
                   insert_at=("<!-- pp_process_idx=%d -->\n" %
                              _pp_conf.pp_process_idx))

    return None


### individual pipeline process diagnostic websites

def create_index(filenames, directory, obsparam, display=False):
    """
    create index.html
    diagnostic root website for one pipeline process
    """

    if display:
        print('create frame index table and frame images')
    logging.info('create frame index table and frame images')

    # obtain filtername from first image file
    refheader = fits.open(filenames[0], ignore_missing_end=True)[0].header
    filtername = obsparam['filter_translations'][refheader[obsparam['filter']]]

    html = "<H2>data directory: %s</H2>\n" % directory

    html += ("<H1>%s/%s-band - Diagnostic Output</H1>\n" + \
               "%d frames total, see full pipeline " + \
               "<A HREF=\"%s\">log</A> for more information\n") % \
               (obsparam['telescope_instrument'], filtername,
                len(filenames),
                '.diagnostics/' +
                _pp_conf.log_filename.split('.diagnostics/')[1])

    ### create frame information table
    html += "<P><TABLE BORDER=\"1\">\n<TR>\n"
    html += "<TH>Idx</TH><TH>Filename</TH><TH>Midtime (JD)</TH>" + \
            "<TH>Objectname</TH><TH>Filter</TH>" + \
            "<TH>Airmass</TH><TH>Exptime (s)</TH>" + \
            "<TH>FoV (arcmin)</TH>\n</TR>\n"

    # fill table and create frames
    filename = filenames
    for idx, filename in enumerate(filenames):


        ### fill table
        hdulist = fits.open(filename, ignore_missing_end=True)
        header = hdulist[0].header

        # read out image binning mode
        if '_' in obsparam['binning'][0]:
            if '_blank' in obsparam['binning'][0]:
                binning_x = float(header[obsparam['binning'][0].\
                                         split('_')[0]].split()[0])
                binning_y = float(header[obsparam['binning'][1].\
                                         split('_')[0]].split()[1])
            elif '_x' in obsparam['binning'][0]:
                binning_x = float(header[obsparam['binning'][0].\
                                         split('_')[0]].split('x')[0])
                binning_y = float(header[obsparam['binning'][1].\
                                         split('_')[0]].split('x')[1])
            elif '_CH_' in obsparam['binning'][0]:
                # only for RATIR
                channel = header['INSTRUME'].strip()[1]
                binning_x = float(header[obsparam['binning'][0].
                                         replace('_CH_', channel)])
                binning_y = float(header[obsparam['binning'][1].
                                         replace('_CH_', channel)])
        else:
            binning_x = header[obsparam['binning'][0]]
            binning_y = header[obsparam['binning'][1]]

        #framefilename = _pp_conf.diagroot + '/' + filename + '.png'
        framefilename = '.diagnostics/' + filename + '.png'

        try:
            objectname = header[obsparam['object']]
        except KeyError:
            objectname ='Unknown Target'

        html += ("<TR><TD>%d</TD><TD><A HREF=\"%s\">%s</A></TD>" + \
                 "<TD>%16.8f</TD><TD>%s</TD>" + \
                 "<TD>%s</TD><TD>%4.2f</TD><TD>%.1f</TD>" + \
                 "<TD>%.1f x %.1f</TD>\n</TR>\n") % \
            (idx+1, framefilename, filename, header["MIDTIMJD"],
             objectname,
             header[obsparam['filter']],
             float(header[obsparam['airmass']]),
             float(header[obsparam['exptime']]),
             header[obsparam['extent'][0]]*obsparam['secpix'][0]*binning_x/60.,
             header[obsparam['extent'][1]]*obsparam['secpix'][1]*binning_y/60.)


        ### create frame image
        imgdat = hdulist[0].data

        median = numpy.median(imgdat[int(imgdat.shape[1]*0.25):
                                     int(imgdat.shape[1]*0.75),
                                     int(imgdat.shape[0]*0.25):
                                     int(imgdat.shape[0]*0.75)])
        std    = numpy.std(imgdat[int(imgdat.shape[1]*0.25):
                                  int(imgdat.shape[1]*0.75),
                                  int(imgdat.shape[0]*0.25):
                                  int(imgdat.shape[0]*0.75)])

        downscale = 2. # scale down image by this factor
        fig = plt.figure(figsize=(old_div(header[obsparam['extent'][0]],(downscale*100)),
                                old_div(header[obsparam['extent'][1]],(downscale*100))),
                                  dpi=downscale*100)

        img = plt.imshow(imgdat, cmap='gray', vmin=median-0.5*std,
                         vmax=median+0.5*std, origin='lower')
        # remove axes
        plt.axis('off')
        img.axes.get_xaxis().set_visible(False)
        img.axes.get_yaxis().set_visible(False)

        plt.savefig(framefilename, format='png', bbox_inches='tight',
                    pad_inches=0)
        plt.close()
        hdulist.close()

    html += '</TABLE>\n'

    create_website(_pp_conf.index_filename, html)


    ### add to summary website, if requested
    if _pp_conf.use_diagnostics_summary:
        add_to_summary(refheader[obsparam['object']], filtername,
                       len(filenames))

    return None


### registration results website

def add_registration(data, extraction_data):
    """
    add registration results to website
    """
    obsparam = extraction_data[0]['parameters']['obsparam']


    # create registration website
    html  = "<H2>Registration Results</H2>\n"
    html += "<TABLE BORDER=\"1\">\n<TR>\n"
    html += "<TH>Filename</TH><TH>AS_CONTRAST</TH><TH>XY_CONTRAST</TH>" \
            + "<TH>RA_sig (arcsec)</TH><TH>DEC_sig (arcsec)</TH>" \
            + "<TH>Chi2_Reference</TH><TH>Chi2_Internal</TH>\n</TR>\n"
    for dat in data['fitresults']:
        html += ("<TR><TD><A HREF=\"%s\">%s</A></TD>" \
                 + "<TD>%4.1f</TD><TD>%4.1f</TD>" \
                 + "<TD>%5.3f</TD><TD>%5.3f</TD>" \
                 + "<TD>%e</TD><TD>%e</TD>\n</TR>\n" )% \
                (dat[0] + '_astrometry.png',
                 dat[0], dat[1], dat[2], dat[3], dat[4], dat[5], dat[6])
    html += "</TABLE>\n"
    html += "<P>AS_CONTRAST: position angle/scale contrast " + \
            "(>%.1f usually ok)\n" % _pp_conf.scamp_as_contrast_limit
    html += "<BR>XY_CONTRAST: xy-shift contrast (>%.1f usually ok)\n" % \
            _pp_conf.scamp_xy_contrast_limit
    create_website(_pp_conf.reg_filename, content=html)


    # load reference catalog
    refcat = catalog(data['catalog'])
    for filename in os.listdir('.'):
        if data['catalog'] in filename and '.cat' in filename:
            refcat.read_ldac(filename)
            break


    ### create frame images
    for dat in extraction_data:
        framefilename = '.diagnostics/' + dat['fits_filename'] + \
                        '_astrometry.png'
        imgdat = fits.open(dat['fits_filename'],
                           ignore_missing_end=True)[0].data
        header = fits.open(dat['fits_filename'],
                           ignore_missing_end=True)[0].header
        median = numpy.median(imgdat[int(imgdat.shape[1]*0.25):
                                     int(imgdat.shape[1]*0.75),
                                     int(imgdat.shape[0]*0.25):
                                     int(imgdat.shape[0]*0.75)])
        std    = numpy.std(imgdat[int(imgdat.shape[1]*0.25):
                                     int(imgdat.shape[1]*0.75),
                                     int(imgdat.shape[0]*0.25):
                                     int(imgdat.shape[0]*0.75)])

        # turn relevant header keys into floats
        # astropy.io.fits bug
        for key, val in list(header.items()):
            if 'CD1_' in key or 'CD2_' in key or \
               'CRVAL' in key or 'CRPIX' in key or \
               'EQUINOX' in key:
                header[key] = float(val)

        downscale = 2. # scale down image by this factor
        fig = plt.figure(figsize=(old_div(header[obsparam['extent'][0]],(downscale*100)),
                                old_div(header[obsparam['extent'][1]],(downscale*100))),
                         dpi=downscale*100)
        img = plt.imshow(imgdat, cmap='gray', vmin=median-0.5*std,
                         vmax=median+0.5*std, origin='lower')
        # remove axes
        plt.axis('off')
        img.axes.get_xaxis().set_visible(False)
        img.axes.get_yaxis().set_visible(False)

        # plot reference sources
        if refcat.shape[0] > 0:
            w = wcs.WCS(header)
            world_coo = numpy.array(list(zip(refcat['X_WORLD'], refcat['Y_WORLD'])))
            img_coo = w.wcs_world2pix(world_coo, True )
            img_coo = [c for c in img_coo if (c[0] > 0 and c[1] > 0 and
                                        c[0] < header[obsparam['extent'][0]]
                                        and
                                        c[1] < header[obsparam['extent'][1]])]
            plt.scatter([c[0] for c in img_coo], [c[1] for c in img_coo],
                        s=20, marker='o', edgecolors='red', facecolor='none')

        plt.savefig(framefilename, format='png', bbox_inches='tight',
                    pad_inches=0)
        plt.close()



    # update index.html
    html  = '<H2>Registration</H2>\n'
    html += '%d/%d files have been registered successfully based on %s; ' % \
            (len(data['goodfits']), len(data['goodfits']+data['badfits']),
             data['catalog'])
    if len(data['badfits']) > 0:
        html += '<B>%d files could not be registered</B>;' % \
                len(data['badfits'])
    html += 'see <A HREF=\"%s\">registration website</A> for details\n' % \
            _pp_conf.reg_filename

    append_website(_pp_conf.index_filename, html,
                   replace_below="<H2>Registration Results</H2>\n")

    return None



def add_photometry(data, extraction):
    """
    add photometry results to website
    """

    parameters = data['parameters']
    growth_filename = '.diagnostics/curve_of_growth.png'
    fwhm_filename   = '.diagnostics/fwhm.png'

    ##### plot curve-of-growth data
    plt.subplot(211)
    plt.xlabel('Aperture Radius (px)')
    plt.ylim([-0.1,1.1])
    plt.xlim([min(parameters['aprad']), max(parameters['aprad'])])
    plt.ylabel('Fractional Combined Flux')
    if not parameters['target_only']:
        plt.errorbar(parameters['aprad'], data['background_flux'][0],
                     data['background_flux'][1], color='black',
                     linewidth=1,
                     label='background objects')
    if not parameters['background_only']:
        plt.errorbar(parameters['aprad'], data['target_flux'][0],
                     data['target_flux'][1], color='red', linewidth=1,
                     label='target')
    plt.plot([data['optimum_aprad'], data['optimum_aprad']],
             [plt.ylim()[0], plt.ylim()[1]],
             linewidth=2, color='black')
    plt.plot([plt.xlim()[0], plt.xlim()[1]],
             [data['fluxlimit_aprad'], data['fluxlimit_aprad']],
             color='black', linestyle='--')
    plt.grid()
    plt.legend(loc=4)

    plt.subplot(212)
    plt.ylim([-0.1,1.1])
    plt.xlim([min(parameters['aprad']), max(parameters['aprad'])])
    plt.xlabel('Aperture Radius (px)')
    plt.ylabel('SNR')
    if not parameters['target_only']:
        plt.errorbar(parameters['aprad'], data['background_snr'],
                     color='black', linewidth=1)
    if not parameters['background_only']:
        plt.errorbar(parameters['aprad'], data['target_snr'],
                     color='red', linewidth=1)
    plt.plot([data['optimum_aprad'], data['optimum_aprad']],
             [plt.ylim()[0], plt.ylim()[1]],
             linewidth=2, color='black')
    plt.grid()
    plt.savefig(growth_filename, format='png')
    plt.close()
    data['growth_filename'] = growth_filename


    ##### plot fwhm as a function of time
    frame_midtimes = [frame['time'] for frame in extraction]
    fwhm = [numpy.median(frame['catalog_data']['FWHM_IMAGE'])
            for frame in extraction]
    fwhm_sig = [numpy.std(frame['catalog_data']['FWHM_IMAGE'])
                for frame in extraction]

    plt.subplot()
    plt.title('Median PSF FWHM per Frame')
    plt.xlabel('Observation Midtime (JD)')
    plt.ylabel('Point Source FWHM (px)')
    plt.scatter(frame_midtimes, fwhm, marker='o',
                color='black')
    xrange = [plt.xlim()[0], plt.xlim()[1]]
    plt.plot(xrange, [data['optimum_aprad']*2, data['optimum_aprad']*2],
             color='red')
    plt.xlim(xrange)
    plt.ylim([0, max([data['optimum_aprad']*2+1, max(fwhm)])])

    plt.grid()
    plt.savefig(fwhm_filename, format='png')
    plt.close()
    data['fwhm_filename'] = fwhm_filename


    ### update index.html
    html  = "<H2>Photometric Calibration - Aperture Size </H2>\n"
    html += ("optimum aperture radius derived as %5.2f (px) " + \
             "through curve-of-growth analysis based on\n") % \
        data['optimum_aprad']
    if data['n_target'] > 0 and data['n_bkg'] > 0:
        html += ("%d frames with target and %d frames with " + \
                "background detections.\n") % \
                (data['n_target'], data['n_bkg'])
    elif data['n_target'] == 0 and data['n_bkg'] > 0:
        html += "%d frames with background detections.\n" % data['n_bkg']
    elif data['n_bkg'] ==0 and data['n_target'] > 0:
        html += "%d frames with target detections.\n" % data['n_target']
    else:
        html += "no target or background detections."

    html += "<P><IMG SRC=\"%s\">\n" % data['growth_filename']
    html += "<IMG SRC=\"%s\">\n" % data['fwhm_filename']
    html += ("<P> Current strategy for finding the optimum aperture " + \
             "radius: %s\n" % data['aprad_strategy'])

    append_website(_pp_conf.index_filename, html,
                   replace_below=("<H2>Photometric Calibration" +
                                  " - Aperture Size </H2>\n"))

    return None


def add_calibration(data):
    """
    add calibration results to website
    """

    ### produce calibration plot for each frame
    for idx, cat in enumerate(data['catalogs']):
        if not data['zeropoints'][idx]['success']:
            continue
        ax1 = plt.subplot(211)
        ax1.set_title('%s: %s-band from %s' %
                      (cat.catalogname, data['filtername'],
                       data['ref_cat'].catalogname))
        ax1.set_xlabel('Number of Reference Stars')
        ax1.set_ylabel('Magnitude Zeropoint', fontdict={'color':'red'})
        #ax1.ticklabel_format(style='sci', axis='y', scilimits=(-5,5))

        zp_idx = data['zeropoints'][idx]['zp_idx']
        clipping_steps = data['zeropoints'][idx]['clipping_steps']

        x = [len(clipping_steps[i][3]) for i in range(len(clipping_steps))]

        ax1.errorbar(x, [clipping_steps[i][0] for i
                         in range(len(clipping_steps))],
                     yerr=[clipping_steps[i][1] for i
                           in range(len(clipping_steps))], color='red')
        ax1.set_ylim(ax1.get_ylim()[::-1]) # reverse y axis
        ax1.plot([len(clipping_steps[zp_idx][3]),
                  len(clipping_steps[zp_idx][3])],
                 ax1.get_ylim(), color='black')

        ax2 = ax1.twinx()
        ax2.plot(x, [clipping_steps[i][2] for i
                     in range(len(clipping_steps))],
                 color='blue')
        ax2.set_ylabel(r'reduced $\chi^2$', fontdict={'color':'blue'})
        ax2.set_yscale('log')

        # residual plot
        ax3 = plt.subplot(212)
        ax3.set_xlabel('Reference Star Magnitude')
        ax3.set_ylabel('Calibration-Reference (mag)')

        match = data['zeropoints'][idx]['match']
        x             = match[0][0][clipping_steps[zp_idx][3]]
        residuals     = match[1][0][clipping_steps[zp_idx][3]] \
                        + clipping_steps[zp_idx][0] \
                        - match[0][0][clipping_steps[zp_idx][3]]
        residuals_sig = numpy.sqrt(match[1][1][clipping_steps[zp_idx][3]]**2\
                                   + clipping_steps[zp_idx][1]**2)

        ax3.errorbar(x, residuals, yerr=residuals_sig, color='black',
                     linestyle='')
        ax3.plot(ax3.get_xlim(), [0,0], color='black', linestyle='--')
        ax3.set_ylim(ax3.get_ylim()[::-1]) # reverse y axis

        plt.grid()
        plt.savefig(('.diagnostics/%s_photcal.png') % cat.catalogname,
                    format='png')
        data['zeropoints'][idx]['plotfilename'] = \
                                        ('.diagnostics/%s_photcal.png') % \
                                        cat.catalogname
        plt.close()


    ### create zeropoint overview plot
    times = [dat['obstime'][0] for dat in data['zeropoints']]
    zp    = [dat['zp'] for dat in data['zeropoints']]
    zperr = [dat['zp_sig'] for dat in data['zeropoints']]

    plt.subplot()
    plt.errorbar(times, zp, yerr=zperr, linestyle='')
    plt.xlabel('Observation Midtime (JD)')
    plt.ylabel('Magnitude Zeropoints (mag)')
    plt.show()
    plt.ylim([plt.ylim()[1], plt.ylim()[0]])
    plt.grid()
    plt.savefig('.diagnostics/zeropoints.png', format='png')
    plt.close()
    data['zpplot'] = 'zeropoints.png'


    ### create registration website
    html  = "<H2>Calibration Results</H2>\n"
    html += ("<P>Calibration input: minimum number/fraction of reference " \
             + "stars %.2f, reference catalog: %s, filter name: %s\n") % \
        (data['minstars'], data['ref_cat'].catalogname, data['filtername'])
    html += "<TABLE BORDER=\"1\">\n<TR>\n"
    html += "<TH>Filename</TH><TH>Zeropoint (mag)</TH><TH>ZP_sigma (mag)</TH>" \
            + "<TH>N_stars</TH><TH>N_matched</TH>\n</TR>\n"
    for dat in data['zeropoints']:
        if 'plotfilename' in list(dat.keys()):
            html += ("<TR><TD><A HREF=\"#%s\">%s</A></TD>" \
                     + "<TD>%7.4f</TD><TD>%7.4f</TD><TD>%d</TD>" \
                     + "<TD>%d</TD>\n</TR>" ) % \
                (dat['plotfilename'].split('.diagnostics/')[1],
                 dat['filename'], dat['zp'],
                 dat['zp_sig'], dat['zp_nstars'],
                 len(dat['match'][0][0]))
    html += "</TABLE>\n"
    html += "<P><IMG SRC=\"%s\">" % data['zpplot']
    for dat in data['zeropoints']:
        if not dat['success']:
            continue
        catframe = '.diagnostics/'+ \
                   dat['filename'][:dat['filename'].find('.ldac')] + \
                   '.fits_reference_stars.png'
        html += ("<H3>%s</H3>" \
                 + "<TABLE BORDER=\"0\">\n" \
                 + "<TR><TD><A HREF=\"%s\">" \
                 + "<IMG ID=\"%s\" SRC=\"%s\" HEIGHT=300 WIDTH=400>" \
                 + "</A></TD><TD><A HREF=\"%s\">" \
                 + "<IMG ID=\"%s\" SRC=\"%s\" HEIGHT=400 WIDTH=400>" \
                 + "</A></TD>\n") % \
                (dat['filename'],
                 dat['plotfilename'].split('.diagnostics/')[1],
                 dat['plotfilename'].split('.diagnostics/')[1],
                 dat['plotfilename'].split('.diagnostics/')[1],
                 catframe.split('.diagnostics/')[1],
                 catframe.split('.diagnostics/')[1],
                 catframe.split('.diagnostics/')[1])
        html += "<TD><TABLE BORDER=\"1\">\n<TR>\n"
        html += "<TH>Idx</TH><TH>Name</TH><TH>RA</TH><TH>Dec</TH>" \
                + "<TH>Catalog (mag)</TH>" \
                + "<TH>Instrumental (mag)</TH><TH>Calibrated (mag)</TH>" \
                + "<TH>Residual (mag</TH>\n</TR>\n"
        for i, idx in enumerate(dat['zp_usedstars']):
            html += ("<TR><TD>%d</TD><TD>%s</TD><TD>%12.8f</TD>" \
                     + "<TD>%12.8f</TD><TD>%.3f+-%.3f</TD>" \
                     + "<TD>%.3f+-%.3f</TD>" \
                     + "<TD>%.3f+-%.3f</TD><TD>%.3f</TD></TR>") % \
                (i+1, dat['match'][0][2][idx], dat['match'][0][3][idx],
                 dat['match'][0][4][idx], dat['match'][0][0][idx],
                 dat['match'][0][1][idx],
                 dat['match'][1][0][idx], dat['match'][1][1][idx],
                 dat['zp']+dat['match'][1][0][idx],
                 numpy.sqrt(dat['zp_sig']**2 + dat['match'][1][1][idx]**2),
                 (dat['zp']+dat['match'][1][0][idx])-dat['match'][0][0][idx])
        html += "</TABLE><P>derived zeropoint: %7.4f+-%6.4f mag\n" % \
                (dat['zp'], dat['zp_sig'])
        html += "</TR></TD></TR></TABLE>\n"

        ### create catalog frame
        fits_filename = dat['filename'][:dat['filename'].find('.ldac')] + \
                        '.fits'
        imgdat = fits.open(fits_filename, ignore_missing_end=True)[0].data
        header = fits.open(fits_filename, ignore_missing_end=True)[0].header
        median = numpy.median(imgdat[int(imgdat.shape[1]*0.25):
                                     int(imgdat.shape[1]*0.75),
                                     int(imgdat.shape[0]*0.25):
                                     int(imgdat.shape[0]*0.75)])
        std    = numpy.std(imgdat[int(imgdat.shape[1]*0.25):
                                     int(imgdat.shape[1]*0.75),
                                     int(imgdat.shape[0]*0.25):
                                     int(imgdat.shape[0]*0.75)])

        # turn relevant header keys into floats
        # astropy.io.fits bug
        for key, val in list(header.items()):
            if 'CD1' in key or 'CD2' in key or \
               'CRVAL' in key or 'CRPIX' in key or \
               'EQUINOX' in key:
                header[key] = float(val)

        fig = plt.figure(figsize=(old_div(imgdat.shape[0],300.),
                                  old_div(imgdat.shape[1],300.)),
                         dpi=300)
        img = plt.imshow(imgdat, cmap='gray', vmin=median-0.5*std,
                         vmax=median+0.5*std, origin='lower')
        # remove axes
        plt.axis('off')
        img.axes.get_xaxis().set_visible(False)
        img.axes.get_yaxis().set_visible(False)

        # plot reference sources
        if len(dat['match'][0][3]) > 0 and len(dat['match'][0][4]) > 0:
            w = wcs.WCS(header)
            world_coo = [[dat['match'][0][3][idx], dat['match'][0][4][idx]] \
                         for idx in dat['zp_usedstars']]
            img_coo = w.wcs_world2pix(world_coo, True )
            plt.scatter([c[0] for c in img_coo], [c[1] for c in img_coo],
                        s=40, marker='o', edgecolors='red', facecolor='none')
            for i in range(len(dat['zp_usedstars'])):
                plt.annotate(str(i+1), xy=(img_coo[i][0]+30, img_coo[i][1]),
                             color='red', horizontalalignment='left',
                             verticalalignment='center')

        plt.savefig(catframe, format='png', bbox_inches='tight',
                    pad_inches=0)
        plt.close()




    create_website(_pp_conf.cal_filename, content=html)

    ### update index.html
    html  = "<H2>Photometric Calibration - Catalog Match </H2>\n"
    html += "match image data with %s (%s);\n" % \
            (data['ref_cat'].catalogname, data['ref_cat'].history)
    html += "see <A HREF=\"%s\">calibration</A> website for details\n" % \
            _pp_conf.cal_filename
    html += "<P><IMG SRC=\"%s\">\n" % ('.diagnostics/' + data['zpplot'])

    append_website(_pp_conf.index_filename, html,
                   replace_below=("<H2>Photometric Calibration " +
                                  "- Catalog Match </H2>\n"))

    return None


def add_results(data):
    """
    add results to website
    """

    ### create lightcurve plots for each target

    data['lightcurveplots'] = {}
    for target in data['targetnames']:
        logging.info('create lightcurve plot for %s' % target)
        plt.plot()
        plt.title(target)
        plt.xlabel('Observation Midtime (JD)')
        plt.ylabel('Magnitude')
        plt.errorbar([dat[9][0] for dat in data[target]],
                     [dat[7] for dat in data[target]],
                     yerr=[dat[8] for dat in data[target]],
                     linestyle='', color='black')
        plt.ylim([plt.ylim()[1], plt.ylim()[0]])
        plt.grid()
        plt.savefig('.diagnostics/' + ('%s.png' % target.replace(' ', '_')),
                    format='png')
        plt.close()
        data['lightcurveplots'][target] = ('.diagnostics/' + '%s.png' %
                                           target.replace(' ', '_'))

    ##### create thumbnail images

    data['thumbnailplots'] = {}
    data['gifs'] = {}
    boxsize = 300 # thumbnail boxsize
    for target in data['targetnames']:
        data['thumbnailplots'][target] = []
        for dat in data[target]:
            for fitsfilename in ['.fits', '.fit']:
                fitsfilename = dat[10][:dat[10].find('.ldac')]+fitsfilename
                if os.path.isfile(fitsfilename):
                    break
                #= dat[10][:dat[10].find('.ldac')]+'.fits'
            hdulist = fits.open(fitsfilename, ignore_missing_end=True)

            logging.info('create thumbnail image for %s/%s' % (target,
                                                            fitsfilename))

            # turn relevant header keywords into floats
            # should be fixed in astropy.wcs
            for key, val in list(hdulist[0].header.items()):
                if 'CD1' in key or 'CD2' in key or \
                   'CRVAL' in key or 'CRPIX' in key or \
                   'EQUINOX' in key:
                    hdulist[0].header[key] = float(val)
                # if 'PV1' in key or 'PV2' in key:
                #     del hdulist[0].header[key]

            w = wcs.WCS(hdulist[0].header)
            obj_x, obj_y = dat[11], dat[12]
            image_coords = w.wcs_world2pix(numpy.array([[dat[1], dat[2]]]),
                                           True)
            exp_x, exp_y = image_coords[0][0], image_coords[0][1]

            # create margin around image allowing for any cropping
            composite = numpy.zeros((hdulist[0].data.shape[0]+2*boxsize,
                                     hdulist[0].data.shape[1]+2*boxsize))

            composite[boxsize:boxsize+hdulist[0].data.shape[0],
                      boxsize:boxsize+hdulist[0].data.shape[1]] = \
                                                            hdulist[0].data

            # extract thumbnail data accordingly
            thumbdata = composite[int(boxsize+obj_y-old_div(boxsize,2)):
                                  int(boxsize+obj_y+old_div(boxsize,2)),
                                  int(boxsize+obj_x-old_div(boxsize,2)):
                                  int(boxsize+obj_x+old_div(boxsize,2))]

            ## run statistics over center of the frame around the target
            if thumbdata.shape[0] > 0 and thumbdata.shape[1] > 0:
                median = numpy.median(thumbdata[old_div(boxsize,2)-20:old_div(boxsize,2)+20,
                                                old_div(boxsize,2)-20:old_div(boxsize,2)+20])
                std = numpy.std(thumbdata[old_div(boxsize,2)-20:old_div(boxsize,2)+20,
                                          old_div(boxsize,2)-20:old_div(boxsize,2)+20])
                maxval = numpy.max(thumbdata[old_div(boxsize,2)-20:old_div(boxsize,2)+20,
                                             old_div(boxsize,2)-20:old_div(boxsize,2)+20])
            else:
                logging.warning('cannot produce thumbnail image ' + \
                                'for %s in frame %s' % (target, dat[10]))
                continue



            # ## run statistics over whole frame
            # if thumbdata.shape[0] > 0 and thumbdata.shape[1] > 0:
            #     median = numpy.median(numpy.ma.masked_equal(thumbdata,
            #                                                 0).compressed())
            #     std = numpy.std(numpy.ma.masked_equal(thumbdata,
            #                                           0).compressed())
            #     maxval = numpy.max(thumbdata[boxsize/2-10:boxsize/2+10,
            #                                  boxsize/2-10:boxsize/2+10])
            # else:
            #     logging.warning('cannot produce thumbnail image ' + \
            #                     'for %s in frame %s' % (target, dat[10]))
            #     continue



            # extract aperture radius
            aprad = float(hdulist[0].header['APRAD'])

            # create plot
            plotsize = 7. # inches
            fig = plt.figure(figsize=(plotsize,plotsize),
                             dpi=old_div(boxsize,plotsize))
            img = plt.imshow(thumbdata, cmap='gray',
                             vmin=median-2*std,
                             #vmax=maxval,
                             vmax=min([median+2*std,maxval]),
                             origin='lower')
            # remove axes
            plt.axis('off')
            img.axes.get_xaxis().set_visible(False)
            img.axes.get_yaxis().set_visible(False)

            plt.annotate('%s\n%5.3f+-%5.3f mag' % (fitsfilename,
                                                   dat[7], dat[8]), (3,10),
                         color='white')

            # place aperture
            circle = plt.Circle((old_div(boxsize,2.), old_div(boxsize,2.)),
                                aprad, ec='red', fc='none', linewidth=1)
            plt.gca().add_patch(circle)

            # place expected position (if within thumbnail)
            if (abs(exp_x-obj_x) <= old_div(boxsize,2.) and
                abs(exp_y-obj_y) <= old_div(boxsize,2.)):
                plt.scatter(exp_x-obj_x+old_div(boxsize,2.),
                            exp_y-obj_y+old_div(boxsize,2.),
                            marker='+', s=100, color='green')

            thumbfilename = '.diagnostics/' + target.replace(' ', '_')+'_'+ \
                            fitsfilename[:fitsfilename.find('.fit')] + \
                            '_thumb.png'
            plt.savefig(thumbfilename, format='png', bbox_inches='tight',
                        pad_inches=0)
            plt.close()
            hdulist.close()
            data['thumbnailplots'][target].append((fitsfilename,
                                                     thumbfilename))

        ## create gif animation
        gif_filename = ('%s.gif' %
                        (target.replace(' ', '_')))
        logging.info('converting images to gif: %s' % gif_filename)
        root = os.getcwd()
        os.chdir(_pp_conf.diagroot)
        try:
            convert = subprocess.Popen(['convert', '-delay', '50',
                                        ('%s*thumb.png' %
                                (target.replace(' ', '_'))),
                                        '-loop', '0',
                                        ('%s' % gif_filename)])

            convert.wait()
        except:
            logging.warning('could not produce gif animation for ' \
                            + 'target %s' % target)
        data['gifs'][target] = '.diagnostics/' + gif_filename
        os.chdir(root)


    ### create results website for each target
    data['resultswebsites'] = {}
    for target in data['targetnames']:
        html  = "<H2>%s - Photometric Results</H2>\n" % target
        html += "<P><IMG SRC=\"%s\">\n" % \
                data['lightcurveplots'][target].split('.diagnostics/')[1]
        html += "<IMG SRC=\"%s\">\n" % \
                data['gifs'][target].split('.diagnostics/')[1]

        # create summary table
        html += "<TABLE BORDER=\"1\">\n<TR>\n"
        html += "<TH>Filename</TH><TH>Julian Date</TH><TH>Target (mag)</TH>" \
            + "<TH>sigma (mag)</TH><TH>Target RA (deg)</TH>" \
            + "<TH>Target Dec (deg)</TH><TH>RA Offset (\")</TH>" \
            + "<TH>Dec Offset (\")</TH>\n</TR>\n"
        for dat in data[target]:
            html += ("<TR><TD><A HREF=\"#%s\">%s</A></TD>" \
                     + "<TD>%15.7f</TD><TD>%7.4f</TD>" \
                     + "<TD>%6.4f</TD><TD>%13.8f</TD>" \
                     + "<TD>%+13.8f</TD><TD>%5.2f</TD><TD>%5.2f</TD>\n" \
                     + "</TR>\n" )% \
                (dat[10], dat[10], dat[9][0], dat[7], dat[8], dat[3], dat[4],
                 ((dat[1]-dat[3])*3600.), ((dat[2]-dat[4])*3600.))
        html += "</TABLE>\n"

        # plot individual thumbnails
        html += "<H3>Thumbnails</H3>\n"
        for idx, plts in enumerate(data['thumbnailplots'][target]):
            html += "<P>%s<IMG ID=\"%s\" SRC=\"%s\">\n" % (plts[0],
                                    data[target][idx][10],
                                    plts[1].split('.diagnostics/')[1])
        filename = '.diagnostics/'+target.replace(' ', '_')+'_'+'results.html'
        create_website(filename, html)
        data['resultswebsites'][target] = filename


    ### update index.html
    html  = "<H2>Photometry Results</H2>\n"
    html += "<P>photometric data obtained for %d object(s): \n" % \
            len(data['targetnames'])
    for target in data['targetnames']:
        html += "<BR><A HREF=\"%s\">%s</A>\n" % \
                (data['resultswebsites'][target], target)
    for target in data['targetnames']:
        html += "<P><IMG SRC=\"%s\">\n" % data['lightcurveplots'][target]
        html += "<IMG SRC=\"%s\">\n" % data['gifs'][target]
    append_website(_pp_conf.index_filename, html,
                   replace_below="<H2>Photometry Results</H2>\n")

    return None


def abort(where):
    """
    use this function to add information to index.html that the
    pipeline crashed and where
    """
    html = ("<P><FONT COLOR=\"RED\">Pipeline crashed " \
            + "unexpectedly in module %s; refere to <A HREF=\"%s\">log</A> " \
            + "for additional information</FONT>\n") % (
                _pp_conf.log_filename, where)

    append_website(_pp_conf.index_filename, html)

    return None
