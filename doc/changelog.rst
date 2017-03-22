Changelog
=========

Major changes to the pipeline since 2016-10-01 (see `Mommert 2017`_) are documented here.

* 2017-03-19: if no filtername is provided (``None``) or the ``-instrumental`` option of ``pp_calibrate`` is used, ``pp_run`` will complete all pipeline tasks using these instrumental magnitudes 

* 2017-03-16: implementation of `Pan-STARRS DR1`_ for the photometric calibration; currently, PP uses a home-built access of MAST at STScI, which is limited to catalog queries with a maximum cone radius of 0.5 deg; please note that this kind of query is rather slow compared to Vizier queries of SDSS or APASS

* 2017-02-24: ``pillow`` is now a required python module; the pipeline now supports default distortion parameters for wide-field cameras

* 2017-02-04: catalog.data is now an astropy.table, catalog downloads using astroquery.vizier (no effect to the user), pp now supports Gaia DR1 (CMC, USNOB1, and PPMX have been removed)


  
.. _Mommert 2017: http://adsabs.harvard.edu/abs/2017A%26C....18...47M
.. _Pan-STARRS DR1: http://panstarrs.stsci.edu/



