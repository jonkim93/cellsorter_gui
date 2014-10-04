#!/usr/bin/python

from objects.argParser import *
from objects.pipeline import *
import sys
from objects.constants import *
import cv2


def getSubImages(imgPath):
	prelimPipeline = Pipeline([], {"imgPath": imgPath})
	prelimPipeline.addOp(LoadImageOp(pipeline=prelimPipeline))
	prelimPipeline.addOp(SubDivideOp(pipeline=prelimPipeline, staticParameters={"xDivide": 8, "yDivide": 6}))
	results = prelimPipeline.execute()
	subdividedImgs = results["imgs"]

	processedImgs = []
	for img in subdividedImgs:
		h, w = img.shape[:2]
		processedImgs.append(cv2.resize(img, (2*w, 2*h), interpolation=cv2.INTER_CUBIC))
	return processedImgs

def main(imgPath):
	cellArgParser = ArgParser()
	beadArgParser = ArgParser()
	beadAttachedArgParser = ArgParser()

	segmentCellsPipeline = cellArgParser.parse("config/segmentCells.xml")
	segmentBeadsPipeline = beadArgParser.parse("config/segmentBeads.xml")
	countBeadAttachedCellsPipeline = beadAttachedArgParser.parse("config/countBeadAttachedCells.xml")

	subdividedImgs = getSubImages(imgPath)

	cellCount = 0
	for i in xrange(len(subdividedImgs)):
		if DEBUG:
			print "PROCESSING IMG %d" % i
			print "executing segment cells"
		segmentCellsPipeline.values["img"] = subdividedImgs[i]
		cells = segmentCellsPipeline.execute()["blobs"]

		if DEBUG:
			print "executing segment beads"
		segmentBeadsPipeline.values["img"] = subdividedImgs[i]
		beads = segmentBeadsPipeline.execute()["blobs"]

		if DEBUG:
			print "executing counting"
		countBeadAttachedCellsPipeline.values["img"] = subdividedImgs[i]
		countBeadAttachedCellsPipeline.values["cells"] = cells
		countBeadAttachedCellsPipeline.values["beads"] = beads
		results = countBeadAttachedCellsPipeline.execute()

		if DEBUG:
			print "CELL COUNT FOR IMG %d : %d \n" % (i, results["count"])
		cellCount += results["count"]
		segmentCellsPipeline.values = {}
		segmentBeadsPipeline.values = {}
		countBeadAttachedCellsPipeline.values = {}

	print "%s TOTAL CELL COUNT: %d\n" % (imgPath.split("/")[-1],cellCount)

def multi_process(start_num, end_num):
	for i in xrange(start_num, end_num+1):
		main("/Users/Jon/Documents/College/Research/HealyLab/Input/IMG_"+str(i)+"_invert")

if __name__=="__main__":
	option = sys.argv[1]
	if option == "s":
		imgPath = "raw/"+ sys.argv[2]
		main(imgPath)
	elif option == "m":
		start_num = eval(sys.argv[2])
		end_num = eval(sys.argv[3])
		multi_process(start_num, end_num)
	
def old_main(imgPath):
	cellArgParser = ArgParser()
	beadArgParser = ArgParser()
	beadAttachedArgParser = ArgParser()
	segmentCellsPipeline = cellArgParser.parse("segmentCells.xml")
	segmentBeadsPipeline = beadArgParser.parse("testSegmentBeads.xml")
	countBeadAttachedCellsPipeline = beadAttachedArgParser.parse("countBeadAttachedCells.xml")

	prelimPipeline = Pipeline([], {"imgPath": imgPath})
	prelimPipeline.addOp(LoadImageOp(pipeline=prelimPipeline))
	prelimPipeline.addOp(SubDivideOp(pipeline=prelimPipeline, staticParameters={"xDivide": 4, "yDivide": 4}))
	results = prelimPipeline.execute()
	subdividedImgs = results["imgs"]

	cellCount = 0
	for i in xrange(len(subdividedImgs)):
		if DEBUG:
			print "PROCESSING IMG %d" % i
			print "executing segment cells"
		segmentCellsPipeline.values["img"] = subdividedImgs[i]
		cells = segmentCellsPipeline.execute()["blobs"]

		if DEBUG:
			print "executing segment beads"
		segmentBeadsPipeline.values["img"] = subdividedImgs[i]
		beads = segmentBeadsPipeline.execute()["blobs"]

		if DEBUG:
			print "executing counting"
		countBeadAttachedCellsPipeline.values["img"] = subdividedImgs[i]
		countBeadAttachedCellsPipeline.values["cells"] = cells
		countBeadAttachedCellsPipeline.values["beads"] = beads
		results = countBeadAttachedCellsPipeline.execute()

		if DEBUG:
			print "CELL COUNT FOR IMG %d : %d \n" % (i, results["count"])
		cellCount += results["count"]
		segmentCellsPipeline.values = {}
		segmentBeadsPipeline.values = {}
		countBeadAttachedCellsPipeline.values = {}

	print "%s TOTAL CELL COUNT: %d\n" % (imgPath.split("/")[-1],cellCount)


