# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMCreateDialog
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

import _gnm_check
GNM_FOUND = _gnm_check.haveGnm()
if GNM_FOUND:
    from osgeo import gnm
from osgeo import gdal
from osgeo import ogr

import os
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSlot
from qgis.core import *
from PyQt4.QtGui import QIcon
from PyQt4.QtCore import Qt


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'create_dialog.ui'))


class GNMCreateDialog(QtGui.QDialog, FORM_CLASS):

    GNM_CONST_FILEFORMAT = u'GNMFile'
    GNM_CONST_OPT_SRS = u'net_srs'
    GNM_CONST_OPT_NAME = u'net_name'
    GNM_CONST_OPT_DESCR = u'net_description'
    
    NETWORK_DS = None # the main variable which will be taken from the dialog after its successful work
    NETWORK_FULLPATH = ''
    
    def __init__(self, plugindir, parent=None):
        """ Constructor.
        """
        super(GNMCreateDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.butBack.clicked.connect(self.onBackClicked)
        self.butNext.clicked.connect(self.onNextClicked)
        self.butFileParams.clicked.connect(self.onSavingPathClicked_shape)
        self.butAddLayers.clicked.connect(self.onAddLayersClicked)
        self.butRemoveLayer.clicked.connect(self.onRemoveLayerClicked)
        self.butCreate.clicked.connect(self.onCreateClicked)
        self.butOk.clicked.connect(self.onOkClicked)
        
        self.butAddLayers.setIcon(QIcon(plugindir+'/icons/plus.png'))
        self.butRemoveLayer.setIcon(QIcon(plugindir+'/icons/minus.png'))
        
        
    def my_exec_(self):
        """Reset all data in dialog before it actually execs"""
        self.NETWORK_DS = None # we need a deletion of previously created network
        self.NETWORK_FULLPATH = ''
        self.swMain.setCurrentIndex(0)
        self.setCurrentPageName()
        self.setParamsGroupText()
        self.refreshPage1()
        self.refreshPage2()
        self.refreshPage3()
        self.refreshPage4()
        self.butOk.hide()
        self.butNext.setEnabled(True)
        self.butBack.setEnabled(False)
# TODO: remove setReadOnly() when rules will be fully enabled in GNM        
        self.teditRules.setReadOnly(True)
        return self.exec_()
        
        
#******************************************************************************************#
#                                                                                          #
#                                    GUI SLOTS                                             #
#                                                                                          #
#******************************************************************************************#    

    def onNextClicked(self):
        cur_page_index = self.swMain.currentIndex()
        max_page_index = self.swMain.count()
        if cur_page_index < (max_page_index - 1):
            self.swMain.setCurrentIndex(cur_page_index + 1)
        if self.swMain.currentIndex() == (max_page_index - 1):
            self.butNext.setEnabled(False)
        self.butBack.setEnabled(True)
        self.setCurrentPageName()
        # Refresh required page, because if we have returned back before an than click next again, some data can be changed.
        if self.swMain.currentIndex() == 1: 
            self.refreshPage2()
        if self.swMain.currentIndex() == 2:
            self.refreshPage3()
        if self.swMain.currentIndex() == 3:
            self.refreshPage4()    

    def onBackClicked(self):
        # If we return back there is no need to refresh page.
        cur_page_index = self.swMain.currentIndex()
        if cur_page_index > 0:
            self.swMain.setCurrentIndex(cur_page_index-1)
        if self.swMain.currentIndex() == 0:
            self.butBack.setEnabled(False)
        self.butNext.setEnabled(True)
        self.setCurrentPageName()
        
        
    def onSavingPathClicked_shape(self):        
        dir_dlg = QtGui.QFileDialog()
        dir_dlg.setFileMode(QtGui.QFileDialog.Directory);
        dir_dlg.show()
        result = dir_dlg.exec_()
        if result:
            strs = dir_dlg.selectedFiles()
            self.editFileParams.setText(strs[0]) 
       
       
    def onAddLayersClicked(self):
        file_dlg = QtGui.QFileDialog()
        file_dlg.setFileMode(QtGui.QFileDialog.ExistingFiles);
        file_dlg.show()
        result = file_dlg.exec_()
        if result:
            strs = file_dlg.selectedFiles()
            for str in strs:
                list = self.listLayers.findItems(str, Qt.MatchFixedString) # do not allow adding same layers
                if len(list) == 0:
                    self.listLayers.addItem(str)
    
    
    def onRemoveLayerClicked(self):
        if self.listLayers.currentRow() < 0:
            return
        self.listLayers.takeItem(self.listLayers.currentRow()) # note: no manual deletion of returned item!
        
        
    def onCreateClicked(self):
        #gdal.SetConfigOption('CPL_DEBUG','ON');
        #gdal.SetConfigOption('CPL_LOG','D:/nextgis/gnmmanager/gdal_log.txt');
        #gdal.SetConfigOption('CPL_LOG_ERRORS','ON');

        # Start creating network.
        self.butCreate.setEnabled(False)
        self.msg(self.tr(u'Starting network creation...'))
        self.progress(0)
        
        # Obtain network parameters from the dialog.
# TODO: replace it with real saving params via according group of widgets:
        path = self.editFileParams.text()
# TODO: replace it with real format selection via combobox:
        format = self.comboFormat.currentText()
        gnm_format = self.GNM_CONST_FILEFORMAT 
        srs = self.comboSrs.currentText()
        name = self.editName.text()
        descr = self.editDescr.text()
        if self.isStrVoid(path):
            self.msgErr(self.tr(u'The network\'s saving path is set incorrectly!'))
            self.progress(0)
            return
        if self.isStrVoid(name):
            self.msgErr(self.tr(u'The network\'s name is set incorrectly!'))
            self.progress(0)
            return              
        options = []
        self.addOption(options,self.GNM_CONST_OPT_NAME,name)
        self.addOption(options,self.GNM_CONST_OPT_DESCR,descr)
        self.addOption(options,self.GNM_CONST_OPT_SRS,self.getSrsKeyname(srs))
        layer_other_paths = []
        layer_names = []
        cnt = self.listLayers.count()
        if cnt == 0:
            self.msgWarn(self.tr(u'No layers were defined for import. The network will be void!'))
        for i in range(0,cnt):
            #layer_other_name = str(self.listLayers.item(i).text())
            #layer_other_data = str(self.listLayers.item(i).data(Qt.UserRole))
            layer_other_paths.append(self.listLayers.item(i).text())
        try:
            tolerance = float(str(self.editTolerance.text()))
        except ValueError:
            tolerance = 0
        if tolerance < 0:
            self.msgWarn(self.tr(u'Tolerance for layers connection was set incorrectly [ = ')
                +self.editTolerance.text()+u']. '
                +self.tr(u'The default value [ = 0] will be used!'))
            tolerance = 0
        self.progress(5)
        
        # Initialize network via creation.
        self.msg(u'')
        self.msg(self.tr(u'Creating network dataset...'))
        self.msg(self.tr(u'Format: ')+format)
        self.msg(self.tr(u'Path: ')+path)
        self.msg(self.tr(u'SRS: ')+srs)
        driver = gdal.GetDriverByName(str(gnm_format))
        if driver is None:
            self.msgErr(self.tr(u'Unable to initialize network driver via GDAL'))
            self.progress(0)
            return
        dataset = driver.Create(str(path), 0, 0, 0, gdal.GDT_Unknown, options)
        network = gnm.CastToNetwork(dataset) 
        if network is None:
            self.msgErr(self.tr(u'Unable to initialize network dataset via GDAL'))
            self.progress(0)
            return
        gen_network = gnm.CastToGenericNetwork(dataset)  
        if gen_network is None:
            self.msgErr(self.tr(u'Unable to initialize (generic) network dataset via GDAL'))
            self.progress(0)
            return
        self.msg(self.tr(u'...done'))
        self.progress(20)
        
        # Fill network with layers.
        self.msg(u'')
        has_point_layer = False
        has_line_layer = False
        for layer_other_path in layer_other_paths:
            self.msg(self.tr(u'Importing layer: ')+layer_other_path)
            dataset_other = gdal.OpenEx(str(layer_other_path), gdal.OF_VECTOR)
            if dataset_other is None:
                self.msgErr(self.tr(u'Failed to open side dataset'))
                self.progress(0)
                return
            layer_other = dataset_other.GetLayerByIndex(0)
            if layer_other is None:
                self.msgErr(self.tr(u'Failed to fetch layer in a side dataset'))
                self.progress(0)
                return
            layer_name_other = layer_other.GetName()
            layer = network.CopyLayer(layer_other, layer_name_other)
            if layer is None:
                self.msgErr(self.tr(u'Failed to import layer to the network'))
                return
            layer_geom = layer.GetGeomType()
            if layer_geom == ogr.wkbPoint:
                has_point_layer = True
            elif layer_geom == ogr.wkbLineString:
                has_line_layer = True
            layer_names.append(layer.GetName())
            dataset_other = None
# TODO: we do not need such checks if there is some other algorithm of automatic topology creation:            
        if not has_point_layer:
            self.msgWarn(self.tr(u'No layer with point geometry was imported. ' 
                'At least one required to properly build network\'s topology'))
        if not has_line_layer:
            self.msgWarn(self.tr(u'No layer with line geometry was imported. ' 
                'At least one required to properly build network\'s topology'))    
        self.msg(self.tr(u'...done'))
        self.progress(55)
        
        # Establish network connectivity.
        self.msg(u'')
        self.msg(self.tr(u'Creating network\'s topology...'))
# TODO: get weights for the graph edges from the layer's fields via ChangeEdge method:       
        err = gen_network.ConnectPointsByLines(layer_names, tolerance, 1, 1, gnm.GNM_EDGE_DIR_BOTH)
        if err != 0:
            self.msgWarn(self.tr(u'Failed to create topology. Features in the network will be unconnected'))
        self.msg(self.tr(u'...done'))
        self.progress(85)
        
        # Close network for successfull saving all data.
        gen_network = None
        network = None
        dataset = None
        
        # Open network for further returning it outside the dialog.
        net_fullpath = path + '/' + name
        dataset = gdal.OpenEx(net_fullpath)
        network = gnm.CastToNetwork(dataset)
        if network is None:
            self.msgErr(self.tr(u'Network created successfully but it is not able to open it'))
            return        
        self.NETWORK_DS = dataset
        self.NETWORK_FULLPATH = net_fullpath
        self.butBack.setEnabled(False) # no way to return back
        self.butOk.show()
        self.msg(u'')
        self.msg(self.tr(u'Network was successfully created!'))
        self.progress(99)

    
    def onOkClicked(self):
        if self.checkLoad.isChecked():
            self.accept()
        else:
            self.reject()
    

#******************************************************************************************#
#                                                                                          #
#                                     OTHER METHODS                                        #
#                                                                                          #
#******************************************************************************************# 

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
        return QCoreApplication.translate('GNMCreateDialog', message)  
        
        
    def getSrsKeyname(self, str):
        if str == u'WGS 84':
            return u'EPSG:4326'
        elif str == u'WGS 84: Pseudo mercator':
            return u'EPSG:3857'
        else:
            return ''
            
            
    def isStrVoid(self, str):
# TODO: make correct function to check string's voidness
        if str == '':
            return True
        return False


    def addOption(self, options, key, value):
        if len(value) != 0:
            options.append(str(key)+'='+str(value)) # this will change passed array

        
    def refreshPage1(self):
        self.comboFormat.setCurrentIndex(0)
        self.editFileParams.setText('')
        self.comboSrs.setCurrentIndex(0)
        self.editName.setText(u'my_network') # TEMP
        self.editDescr.setText('')
        

    def refreshPage2(self): 
        self.listLayers.clear()
        self.editTolerance.setText(u'0.00005') # TEMP
        
    
    def refreshPage3(self):
        self.teditRules.clear()
# TODO: get network rules in a correct way:       
        self.teditRules.append(u'ALLOW CONNECTS ANY')
        
 
    def refreshPage4(self):
        self.teditCreate.clear()
        self.butCreate.setEnabled(True)
        self.butOk.hide()
    
  
    def setCurrentPageName(self):
        if self.swMain.currentIndex() == 0:
            self.labMain.setText(self.tr(u'Step 1 of 3. Initial parameters'))
        elif self.swMain.currentIndex() == 1:
            self.labMain.setText(self.tr(u'Step 2 of 3. Layers to connect'))            
        elif self.swMain.currentIndex() == 2:
            self.labMain.setText(self.tr(u'Step 3 of 3. Additional rules'))               
        else:
            self.labMain.setText(self.tr(u'Ready to create network')) 

       
    def setParamsGroupText(self):
# TODO: make real selection of this groupbox title depending on network's format.
        self.groupParams.setTitle(self.tr(u'Saving path'))


    def msg(self, text):
        self.teditCreate.append(text)
        
    def msgWarn(self, text):
        self.msg(self.tr(u'[WARNING] ')+text)
    
    def msgErr(self, text):
        self.msg(u'')
        self.msg(self.tr(u'[ERROR] ')+text)
        self.msg(self.tr(u'Creation cancelled'))

        
    def progress(self, val):
        self.progressCreate.setValue(val)
    
       
