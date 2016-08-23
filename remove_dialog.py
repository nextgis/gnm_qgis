# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMRemoveDialog
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


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'remove_dialog.ui'))


class GNMRemoveDialog(QtGui.QDialog, FORM_CLASS):

    FULLY_DELETE = False

    
    def __init__(self, parent=None):
        super(GNMRemoveDialog, self).__init__(parent)
        self.setupUi(self)
        self.checkDelete.clicked.connect(self.onCheckDeleteClicked)
        self.butOk.clicked.connect(self.onOkClicked)
        self.butCancel.clicked.connect(self.onCancelClicked)

        
    def my_exec_(self):
        self.FULLY_DELETE = False
        self.labDelete.setText('')
        return self.exec_()


    def onCheckDeleteClicked(self):
        if self.checkDelete.isChecked():
            self.labDelete.setText(self.tr(u'WARNING. All network data will be fully deleted from disk!'))
            self.FULLY_DELETE = True
        else:
            self.labDelete.setText('')
            self.FULLY_DELETE = False
        
        
    def onCancelClicked(self):
        self.reject()
        
    def onOkClicked(self):
        self.accept()
        
        
        