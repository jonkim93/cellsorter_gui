#!/usr/bin/python

from ArgParser import *
from pipeline import *
import sys
from constants import *
import cv2

def main(imgPath):
	circleDetectCellsParser = ArgParser()
	circleDetectCellsPipeline = circleDetectCellsParser.parse("config/circleDetectCells.xml")

	thresholdDetectCellsParser = ArgParser()
	thresholdDetectCellsPipeline = thresholdDetectCellsParser.parse("config/thresholdDetectCells.xml")

	prelimPipeline = Pipeline([], {"imgPath": "raw/"+imgPath})
	prelimPipeline.addOp(LoadImageOp(pipeline=prelimPipeline))
	prelimPipeline.addOp(SubDivideOp(pipeline=prelimPipeline, staticParameters={"xDivide": 8, "yDivide": 6}))
	results = prelimPipeline.execute()
	subdividedImgs = results["imgs"]

	processedImgs = []
	for img in subdividedImgs:
		res = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
		processedImgs.append(res)

	cellCount = 0
	for i in (14,16,20,21,25,26,27,30,32,33):
		if DEBUG:
			print "PROCESSING IMG %d" % i
			print "executing segment cells"
		circleDetectCellsPipeline.values["img"] = processedImgs[i]
		circleCells = circleDetectCellsPipeline.execute()["blobs"]

		thresholdDetectCellsPipeline.values["img"] = processedImgs[i]
		thresholdCells = thresholdDetectCellsPipeline.execute()["blobs"]

		#if DEBUG:
		#	print "CELL COUNT FOR IMG %d : %d \n" % (i, count)
		#cellCount += count
		#circleDetectCellsPipeline.values = {}

	print "%s TOTAL CELL COUNT: %d\n" % (imgPath.split("/")[-1],cellCount)

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
	


