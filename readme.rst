Photometry Pipeline 
===================

The Photometry Pipeline (PP) is a Python software package for
automated photometric analysis of imaging data from small to
medium-sized observatories. It uses `Source Extractor`_ and `SCAMP`_ to
register and photometrically calibrate images based on catalogs that
are available online; photometry is measured using Source Extractor
aperture photometry. PP has been designed for asteroid observations,
but can be used with any kind of imaging data.


Please note that this project is still under development. 

See `this document`_ for a list of supported instruments and catalogs.

Installation
------------

PP requires `git`_ for the installation, a number of non-standard
Python modules:

  * `numpy`_
  * `scipy`_
  * `astropy`_
  * `astroquery`_
  * `matplotlib`_
  * `callhorizons`_
  * `future`_
  * `pillow`_
    
and some freely available software:

  * `Source Extractor`_
  * `SCAMP`_  

PP is available from `github`_. You can get the source code by typing
into your terminal::

  git clone https://github.com/mommermi/photometrypipeline

PP is evolving. Once you have downloaded PP, you can update to the
latest code by simply running::

  git pull

after changing into the directory where the code resides on your machine.

Documentation
-------------

See the documentation for more information: `documentation`_


Acknowledgments
---------------

If you are using PP for your research, please acknowledge PP by citing

* Mommert 2017, PHOTOMETRYPIPELINE: An Automated Pipeline for Calibrated Photometry, `Astronomy & Computing`_, 18, 47.

PP is supported by NASA grants NNX15AE90G and NNX14AN82G and has been
developed in the framework of the Mission Accessible Near-Earth
Objects Survey (`MANOS`_).


License and Contact
-------------------

The Photometry Pipeline is distributed under the GNU GPLv3 license.

Copyright (C) 2016  Michael Mommert 

Feel free to contact me in case of questions or suggestions: michael . mommert (at) nau . edu


.. _github: http://github.com/mommermi/photometrypipeline
.. _git: http://www.git-scm.com/
.. _numpy: http://www.numpy.org/
.. _scipy: http://www.scipy.org/
.. _astropy: http://www.astropy.org/
.. _astroquery: http://github.com/astropy/astroquery
.. _matplotlib: http://matplotlib.org/
.. _callhorizons: http://pypi.python.org/pypi/CALLHORIZONS
.. _future: http://python-future.org/
.. _pillow: http://python-pillow.org/
.. _Source Extractor: http://www.astromatic.net/software/sextractor
.. _SCAMP: http://www.astromatic.net/software/scamp
.. _documentation: http://photometrypipeline.readthedocs.io/en/latest/
.. _this document: http://photometrypipeline.readthedocs.io/en/latest/supported.html
.. _Astronomy & Computing: http://www.sciencedirect.com/science/article/pii/S2213133716300816
.. _MANOS: http://manosobs.wordpress.com/
