# angles-antenna-referential
![scheme](scheme_angles.png)

This library allows to compute relative wind/waves angles in a SAR antenna referential.

To use this library make sure all the angles (u,v,heading) respects our angle convention:
- North = 0°
- rotation : clockwise
- positive/negative component meaning : "TO convention" i.e. oceanographic convention.

To be super clear: the "TO" convention implicates a positive U means Northward and a positive V means Eastward moving wind. 

## Installation

From `PyPI`

```sh
TO BE DONE
```

From `conda-forge`

```sh
TO BE DONE
```

## Usage

```python

import aar
print(aar.__version__)
from aar.compute_angles import azimuth_direction
azimuth_direction(ground_heading_angle=-12.4,u_component=-0.13,v_component=0.48)

```
