#!/usr/bin/env python

""" MANIDENT - manual target identification tool for the Photometry Pipeline

    v1.0: 2016-08-08, michael.mommert@nau.edu

    this code is based in part on viewseries.py:
    http://spider.wadsworth.org/spider_doc/spider/docs/python/spipylib/examples/viewseries.py
"""
from __future__ import print_function
from __future__ import division

from past.utils import old_div
import os, sys
import numpy
import warnings
from tkinter import *
from PIL import Image
from PIL import ImageTk
from PIL import ImageDraw
import argparse
from astropy.io import fits
from scipy.ndimage import interpolation as interp
from scipy.interpolate import InterpolatedUnivariateSpline

# only import if Python3 is used
if sys.version_info > (3,0):
    from future import standard_library
    standard_library.install_aliases()
    from builtins import range
    from builtins import object


# pipeline-specific modules
from catalog import *


### class structure for Tkinter control
class Clicker(object):

    def __init__(self, master, zoom, filelist):
        self.top = master
        self.files = filelist
        self.zoom = zoom
        self.target_index = [None for i in range(len(self.files))]
        self.interp_index = [None for i in range(len(self.files))]
        self.index = 0
        self.images = []
        self.ldac   = []
        self.mjd    = []

        ### load image data
        print('please wait, loading images...', end=' ')
        sys.stdout.flush()

        self.read_all_fits(self.files)

        print('done!')

        # create title bar
        self.title = Label(text='%s (%d/%d)' %
                           (self.images[0],
                            self.index+1, len(self.files)))
        self.title.pack()


        # select first image
        self.tkimage = ImageTk.PhotoImage(self.images[0], palette=256)
        self.canvas = Canvas(master, height=self.tkimage.height(), width=
                             self.tkimage.width())
        self.image = self.canvas.create_image(0, 0, anchor='nw',
                                              image=self.tkimage)

        # create position indicators:
        # green: sources, yellow: inter/extrapolated, red: manually
        # selected
        self.green_circles = []

        self.redcircle_id = self.canvas.create_oval(-100, -100, -100,
                                                    -100, outline='red',
                                                    width=2)
        self.yellowcircle_id = self.canvas.create_oval(-100, -100, -100,
                                                    -100, outline='orange',
                                                       width=1)

        # frame counter variable
        self.evar = IntVar()
        self.evar.set(1)

        self.canvas.pack(side='top', expand=1)

        # display image
        self.nextframe()

        # events
        self.canvas.focus_set()
        self.canvas.bind("<Key>", self.key)
        self.canvas.bind("<Button 1>", self.left_click)
        self.canvas.bind("<Button 3>", self.right_click)


    def left_click(self, event):
        """ select source """
        x, y = old_div(event.x,self.zoom), old_div(event.y,self.zoom)

        # find source closest to click position in ldac, identify
        # source index
        residuals = numpy.sqrt((self.ldac[self.index]['XWIN_IMAGE']-x)**2 +
                               (self.ldac[self.index]['YWIN_IMAGE']-y)**2)
        closest_idx = numpy.argmin(residuals)
        self.target_index[self.index] = closest_idx
        self.nextframe(0)


    def right_click(self, event):
        """ next frame """
        self.nextframe(1)

    def key(self, event):
        """ keyboard events """
        if event.char == 'a':
            # previous frame
            self.nextframe(-1)
        elif event.char == 'd':
            # next frame
            self.nextframe(1)
        elif event.char == 'q':
            # quit
            self.top.quit()
        elif event.char == '+':
            # zoom in
            if self.zoom < 4.:
                self.zoom *= 2
            self.nextframe(0)
        elif event.char == '-':
            # zoom out
            if self.zoom > 0.25:
                self.zoom /= 2
            self.nextframe(0)

    def read_all_fits(self, filenames, zoom=0.5):
        """ read in all image data, scale images """
        for idx, filename in enumerate(filenames):
            if idx > 0:
                print('\b\b\b\b%3d' % (idx+1), end=' ')
            else:
                print('%3d' % (idx+1), end=' ')
            sys.stdout.flush()

            ## read image data
            hdulist = fits.open(filename, ignore_missing_end=True)
            imgdat = hdulist[0].data

            # median = numpy.median(imgdat)
            # std    = numpy.std(imgdat)

            median = numpy.median(imgdat[int(imgdat.shape[1]*0.25):
                                         int(imgdat.shape[1]*0.75),
                                         int(imgdat.shape[0]*0.25):
                                         int(imgdat.shape[0]*0.75)])
            std    = numpy.std(imgdat[int(imgdat.shape[1]*0.25):
                                      int(imgdat.shape[1]*0.75),
                                      int(imgdat.shape[0]*0.25):
                                      int(imgdat.shape[0]*0.75)])

            imgdat = old_div(numpy.clip(imgdat, median-0.5*std,
                                median+0.5*std),(old_div(std,256)))
            imgdat = imgdat - numpy.min(imgdat)
            imgdat = interp.zoom(imgdat, self.zoom)

            self.images.append(Image.fromarray(imgdat))

            ## read ldac data
            cat = catalog(filename)

            ldac_filename = filename[:filename.find('.fit')]+'.ldac'
            cat.read_ldac(ldac_filename, filename, maxflag=4)

            self.ldac.append(cat)

            ## read header data (MJD)
            self.mjd.append(float(hdulist[0].header['MIDTIMJD']))



    def nextframe(self,i=1, imgnum=-1):
        """ display frame using iterator i"""

        if imgnum == -1:
            self.index += i
        else:
            self.index = imgnum - 1
        if self.index >= len(self.files):
            self.index = 0
        elif self.index < 0:
            self.index = len(self.files) - 1
        filename = self.files[self.index]
        if not os.path.exists(filename):
            print("Unable to find %s" % filename)
            self.top.quit()
        self.evar.set(self.index+1)

        self.title.configure(text='%s (%d/%d)' %
                           (os.path.basename(filename),
                            self.index+1, len(self.files)))

        im = self.images[self.index]

        ## draw red circle, if target has been identified
        # yellow circle if extrapolation
        interp_idx = None
        if self.target_index[self.index] is not None:
            idx = self.target_index[self.index]
            self.canvas.coords(self.redcircle_id,
                    (self.ldac[self.index][idx]['XWIN_IMAGE']*self.zoom-4,
                     self.ldac[self.index][idx]['YWIN_IMAGE']*self.zoom-4,
                     self.ldac[self.index][idx]['XWIN_IMAGE']*self.zoom+4,
                     self.ldac[self.index][idx]['YWIN_IMAGE']*self.zoom+4))
            self.canvas.coords(self.yellowcircle_id, (-100, -100, -100, -100))
        else:
            # if no coordinates available, move red circle out of canvas
            self.canvas.coords(self.redcircle_id, (-100, -100, -100, -100))

            # use yellow circle if sufficient target positions known
            interp_idx = self.extrapolate(self.mjd[self.index])
            if interp_idx is not None:
                self.canvas.coords(self.yellowcircle_id,
                (self.ldac[self.index][interp_idx]['XWIN_IMAGE']*self.zoom-4,
                 self.ldac[self.index][interp_idx]['YWIN_IMAGE']*self.zoom-4,
                 self.ldac[self.index][interp_idx]['XWIN_IMAGE']*self.zoom+4,
                 self.ldac[self.index][interp_idx]['YWIN_IMAGE']*self.zoom+4))
            else:
                self.canvas.coords(self.yellowcircle_id,
                                   (-100, -100, -100, -100))

        self.interp_index[self.index] = interp_idx

        # plot all sources
        for circ in self.green_circles:
            self.canvas.delete(circ)
        x = self.ldac[self.index]['XWIN_IMAGE']
        y = self.ldac[self.index]['YWIN_IMAGE']
        indices = list(range(len(x)))
        if self.target_index[self.index] is not None:
            indices.pop(self.target_index[self.index])
        if interp_idx is not None:
            indices.pop(interp_idx)
        self.green_circles = \
            [self.canvas.create_oval(x[i]*self.zoom-4,
                                     y[i]*self.zoom-4,
                                     x[i]*self.zoom+4,
                                     y[i]*self.zoom+4,
                                     outline='green',
                                     width=1)
             for i in indices]

        self.tkimage.paste(im)



    def extrapolate(self, time):
        """fit path with spline, identify nearest source"""

        x, y, t = [], [], []
        for i in range(len(self.files)):
            if self.target_index[i] is not None:
                t.append(self.mjd[i])
                x.append(self.ldac[i][self.target_index[i]]['XWIN_IMAGE'])
                y.append(self.ldac[i][self.target_index[i]]['YWIN_IMAGE'])

        k = min([len(t), 3])-1

        if k >= 1:
            # extrapolate position
            fx = InterpolatedUnivariateSpline(numpy.array(t), numpy.array(x),
                                              k=k)
            fy = InterpolatedUnivariateSpline(numpy.array(t), numpy.array(y),
                                              k=k)

            # identify closest source
            residuals = numpy.sqrt((self.ldac[self.index]['XWIN_IMAGE']-
                                    fx(time))**2 +
                                   (self.ldac[self.index]['YWIN_IMAGE']-
                                    fy(time))**2)
            return numpy.argmin(residuals)
        else:
            return None

# --------------------------------------------------------------------

if __name__ == "__main__":

############# here


    # define command line arguments
    parser = argparse.ArgumentParser(description='manual target identification')
    parser.add_argument('-zoom', help='image zoom factor', default=0.5)
    parser.add_argument('images', help='images to process', nargs='+')
    args = parser.parse_args()
    zoom = float(args.zoom)
    filenames = args.images

    root = Tk()
    app = Clicker(root, zoom, filenames)
    root.mainloop()

    outf = open('positions.dat', 'w')
    outf.write('#                                         filename        midtime_JD          RA        Dec\n' +
               '# note that RA and Dec might be based on a fake plate solution and hence are not astrometric\n')

    # recalculate target coordinates and write them into a file
    for image_idx, image_name in enumerate(app.files):
        # accurate position
        if app.target_index[image_idx] is not None:
            outf.write('%50.50s   %9.5f  %9.5f   %15.7f\n' % (image_name,
                app.ldac[image_idx][app.target_index[image_idx]]['ra.deg'],
                app.ldac[image_idx][app.target_index[image_idx]]['dec.deg'],
                app.mjd[image_idx]))
        # interpolated position
        else:
            app.index = image_idx
            interp_idx = app.extrapolate(app.mjd[image_idx])

            outf.write('%50.50s   %9.5f  %9.5f  %15.7f\n' % (image_name,
                app.ldac[image_idx][interp_idx]['ra.deg'],
                app.ldac[image_idx][interp_idx]['dec.deg'],
                app.mjd[image_idx]))

    print(image_idx+1, 'target positions written to file positions.dat')

    outf.close()


