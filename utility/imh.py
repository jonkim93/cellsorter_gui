#!/usr/bin/python
import cv2
import numpy as np
import time
import math
from collections import Counter

from constants import *

#DEBUG = False
#PREFIXES = ["CellBoundImages/", "WrightStainImages/", "CellScope/" ]
#SUFFIXES = [".jpg", ".png", ".jpeg", ".tif"]


#=================== IMAGE DATA FUNCTIONS ==========================#
"""
functions that pull data from an image without changing the image itself
"""

def resizeImg(img, scale_factor):
    return cv2.resize(img, (int(img.shape[1]*scale_factor),int(img.shape[0]*scale_factor)))

def getROI(image, x1, x2, y1, y2):
    return image[x1:x2, y1:y2]

def subDivideImage(img, w_div=4, h_div=4):
    width = img.shape[0]
    height = img.shape[1]
    sub_w = float(width)/float(w_div)
    sub_h = float(height)/float(h_div)
    subdividedimgs = []
    for x in xrange(w_div):
        for y in xrange(h_div):
            subdividedimgs.append(getROI(img, sub_w*x, sub_w*x+sub_w, sub_h*y, sub_h*y+sub_h))
    return subdividedimgs
    


#TODO: ignore all bounding boxes that are inside of each other
def segmentCellsGray(image, mincellsize=10, lower=130, upper=255):
    boundingBoxes = []
    image = blur(image, 3)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray,lower,upper,cv2.THRESH_BINARY) 
    
    cv2.imshow("thresh", thresh)
    
    contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area > mincellsize:
            boundingBoxes.append(cv2.boundingRect(contour))
    boxImg = drawBoundingBoxes(image, boundingBoxes)
    return boundingBoxes, boxImg

def segmentCellsCanny(image, mincellsize=10, lower=130, upper=255):

    boundingBoxes = []
    gray = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    gray = blur(gray, 7)
    gray = erodeAndDilate(gray, 15, 3)
    cv2.imshow("gray", gray)
    
    canny = cv2.Canny(gray, 5, 50)  # PLAY AROUND WITH THESE VALUES

    element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(4,4))
    canny = cv2.dilate(canny, element)
    element1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2))
    canny = cv2.erode(canny, element1)
    
    cv2.imshow("canny", canny)
    
    contours, hierarchy = cv2.findContours(canny,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    #print type(contours)
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area > mincellsize:
            boundingBoxes.append(cv2.boundingRect(contour))
    boxImg = drawBoundingBoxes(image, boundingBoxes)
    return boundingBoxes, boxImg, canny 


def segmentBeadsCanny(image, minBeadSize=10, lower=130, upper=255):

    boundingBoxes = []
    gray = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2GRAY)
    gray = blur(gray, 7)
    #gray = erodeAndDilate(gray, 15, 3)
    #cv2.imshow("gray", gray)
    
    canny = cv2.Canny(gray, 5, 50)  # PLAY AROUND WITH THESE VALUES


    # PLAY AROUND WITH THIS STUFF ==================================
    element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(6,6))
    canny = cv2.dilate(canny, element)
    element1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2))
    canny = cv2.erode(canny, element1)
    # ==============================================================
    #circles = cv2.HoughCircles(canny.copy(), cv2.cv.CV_HOUGH_GRADIENT, 2, 10, np.array([]), 40, 60, 5, 1000)
    circles = cv2.HoughCircles(canny.copy(),
                               cv2.cv.CV_HOUGH_GRADIENT,
                               1,
                               50,           # min distance allowed between circles
                               param1=50, 
                               param2=10,    # if too many circles, increase, and vice versa
                               minRadius=5,  # duh
                               maxRadius=20) # duh
    if circles != None:
        if DEBUG:
            print ("NUMBER OF BEADS: "+str(len(circles[0])))
    beadImg = drawCircles(image.copy(), circles)
    
    contours, hierarchy = cv2.findContours(canny,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    #print type(contours)
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area > minBeadSize:
            boundingBoxes.append(cv2.boundingRect(contour))
    boxImg = drawBoundingBoxes(image, boundingBoxes)
    return boundingBoxes, boxImg, canny, beadImg, circles  

#================== HSV FUNCTIONS ==================================#
def getHSVValues(img):
    image_hsv_values = []
    for x in range(0, img.shape[0]): 
        for y in range(0, img.shape[1]):
            image_hsv_values.append(img[x,y])
    return image_hsv_values

def calculateHSVBoundsAverage(img, margin=30):
    if DEBUG:
        start_time = time.time()
        print "IMG SHAPE: ",img.shape
    hsv_values = getHSVValues(img)
    averages = [sum(y)/len(y) for y in zip(*hsv_values)]
    lower = (averages[0]-margin, 100, 100)
    upper = (averages[0]+margin, 255, 255)
    if DEBUG:
        print "TIME OF EXECUTION", time.time() - start_time, "seconds"
        print "AVERAGE HSV: ",str(averages)
    print "\t\t",str(averages)
    return lower, upper 

def calculateHSVBoundsMode(img, avg_length=20, margin=30):
    if DEBUG:
        start_time = time.time()
        print "IMG SHAPE: ",img.shape

    hsv_values = getHSVValues(img)

    """
    averages = []
    firstsum = 0
    for i in xrange(avg_length):
        firstsum += hsv_values[i][0]
    firstavg = firstsum/avg_length
    averages.append(firstavg)
    prevavg = firstavg
    for i in xrange(avg_length,len(hsv_values)):
        prevavg = prevavg + hsv_values[i][0]/avg_length - hsv_values[i-avg_length][0]/avg_length
        averages.append(prevavg)
    modehue = max(averages)
    """

    hues = [x[0] for x in hsv_values]
    hueCounter = Counter(hues)
    if len(hueCounter) != 0:
        modehue = hueCounter.most_common(1)[0][0]
    else:
        #print "no values"
        return None, None, None 

    if modehue > margin and modehue < (255-margin):
        lower = (modehue-margin, 100, 100)
        upper = (modehue+margin, 255, 255)
    elif modehue <= margin:
        lower = (0, 100, 100)
        upper = (modehue+margin, 255, 255)
    elif modehue >= (255-margin):
        lower = (modehue-margin, 100, 100)
        upper = (255, 255, 255)
    return lower, upper, modehue

def getContours(img, mode=cv2.RETR_CCOMP, method=cv2.CHAIN_APPROX_SIMPLE):
    contours, hierarchy = cv2.findContours(img, mode, method)
    print "NUMBER OF CELLS: "+str(len(contours))
    return contours, len(contours), hierarchy

def filterBeads(img, circles, lower, upper):
    circle_roi_list = []
    filtered_beads = []
    if circles != None:
        for circle in circles[0]:
            y1 = int(circle[0]-circle[2])
            y2 = int(circle[0]+circle[2])
            x1 = int(circle[1]-circle[2])
            x2 = int(circle[1]+circle[2])
            #print circle 
            #print str(x1)+", "+str(x2)+ ": "+str(y1)+", "+str(y2)
            circle_roi_list.append(getROI(img, x1, x2, y1, y2))
        for x in xrange(len(circle_roi_list)):
            #showImage(circle_roi_list[x])
            hue_mode = calculateHSVBoundsMode(circle_roi_list[x])[2]
            if hue_mode != None:
                if (int(hue_mode) <= int(upper)) and (int(hue_mode) >= int(lower)):
                    filtered_beads.append(circles[0][x])
    return filtered_beads

def distance(coord1, coord2):
    return math.sqrt((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)

def filterContoursByArea(img, contours, area_lower_threshold=10000, area_upper_threshold=1000000, draw=False):
    areas = []
    filtered = []
    filtered_bounding_boxes = []
    num_big_contours = 0
    for i in xrange(len(contours)):
        contour_area = cv2.contourArea(contours[i])
        areas.append(contour_area)
        if contour_area > area_lower_threshold and contour_area < area_upper_threshold:
            num_big_contours += 1
            filtered.append(contours[i])
            x, y, w, h = cv2.boundingRect(contours[i])
            filtered_bounding_boxes.append((x,y,w,h))
            if draw:
                cv2.drawContours(img, contours, i, (0, 255, 0))
                cv2.rectangle(img,(x,y),(x+w,y+h),(60,140,40),2)
    return num_big_contours, areas, img, filtered, filtered_bounding_boxes

def drawBoundingBoxes(img, boxes):
    for box in boxes:
        x, y, w, h = box
        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
    return img 

def drawBoundingBox(img, box):
    x, y, w, h = box
    cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
    return img 

def getCircles(img,minRadius=1, maxRadius=30,method=cv2.cv.CV_HOUGH_GRADIENT):
    img = cv2.Canny(img, 10, 80)
    cv2.imshow("canny", img)
    circles = cv2.HoughCircles(img, cv2.cv.CV_HOUGH_GRADIENT, 2, 10, np.array([]), 40, 60, 5, 1000)
    #circles = cv2.HoughCircles(img,method,1,20,50,100,minRadius,maxRadius)
    if circles != None:
        if DEBUG:
            print "NUMBER OF CIRCLES: ",str(len(circles[0]))
    return circles 

def drawCircles(img, circles):
    if circles != None:
        circles = np.uint16(np.around(circles))
        for circle in circles:
            for i in circles[0,:]:
                # draw the outer circle
                cv2.circle(img,(i[0],i[1]),i[2],(0,255,0),2)
                # draw the center of the circle
                cv2.circle(img,(i[0],i[1]),2,(0,0,255),3)
    else:
        if DEBUG:
            print "ERROR: NO CIRCLES"
    return img 

def countByArea(blobArea, cellSize):
    print "BLOB AREA : %d" % blobArea
    print "CELL SIZE : %d" % cellSize
    blobArea += 1
    return -(-blobArea // cellSize) # use upside-down floor divison to round up 


#=================== IMAGE EDITING FUNCTIONS =======================#

def overall(img, gen_params, bead_params):
    """ overall image processing
    gen_params: 
        0 = before threshold blur kernel size
        1 = before threshold erode/dilate iterations
        2 = before threshold erode/dilate kernel size
        3 = threshold style
        4 = cell upper hue
        5 = cell lower hue
        6 = after threshold blur kernel size
        7 = after threshold erode/dilate iterations
        8 = after threshold eorde/dilate kernel size
        9 = lower threshold on cell area 
        10 = upper threshold on cell area 
        11 = max distance between bead and cell

    bead_params:
        0 = bead lower hue
        1 = bead upper hue 
        2 = bead lower area
    """
    g = gen_params
    b = bead_params
    max_distance = g[11]
    print max_distance

    # run a general thresholding operation
    final, bt_blurred, bt_ed, cvted_img, thresh, at_blurred, at_ed = generalProcess(img, g[0], g[1], g[2], g[3], (g[4], 255,255), (g[5], 50, 50),
                    g[6], g[7], g[8])

    # use canny edge detection and hough circle detection to locate beads within image
    boundingBoxes, boxImg, canny, beadImg, circles = segmentBeadsCanny(img.copy(), b[0], b[1], b[2])

    # filter resulting beads for size and color
    filteredBeads = filterBeads(img, circles, b[1], b[2]) #filteredBeads is an array of 3-vectors of form (x,y,radius)
    beadCenters = []
    for bead in filteredBeads:
        beadCenters.append((bead[0], bead[1]))

    # run a contour detection algorithm on the thresholded result of the general process
    contours, tot_num_contours, hierarchy = getContours(final.copy())

    # filter contours by area
    num_big_contours, areas, cont_img, filteredCells, filteredBoundingBoxes = filterContoursByArea(img.copy(), \
        contours, g[9], g[10], draw=True)

    cellCenters = []
    for cell in filteredBoundingBoxes:
        cellCenters.append((cell[0]+cell[2]/2, cell[1]+cell[3]/2, (cell[2]+cell[3])/2))
    
    # get list of all the cells within a certain distance of a bead
    beadAttachedCells = [[]]
    numBeadAttachedCells = 0
    print "LEN CELL CENTERS: %d" % len(cellCenters)
    print "LEN BEAD CENTERS: %d" % len(beadCenters)
    for i in xrange(len(cellCenters)):
        cell = cellCenters[i]
        for bead in beadCenters:
            if distance((cell[0], cell[1]),bead) < max_distance:
                print "CELL: "+str(cell)
                beadAttachedCells[0].append(cell)
                numBeadAttachedCells += countByArea(areas[i], 300)
                break
    finalCellImg = drawCircles(img.copy(), beadAttachedCells)
    #numBeadAttachedCells = len(beadAttachedCells[0])
    resultImages = [finalCellImg, thresh, boxImg, beadImg, cont_img]
    cv2.imwrite(SAVEDIR+"IMG_6835_10"+"_processed.png", finalCellImg)
    return resultImages, numBeadAttachedCells


def generalProcess(img, bt_blur_ksize, bt_ed_iter, bt_ed_ksize, thresh_style, upper, lower, at_blur_ksize, at_ed_iter, at_ed_ksize):
    bt_blurred = None
    bt_ed = None
    cvted_img = None
    thresh = None
    at_blurred = None
    at_ed = None
    final = None 

    #print lower
    #print upper

    # bt = before thresholding
    if bt_blur_ksize > 0:
        bt_blurred = blur(img.copy(), bt_blur_ksize)
    if bt_ed_iter > 0:
        if bt_blurred != None:
            bt_ed = erodeAndDilate(bt_blurred.copy(), bt_ed_iter, bt_ed_ksize)
        else:
            bt_ed = erodeAndDilate(img.copy(), bt_ed_iter, bt_ed_ksize)

    if bt_ed != None:
        bt_intermediate = bt_ed
    elif bt_blurred != None:
        bt_intermediate = bt_blurred
    else:
        bt_intermediate = img.copy() 

    #cv2.imshow("bt_intermediate", bt_intermediate)
    # what style of thresholding?
    if thresh_style == "hsv":
        cvted_img = cv2.cvtColor(bt_intermediate.copy(), cv2.COLOR_BGR2HSV)
        thresh = thresholdHSV(cvted_img.copy(), lower, upper)
    elif thresh_style == "gray":
        cvted_img = cv2.cvtColor(bt_intermediate.copy(), cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(cvted_img.copy(), lower, upper, cv2.THRESH_BINARY)

    # at = after thresholding
    if at_blur_ksize > 0:
        at_blurred = blur(thresh.copy(), at_blur_ksize)
    if at_ed_iter > 0:
        if at_blurred != None:
            at_ed = erodeAndDilate(at_blurred.copy(), at_ed_iter, at_ed_ksize)
        else:
            at_ed = erodeAndDilate(thresh.copy(), at_ed_iter, at_ed_ksize)

    if at_ed != None:
        final = at_ed
    elif at_blurred != None:
        final = at_blurred
    elif thresh != None:
        final = thresh
    elif cvted_img != None:
        final = cvted_img
    elif bt_ed != None:
        final = bt_ed
    elif bt_blurred != None:
        final = bt_blurred
    else:
        final = img
    return (final, bt_blurred, bt_ed, cvted_img, thresh, at_blurred, at_ed) 


"""
functions that actually act on the image and change its state
"""
def thresholdHSV(img, lowerHSV, upperHSV):
    """ 
    Thresholds an image for a certain range of hsv values 
    """ 
    threshImg = img.copy()
    print "\nBOUNDS"
    print lowerHSV
    print upperHSV
    threshImg = cv2.inRange(img, lowerHSV, upperHSV, threshImg)
    return threshImg

def blur(img, ksize=15):
    img = cv2.medianBlur(img,ksize)
    return img 

def erodeAndDilate(img, iterations=5, ksize=4):
    element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(ksize,ksize))
    for i in xrange(iterations):
        img = cv2.erode(img, element)
        img = cv2.dilate(img, element)
    return img 

#==================  DIRECTORY HELPER FUNCTIONS   ====================#

"""
functions that act on files and load images, etc
"""

def loadImage(inputfile):
    suff_ind = 0
    suffix = SUFFIXES[suff_ind]
    for prefix in PREFIXES:
        for suffix in SUFFIXES:
            path = prefix+inputfile+suffix
            img = cv2.imread(path)
            if img != None:
                break
        if img != None:
            break
    if img == None:
        print "ERROR: image not found ", path
        return
    return img 


def showImage(image, windowName="img", key=1):
    cv2.imshow(windowName, image)
    cv2.waitKey(0)
    cv2.destroyWindow(windowName)

