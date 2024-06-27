# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:00:47 2024

@author: kristina
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 16:15:08 2024

@author: kristina

https://www.youtube.com/watch?v=n-ipFUQRBBk
PyQt : Show Image Inside QTableWidget
#pixmap.loadFromData(image,'jpg') # wenn img von DB als blob zB.. https://www.youtube.com/watch?v=n-ipFUQRBBk


status: 

Liste OK
cam ok
Mouse OK
POI Capture YES...but problem with coordinate violation between frame capture and UI !
FIRST test with QGraphicsView

_Test2:
    statt label NUR nch QGraphicsView
    WOW..workaround gefunden!..rectangle mit LINKER mouse (obere rect kante ) anfangen ..Endpunkt rectUntenRechts mit RECHTER mouse
    zusätzlich klicken!  ISSUE: im QGraphicsView wird der releaseMouse NICHT ausgelöst. Das issue ist draußen bekannt :-(.
    Profillösung wäre wohl ein überschreiben der Class QGraphicsView...HIER geht es im moment NUR um den ROI für Demo-Zwecke! ..reicht

    ROI wird so gut eingefangen..coordinaten stimmen!                                                                                                                    

_Test3:
    
    roi wird richtig erkannt und abgespeichert
     wir werden roiCam und OCR per Button getrennt ansteuern   
     
_Test4:
    templateDetection_4_OCR bekommt cam..greift auf template zu 
    
08.05:
          https://pyimagesearch.com/2020/05/25/tesseract-ocr-text-localization-and-detection/
    pytesseract kann schrift auch DETECTEN...d.g. macht eigene reagions und confidence                                                                                                            
    
"""


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import (
    QMessageBox, 
    QListWidget, 
    QTableWidget,
    QPushButton, 
    QComboBox, 
    QCheckBox, 
    QLabel,
    QLineEdit,
    QWidget,
    )
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt, QEvent

#from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import  QGraphicsScene,  QGraphicsPixmapItem

import pytesseract
pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR/tesseract.exe'  # your path may be different
from pytesseract import Output


import os
import cv2
import traceback
from pathlib import Path
import logging

import pytesseract

#import MY own classes
from class_tools import tools
tz = tools()  

import image_rc  

tz.drawing = False
tz.ix, tz.iy = -1,-1
tz.ixx, tz.iyy = -1,-1
tz.img2 = None

global _templateGray 

logging.basicConfig(filename= os.getcwd() + "\\" +"companyTasks.log",  level=logging.INFO)
logging.info(tz.dt() + '******** This is Module ocrTemplateUI.py  GO ***************************')

print(cv2.__file__) 
print (cv2. __version__ )
logging.info(tz.dt() + cv2. __version__ )

from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
print("Qt: v", QT_VERSION_STR, "\tPyQt: v", PYQT_VERSION_STR)


#check if directory exist..if not make one

_BaseDir = os.getcwd()
logging.info(tz.dt() + '_BaseDir: ' + _BaseDir)
logging.info(tz.dt() + 'os.__file__: ' + os.__file__)
logging.info(tz.dt() + 'os.getcwd(): ' + os.getcwd())

_UI_FILE = os.path.join(_BaseDir,"ocrTemplateUI.ui" )
logging.info(tz.dt() + 'UI file: ' + _UI_FILE)

_IMG_DIR = _BaseDir + "\\imagesOCR" 
Path(_IMG_DIR).mkdir(parents=True, exist_ok=True)
logging.info(tz.dt() + 'OCR images path: ' + _IMG_DIR)

_IMG_TMP = _BaseDir + "\\tmpPic" 
Path(_IMG_TMP).mkdir(parents=True, exist_ok=True)
logging.info(tz.dt() + 'tmp images path: ' + _IMG_TMP)


if os.path.exists(_IMG_TMP + '/rectMouse_ROI.jpg'):   #
    _templateGray = cv2.imread(_IMG_TMP + '/rectMouse_ROI.jpg', cv2.IMREAD_GRAYSCALE)   # 
    assert _templateGray is not None, "file could not be read, check with os.path.exists()"
else:
    #_templateGray= np.zeros((40,40,3),np.uint8)  # 
    #_templateGray = cv2.cvtColor(_templateGray, cv2.COLOR_BGR2GRAY)
    pass



class MainWindow_ocrTemplate(QtWidgets.QMainWindow):    
    def __init__(self):
        #super(MainWindow_ocrTemplate,self).__init__()
        super().__init__()

        logging.info(tz.dt() + 'super(window...init..done')
        # load ui file
        try:  
            uic.loadUi( _UI_FILE, self)
        except Exception as e:
            print(e)
            logging.error(traceback.format_exc())        
        
        #mit self in UI muss nach den elementen in der UI nicht mehr gesucht werden :-)           
        self.pushButton_listElements.clicked.connect(self.listElements)   
        self.pushButton_startCamera.clicked.connect(self.loadImage)
        self.pushButton_camTemplateDetect.clicked.connect(self.templateDetection_4_OCR)
        
        self.pushButton_camTemplateDetect.setText('Start Template Detection (WebCam)')       
        self.pushButton_startCamera.setText('START Object-Camera (WebCam)')  
        
        #template vorladen
        self._objImgWindowWidth = 100
        self._objImgWindowHeight = 100
        
        self.firstrun = False
        self._meth = "cv2.TM_CCOEFF_NORMED"
        self.fps=0
        self.started = False
        self.startedTpl = False
        
        # Install an event filter to capture mouse events
        self.centralwidget.installEventFilter(self)

        #experiment GraphicView
        print(self.graphicsView_play.scene())
        
        self.scene = QGraphicsScene()
        self.graphicsView_play.setScene(self.scene)  
        self.graphicsView_play.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

       
        #load test:
        
        '''
        file_name = "webcam.png"
        self.image_qt = QImage(file_name)
        pic = QGraphicsPixmapItem()
        pic.setPixmap(QPixmap.fromImage(self.image_qt))
        self.scene.setSceneRect(0, 0, 400, 400)
        self.scene.addItem(pic)
        '''    
                
        #HIER gehts los     
        self.listElements()        
    
    
    # handle the red cross event
    def closeEvent(self, event): 
        try:
            self.started = False
            self.startedTpl = False
            logging.shutdown()
            self.close()            
            #QtWidgets.QApplication.quit()
            #QtWidgets.QCoreApplication.instance().quit()            
            event.accept()
            print('Window closed')
            #sys.exit() # die beiden KILL python ALL - restart Kernel :-)
            
        except Exception as e:
            print(e)
            logging.error(traceback.format_exc())        
        
    # event mouse für QGraphicScene

    '''
    # todo:  tut nicht muss noch erforscht werden !!!!!!!!!!!!
    def mousePressEvent(self, event):
        
        pen = QPen(QtCore.Qt.black)
        brush = QBrush(QtCore.Qt.black)
        #x = event.scenePos().x()  # kennt er nicht?
        #y = event.scenePos().y()
        
        #self.addEllipse(x, y, 4, 4, pen, brush)
        #print(x, y)
    '''    
    '''
    Install an event filter to capture mouse events..from many ..this mouse is mostly working.
    Saw lots of examples with overwriting the QGraphicsScene class. But i like this compact solution here.
    event is fired properly . BUT not the release of left mouse button. So we use for release the RIGHT button on
    Mouse...its a workaround...and is working fine for us...and a good exercise for human hand :-)
    '''
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            x = event.x()
            y = event.y()
            print(f"Mouse moved to ({x}, {y})")
            self.label_mouseTrackerLabel.setText(f"Mouse moved to ({x}, {y})")
            tz.drawing = True
        
        elif event.type() == QEvent.MouseButtonPress:
            x = event.x()
            y = event.y()
            button = ""
            if event.button() == Qt.LeftButton:
                button = "Left"
                tz.drawing = True
                tz.ix = x
                tz.iy = y
                tz.img2 = tz.capFrame
                print("down.." + "x= " + str(x), " ix= " + str(tz.ix) + "    y= " + str(y), " iy= " + str(tz.iy)  )  
            elif event.button() == Qt.RightButton:
                button = "Right"
                x = event.x()
                y = event.y()
                tz.drawing = False
                tz.ixx = x
                tz.iyy = y
                print("rightEnd.." + "x= " + str(x), " ix= " + str(tz.ix) + " y= " + str(y), " iy= " + str(tz.iy)  )     
                 
            elif event.button() == Qt.MiddleButton:
                button = "Middle"
            print(f"{button} button clicked")
            self.label_mouseTrackerLabel.setText(f"{button} button clicked")

        elif  event.type() == QEvent.MouseButtonRelease:
            x = event.x()
            y = event.y()
            tz.drawing = False
            tz.ixx = x
            tz.iyy = y
            print("up.." + "x= " + str(x), " ix= " + str(tz.ix) + " y= " + str(y), " iy= " + str(tz.iy)  )     
                       
            self.update()          
          
        return super().eventFilter(obj, event)        

            
    def listElements(self):
        logging.info(tz.dt() + 'listElements()') 
        
        #Remove old elements first - https://stackoverflow.com/questions/63334382/how-to-remove-data-from-qtablewidget-in-pyqt5-in-python
        self.tableWidget_ocrImage.setRowCount(0)
        row=0
        
        for file in os.listdir(_IMG_DIR):
            filename = os.fsdecode(file)  
            
            if filename.endswith(".png") or filename.endswith(".jpg"): 
                self.tableWidget_ocrImage.insertRow(row)                 
                imgPath = os.path.join(_IMG_DIR, file )
                print( imgPath )   
                logging.info(tz.dt() + 'listElements() - ' + imgPath) 
                
                
                item = self.getImageFromLabel(imgPath)
                self.tableWidget_ocrImage.setCellWidget(row,0, item)
                
                #text ok
                self.tableWidget_ocrImage.setItem(row,1, QtWidgets.QTableWidgetItem(imgPath))
                row+=1
        #GEBASTEL.. viel probiert damit bild und text full size da rein gehen
        self.tableWidget_ocrImage.verticalHeader().setDefaultSectionSize(100)
        self.tableWidget_ocrImage.horizontalHeader().setDefaultSectionSize(100)        
        self.tableWidget_ocrImage.resizeColumnToContents(1)
        
    def getImageFromLabel(self, imgFilePath):
        imgLabel = QtWidgets.QLabel(self.centralwidget)
        imgLabel.setText("")
        imgLabel.setScaledContents(True) 
        logging.info(tz.dt() + 'getImageFromLabel() - lastTakenPic:' + imgFilePath)
        pixmap = QtGui.QPixmap(imgFilePath)
        imgLabel.setPixmap(pixmap) 
           
        return imgLabel       
   
# THE CAM part + OCR

    def templateDetection_4_OCR (self):  
        cap = cv2.VideoCapture(int(self.lineEdit_camNr.text()),cv2.CAP_DSHOW) # standard cam 1 statt webcam(0) gesetzt in UI
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        self.getCamFrameDimensions(cap)   
                
        self.started = False # drüben geht das licht aus
        self.pushButton_startCamera.setText('On HOLD')    
        
        if self.startedTpl:                 
            self.startedTpl = False
            self.pushButton_camTemplateDetect.setText('Start Template Detection (WebCam)')       
            self.pushButton_startCamera.setText('START Object-Camera (WebCam)')  
        else:
            self.startedTpl=True
            self.pushButton_camTemplateDetect.setText('STOP Template Detection (WebCam)')
            
        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            cv2.destroyAllWindows()
            return  
        
        while True:  
            ret, capFrame = cap.read()  
             
            QtWidgets.QApplication.processEvents()  
            
            '---------------- Template Detection ----------------------'      
            
            if capFrame is None:
                print("templateDetection_4_OCR() / CapFRame is not availabe! - NO OCR")
                return 
            
            # convert both the image and template to grayscale
            capFrameGray = cv2.cvtColor(capFrame, cv2.COLOR_BGR2GRAY)        
            
            #OCR
            try:
                
                self.aText = ""
                results = pytesseract.image_to_data(capFrameGray, output_type=Output.DICT)                
               
                # loop over each of the individual text localizations
                for i in range(0, len(results["text"])):
                    # extract the bounding box coordinates of the text region from
                    # the current result
                    x = results["left"][i]
                    y = results["top"][i]
                    w = results["width"][i]
                    h = results["height"][i]
                    # extract the OCR text itself along with the confidence of the
                    # text localization
                    text = results["text"][i]
                    conf = int(results["conf"][i])


                # filter out weak confidence text localizations
                
                    
                    
                    if self.lineEdit_minConfidence.text():
                        minConf = int(self.lineEdit_minConfidence.text(), base =10 )
                        #print("minconf: " + str(minConf))
                    else:
                        minConf = 0
                        
                        
                    if conf > minConf:
                        # display the confidence and text to our terminal
                        #print("Confidence: {}".format(conf))
                        ##print("Text: {}".format(text))
                        print("")
                        # strip out non-ASCII text so we can draw the text on the image
                        # using OpenCV, then draw a bounding box around the text along
                        # with the text itself
                        text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
                        cv2.rectangle(capFrame, (x, y), (x + w, y + h), (0, 255, 0), 1)
                        cv2.putText(capFrame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 0, 255), 3)
                        
                        self.aText = self.aText +  " " + str(text)
                        print(self.aText) # schon ganz ok aber verzogen
                        self.textEdit_ocrText.setText(self.aText)
                # show the output image
                
                frame = cv2.cvtColor(capFrame, cv2.COLOR_BGR2RGB)
                img = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)        
                pixmap = QtGui.QPixmap.fromImage(img)
                #pixmap = pixmap.scaled(self._objImgWindowWidth, self._objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
                self.lbl_camTemplateDetection.setPixmap(pixmap) 
                
                
                
            except Exception as e:
                logging.error(traceback.format_exc())
                print(e)  
                cap.release()
                cv2.destroyAllWindows()
                break
                
                
            
            '---------------- End Template Detection -------------------' 
            
            if ret==False:
                break
                    
            #EXIT CHECKER - ckoss
            if self.startedTpl==False:
                cap.release()
                cv2.destroyAllWindows()
                #exit()       
                print('Loop break')
                break 
   

# auch gut ..braucht aber dieses template...das wird im image gesucht..under roi daraus ist dann der input 
# tesseract  NICHT LÖSCHEN

    def templateDetection_4_OCRXXX (self):  
        cap = cv2.VideoCapture(int(self.lineEdit_camNr.text()),cv2.CAP_DSHOW) # standard cam 1 statt webcam(0) gesetzt in UI
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        self.getCamFrameDimensions(cap)   
                
        self.started = False # drüben geht das licht aus
        self.pushButton_startCamera.setText('On HOLD')    
        
        if self.startedTpl:                 
            self.startedTpl = False
            self.pushButton_camTemplateDetect.setText('Start Template Detection (WebCam)')       
            self.pushButton_startCamera.setText('START Object-Camera (WebCam)')  
        else:
            self.startedTpl=True
            self.pushButton_camTemplateDetect.setText('STOP Template Detection (WebCam)')
            
        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            cv2.destroyAllWindows()
            return  
        
        while True:  
            ret, capFrame = cap.read()  
             
            QtWidgets.QApplication.processEvents()  
            
            '---------------- Template Detection ----------------------'      
            
            if capFrame is None or os.path.isfile(_IMG_TMP + '/rectMouse_ROI.jpg') is None:
                print("templateDetection_4_OCR() / CapFRame or ROI is not availabe! - NO OCR")
                return 
            
            # convert both the image and template to grayscale
            capFrameGray = cv2.cvtColor(capFrame, cv2.COLOR_BGR2GRAY)        
            templateGray = cv2.imread(_IMG_TMP + '/rectMouse_ROI.jpg', cv2.IMREAD_GRAYSCALE)   
            
            w, h = templateGray.shape[::-1] 
            
            # All the 6 methods for comparison in a list
            methods = [ 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCOEFF', 'cv2.TM_CCORR',
                       'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']        
            methods = [ 'cv2.TM_CCOEFF_NORMED']        
                        
            for meth in methods:            
                method = eval(meth)
                global _meth
                _meth = meth
                
                #OCR
                try:
                    
                    # Apply template Matching
                    res = cv2.matchTemplate(capFrameGray, templateGray, method)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                    
                    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
                    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                        top_left = min_loc
                    else:
                        top_left = max_loc
                        
                    bottom_right = (top_left[0] + w, top_left[1] + h)
                    
                    cv2.rectangle(capFrameGray,top_left, bottom_right, 255, 2)  
                    
                    frame = cv2.cvtColor(capFrameGray, cv2.COLOR_BGR2RGB)
                    img = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)        
                    pixmap = QtGui.QPixmap.fromImage(img)
                    #pixmap = pixmap.scaled(self._objImgWindowWidth, self._objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
                    self.lbl_camTemplateDetection.setPixmap(pixmap) 
                    
                    roi = frame[top_left[1]:top_left[1]+h, top_left[0]:top_left[0]+w]    # region of interest
                    print("match: " + "ix= " + str(top_left[0]), " iy= " + str(top_left[1]) + "  h= " + str(h) + " w= " + str(w)  )      
                    ocr_result = pytesseract.image_to_string(roi)
                    print(ocr_result) # schon ganz ok aber verzogen
                    self.textEdit_ocrText.setText(ocr_result)
                    
                except Exception as e:
                    logging.error(traceback.format_exc())
                    print(e)  
                    cap.release()
                    cv2.destroyAllWindows()
                    break
                
            
            '---------------- End Template Detection -------------------' 
            
            if ret==False:
                break
                    
            #EXIT CHECKER - ckoss
            if self.startedTpl==False:
                cap.release()
                cv2.destroyAllWindows()
                #exit()       
                print('Loop break')
                break 
   

#webcam

    def getCamFrameDimensions(self, cap):
        
        width =  cap.get(cv2.CAP_PROP_FRAME_WIDTH )
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT )
        fps =   cap.get(cv2.CAP_PROP_FPS)
        
        #print('label_image(cam): ', str(self.label_image.size()))              
        print("frame fps: " + str(fps) + " w = " +str( width) + " h = " + str(height)  )

    def loadImage(self):
        """ This function will load the camera device, obtain the image
            and set it to label using the setPhoto function
        """
        
        self.webcam_0_Found = True
        self.webcam_1_Found = True
        self.webcamNr = 0 # FIRST choicxe              
        
        
        frames_to_count= 30
        
        if  tz.testDevice(0)  == False:  # no printout if cam (0) is available
            #toolz.msgBoxInfoOkCancel("Webcam (0) NOT found!","Webcam ISSUE - PLEASE CHECK!")
            self.webcam_0_Found = False
            self.webcamNr = 1 # 2. chance        
            
        if tz.testDevice(1) == False:  # no printout if cam (0) is available
            #toolz.msgBoxInfoOkCancel("Webcam (1) NOT found!","Webcam ISSUE - PLEASE CHECK!")
            self.webcam_1_Found = False
            self.webcamNr = 99  ## ERR
            
        if self.webcam_0_Found == False  and self.webcam_1_Found == False:
            tz.msgBoxInfoOkCancel("NO Webcam available","Webcam I S S U E - PLEASE CHECK!")
            return                 
        
        self.startedTpl = False # drüben geht das licht aus
        self.pushButton_camTemplateDetect.setText('On HOLD')   
        
        if self.started:
            self.started=False
            self.pushButton_startCamera.setText('START Object-Camera (WebCam)')      
            self.pushButton_camTemplateDetect.setText('Start Template Detection (WebCam)')   
        else:
            self.started=True
            self.pushButton_startCamera.setText('STOP Object-Camera (WebCam)')
        
        
        #https://forum.opencv.org/t/how-to-use-waitkey-with-videocapture/10718
        #https://stackoverflow.com/questions/19448078/python-opencv-access-webcam-maximum-resolution
        
               
        cap = cv2.VideoCapture(int(self.lineEdit_camNr.text()),cv2.CAP_DSHOW) # standard cam 1 statt webcam(0) gesetzt in UI
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

        self.getCamFrameDimensions(cap)   
        
        if not cap.isOpened():
            print("Cannot open camera")
            cap.release()
            cv2.destroyAllWindows()
            return      
        
        
        while True:  
            ret, capFrame = cap.read()  
             
            QtWidgets.QApplication.processEvents()  
            
            frame = cv2.cvtColor(capFrame, cv2.COLOR_BGR2RGB)
            img = QImage(frame, frame.shape[1],frame.shape[0],frame.strides[0],QImage.Format_RGB888)        
            pixmap = QtGui.QPixmap.fromImage(img)
            
            try:
                self.scene.clear()
                pic = QGraphicsPixmapItem()
                #pic.setPixmap(QPixmap.fromImage(self.image_qt))
                pic.setPixmap(pixmap)
                self.graphicsView_play.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
                self.scene.setSceneRect(0, 0, 400, 400)
                self.scene.addItem(pic)  
            except Exception as e:
                logging.error(traceback.format_exc())
                print(e)  
                cap.release()
                cv2.destroyAllWindows()
                break
            
             
            if tz.drawing == False:
                #print(".." + "ix= " + str(tz.ix), " ixx= " + str(tz.ixx) + "  iy= " + str(tz.iy), " iyy= " + str(tz.iyy)  ) 
                #save as ROI
                try:  
                    
                    frameWithROI = cv2.rectangle(frame, (tz.ix, tz.iy),(tz.ixx, tz.iyy),(0, 255, 0),2) # erscheint grau da update() alles grau macht  egal
                  
                    roi = frameWithROI[tz.iy:tz.iyy, tz.ix:tz.ixx]    # region of interest
                    if not roi.size:
                        pass
                    else:
                        
                        #SHOW template / ROI
                        #image = imutils.resize(image,width=640)
                        frameROI = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB) #? raus?
                        img = QImage(frameROI, frameROI.shape[1],frameROI.shape[0],frameROI.strides[0],QImage.Format_RGB888)        
                        pixmapROI = QtGui.QPixmap.fromImage(img)
                        #pixmap = pixmap.scaled(self._objImgWindowWidth, self._objImgWindowHeight, QtCore.Qt.KeepAspectRatio)
                        self.label_templateImg.setPixmap(pixmapROI)  
                        
                        #store roi on hdd
                        cv2.imwrite(_IMG_TMP + '/rectMouse_ROI.jpg',roi)
                        
                        #show frame with ROI                        
                        
                        img = QImage(frameWithROI, frameWithROI.shape[1],frameWithROI.shape[0],frameWithROI.strides[0],QImage.Format_RGB888)        
                        pixmap = QtGui.QPixmap.fromImage(img)
                         
                        #graphicsViewTest - statt label auf graphicsView
                        self.scene.clear()
                        pic = QGraphicsPixmapItem()
                        #pic.setPixmap(QPixmap.fromImage(self.image_qt))
                        pic.setPixmap(pixmap)
                        self.scene.setSceneRect(0, 0, 400, 400)
                        self.scene.addItem(pic)                       
                        
                        #roi ist gespeichert ...bis neier ROI kommt alles rücksetzen
                        tz.drawing = False
                        #tz.ix, tz.iy = -1,-1  #MIT isr recht eck nicht mehr sichtbar
                        #tz.ixx, tz.iyy = -1,-1
                       
                except Exception as e:
                    logging.error(traceback.format_exc())
                    print(e)  
                    break
                
            if ret==False:
                break
            #EXIT CHECKER - ckoss
            if self.started==False:
                cap.release()
                cv2.destroyAllWindows()
                #exit()       
                print('Loop break')
                break 
        
   
#THIS sector is needed for stand alone mode 
'''         
def app():
    app = QtWidgets.QApplication(sys.argv)      
    win = MainWindow_ocrTemplate()
    win.show()    
    sys.exit(app.exec_())

app() 
'''  



 
        