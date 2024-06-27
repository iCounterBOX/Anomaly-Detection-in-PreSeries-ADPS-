# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 16:15:08 2024

@author: kristina
itemClicked:
https://stackoverflow.com/questions/54436909/the-slot-dont-work-for-qlistwidget-itemclicked-pyqt

resize raster of pic:
https://stackoverflow.com/questions/21802868/python-how-to-resize-raster-image-with-pyqt

status: linker teil soweit ok..scrollen durch liste preview und variablen füllen ok

merke:
    self.tmp = image
    #image = imutils.resize(image,width=640)
    frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)
    self.lbl_cameraView.setPixmap(QtGui.QPixmap.fromImage(image))
12.04.24: anomaly anpassen an loadui technik    

todo:
    in anomaly selbe filter aus metadata der ref bilder anwenden
    issue:
        KEIN anomalyFlicker bei Still Image...siehe: https://www.youtube.com/watch?v=oOuswkbsBCU
        versuche aus stream per 1 sec einen frame zu bekommen und die anomaly über diesen frame zu erhalten ( bild für bild)

#wenn der score > 0.979 dann ist das bild gleich ..nachkommastellen führen zum flickern
#wir nehmen so lange das before pic bis eine ECHtE anomaly eintritt   TEST!!!!!
#todo: score muss FILTERBAR sein ..ab einem bestimmten score (hier 0,98 ) hört das flickern bei kleinen
#differenzen der Bilder auf...Dann wird NUR noch die Anomaly dargestellt

"""


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import (
    QMessageBox, 
    QListWidget, 
    QPushButton, 
    QComboBox, 
    QCheckBox, 
    QLabel,
    QLineEdit,
    )
from PyQt5.QtGui import QImage

import image_rc 

import sys
import os
import re
import time
import cv2, imutils
import shutil
import traceback
from pathlib import Path
from PIL import Image  # https://stackoverflow.com/questions/58399070/how-do-i-save-custom-information-to-a-png-image-file-in-python
from PIL.PngImagePlugin import PngInfo
from cvzone.SelfiSegmentationModule import SelfiSegmentation


import logging

#import MY own classes
from class_tools import tools
toolz = tools()  

#es wird der log benannt der in mdiMain an erster stelle geladen wird.
#verwirrung? es einen log...nicht jede py hat einen eigenen...wir hängen in einer app unter mdi..
logging.basicConfig(filename= os.getcwd() + "\\" +"companyTasks.log", level=logging.INFO)
logging.info(toolz.dt() + '******** This is Module anomalyMain.py  GO ***************************')

from skimage.metrics import structural_similarity
#from PIL import Image
import numpy as np

#Version infos
print(cv2.__file__) 
print (cv2. __version__ )
logging.info(toolz.dt() + cv2. __version__ )

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
print("Qt: v", QT_VERSION_STR, "\tPyQt: v", PYQT_VERSION_STR)

#some VARIABLES
# colors
RED = (0, 0, 255)  # opencv uses BGR not RGB
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)

_objImgWindowWidth = 400
_objImgWindowHeight = 400

#check if directory exist..if not make one
cur_dir = os.getcwd() + '\learnedRefPictures'
Path(cur_dir).mkdir(parents=True, exist_ok=True)
logging.info(toolz.dt() + 'FolderPath and Check done: ' + cur_dir)

cur_dirAnomaly = os.getcwd() + '\imagesAnomaly'
Path(cur_dirAnomaly).mkdir(parents=True, exist_ok=True)
logging.info(toolz.dt() + 'FolderPath and Check done: ' + cur_dirAnomaly)

tmpPic_dir = os.getcwd() + "\\" + 'tmpPic' 
Path(tmpPic_dir).mkdir(parents=True, exist_ok=True)
logging.info(toolz.dt() + 'FolderPath and Check done: ' + tmpPic_dir)

defaultVideoIfNoWebCamFoundPath = os.getcwd() + "\\" + 'defaultVideo.mp4' 
motorErrTypeA = os.getcwd() + "\\" + 'motorErrTypeA.png' 
motorErrTypeA = os.getcwd() + "\\" + 'dose.png' 

#CURRENT selected reference picture in the LIST ( by user)


#gave crash in auto-py-to-exe created exe...could not find files from mediapipe!? used by cvzone
try:
   logging.info(toolz.dt() + 'try..segmentor = SelfiSegmentation() ')
   segmentor = SelfiSegmentation()
except Exception as e:
    print(e)
    logging.error(traceback.format_exc())
    # Logs the error appropriately. 
  

class anomalyWindowUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(anomalyWindowUI,self).__init__()
        logging.info(toolz.dt() + 'super(window...init..done')
        # load ui file
        try:            
            fp = 'anomalyUI.ui'
            uic.loadUi(fp, self)
        except Exception as e:
            print(e)
            logging.error(traceback.format_exc())        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)   # added newly
        
        
        self.listWidget_learnedMotor = self.findChild(QListWidget,"listWidget_learnedMotor")
        self.listWidget_learnedMotor.clicked.connect(self.previewSelectedListObject)
        
        self.pushButton_SaveAnomalyDetectImage =  self.findChild(QPushButton,"pushButton_SaveAnomalyDetectImage")      
        self.pushButton_SaveAnomalyDetectImage.clicked.connect(self.saveAnomalyDetectedImage)  
        
        self.pushButton_StartStopCam =  self.findChild(QPushButton,"pushButton_StartStopCam")      
        self.pushButton_StartStopCam.clicked.connect(self.loadImage)
       
        self.pushButton_send2CurrentDetection =  self.findChild(QPushButton,"pushButton_send2CurrentDetection")      
        self.pushButton_send2CurrentDetection.clicked.connect(self.send2CurrentAnomalyDetection)
        
        self.pushButton_WriteErrorProtocol =  self.findChild(QPushButton,"pushButton_WriteErrorProtocol")      
        #self.pushButton_WriteErrorProtocol.clicked.connect(self.writeErrorProtocol)
        
        
        self.lbl_refObjectPicture = self.findChild(QLabel, "lbl_refObjectPicture")
        self.label_refObjectFileName = self.findChild(QLabel, "label_refObjectFileName")
        self.label_currentAnomalyImage = self.findChild(QLabel, "label_currentAnomalyImage")
        
        self.lineEdit_camNr = self.findChild(QLineEdit, "lineEdit_camNr")
        
       
        #enable / disable elements
        self.pushButton_SaveAnomalyDetectImage.setEnabled(False)
        self.pushButton_send2CurrentDetection.setDisabled(True)
        self.pushButton_WriteErrorProtocol.setDisabled(True)
        
        logging.info(toolz.dt() + 'set..pushButton_..done')
       
        
        #set status TIP
        self.listWidget_learnedMotor.setStatusTip("Location of learned Images: " + cur_dir)
        self.lbl_refObjectPicture.setStatusTip("Location of LAST taken Image: " + tmpPic_dir)
        #self.pushButton_SaveAsReference.setStatusTip("BEFORE saving! E N S U R E  that parameter-fields (on the left) are filled properly!")
        self.lbl_cameraView.setStatusTip("This window show your  W e b c a m!  Click START-Object-Camera ( Button below )")
        #self.pushButton_MakePicture.setStatusTip("..Is making a picture from current Webcam image stream! Picture is shown in sector: Last taken Picture from Live View Webcam (mid of the UI)! Its stored in a tmp folder!")
        
        
        # Added code here
        self.filename = 'Snapshot '+str(time.strftime("%Y-%b-%d at %H.%M.%S %p"))+'.png' # Will hold the image address location
        self.tmp = None # Will hold the temporary image for display       
        self.fps=0
        self.started = False
        self._currentSelectedRefPictureAndPath =""
        
        # -.. AB ins programm
        self.listLearnedMotors()
        self.previewSelectedListObject()
     
    # handle the red cross event
    def closeEvent(self, event):   
            self.started = False
            logging.shutdown()
            self.close()
            self.destroy()           
            event.accept()
            print('Window closed')
            
            
        
    
    def loadImage(self):
        """ This function will load the camera device, obtain the image
            and set it to label using the setPhoto function
        """
        
        self.webcam_0_Found = True
        self.webcam_1_Found = True
        self.webcamNr = 0 # FIRST choicxe
        cam = False # True for webcam
        
        if  toolz.testDevice(0)  == False:  # no printout if cam (0) is available
            #toolz.msgBoxInfoOkCancel("Webcam (0) NOT found!","Webcam ISSUE - PLEASE CHECK!")
            self.webcam_0_Found = False
            self.webcamNr = 1 # 2. chance        
            
        if toolz.testDevice(1) == False:  # no printout if cam (0) is available
            #toolz.msgBoxInfoOkCancel("Webcam (1) NOT found!","Webcam ISSUE - PLEASE CHECK!")
            self.webcam_1_Found = False
            self.webcamNr = 99  ## ERR
            
        if self.webcam_0_Found == False  and self.webcam_1_Found == False:
            toolz.msgBoxInfoOkCancel("NO Webcam available -Show default Film","Webcam I S S U E - PLEASE CHECK!")
            cam = False
        else:
            cam = True                  
        
        if self.started:
            self.started=False
            self.pushButton_StartStopCam.setText('START Camera (WebCam)')   
            self.pushButton_send2CurrentDetection.setEnabled(False)
        else:
            self.started=True
            self.pushButton_StartStopCam.setText('STOP Camera (WebCam)')
            self.pushButton_send2CurrentDetection.setEnabled(True)
            
        if cam:            
            vid = cv2.VideoCapture(int(self.lineEdit_camNr.text()))            
        else:
            #vid = cv2.VideoCapture(defaultVideoIfNoWebCamFoundPath)            
            self.image = cv2.imread(motorErrTypeA)
            self.image  = cv2.resize(self.image, (640, 480)) 
            print(self.image.shape)
            self.setPhoto(self.image)
            self.pushButton_send2CurrentDetection.setEnabled(True)
            return
        
        
        #frames_to_count=20 # original 20
        frames_to_count= vid.get(cv2.CAP_PROP_FPS)
        print("vid.get(cv2.CAP_PROP_FPS) =" + str(frames_to_count))
        
        #ok aber mir gefällt nicht der enlose count - https://stackoverflow.com/questions/22704936/reading-every-nth-frame-from-videocapture-in-opencv
        '''
        count = 0

        while(vid.isOpened()): 
            QtWidgets.QApplication.processEvents()
            ret, self.image = vid.read()
        
            if ret:
                self.setPhoto(self.image)
                count += frames_to_count * 10 # i.e. at 30 fps, this advances one second
                vid.set(cv2.CAP_PROP_POS_FRAMES, count)
                print ("loadImage(): count = " + str(count))
            
            if self.started==False:
                cv2.destroyAllWindows() 
                vid.release()
                print('Loop break')
                break
        '''
        #https://www.youtube.com/watch?v=oOuswkbsBCU
        n = 0
        i = 0
        
        while(vid.isOpened()):  
            QtWidgets.QApplication.processEvents()    
            ret, self.image = vid.read()               
        
            if (2*n) % frames_to_count == 0:
                self.setPhoto(self.image)
                i+=1
            n+=1
            if ret==False:
                break
        
            
            #EXIT CHECKER - ckoss
            if self.started==False:
                cv2.destroyAllWindows() 
                print('Loop break')
                break
                          

    def setPhoto(self,image):
        #This function will take image input and resize it only for display purpose and convert it to QImage to set at the label.
        
        #Wenn KEIN Referenz-Bild vorliegt macht die ANOMALY keinen SINN!  RETURN
        if not self._currentSelectedRefPictureAndPath:
            print(toolz.dt() + 'setPhoto() / PROBLEM - NO Reference Objects availabe!!')
            self.pushButton_SaveAnomalyDetectImage.setEnabled(False)
            self.pushButton_send2CurrentDetection.setDisabled(True)
            self.pushButton_WriteErrorProtocol.setDisabled(True)
            self.statusBar().showMessage("!!!! NO REFERENCE OBJECTS AVAILABLE !!!! Please first go to LEARN OBJECT to create References!")
            # setting color to status bar 
            self.statusBar().setStyleSheet("background-color : yellow") 
            return
  
        #START der ANOMALY detection:
            
        before = cv2.imread(self._currentSelectedRefPictureAndPath)
        after = image #image von CAM oder video
        self.detectAnomaly_V1(before, after)
        
   
        
   
        #  https://pyimagesearch.com/2014/09/15/python-compare-two-images/
        # TODO
    def detectAnomaly_V1(self, before, after):         
        
        mse = toolz.mse( before, after)
        print ("ref: " +  self._currentSelectedRefPictureAndPath + " MSE/frame = " +  str(round(mse,2) ))        
     
        
        grayA = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
        
        #we also show thw ORIGINAL camera image...kind of PREVIEW of the RAW video stream
        frame = cv2.cvtColor(after, cv2.COLOR_BGR2RGB)
        img = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)       
        pixmap = QtGui.QPixmap.fromImage(img)
        pixmap = pixmap.scaled(_objImgWindowWidth, _objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
        self.label_webcamRaw.setPixmap(pixmap)        
        
        (score, diff) = structural_similarity(grayA, grayB, full=True)
        diff = (diff * 255).astype("uint8")
        #print("SSIM: {}".format(score))
        
        # threshold the difference image, followed by finding contours to
        # obtain the regions of the two input images that differ
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        
        score = round(score,4)
        print ("Similarity: {:.4f}%".format(score * 100) + " raw = " + str(score) +  " MSE = " +  str(round(toolz.mse(before,after),2) )) 
       
        # loop over the contours
        for c in cnts:
            # compute the bounding box of the contour and then draw the
            # bounding box on both input images to represent where the two
            # images differ
            
            if cv2.contourArea(c) > 40 and score < 0.99: 
               
                #print ("cnts-area = " + str(cv2.contourArea(c)) + " nrCNTS = " + str(len(cnts)) ) 
               
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(before, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.rectangle(after, (x, y), (x + w, y + h), (0, 0, 255), 2) # object with rectangle anomaly
                font = cv2.FONT_HERSHEY_COMPLEX
                cv2.putText(after,'Anomaly',(0,50),font,1,(255,255,255),2)  #text,coordinate,font,size of text,color,thickness of font
            
            self.tmp = after
            frame = cv2.cvtColor(after, cv2.COLOR_BGR2RGB)
            objectWithErr = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(objectWithErr)
            pixmap = pixmap.scaled(_objImgWindowWidth, _objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
            self.lbl_cameraView.setPixmap(pixmap) 
                               
        
                
    def detectAnomaly_V2(self, before, after):    
        # Convert images to grayscale
        before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
        after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
        
        #Issue the size can be different if we use the default video in case of NO cam
        print(before_gray.shape)
        print(after_gray.shape)

        # Compute SSIM between the two images
        (score, diff) = structural_similarity(before_gray, after_gray, full=True)
        print("Image Similarity: {:.4f}%".format(score * 100) + " score raw = " + str(score))
      

        #wenn der score > 0.979 dann ist das bild gleich ..nachkommastellen führen zum flickern
        #wir nehmen so lange das before pic bis eine ECHtE anomaly eintritt   TEST!!!!!
        #todo: score muss FILTERBAR sein ..ab einem bestimmten score (hier 0,98 ) hört das flickern bei kleinen
        #differenzen der Bilder auf...Dann wird NUR noch die Anomaly dargestellt
        #FUNKTIONIERT...aber muss ständig nachjustiert werden :-(
        
        '''
        if score > 0.98:            
            print("score >= 0.98 -  we take the original Picture")
            frame = cv2.cvtColor(originalImage, cv2.COLOR_BGR2RGB)
            img = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)       
            pixmap = QtGui.QPixmap.fromImage(img)
            pixmap = pixmap.scaled(_objImgWindowWidth, _objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
            self.lbl_cameraView.setPixmap(pixmap)
            return
        '''

        # The diff image contains the actual image differences between the two images
        # and is represented as a floating point data type in the range [0,1] 
        # so we must convert the array to 8-bit unsigned integers in the range
        # [0,255] before we can use it with OpenCV
        diff = (diff * 255).astype("uint8")
        diff_box = cv2.merge([diff, diff, diff])

        # Threshold the difference image, followed by finding contours to
        # obtain the regions of the two input images that differ  standard threshould = 255
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if len(contours) == 2 else contours[1]

        mask = np.zeros(before.shape, dtype='uint8')
        objectWithErr = after.copy()

        for c in contours:
            area = cv2.contourArea(c)
            if area > 40:   # flicker? origial ist 40
                x,y,w,h = cv2.boundingRect(c)
                cv2.rectangle(before, (x, y), (x + w, y + h), (36,255,12), 2)
                cv2.rectangle(after, (x, y), (x + w, y + h), (36,255,12), 2)
                cv2.rectangle(diff_box, (x, y), (x + w, y + h), (36,255,12), 2)
                cv2.drawContours(mask, [c], 0, (255,255,255), -1)            
                cv2.drawContours(objectWithErr, [c], 0, RED, -1)           
        
        #cv2.imshow('MotorOK', before)
        #cv2.imshow('MotorERROR', after)
        #cv2.imshow('diff', diff)
        #cv2.imshow('diff_box', diff_box)
        #cv2.imshow('mask', mask)
        #cv2.imshow('MotorWithLabeldedError', objectWithErr)
                
        self.tmp = objectWithErr  # class GLOBAL for potential save of the detected image
        #objectWithEr = imutils.resize(image,width=640)
        frame = cv2.cvtColor(objectWithErr, cv2.COLOR_BGR2RGB)
        objectWithErr = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(objectWithErr)
        pixmap = pixmap.scaled(_objImgWindowWidth, _objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
        self.lbl_cameraView.setPixmap(pixmap) 
        

    


    '''
    User has detected an Anomaly in the LifeView Camera - pressed a button to save the picture ( tmp).
    ..kind of preview before we store this as a detected anomaly in the anomaly-folder...
    '''
    def send2CurrentAnomalyDetection(self):
        """ This function will save the image"""
        #filename = 'Snapshot '+str(time.strftime("%Y-%b-%d at %H.%M.%S %p"))+'.png'
        filename = tmpPic_dir +  '\lastTakenPicture.png'
        cv2.imwrite(filename,self.tmp)  # Take the class GLOBAL for potential save of the detected image
        print('Image saved as:',filename)
        self.label_currentAnomalyImage.setText(filename)
        pixmap = QtGui.QPixmap(filename)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(_objImgWindowWidth, _objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
            self.lbl_curDetectedAnoImage.setPixmap(pixmap)        
        # save Anomaly wird wieder aktiviert
        self.pushButton_SaveAnomalyDetectImage.setEnabled(True)
        
            
              
    def saveAnomalyDetectedImage(self):
        if self.lineEdit_prodBezeichng.text() and self.lineEdit_ttNr.text() and self.lineEdit_musterPhase.text():
            print("ok - every field is filled")
            newAnomalyObjectFileName = "a_" +    os.path.basename(self.label_refObjectFileName.text())
            returnValue = toolz.msgBoxInfoOkCancel(newAnomalyObjectFileName,"Save File - PLEASE CHECK!" )               
            if returnValue == QMessageBox.Ok:
                print('OK we will store this NEW refObject') 
                src = tmpPic_dir +  '\lastTakenPicture.png'
                dst = cur_dirAnomaly + "\\" + newAnomalyObjectFileName 
                try:
                    os.remove(dst) # der selbe name darf überschrieben werden
                except OSError:                    
                    pass
                shutil.copy2(src,dst) # complete target filename given
                # WOW..store metaData INTO the png - https://stackoverflow.com/questions/58399070/how-do-i-save-custom-information-to-a-png-image-file-in-python
                targetImage = Image.open(dst)
                metadata = PngInfo()
                metadata.add_text("errTypeA", "yes")
                metadata.add_text("errTypeB", "no")
                metadata.add_text("errTypeC", "no")                
                targetImage.save(dst, pnginfo=metadata)
                targetImage = Image.open(dst)
                
                print(targetImage.text)
                
                
        else:
           logging.info(toolz.dt() + 'saveAnomalyDetectedImage() - New object not complete filled')
           toolz.msgBoxInfoOkCancel("Die Felder für die Motorparameter MÜSSEN gefüllt werden!","ACHTUNG - Gültiges Ref.-Objekt auswählen" )
            
    def listLearnedMotors(self):
        included_extensions = ['jpg','jpeg', 'png']
        file_list = [fn for fn in os.listdir(cur_dir)
              if any(fn.endswith(ext) for ext in included_extensions)]
        self.listWidget_learnedMotor.clear()
        self.listWidget_learnedMotor.addItems(file_list)
        self.listWidget_learnedMotor.setCurrentRow(0)
        self.listWidget_learnedMotor.repaint()
        QtCore.QCoreApplication.processEvents()
                
    def previewSelectedListObject(self):    
        logging.info(toolz.dt() + 'previewSelectedListObject')
        cur_index = self.listWidget_learnedMotor.currentRow()
        item = self.listWidget_learnedMotor.item(cur_index)   
        if item is not None:        
            try: # To avoid divide by 0 we put it in try except
                #print('!!! click {}'.format(item.text()))
                print(item.text()) # filename only
                path_of_image = cur_dir + "\\" + item.text()
                self._currentSelectedRefPictureAndPath = path_of_image # global for anomaly detection
                print(self._currentSelectedRefPictureAndPath)
                self.label_refObjectFileName.setText(self._currentSelectedRefPictureAndPath)
                pixmap = QtGui.QPixmap(path_of_image)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(_objImgWindowWidth, _objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
                    self.lbl_refObjectPicture.setPixmap(pixmap)
                    #self.lbl_previewRefMotor.adjustSize()
                    #self.resize(pixmap.size())
                    # split filename in parts and show in variables
                    objectFileName = os.path.splitext(os.path.basename(item.text()))[0]
                    objList = re.split('\#', objectFileName)
                    print(objList)           
                    self.lineEdit_prodBezeichng.setText(objList[0])
                    self.lineEdit_ttNr.setText(objList[1])
                    self.lineEdit_musterPhase.setText(objList[2])
                    #objList[3] ist eine laufende Nr wird später gebraucht!
                    # setting current index - https://www.geeksforgeeks.org/pyqt5-setting-current-index-in-combobox/
                    self.comboBox_TestPos.setCurrentIndex(int(objList[4])) 
            except Exception:
                traceback.print_exc()
                logging.error(traceback.format_exc())
        else:
             toolz.msgBoxInfoOkCancel("Please FIRST crate Objects in LearnProgram!","PROBLEM - NO Reference Objects availabe!!" )
             logging.error(toolz.dt() + 'PROBLEM - NO Reference Objects availabe!!')
             self.pushButton_SaveAnomalyDetectImage.setEnabled(False)
             self.pushButton_send2CurrentDetection.setDisabled(True)
             self.pushButton_WriteErrorProtocol.setDisabled(True)
   
                
#THIS sector is needed for stand alone mode 
'''         
def app():
    app = QtWidgets.QApplication(sys.argv)  
    
    win = anomalyWindowUI()
    win.show()
    sys.exit(app.exec_())

app()     
'''
        