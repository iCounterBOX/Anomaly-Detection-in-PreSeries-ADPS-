set root=C:\Users\kristina\anaconda3

call %root%\Scripts\activate.bat %root%
call activate py38
p:
call cd D:\ALL_PROJECT\a_Factory\_AnomalySSIM\py38
call pyrcc5 -o image_rc.py image.qrc
call auto-py-to-exe

cmd \k 