# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 16:15:08 2024

@author: kristina
itemClicked:
https://stackoverflow.com/questions/54436909/the-slot-dont-work-for-qlistwidget-itemclicked-pyqt

resize raster of pic:
https://stackoverflow.com/questions/21802868/python-how-to-resize-raster-image-with-pyqt

status: 

05.04.24: Hier NUR die qwindows-Class ( no app() run ) - aufgerufen durch ein MDIarea
todo:
    abspeichern aller image data in metadaten..auch die filter!!
    
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
'''
ONLY import the UI resource file here - https://stackoverflow.com/questions/50627220/loadui-loads-everything-but-no-images-in-pyqt
pyrcc5 -o image_rc.py image.qrc
Issue: without..No Images will be displayed!!
'''
import image_rc  

import sys
import os
import re
import time
import cv2, imutils
import shutil
import traceback
from pathlib import Path
from cvzone.SelfiSegmentationModule import SelfiSegmentation


from PIL import Image
from image_tools.sizes import resize_and_crop

import logging

#import MY own classes
from class_tools import tools
toolz = tools()  

'''
https://stackoverflow.com/questions/7484454/removing-handlers-from-pythons-logging-loggers
Zäh! einmal angelegt wird der name dem Handler übergeben..das auch NUR in einem unserer Module!
Im notfall wenn sich mal der namen des log ändern sollte, dann den Handler rücksetzen:
        
    logging.getLogger().removeHandler(logging.getLogger().handlers[0])
    
    logFileName = os.getcwd() + "\\" +"companyTasks.log"
    logger = logging.getLogger(logFileName)
    logging.basicConfig(filename='companyTasks.log', encoding='utf-8', level=logging.INFO)
    logger.debug('This message should go to the log file')
    logger.info('So should this')
    logger.warning('And this, too')
    logger.error('And non-ASCII stuff, too, like Øresund and Malmö')
'''

logFileName = os.getcwd() + "\\" +"companyTasks.log"
logger = logging.getLogger(logFileName)
#logging.basicConfig(filename='companyTasks.log', encoding='utf-8', level=logging.INFO)
logging.basicConfig(filename = logFileName,  level=logging.INFO)

logging.info(toolz.dt() + '******** This is Module einrichtungMain.py  GO ***************************')

print(cv2.__file__) 
print (cv2. __version__ )
logging.info(toolz.dt() + cv2. __version__ )

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
print("Qt: v", QT_VERSION_STR, "\tPyQt: v", PYQT_VERSION_STR)

_objImgWindowWidth = 400
_objImgWindowHeight = 400

#check if directory exist..if not make one
cur_dir = os.getcwd() + '\learnedRefPictures'
Path(cur_dir).mkdir(parents=True, exist_ok=True)
logging.info(toolz.dt() + 'FolderPath and Check done: ' + cur_dir)
 
tmpPic_dir = os.getcwd() + "\\" + 'tmpPic' 
Path(tmpPic_dir).mkdir(parents=True, exist_ok=True)
logging.info(toolz.dt() + 'FolderPath and Check done: ' + tmpPic_dir)

#gave crash in auto-py-to-exe created exe...could not find files from mediapipe!? used by cvzone
try:
   logging.info(toolz.dt() + 'try..segmentor = SelfiSegmentation() ')
   segmentor = SelfiSegmentation()
except Exception as e:
    print(e)
    logging.error(traceback.format_exc())
    # Logs the error appropriately. 
    

class window(QtWidgets.QMainWindow):
    def __init__(self):
        super(window,self).__init__()
        logging.info(toolz.dt() + 'super(window...init..done')
        # load ui file
        try:            
            fp = 'einrichtungUI.ui'
            uic.loadUi(fp, self)
        except Exception as e:
            print(e)
            logging.error(traceback.format_exc())        
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)   # added newly
                          
        self.listWidget_learnedMotor = self.findChild(QListWidget,"listWidget_learnedMotor")
        self.listWidget_learnedMotor.clicked.connect(self.previewSelectedListObject)
        self.listWidget_learnedMotor.doubleClicked.connect(self.deleteLearnedMotor)
                
        self.pushButton_StartStopCam =  self.findChild(QPushButton,"pushButton_StartStopCam")      
        self.pushButton_StartStopCam.clicked.connect(self.loadImage)
        
        self.pushButton_MakePicture =  self.findChild(QPushButton,"pushButton_MakePicture")      
        self.pushButton_MakePicture.clicked.connect(self.makePictureFromFrame)
        
        self.pushButton_SaveAsReference =  self.findChild(QPushButton,"pushButton_SaveAsReference")      
        self.pushButton_SaveAsReference.clicked.connect(self.saveLatestPicAsReferenceImage)
        
        self.comboBox_TestPos =  self.findChild(QComboBox,"comboBox_TestPos")         
        self.checkBox_cvFilter = self.findChild(QCheckBox,"checkBox_cvFilter")
        self.lbl_cameraView = self.findChild(QLabel,"lbl_cameraView")
        
        self.lineEdit_prodBezeichng = self.findChild(QLineEdit, "lineEdit_prodBezeichng")
        self.lineEdit_ttNr = self.findChild(QLineEdit, "lineEdit_ttNr")
        self.lineEdit_musterPhase = self.findChild(QLineEdit, "lineEdit_musterPhase")
        self.lineEdit_camNr = self.findChild(QLineEdit, "lineEdit_camNr")
        
        self.lbl_previewRefMotor = self.findChild(QLabel, "lbl_previewRefMotor")
        self.lbl_lastTakenPic = self.findChild(QLabel, "lbl_lastTakenPic")        
        self.label_filterSymbolBild = self.findChild(QLabel,"label_filterSymbolBild")
        
      
        
        logging.info(toolz.dt() + 'clicked.connect....done')
        
        #enable / disable elements
        self.pushButton_MakePicture.setEnabled(False)
        self.pushButton_SaveAsReference.setDisabled(True)
        logging.info(toolz.dt() + 'set..pushButton_..done')
       
        
        #set status TIP
        self.listWidget_learnedMotor.setStatusTip("Location of learned Images: " + cur_dir)
        self.lbl_lastTakenPic.setStatusTip("Location of LAST taken Image: " + tmpPic_dir)
        self.pushButton_SaveAsReference.setStatusTip("BEFORE saving! E N S U R E  that parameter-fields (on the left) are filled properly!")
        self.lbl_cameraView.setStatusTip("This window show your  W e b c a m!  Click START-Object-Camera ( Button below )")
        self.pushButton_MakePicture.setStatusTip("..Is making a picture from current Webcam image stream! Picture is shown in sector: Last taken Picture from Live View Webcam (mid of the UI)! Its stored in a tmp folder!")
        self.horizontalSlider_thresh1.valueChanged['int'].connect(self.thresh1_value) # type: ignore
        self.horizontalSlider_thresh1.setMaximum(100)
        logging.info(toolz.dt() + 'set..status tips _..done')       
        
        # Added code here
        self.tmpImg = None # Will hold the temporary image for display       
        self.fps=0
        self.started = False
        self.thresh1_value_now = 0.5
        logging.info(toolz.dt() + 'set..global variables..done')
        
        #HIER gehts los     
        self.listLearnedMotors()
        self.previewSelectedListObject()
    
           
    # OpenCV-Filter    
    def thresh1_value(self,value):
        """ This function will take value from the slider
            for the threshould from 0 to 99
        """
        self.thresh1_value_now = value/100
        print('thresh1_value_now: ',self.thresh1_value_now)
        self.lineEdit_thresh1.setText(str(self.thresh1_value_now))    
     
      
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
        self.pushButton_MakePicture.setEnabled(True)
        self.pushButton_SaveAsReference.setDisabled(True)
        self.webcam_0_Found = True
        self.webcam_1_Found = True
        self.webcamNr = 0 # FIRST choicxe       
        
        
        n = 0
        i = 0
        frames_to_count= 30
        
        if  toolz.testDevice(0)  == False:  # no printout if cam (0) is available
            #toolz.msgBoxInfoOkCancel("Webcam (0) NOT found!","Webcam ISSUE - PLEASE CHECK!")
            self.webcam_0_Found = False
            self.webcamNr = 1 # 2. chance        
            
        if toolz.testDevice(1) == False:  # no printout if cam (0) is available
            #toolz.msgBoxInfoOkCancel("Webcam (1) NOT found!","Webcam ISSUE - PLEASE CHECK!")
            self.webcam_1_Found = False
            self.webcamNr = 99  ## ERR
            
        if self.webcam_0_Found == False  and self.webcam_1_Found == False:
            toolz.msgBoxInfoOkCancel("NO Webcam available","Webcam I S S U E - PLEASE CHECK!")
            return                 
        
        if self.started:
            self.started=False
            self.pushButton_StartStopCam.setText('START Object-Camera (WebCam)')    
        else:
            self.started=True
            self.pushButton_StartStopCam.setText('STOP Object-Camera (WebCam)')
        
        cam = True # True for webcam
        if cam:            
            vid = cv2.VideoCapture(int(self.lineEdit_camNr.text()))  
        else:
            return
        
        
        #frames_to_count=20 # original 20
        frames_to_count= vid.get(cv2.CAP_PROP_FPS)
        
        print("vid.get(cv2.CAP_PROP_FPS) =" + str(frames_to_count))
        
       
        #https://www.youtube.com/watch?v=oOuswkbsBCU
        n = 0
        i = 0
        
        while(vid.isOpened()):  
            QtWidgets.QApplication.processEvents()    
            ret, image = vid.read()               
        
            if (2*n) % frames_to_count == 0:
                self.update(image)
                i+=1
            n+=1
            if ret==False:
                break
                    
            #EXIT CHECKER - ckoss
            if self.started==False:
                cv2.destroyAllWindows() 
                print('Loop break')
                break
        
               
        
        
    
    '''
    CVZONE - opencv filtering 
    #https://github.com/cvzone/cvzone?tab=readme-ov-file#installations
    #https://dev.to/azure/opencv-10-lines-to-remove-the-background-in-an-image-3m98
    '''
    #https://github.com/cvzone/cvzone?tab=readme-ov-file#installations
    #https://dev.to/azure/opencv-10-lines-to-remove-the-background-in-an-image-3m98

    def bgremove(self, myimage):
        #BLACK = (0, 0, 0)   PINK = (255, 0, 255)    GREEN = (0, 255, 0)
        finalimage  = segmentor.removeBG(myimage,  imgBg=(0, 0, 0), cutThreshold=0.5)
        return finalimage    
                       
    
    def update(self, image):
        """ This function will update the photo according to the 
            current values of blur and brightness and set it to photo label.
        """     
        # frame der cam
        self.tmpImg = image
        self.compareLiveVideoFrame_vs_savedReferenceImage( image)
        if self.checkBox_cvFilter.isChecked() == True:
            image = self.bgremove(image)            
            
        
        #image = imutils.resize(image,width=640)
        frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)        
        pixmap = QtGui.QPixmap.fromImage(img)
        pixmap = pixmap.scaled(_objImgWindowWidth, _objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
        self.lbl_cameraView.setPixmap(pixmap)                
       
        
    def compareLiveVideoFrame_vs_savedReferenceImage(self,  frameImg):    
        try:
            cur_index = self.listWidget_learnedMotor.currentRow()
            item = self.listWidget_learnedMotor.item(cur_index)   
            if item is not None:          
               refImg = cur_dir + "\\" + item.text()
               referenceImageStored = cv2.imread(refImg)
               #lastTakenPicFromCam =  cv2.imread(tmpPic_dir +  '\lastTakenPicture.png')
               lastTakenPicFromCam = frameImg # live frame image from webcam 
               
               #hier können filter tests rein
               
                          
               mse = toolz.mse( lastTakenPicFromCam, referenceImageStored)
               print ("ref: " +  item.text() + " MSE/frame = " +  str(round(mse,2) ))        
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            
        
    def makePictureFromFrame(self):
        logging.info(toolz.dt() + 'makePictureFromFrame()') 
        """ This function will save the image"""
        try:
            filename = tmpPic_dir +  '\lastTakenPicture.png'
            toolz.removeFile(filename)
            cv2.imwrite(filename,self.tmpImg)
            print('Frame Image saved as:',filename)
            pixmap = QtGui.QPixmap(filename)
            if not pixmap.isNull():
                pixmap = pixmap.scaledToWidth(320)
                self.lbl_lastTakenPic.setPixmap(pixmap)
            #clear the parameter-fields..so user can enter new data
            self.lineEdit_prodBezeichng.clear()
            self.lineEdit_ttNr.clear()
            self.lineEdit_musterPhase.clear()
            self.comboBox_TestPos.setCurrentIndex(0) 
            # save Photo wird wieder aktiviert
            self.pushButton_SaveAsReference.setEnabled(True)
        except Exception as e:
            logging.error(traceback.format_exc())
            print(e)
            # Logs the error appropriately.   
    
              
    def saveLatestPicAsReferenceImage(self):
        logging.info(toolz.dt() + 'saveLatestPicAsReferenceImage()') 
        if self.lineEdit_prodBezeichng.text() and self.lineEdit_ttNr.text() and self.lineEdit_musterPhase.text():
            try:                
                print("ok - every field is filled")
                logging.info(toolz.dt() + 'saveLatestPicAsReferenceImage() - every field is filled')
                newRefObject = self.lineEdit_prodBezeichng.text() + "#" + self.lineEdit_ttNr.text() + "#" + self.lineEdit_musterPhase.text() + "#"+ "000" + "#" + self.comboBox_TestPos.currentText()
                returnValue = toolz.msgBoxInfoOkCancel(newRefObject,"THIS NEW image will now be saved - PLEASE CHECK!" )               
                if returnValue == QMessageBox.Ok:
                    print('OK we will store this NEW refObject') 
                    logging.info(toolz.dt() + 'saveLatestPicAsReferenceImage() - OK we will store this NEW refObject')
                    src = tmpPic_dir +  '\lastTakenPicture.png'
                    dst = cur_dir + "\\" + newRefObject + ".png"
                    toolz.removeFile(dst)
                    shutil.copy2(src,dst) # complete target filename given
                    self.listLearnedMotors()
                else:
                    return
            except Exception as e:
                logging.error(traceback.format_exc())
                print(e)
                # Logs the error appropriately.                 
        else:
            logging.info(toolz.dt() + 'saveLatestPicAsReferenceImage() - New object not complete filled')
            toolz.msgBoxInfoOkCancel("Die Felder für die Motorparameter MÜSSEN gefüllt werden!","ACHTUNG" )
            
            
    def listLearnedMotors(self):
        logging.info(toolz.dt() + 'listLearnedMotors()')  
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
                logging.info(toolz.dt() + 'previewSelectedListObject() - selection from List:' + item.text())
                print(item.text()) # filename only
                path_of_image = cur_dir + "\\" + item.text()
                pixmap = QtGui.QPixmap(path_of_image)
                if not pixmap.isNull():
                    pixmap = pixmap.scaledToWidth(320)
                    self.lbl_previewRefMotor.setPixmap(pixmap)
                    #self.lbl_previewRefMotor.adjustSize()
                    #self.resize(pixmap.size())
                    # split filename in parts and show in variables
                    objectFileName = os.path.splitext(os.path.basename(item.text()))[0]
                    objList = re.split('\#', objectFileName)
                    logging.info(toolz.dt() + 'previewSelectedListObject() - objectFileName:' + objectFileName)                   
                    print(objList)           
                    self.lineEdit_prodBezeichng.setText(objList[0])
                    self.lineEdit_ttNr.setText(objList[1])
                    self.lineEdit_musterPhase.setText(objList[2])
                    #objList[3] ist eine laufende Nr wird später gebraucht!
                    # setting current index - https://www.geeksforgeeks.org/pyqt5-setting-current-index-in-combobox/
                    self.comboBox_TestPos.setCurrentIndex(int(objList[4])) 
                #show the last taken Reference Picture    
                filename = tmpPic_dir +  '\lastTakenPicture.png'
                logging.info(toolz.dt() + 'previewSelectedListObject() - lastTakenPic:' + filename)
                pixmap = QtGui.QPixmap(filename)
                if not pixmap.isNull():
                    pixmap = pixmap.scaledToWidth(320)
                    self.lbl_lastTakenPic.setPixmap(pixmap) 
            except Exception:
                traceback.print_exc()

    def deleteLearnedMotor(self):
        logging.info(toolz.dt() + 'deleteLearnedMotor()') 
        try:
            for idx in self.listWidget_learnedMotor.selectionModel().selectedIndexes():
                row_number = idx.row()            
                item = self.listWidget_learnedMotor.item(row_number)            
                path_of_image = cur_dir + "\\" + item.text()
                print ("delete: " + path_of_image)
                returnValue = toolz.msgBoxInfoOkCancel(path_of_image,"SURE? Delete this Image?" ) 
                if returnValue == QMessageBox.Ok:
                    logging.info(toolz.dt() +"This image will be deleted: " + path_of_image)
                    os.remove(path_of_image) if os.path.exists(path_of_image) else None
                    self.listLearnedMotors()
                    self.previewSelectedListObject()
        except Exception as e:
            print(e)
            logging.error(traceback.format_exc())
            # Logs the error appropriately.   

#THIS sector is needed for stand alone mode 
'''          
def app():
    app = QtWidgets.QApplication(sys.argv)      
    win = window()
    win.show()    
    sys.exit(app.exec_())

app()   
'''
 
        