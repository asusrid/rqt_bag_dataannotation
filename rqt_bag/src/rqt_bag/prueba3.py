import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSlot
from PyQt5.QtWidgets import QLabel, QApplication, QRubberBand, QWidget, QVBoxLayout, QMenu, QMainWindow, QPlainTextEdit, QFileDialog, QMessageBox, QLineEdit, QAction, QPushButton
import rosbag
import time
from random import randint
from rqt_bag.msg import ImageLabel
from rqt_bag.msg import Rectangle
from PyQt5 import QtTest

class QExampleLabel (QLabel):

    sequence = []
    bag = None
    imageLabel = ImageLabel()
    

    def __init__(self, pixmap, timeline, topic, msg, widget, stamp):
        super(QExampleLabel, self).__init__()

	self.setPixmap(pixmap)
	self._timeline = timeline
	self._topic = topic
	self.widget = widget
	self.widget.addWidget(self)
    	#INICIALIZAMOS EL MENSAJE Y LOS ATRIBUTOS COMUNES
	self._msg = msg
	self.imageLabel.header = self._msg.header
    	self.imageLabel.imageTopic = self._topic
	#PARA NO PERMITIR ETIQUETAR UN PUNTO
	self.arrastrado = False
	#TIEMPO ORIGINAL DEL BAG PARA GUARDAR EN EL NUEVO BAG EL MISMO TIEMPO
	self.stamp = stamp
	

	#ESTO LO HACEMOS PORQUE LOS RECT QUE SE GUARDAN EN SEQUENCE ESTAN VINCULADOS CON EL WIDGET EN QUE SE CREARON.
	#POR TANTO, HAY QUE VINCULARLOS AL ACTUAL PARA QUE SE PUEDAN VISUALIZAR Y BORRAR.
	#***OJO***: LOS OBJETOS QUE ESTAN EN SEQUENCE SON DE TIPO QRUBBERBAND Y LOS QUE ESTAN 
	#EN IMAGELABEL SON DE TIPO RECTANGLE  
	if len(self.sequence) > 0:
		aux_sequence = []
		for rectangle in self.sequence:
		    self.currentQRubberBand = QRubberBand(QRubberBand.Rectangle, self)
		    self.currentQRubberBand.setGeometry(rectangle.x(), rectangle.y(), rectangle.width(), rectangle.height())
		    aux_sequence.append(self.currentQRubberBand)
		    self.currentQRubberBand.show()
		del self.sequence[:]
		for rectangle in aux_sequence:
		    self.sequence.append(rectangle)
		


    
		

    def mousePressEvent (self, eventQMouseEvent):
	if eventQMouseEvent.buttons() == Qt.LeftButton:
		self.originQPoint = eventQMouseEvent.pos()
        	self.currentQRubberBand = QRubberBand(QRubberBand.Rectangle, self)
		self.sequence.append(self.currentQRubberBand)

		layout = QtWidgets.QHBoxLayout(self.currentQRubberBand)
		layout.setContentsMargins(0, 0, 0, 0)
		layout.addWidget(QtWidgets.QSizeGrip(self.currentQRubberBand), 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
		layout.addWidget(QtWidgets.QSizeGrip(self.currentQRubberBand), 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)

		#TE COLOREA CUALQUIER RECTANGULO QUE SE DIBUJE POR ESTAR SIEMPRE LIGADO A WIDGET
		r = randint(0, 255)
		g = randint(0, 255)
		b = randint(0, 255)
		palette = QPalette()
		palette.setColor(self.currentQRubberBand.foregroundRole(), QColor(r, g, b))
		self.widget.setPalette(palette)
		
        	self.currentQRubberBand.setGeometry(QRect(self.originQPoint, QSize()))
        	self.currentQRubberBand.show()
							
	elif eventQMouseEvent.buttons() == Qt.RightButton:
		found = False
		for rect in self.sequence:
			if(rect.geometry().contains(eventQMouseEvent.pos())):
				self.menu = MenuRectangle(self._timeline, eventQMouseEvent, rect, self.imageLabel, self.sequence)
				found = True
		if not found:
			self.menuglobalimage = MenuGlobalImage(self._timeline, eventQMouseEvent, self._topic, self.sequence, self.imageLabel, self.stamp, eventQMouseEvent.pos())


    def mouseMoveEvent (self, eventQMouseEvent):
        self.currentQRubberBand.setGeometry(QRect(self.originQPoint, eventQMouseEvent.pos()).normalized())
	self.arrastrado = True


    #def mouseReleaseEvent (self, eventQMouseEvent):
		
       	#cropQPixmap = self.pixmap().copy(currentQRect)
        #cropQPixmap.save('/home/alejandro/output.png')

    
	
	
class MenuGlobalImage(QMenu):

    #bag = None
    
    def __init__(self, timeline, event, topic, sequence, imageLabel, stamp, pos):
        super(MenuGlobalImage, self).__init__()

        self.parent = timeline
	self.sequence = sequence
	self.imageLabel = imageLabel
	self.stamp = stamp
	self.topic = topic
	self.pos = pos


	#SE CREA EL DESPLEGABLE LEYENDOSE LAS ETIQUETAS DEL FICHERO TXT
	with open('/home/alejandro/catkin_tfg/src/rqt_bag/src/rqt_bag/tags_file.txt', 'r') as f:
		line = f.readlines()
		for x in line:
			self._setLabel = self.addAction(x.strip())

	self.addSeparator()
	self._setNewLabel = self.addAction('Otra...')  
	self.addSeparator()
	
	self._setNewLabel = self.addAction('Limpiar todo') 
	self._setNewLabel = self.addAction('Guardar')  
	
        action = self.exec_(event.globalPos())
        if action is not None and action != 0:
		#ETIQUETO LA IMAGEN COMPLETA
		if action.text() != 'Otra...' and action.text() != 'Guardar' and action.text() != 'Limpiar todo':
			self.imageLabel.globalImageLabel = action.text()
		#ETIQUETO CON UNA NUEVA ETIQUETA LA IMAGEN COMPLETA
		if action.text() == 'Otra...':
			self.window = App(self.imageLabel, None)
			self.window.show()
			self.exec_()
		if action.text() == 'Limpiar todo' and len(self.sequence) > 0:
			for rect in self.sequence:
				#DELETE RECT FROM WIDGET
				rect.deleteLater()
			del self.sequence[:]
			del self.imageLabel.rect[:]
		#GUARDAR BAG
		if action.text() == 'Guardar':
			if QExampleLabel.bag == None:
				filename = QFileDialog.getSaveFileName(QWidget(), QWidget().tr('Select prefix for new Bag File'), '.', QWidget().tr('Bag files {.bag} (*.bag)'))
				if filename[0] != '':
				    	prefix = filename[0].strip()
				    	record_filename = time.strftime('%Y-%m-%d-%H-%M-%S.bag', time.localtime(time.time()))
				if prefix.endswith('.bag'):
					prefix = prefix[:-len('.bag')]
				if prefix:
					record_filename = '%s_%s' % (prefix, record_filename)
				
				#SI HACE FALTA HACER COMPROBACION DE LOS CAMPOS DE LOS MENSAJES SE HARIA AQUI
				bag = rosbag.Bag(record_filename, 'w')
				QExampleLabel.bag = bag
				bag.write(self.topic + '/label', self.imageLabel, self.stamp)
				bag.close()
				txt_file = open('/home/alejandro/txt_file', 'w')
				txt_file.write('imageTopic: ' + self.imageLabel.imageTopic + '\n')
				for rect in self.imageLabel.rect:
					txt_file.write(
							' X: ' + str(rect.x) + 
							' Y: ' + str(rect.y) +
							' Width: ' + str(rect.width) + 
							' Height: ' + str(rect.height) +
							' Label: ' + str(rect.label) + '\n\n'
							)
				txt_file.write(' Global: ' + str(self.imageLabel.globalImageLabel))
				
				txt_file.close()
			else:
				bag = rosbag.Bag(QExampleLabel.bag.filename, 'a')
				bag.write(self.topic + '/label', self.imageLabel, self.stamp)
				bag.close()
				txt_file = open('/home/alejandro/txt_file', 'w')
				txt_file.write('imageTopic: ' + self.imageLabel.imageTopic + '\n')
				for rect in self.imageLabel.rect:
					txt_file.write(
							' X: ' + str(rect.x) + 
							' Y: ' + str(rect.y) +
							' Width: ' + str(rect.width) + 
							' Height: ' + str(rect.height) +
							' Label: ' + str(rect.label) + '\n\n'
							)
				txt_file.write(' Global: ' + str(self.imageLabel.globalImageLabel))
				
				txt_file.close()
				



class MenuRectangle(QMenu):
    
    def __init__(self, timeline, event, rect, imageLabel, sequence):
        super(MenuRectangle, self).__init__()

        self.parent = timeline
	self.rect = rect
	self.imageLabel = imageLabel
	self.time = time
	self.sequence = sequence

	#SE CREA EL DESPLEGABLE LEYENDOSE LAS ETIQUETAS DEL FICHERO TXT
	with open('/home/alejandro/catkin_tfg/src/rqt_bag/src/rqt_bag/tags_file.txt', 'r') as f:
		line = f.readlines()
		for x in line:
			self._setLabel = self.addAction(x.strip())

	self.addSeparator()
	self._setNewLabel = self.addAction('Otra...')  
	self.addSeparator()
	self._setNewLabel = self.addAction('Limpiar') 
	
        action = self.exec_(event.globalPos())
        if action is not None and action != 0:
		#SI ETIQUETO UN RECTANGULO 
		if action.text() != 'Otra...' and action.text() != 'Limpiar':
			rectangle = Rectangle()
			rectangle.label = action.text()
			rectangle.width = self.rect.width()
			rectangle.height = self.rect.height()
			rectangle.x = self.rect.x()
			rectangle.y = self.rect.y()
			self.imageLabel.rect.append(rectangle)
		#ELIMINO LOS RECTANGULOS DIBUJADOS
		if action.text() == 'Limpiar':
			txt_file = open('/home/alejandro/txt_file2', 'w')
			rect.deleteLater()
			index = self.sequence.index(rect)
			
			del self.sequence[index]
			for rectangle in self.imageLabel.rect:
				if rectangle.x == rect.x() and rectangle.y == rect.y():
					index = self.imageLabel.rect.index(rectangle)
					del self.imageLabel.rect[index]
					txt_file.write('index: ' + str(index) + '\n')
					txt_file.close()
		#SI ETIQUETO CON UNA ETIQUETA NUEVA UN RECTANGULO
		if action.text() == 'Otra...':
			self.window = App(self.imageLabel, self.rect)
			self.window.show()
			self.exec_()



class App(QMainWindow):
 
    def __init__(self, message, rect):
        QMainWindow.__init__(self)
        self.title = 'Nueva etiqueta'
        self.left = 10
        self.top = 10
        self.width = 400
        self.height = 140
	self.message = message
	self.rect = rect

        self.initUI()
 
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        # Create textbox
        self.textbox = QLineEdit(self)
        self.textbox.move(20, 20)
        self.textbox.resize(280,40)
 
        # Create a button in the window
        self.button = QPushButton('Agregar', self)
        self.button.move(20,80)

        # connect button to function on_click
        self.button.clicked.connect(self.on_click)
        self.show()
 
    @pyqtSlot()
    def on_click(self):

        textboxValue = self.textbox.text()	
	tags_file = open('/home/alejandro/catkin_tfg/src/rqt_bag/src/rqt_bag/tags_file.txt', 'a')
	tags_file.write(textboxValue + '\n')
	tags_file.close()
	if self.rect is not None:
		rectangle = Rectangle()
		rectangle.label = textboxValue
		rectangle.width = self.rect.width()
		rectangle.height = self.rect.height()
		rectangle.x = self.rect.x()
		rectangle.y = self.rect.y()
		self.message.rect.append(rectangle)
	else:
		self.message.globalImageLabel = textboxValue
	self.close()


