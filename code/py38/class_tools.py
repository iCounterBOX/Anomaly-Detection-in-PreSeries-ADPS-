# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 08:21:01 2024
Class to hold all kind of tools

@author: kristina
"""
from PyQt5.QtWidgets import  QMessageBox
import logging
import datetime
import numpy as np
import os
import cv2
import traceback


class tools:        
    def __init__(self):
        #kind of global for draw_rectangle() / a mouse callBack where we cannot give parameters in Method
        self.drawing = False
        self.ix, self.iy = -1,-1
        self.ixx, self.iyy = -1,-1
        self.img2 = None
        self.capFrame = None
        print("CV2 in class tools loaded")        
    
    '''
    MsgBox von pyQt / https://doc.qt.io/qt-6/qmessagebox.html  / - OK  Cancel
    '''
    def msgBoxInfoOkCancel(self,txt,title):
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' - '
        logging.info(dt + 'msgBoxInfoOkCance()')
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)           
        msgBox.setText(txt)
        msgBox.setWindowTitle(title)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  
        v = msgBox.exec()
        return v
    
    def msgBoxYesCancel(self,txt,title):
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' - '
        logging.info(dt + 'msgBoxYes()')
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)           
        msgBox.setText(txt)
        msgBox.setWindowTitle(title)
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        return msgBox.exec()
    
    def testDevice(self, webcamNr):
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' - '
        logging.info(dt + 'testDevice() - we now check device: ' + str(webcamNr))
        cap = cv2.VideoCapture(webcamNr)         
        if cap is None or not cap.isOpened():
            print('Warning: unable to open video source: ' + str(webcamNr))
            logging.info(dt + 'Warning: unable to open video source: ' + str(webcamNr))
            return False
        else:
            print('YEAA: this video source seem ok: ' + str(webcamNr))
            logging.info(dt + 'YEAA: this video source seem ok: ' + str(webcamNr))
            return True 
        
    def dt(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' - '

    
    def mse(self, imageA, imageB):
        #https://pyimagesearch.com/2014/09/15/python-compare-two-images/
          # the 'Mean Squared Error' between the two images is the
          # sum of the squared difference between the two images;
          # NOTE: the two images must have the same dimension
        # the original image is identical to itself, with a value of 0.0 for MSE and 1.0 for SSIM
        err = 0.0
        try:
              err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
              err /= float(imageA.shape[0] * imageA.shape[1])
        except:
            pass
                    # return the MSE, the lower the error, the more "similar"
          # the two images are
        return err 
    
    
    # delete file if exist
    def removeFile(self, filePath):
        # check whether the file exists
        try:
            if os.path.exists(filePath):
                # delete the file
                os.remove(filePath)
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
        
        
# ab hier..methoden von OpenCVTemplateMatching_rectangle4ROI_ocrAuf den Roi_HD.py

    def showInMovedWindow(self,  winname, img, x, y):
        cv2.namedWindow(winname)        # Create a named window
        cv2.moveWindow(winname, x, y)   # Move it to (x,y)...THis way the image ma appear on TOP of other screens!
        cv2.imshow(winname,img)
        
    
    # define mouse CALLBACK function to draw circle - So geht die globale variablenübergabe
    # Parameters are given via class-Variables..GLOBAL did NOT work!!!
    def draw_rectangle(self, event, x, y, flags, param):       
       if event == cv2.EVENT_LBUTTONDOWN:  # START pos of rectangle
          self.drawing = True
          self.ix = x
          self.iy = y
          self.img2 = self.capFrame.copy()
          #print("down.." + "x= " + str(x), " ix= " + str(ix) + "    y= " + str(y), " iy= " + str(iy)  )      
       elif event == cv2.EVENT_MOUSEMOVE:   # draw some dotted lies so we know where we are
          if self.drawing == True:         
             cv2.circle(self.img2, (x,y), radius=1, color=(0, 0, 255), thickness=-1)                  
       elif event == cv2.EVENT_LBUTTONUP:  # draw the rectange
          self.drawing = False
          self.ixx = x
          self.iyy = y
          print("up.." + "x= " + str(x), " ix= " + str(self.ix) + "y= " + str(y), " iy= " + str(self.iy)  )     
         
  
            
