# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMViewDialog
                                 A QGIS plugin
 Manages GDAL GNM networks
                             -------------------
        begin                : 2015-02-03
        git sha              : $Format:%H$
        copyright            : (C) 2015 by NextGIS
        email                : gusevmihs@gmail.com
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
#from PyQt4.QtCore import QStringList
#from PyQt4.QtCore import pyqtSlot

from osgeo import ogr
from osgeo import gnm

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gnm_view_dialog_base.ui'))


class GNMViewDialog(QtGui.QDialog, FORM_CLASS):

    network = None
    network_name = ''
    network_format = ''
    
    ok_to_add_network = False
    
    
    def __init__(self, parent=None):
        """Constructor."""
        super(GNMViewDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.tabWidget.setTabText(0,'File or directory')
        self.tabWidget.setTabText(1,'PostGIS database')
        
        self.pushButton_3.clicked.connect(self.OnViewFileDirClicked)
        self.pushButton_4.clicked.connect(self.OnViewPostgisDbClicked)
        self.pushButton_2.clicked.connect(self.OnAddClicked)
        self.textEdit.append('No network selected')
        
        self.pushButton.clicked.connect(self.OnDirDlgClicked)
        
    

    def my_exec_(self,ok_to_add_network):
        self.network = None
        self.network_name = ''
        self.network_format = ''      
        self.ok_to_add_network = ok_to_add_network
        self.pushButton_2.setEnabled(self.ok_to_add_network)
        return self.exec_()
        
         
                       
    def OnDirDlgClicked (self):
        dir_dlg = QtGui.QFileDialog()
        dir_dlg.setFileMode(QtGui.QFileDialog.Directory);
        dir_dlg.show()
        result = dir_dlg.exec_()
        if result:
            strs = dir_dlg.selectedFiles()
            self.lineEdit.setText(strs[0])
    
    
    
    def OnViewFileDirClicked (self):
        # Form the connection string.
        self.network_name = str(self.lineEdit.text())
        # TODO: make another way to determine network format when new formats will be added to GNM.           
        self.network_format = 'Shapefile'
        self.OnView()
    
    def OnViewPostgisDbClicked (self):
        # Form the connection string.
        self.network_name = '---'
        # TODO: make another way to determine network format when new formats will be added to GNM.           
        self.network_format = 'PostGIS'
        self.OnView()
    
    def OnView (self): 
        # Open network.
        if self.network is not None: # We do not close network and relay on garbage collector.
            #gnm.GdalCloseNetwork(self.network) 
            self.network = None
        self.network = gnm.GdalOpenNetwork(self.network_name)
        self.textEdit.clear()
        if self.network is None:
            self.textEdit.append('Error processing selected network')
            self.pushButton_2.setEnabled(False)
        else:
            self.textEdit.append('Network successfully processed!')
            self.textEdit.append('')
            self.textEdit.append('Network info:')
            network_ds = self.network.GetDataset()
            layer_meta = network_ds.GetLayerByName('_gnm_meta')
            layer_meta.ResetReading()
            feat_meta = layer_meta.GetNextFeature()
            while feat_meta is not None:
                str_param_name = feat_meta.GetFieldAsString('param_name')
                str_param_value = feat_meta.GetFieldAsString('param_val')
                self.textEdit.append(str_param_name + ' = ' + str_param_value)
                feat_meta.Destroy()
                feat_meta = layer_meta.GetNextFeature()
            self.pushButton_2.setEnabled(self.ok_to_add_network)       
        
    
    
    
    def OnAddClicked(self):
        self.accept()
        
        
        
           
        
        