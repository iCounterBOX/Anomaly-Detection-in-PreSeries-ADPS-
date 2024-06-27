set root=C:\Users\kristina\anaconda3

call %root%\Scripts\activate.bat %root%
call activate py38

p:
call cd D:\ALL_PROJECT\a_Factory\_AnomalySSIM\py38
call copy /y mdiMain.ui D:\ALL_PROJECT\a_Factory\_AnomalySSIM\py38\output\mdiMain
call copy /y D:\ALL_PROJECT\a_Factory\_AnomalySSIM\py38\output\mdiMain
call copy /y einrichtungUI.ui D:\ALL_PROJECT\a_Factory\_AnomalySSIM\py38\output\mdiMain
call copy /y ocrTemplateUI.ui D:\ALL_PROJECT\a_Factory\_AnomalySSIM\py38\output\mdiMain

call xcopy /y /I /E imagesOCR   output\mdiMain\imagesOCR
call xcopy /y /I /E learnedRefPictures   output\mdiMain\learnedRefPictures
call xcopy /y /I /E imagesAnomaly   output\mdiMain\imagesAnomaly
call xcopy /y /I /E tmp   output\mdiMain\tmp


cmd \k 