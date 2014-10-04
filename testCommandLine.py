#!/usr/bin/python

from ArgParser import *
from pipeline import *
import sys
from constants import *
import cv2

def main(imgPath):
	testParser = ArgParser()
	unstainedSegmentCellsPipeline = testParser.parse("unstainedSegmentCells.xml")

	prelimPipeline = Pipeline([], {"imgPath": imgPath})
	prelimPipeline.addOp(LoadImageOp(pipeline=prelimPipeline))
	prelimPipeline.addOp(SubDivideOp(pipeline=prelimPipeline, staticParameters={"xDivide": 6, "yDivide": 6}))
	results = prelimPipeline.execute()
	subdividedImgs = results["imgs"]

	processedImgs = []
	for img in subdividedImgs:
		processedImgs.append(cv2.resize(img, 0, 2, 2, cv2.CV_INTER_CUBIC))

	cellCount = 0
	for i in xrange(len(processedImgs)):
		if DEBUG:
			print "PROCESSING IMG %d" % i
			print "executing segment cells"
		unstainedSegmentCellsPipeline.values["img"] = subdividedImgs[i]
		cells = unstainedSegmentCellsPipeline.execute()["blobs"]

		count = len(cells)

		if DEBUG:
			print "CELL COUNT FOR IMG %d : %d \n" % (i, count)
		cellCount += count
		unstainedSegmentCellsPipeline.values = {}

	print "%s TOTAL CELL COUNT: %d\n" % (imgPath.split("/")[-1],cellCount)


def test(imgPath):
	testParser = ArgParser()
	testAlgorithmPipeline = testParser.parse("config/testAlgorithm.xml")

	prelimPipeline = Pipeline([], {"imgPath": "raw/"+imgPath})
	prelimPipeline.addOp(LoadImageOp(pipeline=prelimPipeline))
	prelimPipeline.addOp(SubDivideOp(pipeline=prelimPipeline, staticParameters={"xDivide": 8, "yDivide": 6}))
	results = prelimPipeline.execute()
	subdividedImgs = results["imgs"]

	processedImgs = []
	for img in subdividedImgs:
		dst = img.copy()
		res = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
		processedImgs.append(res)

	cellCount = 0
	#for i in xrange(len(processedImgs)):
	for i in (14,16,20,21,25,26,27,30,32,33):
		if DEBUG:
			print "PROCESSING IMG %d" % i
			print "executing segment cells"
		testAlgorithmPipeline.values["img"] = processedImgs[i]
		testAlgorithmPipeline.execute()


def multi_process(start_num, end_num):
	for i in xrange(start_num, end_num+1):
		main("/Users/Jon/Documents/College/Research/HealyLab/Input/IMG_"+str(i)+"_invert")

if __name__=="__main__":
	option = sys.argv[1]
	if option == "s":
		imgPath = sys.argv[2]
		main(imgPath)
	elif option == "m":
		start_num = eval(sys.argv[2])
		end_num = eval(sys.argv[3])
		multi_process(start_num, end_num)
	elif option == "t":
		imgPath = sys.argv[2]
		test(imgPath)
	


