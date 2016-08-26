# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QNetwork
                                 A QGIS plugin
 Manage and analyse networks via GDAL
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

from PyQt4 import QtGui
#from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
#from PyQt4.QtGui import QAction, QIcon, QMenu, QMessageBox, QColor, QToolButton
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from create_dialog import GNMCreateDialog
from load_dialog import GNMLoadDialog
from remove_dialog import GNMRemoveDialog
import os.path
from qgis.core import *
import qgis.utils
from _gnm_feature_tool import IdentifyGeometry


class GNMManager:
    """Plugin's entry point"""
    
    action_create_network = None
    action_load_network = None
    action_remove_network = None
    action_analyse_network = None
    action_start_flag = None
    action_end_flag = None
    action_block_flags = None
    action_remove_flags = None
    action_path = None
    action_paths = None
    action_connectivity = None
    
    map_tool = None
    
    toolbutton_start_flag = None
    toolbutton_end_flag = None
    toolbutton_block_flags = None
    toolbutton_remove_flags = None
    toolbutton_path = None
    toolbutton_paths = None
    toolbutton_connectivity = None    
    
    LAYERS_DATA = [] # only these layers can be used to set flags for analysis
    LAYER_STARTFLAG = None
    LAYER_ENDFLAG = None
    LAYER_BLOCKFLAGS = None
    LAYER_RESULT_PATH = None
    LAYERS_RESULT_PATHS = []
    LAYER_RESULT_CONNECTIVITY = None
      
    PRESSED_TOOLB = None
    PRESSED_ICON = None # to store the icon for button before pressing   

    GNM_CONST_GFIDFIELD = 'gnm_fid'
    GNM_CONST_PATHNUMFIELD = 'path_num'
    
# TODO: here will be an array of networks.  
    NETWORK_DS = None
    NETWORK_FULLPATH = ''
    NETWORK_NAME = ''
    
    GFID_STARTFLAG = -1
    GFID_ENDFLAG = -1
    GFIDS_BLOCKFLAGS = []
    
    GNM_SETTING_K = 5
    

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GNMManager_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialogs (after translation) and keep reference
        self.dlg_create = GNMCreateDialog(self.plugin_dir)
        self.dlg_load = GNMLoadDialog()
        self.dlg_remove = GNMRemoveDialog()

        # Declare instance attributes
        self.actions = []
        self.toolbuttons = []
        self.menu = self.tr(u'&QNetwork')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QNetwork')
        self.toolbar.setObjectName(u'QNetwork')

        
    def add_action(
        self,
        menu, # to which sub menu add this action. If None action is added to the root via addPluginToMenu()
        icon_path,
        text,
        callback = None,
        enabled_flag = True,
        status_tip = None,
        whats_this = None,
        add_to_toolbar = False,
        parent = None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        toolbutton = QToolButton()
        toolbutton.setIcon(icon)
        
        if callback is not None:
            action.triggered.connect(callback)
            toolbutton.clicked.connect(callback)
            
        action.setEnabled(enabled_flag)
        toolbutton.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
            toolbutton.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
            toolbutton.setWhatsThis(whats_this)
            
        if menu is None:
            self.iface.addPluginToMenu(self.menu, action)
        else:
            menu.addAction(action)  
        self.actions.append(action)
        
        if add_to_toolbar:
            #self.toolbar.addAction(action)   
            self.toolbar.addWidget(toolbutton) # otherwise it is not able to get the toolbutton from toolbar
            self.toolbuttons.append(toolbutton)
        else:
            toolbutton = None
            
        return action, toolbutton

        
    def initGui(self):
        self.action_create_network, stub = self.add_action(
            menu=None,
            icon_path=None,
            text=self.tr(u'Create network'),
            callback=self.onCreateNetworkClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=True)
        self.action_load_network, stub = self.add_action(
            menu=None,
            icon_path=None,
            text=self.tr(u'Load network'),
            callback=self.onLoadNetworkClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=True)
        self.action_remove_network, stub = self.add_action(        
            menu=None,
            icon_path=None,
            text=self.tr(u'Remove network'),
            callback=self.onRemoveNetworkClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False)
        self.action_analyse_network, stub = self.add_action(       
            menu=None,
            icon_path=None,
            text=self.tr(u'Analyse network'),
            callback=None,
            parent=self.iface.mainWindow(),
            enabled_flag=False) 
        menu_analysis = QMenu('menu')
        self.action_analyse_network.setMenu(menu_analysis)
        
        self.action_start_flag, self.toolbutton_start_flag = self.add_action(        
            menu=menu_analysis,
            icon_path=self.plugin_dir+'/icons/start.png',
            text=self.tr(u'Set start flag'),
            callback=self.onStartFlagClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            status_tip=self.tr(u'Mark feature as start node'),
            add_to_toolbar = True)
        self.action_end_flag, self.toolbutton_end_flag = self.add_action(        
            menu=menu_analysis,
            icon_path=self.plugin_dir+'/icons/end.png',
            text=self.tr(u'Set end flag'),
            callback=self.onEndFlagClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            status_tip=self.tr(u'Mark feature as end node'),
            add_to_toolbar = True)          
        self.action_block_flags, self.toolbutton_block_flags = self.add_action(       
            menu=menu_analysis,
            icon_path=self.plugin_dir+'/icons/block.png',
            text=self.tr(u'Set block flags'),            
            callback=self.onBlockFlagClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            status_tip=self.tr(u'Mark features as blocked nodes'),
            add_to_toolbar = True)            
        self.action_remove_flags, self.toolbutton_remove_flags = self.add_action(       
            menu=menu_analysis,
            icon_path=self.plugin_dir+'/icons/remove_all.png',
            text=self.tr(u'Remove all flags'),
            callback=self.onRemoveFlagsClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            status_tip=self.tr(u'Remove all flags: start, end and block'),
            add_to_toolbar = True) 
        self.action_path, self.toolbutton_path = self.add_action(       
            menu=menu_analysis,
            icon_path=self.plugin_dir+'/icons/path.png',
            text=self.tr(u'Calculate shortest path'),
            callback=self.onPathClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            status_tip=self.tr(u'Calculate the shortest path between start and end nodes'),
            add_to_toolbar = True)
        self.action_paths, self.toolbutton_paths = self.add_action(        
            menu=menu_analysis,
            icon_path=self.plugin_dir+'/icons/paths.png',
            text=self.tr(u'Calculate ' + str(self.GNM_SETTING_K) + ' shortest paths'),          
            callback=self.onPathsClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            status_tip=self.tr(u'Calculate ' + str(self.GNM_SETTING_K) + ' shortest paths between start and end nodes'),
            add_to_toolbar = True)
        self.action_connectivity, self.toolbutton_connectivity = self.add_action(       
            menu=menu_analysis,
            icon_path=self.plugin_dir+'/icons/connectivity.png',
            text=self.tr(u'Calculate connectivity'),
            callback=self.onConnectivityClicked,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            status_tip=self.tr(u'Calculate the tree from start node to all connected nodes'),
            add_to_toolbar = True)
            
        # Initialize map tool.
        self.map_tool = IdentifyGeometry(self.iface.mapCanvas())
        QObject.connect(self.map_tool , SIGNAL("geomIdentified") , self.onIdentifyFeature)
        
        # Block all GUI if gnm module is not found in QGIS:
        if GNM_FOUND == False:
            self.action_create_network.setEnabled(False)
            self.action_load_network.setEnabled(False)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QNetwork'),
                action)
            #self.iface.removeToolBarIcon(action)
        del self.toolbar
        self.removeGnmLayersGroup()
        self.NETWORK_DS = None

        
#******************************************************************************************#
#                                                                                          #
#                                    GUI SLOTS                                             #
#                                                                                          #
#******************************************************************************************# 
        
    def onCreateNetworkClicked(self):
        self.dlg_create.show()
        result = self.dlg_create.my_exec_()
        if result == 1:
            self.NETWORK_DS = self.dlg_create.NETWORK_DS
            self.NETWORK_FULLPATH = self.dlg_create.NETWORK_FULLPATH
            self.createGnmLayersGroup()
            self.enableMenusForNetwork(True)
            self.updateLayersToSearchForFlags()
        
        
    def onLoadNetworkClicked(self):
        self.dlg_load.show() 
        result = self.dlg_load.my_exec_()
        if result == 1:
            self.NETWORK_DS = self.dlg_load.NETWORK_DS
            self.NETWORK_FULLPATH = self.dlg_load.NETWORK_FULLPATH
            self.createGnmLayersGroup()
            self.enableMenusForNetwork(True)
            self.updateLayersToSearchForFlags()
        
        
    def onRemoveNetworkClicked(self):
        #gdal.SetConfigOption('CPL_DEBUG','ON')
        #gdal.SetConfigOption('CPL_LOG','D:/nextgis/gnmmanager/gdal_log.txt')
        #gdal.SetConfigOption('CPL_LOG_ERRORS','ON')
        self.dlg_remove.show() 
        result = self.dlg_remove.my_exec_()
        if result == 1:
            self.NETWORK_DS = None
            ok_to_del = self.dlg_remove.FULLY_DELETE
            if ok_to_del:
# TODO: really pass here the selected GNM format:           
                gdal.GetDriverByName('GNMFile').Delete(str(self.NETWORK_FULLPATH))
            self.clickFlagButton(self.PRESSED_TOOLB,None) # unpress any pressed flag button and unset map tool
            self.removeGnmLayersGroup()
            self.enableMenusForNetwork(False)
            self.updateLayersToSearchForFlags()                
            self.NETWORK_FULLPATH = ''
            self.NETWORK_NAME = ''
            self.GFID_STARTFLAG = -1
            self.GFID_ENDFLAG = -1
            self.GFIDS_BLOCKFLAGS = []

        
    def onStartFlagClicked(self):
        self.clickFlagButton(self.toolbutton_start_flag,QIcon(self.plugin_dir+'/icons/start_pressed.png'))
        
    def onEndFlagClicked(self):
        self.clickFlagButton(self.toolbutton_end_flag,QIcon(self.plugin_dir+'/icons/end_pressed.png'))
        
    def onBlockFlagClicked(self):
        self.clickFlagButton(self.toolbutton_block_flags,QIcon(self.plugin_dir+'/icons/block_pressed.png'))
        
        
    def onRemoveFlagsClicked(self):
        ids = [f.id() for f in self.LAYER_STARTFLAG.getFeatures()]
        self.LAYER_STARTFLAG.dataProvider().deleteFeatures(ids)  
        self.LAYER_STARTFLAG.triggerRepaint()   
        self.GFID_STARTFLAG = -1          
        ids = [f.id() for f in self.LAYER_ENDFLAG.getFeatures()]
        self.LAYER_ENDFLAG.dataProvider().deleteFeatures(ids)
        self.LAYER_ENDFLAG.triggerRepaint()
        self.GFID_ENDFLAG = -1
        ids = [f.id() for f in self.LAYER_BLOCKFLAGS.getFeatures()]
        self.LAYER_BLOCKFLAGS.dataProvider().deleteFeatures(ids)
        self.LAYER_BLOCKFLAGS.triggerRepaint()  
        self.GFIDS_BLOCKFLAGS = []


    def onPathClicked(self):
        if self.NETWORK_DS is None:
            return
        network = gnm.CastToGenericNetwork(self.NETWORK_DS)
        if network is None:
            return
        if self.GFID_STARTFLAG == -1:
            self.showMsg(self.tr(u'The start point has not been set! Set it before any calculations'))
            return           
        if self.GFID_ENDFLAG == -1:
            self.showMsg(self.tr(u'The end point has not been set! Set it before calculating shortest path'))
            return
        for bl_gfid in self.GFIDS_BLOCKFLAGS: # block required features
            network.ChangeBlockState(bl_gfid, True)
        res_layer = network.GetPath(self.GFID_STARTFLAG, self.GFID_ENDFLAG, gnm.GATDijkstraShortestPath)
        if res_layer is None:
            self.showMsg(self.tr(u'Unable to calculate shortest path! Some error occured'))
        elif res_layer.GetFeatureCount() == 0:
            self.showMsg(self.tr(u'There is no path between start and end points!'))  
            network.ReleaseResultSet(res_layer)
        else:    
            self.updateResultLayer(res_layer,self.LAYER_RESULT_PATH) # copy features to qgis layer
            network.ReleaseResultSet(res_layer)
        for bl_gfid in self.GFIDS_BLOCKFLAGS: # unblock previously blocked features (anyway!)
            network.ChangeBlockState(bl_gfid, False)
        
    def onPathsClicked(self):
        if self.NETWORK_DS is None:
            return
        network = gnm.CastToGenericNetwork(self.NETWORK_DS)
        if network is None:
            return
        if self.GFID_STARTFLAG == -1:
            self.showMsg(self.tr(u'The start point has not been set! Set it before any calculations'))
            return           
        if self.GFID_ENDFLAG == -1:
            self.showMsg(self.tr(u'The end point has not been set! Set it before calculating shortest paths'))
            return
        for bl_gfid in self.GFIDS_BLOCKFLAGS: 
            network.ChangeBlockState(bl_gfid, True)
        options = []
        options.append('num_paths=' + str(self.GNM_SETTING_K))
        res_layer = network.GetPath(self.GFID_STARTFLAG, self.GFID_ENDFLAG, gnm.GATKShortestPath, options)
        if res_layer is None:
            self.showMsg(self.tr(u'Unable to calculate shortest path! Some error occured'))
        elif res_layer.GetFeatureCount() == 0:
            self.showMsg(self.tr(u'There is no path between start and end points!'))  
            network.ReleaseResultSet(res_layer)
        else:    
            self.updateResultLayers(res_layer,self.LAYERS_RESULT_PATHS) 
            network.ReleaseResultSet(res_layer)
        for bl_gfid in self.GFIDS_BLOCKFLAGS: 
            network.ChangeBlockState(bl_gfid, False)
        
    def onConnectivityClicked(self):
        if self.NETWORK_DS is None:
            return
        network = gnm.CastToGenericNetwork(self.NETWORK_DS)
        if network is None:
            return
        if self.GFID_STARTFLAG == -1:
            self.showMsg(self.tr(u'The start point has not been set! Set it before any calculations'))
            return
        for bl_gfid in self.GFIDS_BLOCKFLAGS: 
            network.ChangeBlockState(bl_gfid, True)
        res_layer = network.GetPath(self.GFID_STARTFLAG, -1, gnm.GATConnectedComponents)
        if res_layer is None:
            self.showMsg(self.tr(u'Unable to calculate shortest path! Some error occured'))
        elif res_layer.GetFeatureCount() == 0:
            self.showMsg(self.tr(u'The start feature has no connections to other features!'))   
            network.ReleaseResultSet(res_layer)
        else:    
            self.updateResultLayer(res_layer,self.LAYER_RESULT_CONNECTIVITY) 
            network.ReleaseResultSet(res_layer)
        for bl_gfid in self.GFIDS_BLOCKFLAGS:
            network.ChangeBlockState(bl_gfid, False)


    def onIdentifyFeature(self,layer,feature):
        if self.PRESSED_TOOLB is None: # skip any actions if no flag button pressed
            return
        features = [] # TEMPORARY. For future several features can be passed here.
        features.append(feature)
        self.createFlags(features)
        self.clickFlagButton(self.PRESSED_TOOLB,None) # unpress any pressed flag button and unset map tool     
        

#******************************************************************************************#
#                                                                                          #
#                                       METHODS                                            #
#                                                                                          #
#******************************************************************************************#

    def enableMenusForNetwork(self, enable):
        for action in self.actions:
            action.setEnabled(enable)
        for toolbutton in self.toolbuttons:
            toolbutton.setEnabled(enable)
        self.action_create_network.setEnabled(not enable)
        self.action_load_network.setEnabled(not enable)
             
        
    def createGnmLayersGroup (self):
        """Create special set of layers for the QGIS GNM"""
        dataset = self.NETWORK_DS
        network = gnm.CastToGenericNetwork(self.NETWORK_DS)
        if network is None:
            self.showMsgBox(self.tr(u'Error working with network'))
            return False
        network_fullpath = self.NETWORK_FULLPATH
        self.NETWORK_NAME = network.GetName()
        network_srs = network.GetProjectionRef()
        
        # 0. Create root group.
        root_layer_tree = QgsProject.instance().layerTreeRoot()
        common_group = root_layer_tree.addGroup(self.NETWORK_NAME)
        
        # 1. Create flag layers.
        flags_group = common_group.addGroup('Flags')
        self.LAYER_STARTFLAG = self.createFlagsLayer(flags_group,'_flag_start',self.plugin_dir+'/styles/start_flag.svg',network_srs)
        if self.LAYER_STARTFLAG is None:
            self.showWarn(self.tr(u'Unable to create start flag\'s layer'))
        self.LAYER_ENDFLAG = self.createFlagsLayer(flags_group,'_flag_end',self.plugin_dir+'/styles/end_flag.svg',network_srs)
        if self.LAYER_ENDFLAG is None:
            self.showWarn(self.tr(u'Unable to create end flag\'s layer'))
        self.LAYER_BLOCKFLAGS = self.createFlagsLayer(flags_group,'_flags_block',self.plugin_dir+'/styles/block_flag.svg',network_srs)
        if self.LAYER_BLOCKFLAGS is None:
            self.showWarn(self.tr(u'Unable to create block flags\' layer'))
            
        # 2. Load data layers.
        layers_passed_count = 0
        data_group = common_group.addGroup('Data')
        data_layer_count = dataset.GetLayerCount()
        for i in range(0,data_layer_count):
            gdal_layer = dataset.GetLayer(i)
            data_layer = self.loadDataLayer(data_group,gdal_layer,network_fullpath)
            if data_layer is None:
                layers_passed_count = layers_passed_count + 1
                continue
            self.LAYERS_DATA.append(data_layer)
        if layers_passed_count != 0:
            self.showWarn(self.tr(u'Network layers skipped (unable to read): ') + str(layers_passed_count))
            
        # 3. Create result layers.
        results_group = common_group.addGroup('Results')
        
        self.LAYER_RESULT_PATH = self.createResultLayer(results_group,'_path_dijkstra',QColor(255,0,0),network_srs)
        if self.LAYER_RESULT_PATH is None:
            self.showWarn(self.tr(u'Unable to create result layer for shortest path calculations'))
            
        paths_group = results_group.addGroup('_paths_k') 
        for i in range(self.GNM_SETTING_K):
            transp_coef = 255 / self.GNM_SETTING_K - 5 
            layer_i = self.createResultLayer(paths_group,'_path_'+str(i),QColor(0,133,63,255-i*transp_coef),network_srs)
            if layer_i is None:
                self.showWarn(self.tr(u'Unable to create result layer for one of the K-paths calculation'))
                continue
            self.LAYERS_RESULT_PATHS.append(layer_i)
        
        self.LAYER_RESULT_CONNECTIVITY = self.createResultLayer(results_group,'_tree_connectivity',QColor(0,157,255),network_srs)
        if self.LAYER_RESULT_CONNECTIVITY is None:
            self.showWarn(self.tr(u'Unable to create result layer for connectivity tree calculations'))        

        return True
        
        
    def removeGnmLayersGroup(self):
        
        self.removeGroup('_paths_k')
        self.removeGroup('Data')
        self.removeGroup('Flags')
        self.removeGroup('Results')
        self.removeGroup(self.NETWORK_NAME)
        
        #for layer in self.LAYERS_DATA:
        #    QgsMapLayerRegistry.instance().removeMapLayers( [layer.id()] )
        #QgsMapLayerRegistry.instance().removeMapLayers( [self.LAYER_STARTFLAG.id()] )
        #QgsMapLayerRegistry.instance().removeMapLayers( [self.LAYER_ENDFLAG.id()] )
        #QgsMapLayerRegistry.instance().removeMapLayers( [self.LAYER_BLOCKFLAGS.id()] )
        #QgsMapLayerRegistry.instance().removeMapLayers( [self.LAYER_RESULT_PATH.id()] )
        #for layer in self.LAYERS_RESULT_PATHS:
        #    QgsMapLayerRegistry.instance().removeMapLayers( [layer.id()] )
        #QgsMapLayerRegistry.instance().removeMapLayers( [self.LAYER_RESULT_CONNECTIVITY.id()] )
        
        self.LAYERS_DATA = [] 
        self.LAYER_STARTFLAG = None
        self.LAYER_ENDFLAG = None
        self.LAYER_BLOCKFLAGS = None
        self.LAYER_RESULT_PATH = None
        self.LAYERS_RESULT_PATHS = []
        self.LAYER_RESULT_CONNECTIVITY = None
 
 
    def loadDataLayer(self,group,gdal_layer,network_fullpath):
        if gdal_layer is None:
            return None
        data_layer_name = gdal_layer.GetName()
# TODO: remove hardcoded .shp loads:          
        layer = QgsVectorLayer(str(network_fullpath) + '/' + data_layer_name + '.shp', data_layer_name, "ogr")
        if not layer.isValid():
            return None
        layer.setReadOnly(True)                
        QgsMapLayerRegistry.instance().addMapLayer(layer,False)
        group.addLayer(layer) 
        #if layer.geometryType() == QGis.Point:
            #layer.selectionChanged.connect(self.onSelectInDataLayer) # connect with slot so it can be able to set analysis flags
        if layer.geometryType() == QGis.Line: 
            symbols = layer.rendererV2().symbols() # also set default black colour for lines
            symbol = symbols[0]
            symbol.deleteSymbolLayer(0)
            sl = QgsSimpleLineSymbolLayerV2()
            sl.setColor(QColor(0,0,0))
            symbol.appendSymbolLayer(sl) 
            qgis.utils.iface.legendInterface().refreshLayerSymbology(layer) 
        return layer

    def createFlagsLayer(self,group,name,icon_path,srs):
        uri_layer = str('{0}?crs={1}').format('Point',srs)
        layer = QgsVectorLayer(uri_layer,name,"memory")
        if layer is None:
            return None
        layer.setReadOnly(True)
        QgsMapLayerRegistry.instance().addMapLayer(layer,False)
        group.addLayer(layer) 
        symbols = layer.rendererV2().symbols()
        symbol = symbols[0]
        symbol.deleteSymbolLayer(0)
        sl = QgsSvgMarkerSymbolLayerV2() # http://qgis.org/api/classQgsSvgMarkerSymbolLayerV2.html
        sl.setPath(icon_path)
        sl.setSize(6.0)
        sl.setHorizontalAnchorPoint(QgsMarkerSymbolLayerV2.Left)
        sl.setVerticalAnchorPoint(QgsMarkerSymbolLayerV2.Bottom)
        symbol.appendSymbolLayer(sl) 
        qgis.utils.iface.legendInterface().refreshLayerSymbology(layer)        
        return layer

    def createResultLayer(self,group,name,color,srs):            
        uri_layer = str('{0}?crs={1}').format('LineString',srs)    
        layer = QgsVectorLayer(uri_layer,name,"memory")
        if layer is None:
            return None  
        layer.setReadOnly(True)
        QgsMapLayerRegistry.instance().addMapLayer(layer,False)
        group.addLayer(layer)    
        symbols = layer.rendererV2().symbols()
        symbol = symbols[0]
        symbol.deleteSymbolLayer(0)
        sl = QgsSimpleLineSymbolLayerV2()
        sl.setWidth(1.9)
        sl.setColor(color)
        symbol.appendSymbolLayer(sl)      
        qgis.utils.iface.legendInterface().refreshLayerSymbology(layer)
        return layer
        
        
    def isDataLayer(self,layer):
        for lr in self.LAYERS_DATA:
            if lr == layer:
                return True
        return False
      
      
    def clickFlagButton(self, toolbutton, icon):
        if self.PRESSED_TOOLB is not None:
            self.PRESSED_TOOLB.setDown(False)
            self.PRESSED_TOOLB.setIcon(self.PRESSED_ICON)
        if toolbutton == self.PRESSED_TOOLB:
            self.PRESSED_TOOLB = None
            self.PRESSED_ICON = None
            self.iface.mapCanvas().unsetMapTool(self.map_tool)
            return    
        self.PRESSED_TOOLB = toolbutton    
        self.PRESSED_ICON = toolbutton.icon()
        toolbutton.setDown(True)
        toolbutton.setIcon(icon)
        self.iface.mapCanvas().setMapTool(self.map_tool)
        

    def createFlags(self, features):
        if features == None or len(features) < 1:
            return
        if self.PRESSED_TOOLB == self.toolbutton_start_flag:
            self.GFID_STARTFLAG = self.resetStartOrEndFlag(features[0],
                self.GFID_STARTFLAG,self.GFID_ENDFLAG,self.LAYER_STARTFLAG)
        elif self.PRESSED_TOOLB == self.toolbutton_end_flag:
            self.GFID_ENDFLAG = self.resetStartOrEndFlag(features[0],
                self.GFID_ENDFLAG,self.GFID_STARTFLAG,self.LAYER_ENDFLAG)
        elif self.PRESSED_TOOLB == self.toolbutton_block_flags:
            gfids = self.appendBlockFlags(features)
            for gfid in gfids:
                self.GFIDS_BLOCKFLAGS.append(gfid)


    def resetStartOrEndFlag(self,feature,gfid_this,gfid_other,layer_this):
        gfid = int(feature.attribute(self.GNM_CONST_GFIDFIELD))
        #QgsMessageLog.logMessage(str(type(gfid)), 'NGM', QgsMessageLog.INFO) 
        # Do logical checks.
        if gfid == gfid_this: 
            return
        if gfid == gfid_other:
            self.showMsg(self.tr(u'The point can not be start and end at the same time, select another point!'))
            return
        for bl_gfid in self.GFIDS_BLOCKFLAGS:
            if bl_gfid == gfid:
                self.showMsg(self.tr(u'The start point can not be blocked, select another point!'))
                return
        # Remove old flag feature.
        ids = [f.id() for f in layer_this.getFeatures()]
        layer_this.dataProvider().deleteFeatures(ids)
        # Create new one.
        geom = feature.geometry()
        point = geom.asPoint()
        new_feature = QgsFeature()
        new_feature.setGeometry(QgsGeometry.fromPoint(point))
        (res, outFeats) = layer_this.dataProvider().addFeatures([new_feature])
        layer_this.triggerRepaint() # Otherwise point in this layer will not be moved. 
        # Return new gfid.
        return gfid
        
    def appendBlockFlags(self,features):
        """See resetStartOrEndFlag()"""
        # Unlike setStartOrEndFlag() here we add several flags to the current set of flags.
        gfids = []
        for feature in features: 
            gfid = int(feature.attribute(self.GNM_CONST_GFIDFIELD))
            if gfid == self.GFID_STARTFLAG:
                continue
            if gfid == self.GFID_ENDFLAG:
                continue
            if gfid in self.GFIDS_BLOCKFLAGS:
                continue
            gfids.append(gfid)
            geom = feature.geometry()
            point = geom.asPoint()
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPoint(point))
            (res, outFeats) = self.LAYER_BLOCKFLAGS.dataProvider().addFeatures([feat])
        self.LAYER_BLOCKFLAGS.triggerRepaint()     
        return gfids
          
            
    def updateResultLayer(self,ogr_layer,qgis_layer):
        """Clear and than fill the layer with line geometries"""
        # TODO: firstly remove duplicates from gfids if occurs?
        # Create all features by gfids (by coping geoms from OGR features).
        features_to_visualize = []
        ogr_layer.ResetReading()
        ogr_feature = ogr_layer.GetNextFeature()
        while ogr_feature is not None:
            # NOTE: some other ways to copy geometries failed. See previous version of this file.
            ogr_geom = ogr_feature.GetGeometryRef()
            wkb = ogr_geom.ExportToWkb(ogr.wkbNDR)
            qgs_geom = QgsGeometry()
            qgs_geom.fromWkb(wkb)
            qgs_feature = QgsFeature()
            qgs_feature.setGeometry(qgs_geom)
            if qgs_feature.geometry().type() == QGis.Line:
                features_to_visualize.append(qgs_feature)
            ogr_feature = ogr_layer.GetNextFeature()
        # Clear layer and add features at once.
        ids = [f.id() for f in qgis_layer.getFeatures()]
        qgis_layer.dataProvider().deleteFeatures(ids)       
        (res, outFeats) = qgis_layer.dataProvider().addFeatures(features_to_visualize)
        qgis_layer.triggerRepaint()
        
    def updateResultLayers(self,ogr_layer,qgis_layers):
        """See updateResultLayer()"""
        # TODO: firstly remove duplicates from gfids if occurs?  
        features_to_visualize = []
        for i in range(self.GNM_SETTING_K):
            features_to_visualize.append([])
        ogr_layer.ResetReading()
        ogr_feature = ogr_layer.GetNextFeature()
        while ogr_feature is not None:
            ogr_geom = ogr_feature.GetGeometryRef() 
            wkb = ogr_geom.ExportToWkb(ogr.wkbNDR)
            qgs_geom = QgsGeometry()
            qgs_geom.fromWkb(wkb)
            qgs_feature = QgsFeature()
            qgs_feature.setGeometry(qgs_geom)
            layer_num = ogr_feature.GetFieldAsInteger(self.GNM_CONST_PATHNUMFIELD) # numbers start from 1
            if qgs_feature.geometry().type() == QGis.Line and layer_num <= self.GNM_SETTING_K:
                features_to_visualize[layer_num-1].append(qgs_feature)
            ogr_feature = ogr_layer.GetNextFeature()
        i = 0
        for qgis_layer in qgis_layers:
            ids = [f.id() for f in qgis_layer.getFeatures()]
            qgis_layer.dataProvider().deleteFeatures(ids) 
            (res, outFeats) = qgis_layer.dataProvider().addFeatures(features_to_visualize[i])
            qgis_layer.triggerRepaint()
            i=i+1
        
        
    def updateLayersToSearchForFlags(self):
        layers = []
        for layer in self.LAYERS_DATA:
            if layer.geometryType() == QGis.Point:
                layers.append(layer)
        self.map_tool.updateLayersToSearch(layers)
        
        
    def removeGroup(self,name):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(name)
        if not group is None:
            for child in group.children():
                dump = child.dump()
                id = dump.split("=")[-1].strip()
                QgsMapLayerRegistry.instance().removeMapLayer(id)
            root.removeChildNode(group)
        
        
    def showMsg(self, text):
        msg_box = QtGui.QMessageBox()
        msg_box.setText(text)
        msg_box.setStandardButtons(QtGui.QMessageBox.Ok)
        msg_box.exec_()  
        
    def showWarn(self, text):
        self.showMsg(self.tr(u'Warning. ') + text)
        
        
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
        return QCoreApplication.translate('GNMManager', message)   

        