#!/usr/bin/python

from ArgParser import *
from pipeline import *
import sys

def main(imgPath):
	beadArgParser = ArgParser()
	segmentBeadsPipeline = beadArgParser.parse("testSegmentBeads.xml")

	prelimPipeline = Pipeline([], {"imgPath": imgPath})
	prelimPipeline.addOp(LoadImageOp(pipeline=prelimPipeline))
	prelimPipeline.addOp(SubDivideOp(pipeline=prelimPipeline, staticParameters={"xDivide": 4, "yDivide": 4}))
	results = prelimPipeline.execute()
	subdividedImgs = results["imgs"]

	#for i in xrange(len(subdividedImgs)):
	i = 5

	print "executing segment beads"
	segmentBeadsPipeline.values["img"] = subdividedImgs[i]
	segmentBeadsPipeline.execute()

if __name__=="__main__":
	imgPath = sys.argv[1]
	main(imgPath)