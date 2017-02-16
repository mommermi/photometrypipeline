.. Photometry Pipeline documentation master file, created by
   sphinx-quickstart on Mon Mar  7 11:53:14 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Photometry Pipeline Documentation
=================================

Introduction
------------

The Photometry Pipeline (PP) is a Python software package for
automated photometric analysis of imaging data from small to
medium-sized observatories. It uses `Source Extractor`_ and `SCAMP`_
to register and photometrically calibrate images based on catalogs
that are available online; photometry is measured using Source
Extractor aperture photometry. PP has been designed for asteroid
observations, but can be used with any kind of imaging data.


Scope and Applicability
-----------------------

PP has been designed to provide automated photometry for the majority
of data coming from small to medium-sized observatories. It is not
intended to provide high-accuracy photometry, nor is it designed to
work on extremely sparse or crowded fields. PP requires a field of
view of a few arcminutes to ensure that sufficient background stars
are available for registration and photometric calibration. For a
field several arcminutes across, calibrated photometric uncertaintes
are usually better than 0.05 mag, if sufficient non-saturated
background stars with cataloged brightness are available. Feel free to
try PP on your data, but please be aware that it has its limitations.

The following features are currently available as part of PP:

* automated aperture photometry based on a curve-of-growth analysis
* photometric calibration in ugriz, BVRI, JHK based on catalog coverage
* full support of moving target photometry
* target identification based on tabulated positions for fixed targets
  and moving targets, target identifier for moving targets
* support of Gaia (DR1) astrometry for image registration
* Python 2 and 3 compatibility (thanks to `boada`_)
  
Future versions of the pipeline will support newly available catalogs
for astrometry and photometry (e.g., GAIA DR2) and enable the extraction
of serendipitously observed targets of interests, e.g., variable stars
or moving targets. If you are interesting in using PP for a specific
task, let me know!


Contents
--------

.. toctree::
   :maxdepth: 2

   install
   quickstart
   supported
   functions
   diagnostics
   problems
   changelog

License and Contact
-------------------

The Photometry Pipeline is distributed under the GNU GPLv3 license.

Copyright (C) 2016  Michael Mommert 

Feel free to contact me in case of questions or suggestions: michael
. mommert (at) nau . edu



Acknowledgments
---------------

If you are using PP for your research, please acknowledge PP by citing

* Mommert 2017, PHOTOMETRYPIPELINE: An Automated Pipeline for Calibrated Photometry, Astronomy & Computing (in press).

PP is supported by NASA grants NNX15AE90G and NNX14AN82G and has been
developed in the framework of the Mission Accessible Near-Earth
Objects Survey (`MANOS`_).


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Source Extractor: http://www.astromatic.net/software/sextractor
.. _SCAMP: http://www.astromatic.net/software/scamp
.. _MANOS: http://manosobs.wordpress.com/
.. _boada: https://github.com/boada
