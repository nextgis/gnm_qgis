# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMCreateDialog
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
from PyQt4.QtCore import pyqtSlot

from qgis.core import *

#from PyQt4.QtGui import QListWidgetItem
from PyQt4.QtCore import Qt

from osgeo import ogr
from osgeo import gnm

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gnm_create_dialog_base.ui'))


class GNMCreateDialog(QtGui.QDialog, FORM_CLASS):

    network = None
    network_path = ''
    network_format = ''
    layer_names_from_project = []


    def __init__(self, parent=None):
        """Constructor."""
        super(GNMCreateDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.pushButton.clicked.connect(self.OnNextClicked)
        self.pushButton_2.clicked.connect(self.OnBackClicked)
        self.comboBox.activated.connect(self.OnFormatSelected)
        self.pushButton_3.clicked.connect(self.OnFormatDirectoryClicked)
        self.pushButton_6.clicked.connect(self.OnLayerEditFileDlgClicked)
        self.pushButton_5.clicked.connect(self.OnAddLayerClicked)
        self.lineEdit_7.textChanged.connect(self.OnLayerEditClicked) # There is no clicked signal so we have to use this one
        self.comboBox_3.activated.connect(self.OnRuleTypeSelected)
        self.comboBox_5.activated.connect(self.OnRuleClassTypeSelected)
        self.comboBox_4.activated.connect(self.OnRuleClassSelected)
        self.pushButton_7.clicked.connect(self.OnAddRule)
        self.pushButton_8.clicked.connect(self.OnCreateNetworkClicked)
        self.pushButton_9.clicked.connect(self.OnOkClicked)
        
        self.label_2.setText(u'Формат сети:')
        self.label_5.setText(u'Каталог:')
        #self.label_6.setText(u'Имя базы данных')
        #self.label_9.setText(u'Пользователь')
        #self.label_8.setText(u'Адрес')
        #self.label_7.setText(u'Пароль')
        self.label_3.setText(u'Система координат:')
        self.label_17.setText(u'Точность привязки при создании топологии:')
        self.label_4.setText(u'Имя сети (не обязательный параметр)')
        self.pushButton.setText(u'Далее >')
        self.pushButton_2.setText(u'< Назад')
        self.label_11.setText(u'Из файловой системы:')
        self.label_10.setText(u'Из открытого проекта:')
        self.label_12.setText(u'Слои для импорта в сеть:')
        self.pushButton_7.setText(u'Сформировать')
        self.label_13.setText(u'Новое правило: ')
        self.comboBox_3.clear()
        self.comboBox_3.addItem(self._temp_makeRusRuleKeyword('CLASS'))
        self.comboBox_3.addItem(self._temp_makeRusRuleKeyword('NETWORK'))
        self.comboBox_5.clear()
        self.comboBox_5.addItem(self._temp_makeRusRuleKeyword('COSTS'))
        self.comboBox_5.addItem(self._temp_makeRusRuleKeyword('INVCOSTS'))
        self.comboBox_5.addItem(self._temp_makeRusRuleKeyword('DIRECTS'))
        self.comboBox_5.addItem(self._temp_makeRusRuleKeyword('BEHAVES'))
        self.comboBox_9.clear()
        self.comboBox_9.addItem(self._temp_makeRusRuleKeyword('CONNECTS'))
        self.label_15.setText(self._temp_makeRusRuleKeyword('WITH'))
        self.label_16.setText(self._temp_makeRusRuleKeyword('VIA'))
        self.comboBox_13.clear()
        self.comboBox_13.addItem(self._temp_makeRusRuleKeyword('EMITTER'))  
        self.comboBox_13.addItem(self._temp_makeRusRuleKeyword('RECEIVER'))
        self.comboBox_13.addItem(self._temp_makeRusRuleKeyword('TRANSMITTER'))
        self.label_14.setText(u'Добавленные правила:')    
        self.pushButton_8.setText(u'Создать сеть')
        self.checkBox.setText(u'Загрузить сеть в проект')
        
        
            
    def _temp_makeRusRuleKeyword(self,word):
        if word == 'CLASS': return u'КЛАСС'
        elif word == u'КЛАСС': return 'CLASS'
        elif word == 'NETWORK': return u'СЕТЬ'
        elif word == u'СЕТЬ': return 'NETWORK'
        elif word == 'COSTS': return u'ВЕСИТ'
        elif word == u'ВЕСИТ': return 'COSTS'
        elif word == 'INVCOSTS': return u'ОБР. ВЕС.'
        elif word == u'ОБР. ВЕС.': return 'INVCOSTS'
        elif word == 'DIRECTS': return u'НАПРАВЛ.'
        elif word == u'НАПРАВЛ.': return 'DIRECTS'
        elif word == 'BEHAVES': return u'ИГРАЕТ РОЛЬ'
        elif word == u'ИГРАЕТ РОЛЬ': return 'BEHAVES'
        elif word == 'CONNECTS': return u'СОЕДИНЯЕТ'
        elif word == u'СОЕДИНЯЕТ': return 'CONNECTS'
        elif word == 'WITH': return u'C'
        elif word == u'C': return 'WITH'
        elif word == 'VIA': return u'ЧЕРЕЗ'
        elif word == u'ЧЕРЕЗ': return 'VIA'
        elif word == 'EMITTER': return u'ИСТОЧНИК'
        elif word == u'ИСТОЧНИК': return 'EMITTER'
        elif word == 'RECEIVER': return u'ПОТРЕБИТЕЛЬ'
        elif word == u'ПОТРЕБИТЕЛЬ': return 'RECEIVER'
        elif word == 'TRANSMITTER': return u'ПЕРЕДАТЧИК'
        elif word == u'ПЕРЕДАТЧИК': return 'TRANSMITTER'
        else: return u''
        
        

        
    # Reset all data in dialog before it actually execs.    
    def my_exec_(self,layers,enable_add_to_project):
        # Clear variables.
        self.network = None
        self.network_path = ''
        self.network_format = ''
        self.layer_names_from_project = []
        # Init gui.
        self.stackedWidget.setCurrentIndex(0)
        self.SetNameForPage()
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(False)
        self.RefreshStep1()
        # Load some constant data to the pages: get Qgs layers from the project.
        self.listWidget.clear() 
        for map_item in layers:
            layer = layers[map_item]
            if layer.type() == QgsMapLayer.VectorLayer:
                geom = layer.dataProvider().geometryType()
                if geom == QGis.WKBPoint or geom == QGis.WKBLineString:
                    list_item = QtGui.QListWidgetItem()
                    list_item.setText(layer.name())
                    # Form the simple array of the layers' field names (of strings), so not to pass the whole map:
                    arr = []
                    if geom == QGis.WKBPoint: # The first one will be geometry type.
                        arr.append('_point') 
                    else: 
                        arr.append('_line') 
                    attrs = layer.dataProvider().fields()
                    for i in range(0,attrs.count()):
                        field = attrs[i]
                        arr.append(field.name())
                    list_item.setData(Qt.UserRole,arr)
                    self.listWidget.addItem(list_item)
        self.listWidget_2.clear()  
        self.comboBox_3.setCurrentIndex(0)
        self.comboBox_5.setCurrentIndex(0)
        self.textEdit.clear()
        self.checkBox.setChecked(enable_add_to_project)
        self.checkBox.setEnabled(enable_add_to_project)
        self.pushButton_9.hide()
        self.pushButton.show()
        self.pushButton_2.show()
        self.progressBar.setValue(0)
        self.textEdit_2.clear()
        return self.exec_()
        
        
        
    def RefreshStep1(self):
        self.stackedWidget_2.setCurrentIndex(0)
        self.comboBox.clear()
        self.comboBox.addItem('ESRI Shapefile')
        self.comboBox.addItem('PostGIS')
        self.comboBox.setCurrentIndex(0)
        self.comboBox_2.clear()
        self.comboBox_2.addItem('WGS 84')
        self.comboBox_2.addItem('WGS 84 Pseudo Mercator')
        self.comboBox_2.setCurrentIndex(0)
        self.lineEdit_2.setText('')
        self.lineEdit_3.setText('')
        self.lineEdit_6.setText('')
        self.lineEdit_4.setText('postgres')
        self.lineEdit_5.setText('127.0.0.1')
        self.lineEdit_10.setText('0.00005')
        self.lineEdit.setText('')
        self.groupBox.setTitle(u'Расположние Shapefile-сети')#('Shapefile network location')

        

    def RefreshStep2(self): 
    # We must not always refresh lists of layers here because we can lose this data during returning back.
        self.listWidget.setCurrentRow(-1)
        self.lineEdit_7.setText('') 
    
    
    
    def RefreshStep3(self):
    # Some parameters depends of data at the previous step (selected layers for import) so we always refresh all combos.
        self.OnRuleTypeSelected(0) # We dont change the fixed combos values but obligatory do this for changeble combos!
        self.OnRuleClassTypeSelected(0)
        self.comboBox_4.clear()
        self.comboBox_10.clear()
        self.comboBox_11.clear()
        self.comboBox_12.clear()
        self.comboBox_12.addItem('<no class>','None')
        count = self.listWidget_2.count()
        # Add selected at the previous step classes, saving its data - available fields - inside items.
        for i in range(0,count):
            layer_name = self.listWidget_2.item(i).text()
            layer_data = self.listWidget_2.item(i).data(Qt.UserRole)
            if layer_name.startswith('[file]'):
                # Get fields from OGR dataset.
                ds = ogr.Open(layer_data)
                if ds is None:
                    continue # Not add to all combos.
                lr = ds.GetLayer(0) # At the previous step we checked exactly 0 layer.
                if lr is None:
                    continue
                dn = lr.GetLayerDefn()
                cn = dn.GetFieldCount()
                farr = []
                gm = lr.GetGeomType()
                if gm == ogr.wkbPoint: # The first one is always geometry type of the layer. 
                    farr.append('_point') 
                else: # We dont check the available types here, but do it somewhere earlier.
                    farr.append('_line') 
                for j in range(0,cn):
                    fd = dn.GetFieldDefn(j)
                    fn = fd.GetNameRef()
                    farr.append(fn)
                self.comboBox_4.addItem(layer_name,farr)
                self.comboBox_10.addItem(layer_name,farr)
                self.comboBox_11.addItem(layer_name,farr)
                self.comboBox_12.addItem(layer_name,farr)
            else:
                # Get fields directly from data, as they were saved during the forming of Qgs layers' initial list.
                self.comboBox_4.addItem(layer_name,layer_data)
                self.comboBox_10.addItem(layer_name,layer_data)
                self.comboBox_11.addItem(layer_name,layer_data)
                self.comboBox_12.addItem(layer_name,layer_data)
        self.OnRuleClassSelected(0) # Refresh fields combos, because the layer combo has been refreshed. 
            

    def RefreshStep4(self):
    # Some data can be changed at previous steps, so we always refresh resulting info.
        self.textEdit_2.clear()
    
        
        
    def OnNextClicked(self):
        cur_page_index = self.stackedWidget.currentIndex()
        max_page_index = self.stackedWidget.count()
        if cur_page_index < (max_page_index - 1):
            self.stackedWidget.setCurrentIndex(cur_page_index + 1)
        if self.stackedWidget.currentIndex() == (max_page_index - 1):
            self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(True)
        self.SetNameForPage()
        # Refresh required page, because if we have returned back before an than click next again, some data can be changed.
        if self.stackedWidget.currentIndex() == 1: 
            self.RefreshStep2()
        if self.stackedWidget.currentIndex() == 2:
            self.RefreshStep3()
        if self.stackedWidget.currentIndex() == 3:
            self.RefreshStep4()    

            
    
    def OnBackClicked(self):
    # If we return back there is no need to refresh page.
        cur_page_index = self.stackedWidget.currentIndex()
        if cur_page_index > 0:
            self.stackedWidget.setCurrentIndex(cur_page_index-1)
        if self.stackedWidget.currentIndex() == 0:
            self.pushButton_2.setEnabled(False)
        self.pushButton.setEnabled(True)
        self.SetNameForPage()
            
        
        
    @pyqtSlot(int)
    def OnFormatSelected(self,index):
        # Shapefile:
        if self.comboBox.currentIndex() == 0:
            self.stackedWidget_2.setCurrentIndex(0)
            self.groupBox.setTitle(u'Расположение Shapefile-сети')#('Shapefile network location')
        # PostGIS:          
        elif self.comboBox.currentIndex() == 1:
            self.stackedWidget_2.setCurrentIndex(1)
            self.groupBox.setTitle(u'Расположение PostGIS-сети')#('PostGIS network location')
            
            
            
    def OnFormatDirectoryClicked(self):
        dir_dlg = QtGui.QFileDialog()
        dir_dlg.setFileMode(QtGui.QFileDialog.Directory);
        dir_dlg.show()
        result = dir_dlg.exec_()
        if result:
            strs = dir_dlg.selectedFiles()
            self.lineEdit_2.setText(strs[0])  


            
    def OnLayerEditFileDlgClicked(self):
        file_dlg = QtGui.QFileDialog()
        file_dlg.setFileMode(QtGui.QFileDialog.ExistingFile);
        file_dlg.show()
        result = file_dlg.exec_()
        if result:
            strs = file_dlg.selectedFiles()
            self.lineEdit_7.setText(strs[0])
            
    # In order to "set focus" to the edit.
    def OnLayerEditClicked(self,string):
        self.listWidget.setCurrentRow(-1)  
        
    def OnAddLayerClicked(self):
        # Add layer from the list of project layers, the layer name must be unique!
        cur_row = self.listWidget.currentRow()
        if (cur_row != -1) and (self.listWidget.count() != 0):
            # Double check if the layer with this name has been already added to the list.
            new_layer_name = self.listWidget.currentItem().text()
            items_found = self.listWidget_2.findItems(new_layer_name,Qt.MatchFixedString) 
            if len(items_found) != 0:
                self.ShowMsgBox(u'Слой с таким именем уже имеется в списке, выберите другой слой')#('There is already layer with this name in the list, please choose another one')
                return  
            new_layer_name_2 = '[file]' + new_layer_name
            items_found = self.listWidget_2.findItems(new_layer_name_2,Qt.MatchFixedString) 
            if len(items_found) != 0:
                self.ShowMsgBox(u'Слой с таким именем уже имеется в списке, выберите другой слой')#('There is already layer with this name in the list, please choose another one')
                return
            item_to_delete = self.listWidget.takeItem(cur_row) # item will be deleted by garbage collector?
            #item = QtGui.QListWidgetItem() 
            #item.setText(new_layer_name) 
            #item.setData(Qt.UserRole,) # Save data: field names.
            #self.listWidget_2.addItem(item) 
            self.listWidget_2.addItem(item_to_delete) # Name and fields will be just copied.
        # Add layer from file, the layer name must be unique!
        else:
            ds = ogr.Open(str(self.lineEdit_7.text()))
            if ds is None:
                self.ShowMsgBox(u'Не удаётся прочитать выбранный файл, выберите другой')#('The layer in the file system can not be processed, please choose another one')
                return
            # TODO: here we take only one layer from one file (like one .shp file)! Add control
            # to select layer from the whole dataset!    
            layer = ds.GetLayer(0)
            if layer is None:
                self.ShowMsgBox(u'Выбранный файл содержит 0 слоёв')#('Selected file contains 0 layers, please choose another one')
                return 
            geom = layer.GetGeomType()
            if not (geom == ogr.wkbLineString or geom == ogr.wkbPoint):
                self.ShowMsgBox(u'Геометрия выбранного слоя должна быть либо линейной, либо точечной. Выберите другой слой')#('Selected layer has neither line nor point geometry, please choose another one')
                return 
            # Double check if the layer with this name has been already added to the list.
            new_layer_name = layer.GetName()
            items_found = self.listWidget_2.findItems(new_layer_name,Qt.MatchFixedString) 
            if len(items_found) != 0:
                self.ShowMsgBox(u'Слой с таким именем уже имеется в списке, выберите другой слой')#('There is already layer with this name in the list, please choose another one')
                return  
            new_layer_name = '[file]' + layer.GetName()
            items_found = self.listWidget_2.findItems(new_layer_name,Qt.MatchFixedString) 
            if len(items_found) != 0:
                self.ShowMsgBox(u'Слой с таким именем уже имеется в списке, выберите другой слой')#('There is already layer with this name in the list, please choose another one')
                return             
            item = QtGui.QListWidgetItem() 
            item.setText(new_layer_name) # Name new layer with '[file]' adding.
            item.setData(Qt.UserRole,self.lineEdit_7.text()) # Save path to the layer.
            self.listWidget_2.addItem(item)
        self.lineEdit_7.setText('')
            
            
            
    @pyqtSlot(int)            
    def OnRuleTypeSelected(self,index):
        # CLASS rule:
        if self.comboBox_3.currentIndex() == 0:
            self.stackedWidget_3.setCurrentIndex(0)
        # NETWORK rule:           
        elif self.comboBox_3.currentIndex() == 1:
            self.stackedWidget_3.setCurrentIndex(1)
    @pyqtSlot(int)
    def OnRuleClassTypeSelected(self,index):
         # COSTS or INVCOSTS:
        if (self.comboBox_5.currentIndex() == 0) or (self.comboBox_5.currentIndex() == 1):
            self.stackedWidget_4.setCurrentIndex(0)
        # DIRECTS:           
        elif self.comboBox_5.currentIndex() == 2:
            self.stackedWidget_4.setCurrentIndex(1) 
        # BEHAVES:            
        elif self.comboBox_5.currentIndex() == 3:
            self.stackedWidget_4.setCurrentIndex(2) 
    # For refreshing field combos:
    @pyqtSlot(int)        
    def OnRuleClassSelected(self,index):
        self.comboBox_7.clear()
        self.comboBox_7.addItem('<no field>')
        self.comboBox_8.clear()
        cur_combo_index = self.comboBox_4.currentIndex()
        if cur_combo_index != -1:
            layer_name = self.comboBox_4.itemText(cur_combo_index)
            layer_fields = self.comboBox_4.itemData(cur_combo_index,Qt.UserRole)
            first_one = False
            for name in layer_fields: # The data is anyway array of strings.
                if not first_one:# The first string is always layer's geometry type.
                    first_one = True
                else:
                    self.comboBox_7.addItem(name)
                    self.comboBox_8.addItem(name)
            
            
            
    def OnAddRule(self):
        if self.comboBox_4.count() == 0 or self.comboBox_10.count() == 0 or self.comboBox_11.count() == 0 or self.comboBox_12.count() == 0 or self.comboBox_8.count() == 0 or self.comboBox_7.count() == 0:
            self.ShowMsgBox(u'Не возможно сформировать правило, т.к. один из списков (слоёв или полей) - пустой')#('Can not make rule becuse one of the lists (for layers or for fields) is void')
            return
        final_rule = ''
        if self.comboBox_3.currentText() == self._temp_makeRusRuleKeyword('CLASS'):
            final_rule = 'CLASS ' + self.MakeRealLayerName(self.comboBox_4.currentText(),self.comboBox_4.itemData(self.comboBox_4.currentIndex())) + ' ' + self._temp_makeRusRuleKeyword(self.comboBox_5.currentText()) + ' '
            if self.comboBox_5.currentText() == self._temp_makeRusRuleKeyword('COSTS') or self.comboBox_5.currentText() == self._temp_makeRusRuleKeyword('INVCOSTS'):
                try:
                    fl_constant = float(str(self.lineEdit_8.text()))
                except ValueError:
                    fl_constant = 0
                if self.comboBox_7.currentText() == '<no field>':
                    final_rule = final_rule + str(fl_constant)
                else:
                    if (self.comboBox_6.currentText() == '+' or self.comboBox_6.currentText() == '-') and fl_constant == 0:
                        final_rule = final_rule + self.comboBox_7.currentText()
                    else:
                        final_rule = final_rule + self.comboBox_7.currentText() + ' ' + self.comboBox_6.currentText() + ' ' + str(fl_constant)
            elif self.comboBox_5.currentText() == self._temp_makeRusRuleKeyword('DIRECTS'):
                final_rule = final_rule + self.comboBox_8.currentText()
            elif self.comboBox_5.currentText() == self._temp_makeRusRuleKeyword('BEHAVES'):
                final_rule = final_rule + self._temp_makeRusRuleKeyword(self.comboBox_13.currentText()) 
        elif self.comboBox_3.currentText() == self._temp_makeRusRuleKeyword('NETWORK'):
            # TODO: replace CONNECTS on other possible values if needed.
            final_rule = 'NETWORK CONNECTS ' + self.MakeRealLayerName(self.comboBox_10.currentText(),self.comboBox_10.itemData(self.comboBox_10.currentIndex())) + ' WITH ' + self.MakeRealLayerName(self.comboBox_11.currentText(),self.comboBox_11.itemData(self.comboBox_11.currentIndex()))
            if self.comboBox_12.currentText() != '<no class>':
                final_rule = final_rule + ' VIA ' + self.MakeRealLayerName(self.comboBox_12.currentText(),self.comboBox_12.itemData(self.comboBox_12.currentIndex()))
        self.textEdit.append(final_rule)
        
    
    
    def SetNameForPage(self):
        if self.stackedWidget.currentIndex() == 0:
            self.label.setText(u'Шаг 1 из 3. Задайте основные параметры сети')#('Step 1 of 3. Define network basic parameters')
        elif self.stackedWidget.currentIndex() == 1:
            self.label.setText(u'Шаг 2 из 3. Выберите слои для импорта')#('Step 2 of 3. Define layers to import to network')            
        elif self.stackedWidget.currentIndex() == 2:
            self.label.setText(u'Шаг 3 и 3. Задайте сетевые правила')#('Step 3 of 3. Define network rules')               
        elif self.stackedWidget.currentIndex() == 3:
            self.label.setText(u'Всё готово к созданию сети')#('Ready to create network')  
            
            
            
    def MakeRealLayerName(self,strr,data):
        if strr.startswith('[file]'):
            strr = strr[len('[file]'):]
        return 'gnm_' + strr + data[0]

        
        
    def ShowMsgBox(self,text):
        msg_box = QtGui.QMessageBox()
        msg_box.setText(text)
        msg_box.setStandardButtons(QtGui.QMessageBox.Ok)
        msg_box.exec_()      
    

    
    def OnCreateNetworkClicked(self):
        self.textEdit_2.clear()
        self.textEdit_2.append(u'Начало создания сети ...')#('Creating network started ...')
        self.textEdit_2.append(' ')
        self.progressBar.setValue(0)
        
        if self.comboBox.currentText() == 'ESRI Shapefile':
            self.network_format = 'Shapefile'
            format = 'ESRI Shapefile'
            self.network_path = str(self.lineEdit_2.text())
        elif self.comboBox.currentText() == 'PostGIS':
            self.network_format = 'PostGIS'
            self.network_path = 'PG:dbname=\'{0}\' host=\'{1}\' port=\'5432\' user=\'{2}\' password=\'{3}\''.format(str(self.lineEdit_3.text()),str(self.lineEdit_5.text()),str(self.lineEdit_4.text()),str(self.lineEdit_6.text()))
            format = 'PostgreSQL'
        else:
            self.textEdit_2.append(u'Не удалось создать сеть: не поддерживается формат {0}'.format(str(self.comboBox.currentText())))#('Error creating network: the network format {0} doesn\'t supported'.format(str(self.comboBox.currentText())))
            self.progressBar.setValue(0)
            return
        self.progressBar.setValue(5)   

        if self.comboBox_2.currentText() == 'WGS84 Pseudo Mercator':
            srs = 'EPSG:3857'
        else:
            srs = 'EPSG:4326'
        # TODO: Form the full list and check incorrect names.
        self.progressBar.setValue(10) 
            
        # TODO: make options with network name!
        self.network = gnm.GdalCreateNetwork(self.network_path, format, srs)#, options)
        if self.network is None:
            #raise Exception("ERROR. Unable to create network!")
            self.textEdit_2.append(u'Не удалось создать сеть: невозможно инициализировать сеть через GDAL. Текущие параметры:')#('Error creating network: unable to init network via GDAL. Current parameters: ')
            self.textEdit_2.append(u'   Формат сети: {0}'.format(format))#('    Format: {0}'.format(format))
            self.textEdit_2.append(u'   Строка подключения (путь): {0}'.format(self.network_path))#('    Connection string: {0}'.format(self.network_path))
            self.textEdit_2.append(u'   Система координат: {0}'.format(srs))#('    Spatial reference system: {0}'.format(srs)) 
            self.textEdit_2.append(u'   Возможная причина: каталог или база данных уже содержит другую сеть')#('Possible reasons: the folder or database already containes some network')
            self.progressBar.setValue(0)
            return
        else:
            self.textEdit_2.append(u'Пустая сеть создана успешно, с параметрами: ')#('Network inited successfully with parameters: ')
            self.textEdit_2.append(u'   Формат сети: {0}'.format(format))#('    Format: {0}'.format(format))
            self.textEdit_2.append(u'   Строка подключения (путь): {0}'.format(self.network_path))#('    Connection string: {0}'.format(self.network_path))
            self.textEdit_2.append(u'   Система координат: {0}'.format(srs))#('    Spatial reference system: {0}'.format(srs))      
        self.progressBar.setValue(20)
        self.textEdit_2.append(' ')
        
        count = self.listWidget_2.count()
        if count == 0:
            self.textEdit_2.append(u'Слои для импорта не были добавлены, импортирование пропускается ...')#('No layers were defined, nothing to be imported ...')
        for i in range(0,count):
            layer_name = str(self.listWidget_2.item(i).text())
            layer_data = str(self.listWidget_2.item(i).data(Qt.UserRole))
            if layer_name.startswith('[file]'): # Import from file DS.
                layer_name = layer_name[len('[file]'):]
                source_ds = ogr.Open(layer_data)
                if source_ds is None:
                    #raise Exception("ERROR. Dataset for import can not be opened")
                    self.textEdit_2.append(u'Предупреждение: невозможно импортировать слой {0} из источника данных {1}'.format(layer_name,layer_data))#('Warning: unable to import layer {0} from Dataset {1}, network will be created without it'.format(layer_name,layer_data))
                else:
                    err = self.network.CopyLayer(source_ds.GetLayer(0),layer_name)
                    if err != 0:
                        self.textEdit_2.append(u'Предупреждение: невозможно импортировать слой {0} из источника данных {1}'.format(layer_name,layer_data))#('Warning: unable to import layer {0} from dataset {1}, network will be created without it'.format(layer_name,layer_data))
                    else:
                        self.textEdit_2.append(u'Слой {0} из источника данных {1} успешно импортирован в сеть'.format(layer_name,layer_data))#('Layer {0} from dataset {1} successfully imported to the network'.format(layer_name,layer_data))       
                    #source_ds.Destroy()   
                    #source_ds = None                 
            else: # Import from the current project.  
                #layer_names_from_project = []
                #for :
                #    layer_names_from_project.append(proj_layer) # Add only that layers which were actually imported.
                pass
        self.progressBar.setValue(50)
        self.textEdit_2.append(' ')
        
        all_rule_text = self.textEdit.toPlainText()
        rule_strings = all_rule_text.split("\n");
        if len(rule_strings) == 0:
            self.textEdit_2.append(u'Правила сети не были заданы, этап создания правил пропускается ...')#('No rules were defined, nothing to be cretaed ...')
        for rule_str in rule_strings:
            err = self.network.CreateRule(str(rule_str))
            if err != 0:
                self.textEdit_2.append(u'Предупреждение: невозможно создать правило \'{0}\''.format(str(rule_str)))#('Warning: unable to create rule \'{0}\', network will be created without it'.format(str(rule_str)))
            else:
                self.textEdit_2.append(u'Правило {0} создано успешно'.format(str(rule_str)))#('Rule {0} created successfully'.format(str(rule_str)))
        self.progressBar.setValue(65)
        self.textEdit_2.append(' ')
        
        try:
            snap = float(str(self.lineEdit_10.text()))
        except ValueError:
            snap = 0
        if snap < 0:
            self.textEdit_2.append(u'Предупреждение: параметр точность привязки, равный \'{0}\' задан некорректно. Будет использовано значение по умолчанию'.format(str(lineEdit_10.text())))#('Warning: the snapping tolerance = {0} is set incorrectly, the default will be used'.format(str(lineEdit_10.text())))
            snap = 0
        self.textEdit_2.append(u'Точность привязки = {0}'.format(snap))#('Snapping tolerance = {0}'.format(snap))
        self.textEdit_2.append(u'Начало создания топологии (связности) сети ...')#('Start creating topology ...')
        self.textEdit_2.repaint() # Or the long procedure of building topology will not allow the text appears in widget immidiatly.
        network_ds = self.network.GetDataset()
        layers = ()
        for i in range(network_ds.GetLayerCount()): # Connect all layers in network.
            layers = layers + (network_ds.GetLayer(i),)
        err = self.network.AutoConnect(layers,snap)
        if err != 0:
            self.textEdit_2.append(u'Не удалось создать связность в сети. Возможная причина: для автоматического соединения объектов сети необходим как минимум 1 линейный и 1 точечный слой')#('Error creating network: unable to connect layers')
            self.progressBar.setValue(0)
            return
        self.textEdit_2.append(u'Связность в сети создана успешно')#('Layers connected successfully') 
        
        network_ds.FlushCache() # Otherwise don't write the last feature of each layer to the disk.

        self.progressBar.setValue(100)        
        self.textEdit_2.append(' ') 
        self.textEdit_2.append('===========================================================') 
        self.textEdit_2.append(' ') 
        self.textEdit_2.append(u'Сеть успешно создана в {0} !'.format(self.network_path))#('Congratulations! Network successfully created at {0}'.format(self.network_path))
        
        self.pushButton_9.show()
        self.pushButton.hide()
        self.pushButton_2.hide()
        
        
        
        
    def OnOkClicked(self):
        # Add or not add network to project.
        if self.checkBox.isChecked():
            self.accept()
        else:
            self.reject()
        
        
        
        
        
        
        
        
        
        
        