Installation and Setup
======================

Installation
------------

Getting PP
~~~~~~~~~~

PP is available from `github`_. You can get the source code by typing
into your terminal::

  git clone https://github.com/mommermi/photometrypipeline

This will create a ``photometrypipeline/`` directory in your current
directory. 

Installing Additional Software
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PP requires `git`_ for the installation, a number of non-standard
Python 2.7 modules (available from the `Python Package Index`_ through
`pip`_):

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

Installation walkthroughs for MAC OS and Ubuntu will be available here, soon!
  

Setup
-----

In order to be able to use PP anywhere on your machine, you have to
add the full path of the ``photometrypipeline/`` directory to your
`PYTHONPATH` and `PATH` variables, and you have to create a
`PHOTPIPEDIR` variable on your system that points to the same
directory (include these commands in your ``.bashrc``, ``.cshrc``, or
``.profile`` file.)

In order to get the latest version of PP, simply change into
``photometrypipeline/`` and type::

  git pull


Example Data
------------

The PP github clone comes with some sample data that can be used to
test if the pipeline works properly. The data were taken with the
VATT4k camera on the VATT and can be found in
``example_data/vatt4k``. In order to run the pipeline on these images,
copy them to a new directory, change there, and run ``pp_run
mscience*fits``. If everything works out properly, the results
(``photometry_3552.dat``) should resemble those in
``example_data/vatt4k/LOG``.


.. _telescope_setup:

Telescope Setup
~~~~~~~~~~~~~~~

PP critically relies on information provided in the FITS image headers
to handle data properly. While the FITS format is standardized, header
keywords are not, leading to additional complications in the
interpretation of FITS files. In order to be able to work with a
multitude of different telescopes and instruments, PP comes with
guidelines of how to read FITS files coming from different
telescopes/instruments. These guidelines are imprinted in the
``setup/telescopes.py`` file. In order to prevent compatibility
issues, you should not change this file directly. Instead, please
create and use a ``setup/mytelescopes.py`` as described below. You can
implement as many telescopes as you want in this file. The advantage
is that the file will not be changed as a result of git pull requests.


The '`telescope file`' includes for each telescope/instrument
combination a dictionary (``*_param``) that translates general
descriptions for FITS header keywords into specific keywords used by
the respective telescope/instrument combination. For example, the
telescope pointing RA keyword might be named ``RA`` for one telescope,
but ``TELRA`` for another -- PP will refer to either of those as
``ra``. The `telescope file` catches these degeneracies and allows the
pipeline to understand images coming from a variety of telescopes.
The meanings of the individual keys in this dictionary are explained
in the comments of the respective key. Furthermore, each
telescope/instrument combination must have parameter files for Source
Extractor and SCAMP (SWARP is currently not supported). Mask files are
used by Source Extractor to mask certain regions of the image detector
-- mask files are only required if field vignetting or image artifacts
(e.g., high noise levels in certain areas of the detector) strongly
affect the detection of sources in the field.

If you want to include you own telescope into the `telescope file`,
follow these steps:

1. Download the `mytelescopes.py`_ file into your ``setup/`` directory
   and duplicate the ``mytelescope_param`` dictionary. Change the
   ``MYTELESCOPE`` identifier of the duplicate and give it a unique
   name (e.g., ``42INCH_CCD``). 
2. Look at the image header of one of your science images and identify
   the different fields of the ``*_param`` file. Replace the
   dictionary item values accordingly.
3. In the ``setup/`` directory, copy the Source Extractor (``.sex``)
   and SCAMP (``.scamp``) parameter files from either telescope and
   name them after your telescope (e.g., ``42inch_ccd.scamp``).
4. Add your telescope's identifier to the ``implemented_telescopes`` list in
   ``setup/mytelescopes.py``, as well as the ``telescope_parameters``
   dictionary. Finally, add your telescope's identifier to the
   ``instrument_identifiers`` dictionary: the value is your
   telescope's identifier, the key is the ``INSTRUME`` header keyword
   (this is present in most FITS data).
5. Run :func:`pp_prepare` over one of your images. Check with `ds9` or
   some other tool if the image orientation provided by
   :func:`pp_prepare` is correct. If not, play with the `flipx`,
   `flipy` parameters in your `telescope file`.

If this sounds too confusing, send me one of your images in an email
and I will take care of implementing your telescope.


.. _github: https://github.com/mommermi/photometrypipeline
.. _git: http://www.git-scm.com/
.. _Python Package Index: https://pypi.python.org/pypi
.. _pip: https://pypi.python.org/pypi/pip/
.. _numpy: http://www.numpy.org/
.. _scipy: https://www.scipy.org/
.. _astropy: http://www.astropy.org/
.. _astroquery: https://github.com/astropy/astroquery
.. _matplotlib: http://matplotlib.org/
.. _callhorizons: https://pypi.python.org/pypi/CALLHORIZONS
.. _future: http://python-future.org/
.. _pillow: http://python-pillow.org/
.. _Source Extractor: http://www.astromatic.net/software/sextractor
.. _SCAMP: http://www.astromatic.net/software/scamp
.. _r345: http://www.astromatic.net/wsvn/public/dl.php?repname=public+software.scamp&path=%2Ftrunk%2F&rev=0&isdir=1
.. _mytelescopes.py: http://134.114.60.45/photometrypipeline/mytelescopes.py
