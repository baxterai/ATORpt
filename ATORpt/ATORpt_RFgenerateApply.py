"""ATORpt_RFgenerateApply.py

# Author:
Richard Bruce Baxter - Copyright (c) 2021-2024 Baxter AI (baxterai.com)

# License:
MIT License

# Installation:
See ATORpt_main.py

# Usage:
See ATORpt_main.py

# Description:
ATORpt RF (receptive field)

"""

import torch as pt
import torch
import torch.nn.functional as F
import numpy as np
import copy

import ATORpt_RFellipseProperties
import ATORpt_RFellipse
import ATORpt_RFtri
import ATORpt_RFfilter
import ATORpt_RFproperties
import ATORpt_RFoperations

class RFneuronClass():
	def __init__(self, resolutionProperties, RFproperties, RFfilter, RFImage):
		self.resolutionIndex = resolutionProperties.resolutionIndex
		self.RFproperties = RFproperties
		# if(debugSaveRFfiltersAndImageSegments):
		self.RFfilter = RFfilter
		self.RFneuronParents = []
		self.RFneuronComponents = []


def normaliseRFComponentWRTparent(resolutionProperties, neuronComponent, RFpropertiesParent):
	neuronComponent.RFpropertiesNormalisedWRTparent = ATORpt_RFproperties.generateRFtransformedProperties(neuronComponent, RFpropertiesParent)
	if resolutionProperties.debugSaveRFfiltersAndImageSegments:
		neuronComponent.RFfilterNormalisedWRTparent = ATORpt_RFfilter.transformRFfilterTF(neuronComponent.RFfilter, RFpropertiesParent)
		neuronComponent.RFImageNormalisedWRTparent = ATORpt_RFfilter.transformRFfilterTF(neuronComponent.RFImage, RFpropertiesParent)


def childRFoverlapsParentRF(neuronRFpropertiesNormalisedGlobal, lowerNeuronRFpropertiesNormalisedGlobal):
	if neuronRFpropertiesNormalisedGlobal.RFtype == ATORpt_RFproperties.RFtypeEllipse:
		return ATORpt_RFellipseProperties.centroidOverlapsEllipse(neuronRFpropertiesNormalisedGlobal, lowerNeuronRFpropertiesNormalisedGlobal)
	elif neuronRFpropertiesNormalisedGlobal.RFtype == ATORpt_RFproperties.RFtypeTri:
		# CHECKTHIS is appropriate for tri;
		return ATORpt_RFellipseProperties.centroidOverlapsEllipse(neuronRFpropertiesNormalisedGlobal, lowerNeuronRFpropertiesNormalisedGlobal)


def normaliseGlobalRFproperties(RFproperties, resolutionFactor):
	# normalise RF respect to original image size
	if RFproperties.RFtype == ATORpt_RFproperties.RFtypeEllipse:
		RFpropertiesNormalisedGlobal = ATORpt_RFellipse.normaliseGlobalEllipseProperties(RFproperties, resolutionFactor)
	elif RFproperties.RFtype == ATORpt_RFproperties.RFtypeTri:
		RFpropertiesNormalisedGlobal = ATORpt_RFtri.normaliseGlobalTriProperties(RFproperties, resolutionFactor)
	return RFpropertiesNormalisedGlobal


def normaliseLocalRFproperties(RFproperties):
	# normalise ellipse respect to major/minor ellipticity axis orientation (WRT self)
	if RFproperties.RFtype == ATORpt_RFproperties.RFtypeEllipse:
		ATORpt_RFellipse.normaliseLocalEllipseProperties(RFproperties)
	elif RFproperties.RFtype == ATORpt_RFproperties.RFtypeTri:
		# CHECKTHIS is appropriate for tri; (ellipseNormalisedAxesLength, ellipseNormalisedAxesLength/q) might create equilateral triangle
		ATORpt_RFtri.normaliseLocalTriProperties(RFproperties)


def generateRFfilters(resolutionProperties, generateRFfiltersEllipse, generateRFfiltersTri):
	RFfiltersList = []
	RFfiltersPropertiesList = []

	if generateRFfiltersEllipse:
		ATORpt_RFellipse.generateRFfiltersEllipse(resolutionProperties, RFfiltersList, RFfiltersPropertiesList)
	if generateRFfiltersTri:
		ATORpt_RFtri.generateRFfiltersTri(resolutionProperties, RFfiltersList, RFfiltersPropertiesList)

	return RFfiltersList, RFfiltersPropertiesList


def applyRFfilters(resolutionProperties, inputImageSegments, RFfiltersTensor, numberOfDimensions, RFfiltersPropertiesList2):
	# perform convolution for each filter size;
	axesLengthMax, filterRadius, filterSize = ATORpt_RFfilter.getFilterDimensions(resolutionProperties)

	RFpropertiesList = []

	inputImageSegmentsPixelsFlattened = inputImageSegments.view(inputImageSegments.shape[0], -1)
	RFfiltersTensorPixelsFlattened = RFfiltersTensor.view(RFfiltersTensor.shape[0], -1)

	filterApplicationResult = pt.matmul(inputImageSegmentsPixelsFlattened, RFfiltersTensorPixelsFlattened.t())
	filterApplicationResult = filterApplicationResult.view(-1)

	isColourFilter = RFfiltersPropertiesList2[0].isColourFilter
	numberOfDimensions = RFfiltersPropertiesList2[0].numberOfDimensions
	RFtype = RFfiltersPropertiesList2[0].RFtype
	filterApplicationResultThreshold = ATORpt_RFfilter.calculateFilterApplicationResultThreshold(filterApplicationResult, ATORpt_RFfilter.minimumFilterRequirement, filterSize, isColourFilter, numberOfDimensions, RFtype)
	filterApplicationResultThresholdIndices = pt.nonzero(filterApplicationResultThreshold).squeeze()

	if not ATORpt_RFoperations.isTensorEmpty(filterApplicationResultThresholdIndices):
		filterApplicationResultThresholded = filterApplicationResult[filterApplicationResultThresholdIndices]

		filterApplicationResultThresholdIndicesList = filterApplicationResultThresholdIndices.tolist()
		filterApplicationResultThresholdedList = filterApplicationResultThresholded.tolist()

		for RFthresholdedListIndex, RFlistIndex in enumerate(filterApplicationResultThresholdIndicesList):
			imageSegmentIndex, RFfilterIndex = divmod(RFlistIndex, len(RFfiltersTensor))
			centerCoordinates1, centerCoordinates2 = divmod(imageSegmentIndex, resolutionProperties.imageSize[1])
			centerCoordinates = (centerCoordinates1, centerCoordinates2)

			RFImage = inputImageSegments[imageSegmentIndex]
			RFfiltersProperties = RFfiltersPropertiesList2[RFfilterIndex]
			RFproperties = copy.deepcopy(RFfiltersProperties)
			RFproperties.centerCoordinates = centerCoordinates
			RFproperties.filterIndex = RFfilterIndex
			RFproperties.imageSegmentIndex = imageSegmentIndex
			RFpropertiesList.append(RFproperties)

	else:
		filterApplicationResultThresholdIndicesList = []
		filterApplicationResultThresholdedList = []

	return filterApplicationResultThresholdIndicesList, filterApplicationResultThresholdedList, RFpropertiesList
