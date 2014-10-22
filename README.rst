BanzaiVis
=========

Visualise results from BanzaiDB


Install
-------

Something like this::

    $ git clone git@github.com:m-emerson/BanzaiVis.git
    $ cd BanzaiVis
    $ python setup.py install


Deploy (work in progress)
-------------------------

Designed to gunicorn+nginx stack:

Something like::
    
    $ git clone git@github.com:m-emerson/BanzaiVis.git
    $ cd BanzaiVis
    $ pip install -r requirements.txt
    $ cd deploy
    $ fab start_gunicorn_server


Usage
-----

In your code import it::

    >>> import banzaivis
    >>> from banzaivis import queries

