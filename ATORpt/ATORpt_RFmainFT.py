"""ATORpt_RFmainFT.py

# Author:
Richard Bruce Baxter - Copyright (c) 2021-2025 Baxter AI (baxterai.com)

# License:
MIT License

# Installation:
See ATORpt_main.py

# Usage:
source activate pytorch3d
python ATORpt_RFmainFT.py images/leaf1.png

# Description:
Perform ATOR receptive field (RF) ellipse detection using pytorch RF filters/masks (FT) (hardware accelerated).

ATORpt RF is a receptive field implementation for ATOR feature/poly detection (ellipse centroids and tri corners).

ATOR RF currently contains its own unique implementation stack, although RF feature detection can be merged into the main code base.

ATORpt RF supports ellipsoid features (for centroid detection), and normalises them with respect to their major/minor ellipticity axis orientation. 

There are a number of advantages of using ellipsoid features over point features;
* the number of feature sets/normalised snapshots required is significantly reduced
* scene component structure can be maintained (as detected component ellipses can be represented in a hierarchical graph structure)
* features can still be detected where there are no point features available

Ellipse features/components are detected based on simulated artificial receptive fields; RF (on/off, off/on).

Future:
Requires upgrading to support 3DOD receptive field detection (ellipses/ellipsoids/features in 3D space)

"""

import os
import torch as pt
import numpy as np
import click
import cv2
import copy
import torch as pt
import torch.nn.functional as F

from ATORpt_RFglobalDefs import *
#import ATORpt_RFmainCV
import ATORpt_RFgenerate
import ATORpt_RFapply

@click.command()
@click.argument('inputimagefilename')
			
def main(inputimagefilename):
	#ATORpt_RFmainCV.main(inputimagefilename)
	RFfiltersListAllRes, RFfiltersPropertiesListAllRes, ATORneuronListAllLayers = ATORpt_RFgenerate.prepareRFhierarchyAccelerated()
	ATORpt_RFapply.updateRFhierarchyAccelerated(RFfiltersListAllRes, RFfiltersPropertiesListAllRes, ATORneuronListAllLayers, inputimagefilename)	#trial image

if __name__ == "__main__":
	main()
