# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMLoadDialog
                                 A QGIS plugin
 Manage and analyse networks via GDAL GNM
                             -------------------
        begin                : 2016-07-21
        git sha              : $Format:%H$
        copyright            : (C) 2016 by NextGIS
        email                : info@nextgis.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSlot
from qgis.core import *
from PyQt4.QtCore import Qt
from osgeo import gdal
from osgeo import ogr
from osgeo import gnm


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'load_dialog.ui'))


class GNMLoadDialog(QtGui.QDialog, FORM_CLASS):

    NETWORK_DS = None
    NETWORK_FULLPATH = ''


    def __init__(self, parent=None):
        super(GNMLoadDialog, self).__init__(parent)
        self.setupUi(self)
        self.butFile.clicked.connect(self.onDirSelectClicked)
        self.butRead.clicked.connect(self.onReadClicked)
        self.butLoad.clicked.connect(self.onLoadClicked)
        
        
    def my_exec_(self):
        self.NETWORK_DS = None # we need a deletion of previously created network 
        self.NETWORK_FULLPATH = ''
        self.butLoad.setEnabled(False)
        self.teditMain.clear()  
        self.editFile.setText('')
        return self.exec_()
        
        
    def onDirSelectClicked(self):
        dir_dlg = QtGui.QFileDialog()
        dir_dlg.setFileMode(QtGui.QFileDialog.Directory);
        dir_dlg.show()
        result = dir_dlg.exec_()
        if result:
            strs = dir_dlg.selectedFiles()
            self.editFile.setText(strs[0])

            
    def onReadClicked(self):
        self.teditMain.clear()
        fullpath = self.editFile.text()
        if fullpath == '':
            self.butLoad.setEnabled(False)
            return
        dataset = gdal.OpenEx(str(fullpath))
        network = gnm.CastToNetwork(dataset)
        if network is None:
            self.butLoad.setEnabled(False)
            self.teditMain.append(self.tr(u'Unable to read network at the given path'))
            return
        self.teditMain.append(self.tr(u'Network read successfully!'))
        self.teditMain.append(self.tr(u'Information: '))
        self.teditMain.append(self.tr(u'    Path: ') + fullpath)
        self.teditMain.append(self.tr(u'    GNM version: ') + str(network.GetVersion()))
        #self.teditMain.append(self.tr(u'    Format: ') + )
        self.teditMain.append(self.tr(u'    Name: ') + network.GetName())
        self.teditMain.append(self.tr(u'    Description: ') + network.GetDescription())
        #self.teditMain.append(self.tr(u'    Rules: '))
        self.NETWORK_DS = dataset
        self.NETWORK_FULLPATH = fullpath
        self.butLoad.setEnabled(True)

        
    def onLoadClicked(self):
        self.accept()
    
    
     # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GNMLoadDialog', message)    
    