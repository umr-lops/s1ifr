# s1ifr

[![CI](https://github.com/umr-lops/s1ifr/actions/workflows/ci.yml/badge.svg)](https://github.com/umr-lops/s1ifr/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/s1ifr.svg)](https://pypi.org/project/s1ifr/)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/s1ifr.svg)](https://anaconda.org/conda-forge/s1ifr)
[![Python versions](https://img.shields.io/pypi/pyversions/s1ifr.svg)](https://pypi.org/project/s1ifr/)
[![License: LGPL-3.0](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![codecov](https://codecov.io/gh/umr-lops/s1ifr/branch/main/graph/badge.svg)](https://codecov.io/gh/umr-lops/s1ifr)
[![Documentation](https://readthedocs.org/projects/s1ifr/badge/?version=latest)](https://s1ifr.readthedocs.io/)

Python methods to find / move / copy / sort / store / count Sentinel-1 SAR mission files in the Ifremer archive.

## Features

- Discover and filter Sentinel-1 SAFE products from the Ifremer archive
- Match SLC / GRD / L1 / L2 products and measurement files
- Move, copy and sort SAFE files between archive tiers
- Detect duplicates and quarantine inconsistent products
- Batch utilities (PBS / SLURM / Apptainer / Singularity) for large-scale operations

## Installation

### From PyPI (recommended)

```shell
pip install s1ifr
```

### From conda-forge

```shell
conda install -c conda-forge s1ifr
```

### From sources

```shell
git clone https://github.com/umr-lops/s1ifr.git
cd s1ifr
pip install .
```

For developers (editable install with test/lint tooling):

```shell
pip install -e ".[dev]"
```

## Usage

```python
import s1ifr

print(s1ifr.__version__)
```

Command-line entry points installed with the package:

```shell
syncsafe -h
syncsafebatch -h
archivesafe -h
get-s1-full-path-safe -h
familyprod -h
```

## Documentation

Full documentation is available at <https://s1ifr.readthedocs.io/>.

To build the docs locally:

```shell
pip install -e ".[docs]"
cd docs
make html
```

## Development

Run the test suite and lint checks locally:

```shell
pip install -e ".[dev]"

pytest tests/ --cov=s1ifr --cov-report=term-missing
ruff check s1ifr tests
black --check s1ifr tests
```

Git hooks (optional but recommended):

```shell
pre-commit install
```

## Production Apptainer image

The Airflow DAG `sentinel1_sort_products_hpc` runs `archivesafe` from an
Apptainer image built with
[`apptainer_python_micromamba_ubuntu.def`](apptainer_python_micromamba_ubuntu.def).

1. Build from a **clean clone** of `main`. `%files` copies the whole current
   directory, including `.git`, which is needed to compute the package version.
   Untracked files or a stale `s1ifr/_version.py` would end up in the image.

   ```shell
   version=$(date +%Y.%-m.%-d)  # e.g. 2026.11.27
   build=/scratch/$USER/s1ifr-build-$version
   git clone https://github.com/umr-lops/s1ifr.git $build/src
   cd $build/src
   export APPTAINER_TMPDIR=$build/tmp APPTAINER_CACHEDIR=$build/cache
   mkdir -p $APPTAINER_TMPDIR
   apptainer build --fakeroot $build/s1ifr-$version.sif apptainer_python_micromamba_ubuntu.def
   ```

2. Test the image:

   ```shell
   apptainer exec $build/s1ifr-$version.sif pip show s1ifr  # version must match `git describe`
   apptainer exec --bind /legacy/project/cersat/public --bind /scale --bind /scratch \
       $build/s1ifr-$version.sif archivesafe --input-safe <spool SAFE> \
       --archivename datawork \
       --config-path /scale/project/lops-siam-airflow/configs_exploit/s1ifr/exploit_hpc.yml \
       --dryrun
   ```

3. Copy it next to the previous images and keep the old ones so you can roll back:

   ```shell
   dest=/scale/project/lops-siam-airflow/envs_exploit/apptainer
   cp $build/s1ifr-$version.sif $dest/
   chgrp siam-airflow $dest/s1ifr-$version.sif && chmod 755 $dest/s1ifr-$version.sif
   ```

4. Update `img_apptainer` in
   `dags/sentinel1/sentinel1_sort_product_in_ifr_archive.py` in the
   [airflow-aas-dags-siam](https://gitlab.ifremer.fr/lops-sys/airflow-aas-dags-siam)
   repository (merge request), then check the next `sort_products_datawork` run.

## Contributing

Issues and pull requests are welcome on GitHub:
<https://github.com/umr-lops/s1ifr/issues>

## License

This project is licensed under the terms of the **MIT License**.
See [LICENSE](https://github.com/umr-lops/s1ifr/blob/main/LICENSE) for details.

## Authors

- Antoine Grouazel — [antoine.grouazel@ifremer.fr](mailto:antoine.grouazel@ifremer.fr) — Ifremer / LOPS
