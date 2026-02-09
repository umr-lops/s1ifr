Usage Guide
===========

The ``s1ifr`` package provides utilities for resolving Sentinel-1 paths, moving data between archives, and managing the core Ifremer Sentinel-1 archive (The Pieuvre).

Path Resolution
---------------

**get-s1-full-path-safe**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Resolves SAFE basenames into their absolute physical paths within the Ifremer archive. It can process a single SAFE name or a bulk listing.

.. code-block:: bash

    # Resolve a single SAFE basename and write the full path to a file
    get-s1-full-path-safe --input S1A_IW_SLC__1SDV_20230101T120000...SAFE --output my_path.txt

    # Resolve a listing of many SAFEs
    get-s1-full-path-safe --input my_basenames.csv --output resolved_full_paths.csv

Data Migration & Synchronization
--------------------------------

**syncsafe**
^^^^^^^^^^^^
Moves a single SAFE product. Note that the destination directory should be the base path *before* the date-based sub-directory structure (``YYYY/JJJ/...``).

.. code-block:: bash

    # Sync a SAFE to a project folder
    syncsafe --input /source/S1A...SAFE \
             --outputdir /home/datawork-project/sarwave/data/products/slc/iw/l1b/

    # Move a SAFE (deleting the source after success)
    syncsafe --input /source/S1A...SAFE \
             --outputdir /destination/path/ \
             --removesource

**syncsafebatch**
^^^^^^^^^^^^^^^^^
Performs batch synchronization using a listing of SAFE paths. This tool is designed for bulk migrations between archives.

.. code-block:: bash

    # Sync all SAFEs listed in a text file
    syncsafebatch --listinginputsafe my_listing.txt \
                  --outputdir /home/datawork-project/archive/

Archive Management
------------------

**archivesafe**
^^^^^^^^^^^^^^^
The "Sentinel-1 Pieuvre" tool used to sort and store SAFE products into the standard Ifremer structure (Datawork or Scale).

.. code-block:: bash

    # Ingest a product into the Datawork archive
    archivesafe --input-safe /incoming/S1A...SAFE --archivename datawork

    # Perform a dry run to check the expected destination path without moving data
    archivesafe --input-safe /incoming/S1A...SAFE --dryrun

Reference Tables
----------------

+-----------------------------+-----------------------------------------------------------------------------------+
| Command                     | Primary Purpose                                                                   |
+=============================+===================================================================================+
| ``get-s1-full-path-safe``   | Converts filenames to absolute paths.                                             |
+-----------------------------+-----------------------------------------------------------------------------------+
| ``syncsafe``                | Moves/Copies one product to a new base directory.                                 |
+-----------------------------+-----------------------------------------------------------------------------------+
| ``syncsafebatch``           | Moves/Copies a list of products (batch mode).                                     |
+-----------------------------+-----------------------------------------------------------------------------------+
| ``archivesafe``             | Standardized sorting and storage (The Pieuvre).                                   |
+-----------------------------+-----------------------------------------------------------------------------------+

Example Workflow
----------------

If you have a listing of basenames and want to move them to a specific project directory:

.. code-block:: bash

    # 1. Resolve basenames to full archive paths
    get-s1-full-path-safe --input basenames.txt --output full_paths.txt

    # 2. Sync the batch to your project storage
    syncsafebatch --listinginputsafe full_paths.txt --outputdir /home/datawork-project/my_study/slc/



Product Family Discovery
------------------------

**familyprod**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This tool takes a list of SLC products and automatically finds all associated downstream products (L1B, L1C, and L2 WAV) available in the Ifremer archive. It searches across different versions (e.g., A14, A23) and storage areas (Datawork and Scale).

.. code-block:: bash

    # Basic usage: search for default versions for a list of SLCs
    familyprod --listing my_slc_list.txt --outputdir ./results/

    # Search for specific processing versions
    familyprod --listing my_slc_list.txt \
                      --l1bversions A14 A23 \
                      --l1cversions B17 \
                      --verbose

How it works:
~~~~~~~~~~~~~
1. **Path Resolution**: The script first locates the physical path of the SLC on Datawork or Scale.
2. **Cross-Referencing**: Using the SLC metadata, it predicts and verifies the existence of L1B, L1C, and L2 paths based on the requested product versions.
3. **Reporting**: It generates a CSV containing the full product "family" for every input SLC.
4. **Filtering**: At the end of execution, the tool prompts the user to select a specific family (e.g., "all available L1B A23") to export as a clean, ready-to-use listing.
