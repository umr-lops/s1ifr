########################################################
s1ifr: python lib to find S1 products in Ifremer archive
########################################################


Documentation
-------------

Overview
........

Python library for wind or waves downstream applications.
It provides both a Python API for developers and Command Line Interface (CLI) tools for archive management.

Python API Usage
................

.. code-block:: python

    import s1ifr

Examples
........

.. code-block:: python

    import s1ifr

    safe = "S1A_IW_SLC__1SDV_20230114T222629_20230114T222656_046786_059BF8_AA99.SAFE"
    safe_fp = s1ifr.get_path_from_base_safe.get_path_from_base_safe(
        inputa=safe, archive_name="datawork"
    )

Command Line Interface
......................

The library includes several entry points (``syncsafe``, ``archivesafe``, etc.) for managing products directly from the terminal.
See the :doc:`usage` page for detailed CLI documentation.


Reference
.........

* :doc:`basic_api`
* :doc:`usage`

Get in touch
------------

- Report bugs, suggest features or view the source code `on gitlab`_.

----------------------------------------------

Last documentation build: |today|




.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Reference

   basic_api
   usage

.. _on gitlab: https://gitlab.ifremer.fr/lops-wave/s1ifr
