# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMManager
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMenu, QMessageBox

# Import the code for the dialog
from gnm_create_dialog import GNMCreateDialog
from gnm_view_dialog import GNMViewDialog
from gnm_delete_dialog import GNMDeleteDialog
from gnm_settings_dialog import GNMSettingsDialog

import os.path

from qgis.core import *
import qgis.utils

from osgeo import ogr
from osgeo import gnm


class GNMManager:
    """GNM QGIS Plugin Implementation."""

    NETWORK = None
    NETWORK_PATH = ''
    NETWORK_FORMAT = ''
    NETWORK_ANALYSER = None
    NETWORK_EMITTER_LAYER_NAMES = []
     
    NETWORK_SYSTEM_LAYERS = []
    NETWORK_CLASS_LAYERS = [] # Only these layers can be used to set flags for analysis.
    NETWORK_STARTFLAG_LAYER = None
    NETWORK_STARTFLAG_GFID = -1
    NETWORK_ENDFLAG_LAYER = None
    NETWORK_ENDFLAG_GFID = -1
    NETWORK_BLOCKFLAG_LAYER = None
    NETWORK_BLOCKFLAG_GFIDS = []
    NETWORK_RESULT_PATH_LAYER = None
    NETWORK_RESULT_PATHS_LAYERS = []
    NETWORK_RESULT_CONNECTIVITY_LAYER = None

    SETTING_K = 3
    
    action_create_network = None
    action_view_network = None
    action_delete_network = None
    action_current_network = None
    action_manage_cur_network = None
    action_analyse_cur_network = None
    action_settings_cur_network = None
    action_start_flag = None
    action_end_flag = None
    action_block_flags = None
    action_remove_flags = None
    action_path = None
    action_paths = None
    action_connectivity = None
    
    
    
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

        # Create the dialog (after translation) and keep reference
        self.dlg_create = GNMCreateDialog()
        self.dlg_view = GNMViewDialog()
        self.dlg_delete = GNMDeleteDialog()
        self.dlg_settings = GNMSettingsDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GNM Manager')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GNMManager')
        self.toolbar.setObjectName(u'GNMManager')

        
        
        
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


        
        
    def add_action(
        self,
        menu, # To which sub menu add this action. If None action is added to the root via addPluginToMenu()
        icon_path,
        text,
        callback = None,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        
        if callback is not None:
            action.triggered.connect(callback)
            
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            if menu is None:
                self.iface.addPluginToMenu(
                    self.menu,
                    action)
            else:
                menu.addAction(action)

        self.actions.append(action)

        return action
        
     
        

    def initGui(self):
        # Main menus.
        self.action_create_network = self.add_action(
            menu=None,
            icon_path=None,
            text=u'Создать сеть',#(u'Create network'),
            callback=self.OnCreateNetworkClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True,
            enabled_flag=True)
        self.action_view_network = self.add_action(
            menu=None,
            icon_path=None,
            text=u'Просмотреть сеть',#self.tr(u'View network'),
            callback=self.OnViewNetworkClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True,
            enabled_flag=True)
        self.action_delete_network = self.add_action(
            menu=None,
            icon_path=None,
            text=u'Удалить сеть',#self.tr(u'Delete network'),
            callback=self.OnDeleteNetworkClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True,
            enabled_flag=True)            
        self.action_current_network = self.add_action(
            menu=None,
            icon_path=None,
            text=u'Текущая сеть',#self.tr(u'Current network'),
            callback=None,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True,
            enabled_flag=False) # It will be enabled only if some network is currently added to the project.
        menu_current = QMenu('menu')
        self.action_current_network.setMenu(menu_current)
        
        # Sub menus.         
        self.action_manage_cur_network = self.add_action(
            menu=menu_current,
            icon_path=None,
            text=u'Управление',#self.tr(u'Manage'),
            callback=None, # For now its not available to manage networks.
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True,
            enabled_flag=False)
        self.action_analyse_cur_network = self.add_action(
            menu=menu_current,
            icon_path=None,
            text=u'Анализ',#self.tr(u'Analysis'),
            callback=None,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True,
            enabled_flag=True) 
        menu_analysis = QMenu()
        self.action_analyse_cur_network.setMenu(menu_analysis)
        self.action_settings_cur_network = self.add_action(
            menu=menu_current,
            icon_path=None,
            text=u'Настройки',#self.tr(u'Settings'),
            callback=self.OnSettingsNetworkClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
            add_to_menu=True,
            enabled_flag=True)
            
        # Sub sub menus.
        ic_path = 'C:/Users/Mikhail/NextGIS QGIS future/python/plugins/gnmmanager/img/start.png'
        self.action_start_flag = self.add_action(
            menu=menu_analysis,
            icon_path=ic_path,
            text=u'Задать начальную точку',#self.tr(u'Mark start point'),
            callback=self.OnStartFlagClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True,
            enabled_flag=False,
            status_tip=u'Выберите точечный объект в любом слое подгруппы Data, а затем нажмите эту кнопку')#self.tr(u'Select the point feature in any GNM network layer and than click this button'))
        ic_path = 'C:/Users/Mikhail/NextGIS QGIS future/python/plugins/gnmmanager/img/end.png'
        self.action_end_flag = self.add_action(
            menu=menu_analysis,
            icon_path=ic_path,
            text=u'Задать конечную точку',#self.tr(u'Mark end point'),
            callback=self.OnEndFlagClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True,
            enabled_flag=False,
            status_tip=u'Выберите точечный объект в любом слое подгруппы Data, а затем нажмите эту кнопку')#self.tr(u'Select the point feature in any GNM network layer and than click this button'))          
        ic_path = 'C:/Users/Mikhail/NextGIS QGIS future/python/plugins/gnmmanager/img/block.png'
        self.action_block_flags = self.add_action(
            menu=menu_analysis,
            icon_path=ic_path,
            text=u'Блокировать объекты',#self.tr(u'Mark blocked points'),
            callback=self.OnBlockFlagClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True,
            enabled_flag=False,
            status_tip=u'Выберите точечные объекты в любом слое подгруппы Data, а затем нажмите эту кнопку')#self.tr(u'Select several point features in any GNM network layers and than click this button'))            
        ic_path = 'C:/Users/Mikhail/NextGIS QGIS future/python/plugins/gnmmanager/img/remove_all.png'
        self.action_remove_flags = self.add_action(
            menu=menu_analysis,
            icon_path=ic_path,
            text=u'Удалить все флаги',#self.tr(u'Remove all flags'),
            callback=self.OnRemoveFlagClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True,
            enabled_flag=False,
            status_tip=u'Нажмите, чтобы удалить все флаги: начальной, конечной и блокированных точек')#self.tr(u'Click this to remove all flags: start, end and block')) 
        ic_path = 'C:/Users/Mikhail/NextGIS QGIS future/python/plugins/gnmmanager/img/path.png'
        self.action_path = self.add_action(
            menu=menu_analysis,
            icon_path=ic_path,
            text=u'Расчёт кратчайшего пути',#self.tr(u'Calculate shortest path'),
            callback=self.OnPathClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True,
            enabled_flag=False,
            status_tip=u'Задайте начальную и конечную точку прежде чем проводить расчёт')#self.tr(u'---'))             
        ic_path = 'C:/Users/Mikhail/NextGIS QGIS future/python/plugins/gnmmanager/img/paths.png'
        self.action_paths = self.add_action(
            menu=menu_analysis,
            icon_path=ic_path,
            text=u'Расчёт нескольких кратчайших путей',#self.tr(u'Calculate several shortest paths'),
            callback=self.OnPathsClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True,
            enabled_flag=False,
            status_tip=u'Задайте количество необходимых путей для поиска в настройках текущей сети')#self.tr(u'---'))             
        ic_path = 'C:/Users/Mikhail/NextGIS QGIS future/python/plugins/gnmmanager/img/connectivity.png'
        self.action_connectivity = self.add_action(
            menu=menu_analysis,
            icon_path=ic_path,
            text=u'Расчёт компонент связности',#self.tr(u'Calculate connectivity'),
            callback=self.OnConnectivityClicked,
            parent=self.iface.mainWindow(),
            add_to_toolbar=True,
            add_to_menu=True,
            enabled_flag=False,
            status_tip=u'Задайте объекты, являющиеся источниками через правила')#self.tr(u'---')) 
            
            
            
            
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GNM Manager'),
                action)
            self.iface.removeToolBarIcon(action)
            
            

# *******************************************************************************************************************
# *                                      Button and other slots                                                     * 
# *******************************************************************************************************************  


    def OnProjectOpen(self):     
        
        return
        
        
        
        
    def OnProjectSave(self):
        
        return
        
        
        
        
    def OnLayerDelete(self):
        # Check if one of the GNM layers is deleted - and show warnings that the network 
        # will work incorrectly.
        
        return

        

        
    def OnCreateNetworkClicked(self):
        if self.NETWORK is None:
            ok_to_add = True
        else:
            ok_to_add = False    
        self.dlg_create.show()
        result = self.dlg_create.my_exec_(QgsMapLayerRegistry.instance().mapLayers(),ok_to_add) 
        if result:
            self.CommonSteps(self.dlg_create.network,self.dlg_create.network_path,self.dlg_create.network_format)        
            #proj_layers = self.dlg_create.layer_names_from_project
            #for proj_layer in proj_layers:
                #pass
                # Copy style from original layer.
                # ...
           
           
           
            
    def OnViewNetworkClicked(self):
        if self.NETWORK is None:
            ok_to_add = True
        else:
            ok_to_add = False  
        self.dlg_view.show() 
        result = self.dlg_view.my_exec_(ok_to_add)
        if result:
            self.CommonSteps(self.dlg_view.network,self.dlg_view.network_name,self.dlg_view.network_format)
            
            


    def OnSettingsNetworkClicked(self):
        self.dlg_settings.show()
        result = self.dlg_settings.exec_()
        if result:
            pass    


            
            
    def OnDeleteNetworkClicked(self):
        self.dlg_delete.show()
        result = self.dlg_delete.exec_()
        if result:
            pass
            
            
            

    def OnStartFlagClicked(self):
        selected_feature = self.GetSelectedPointFeature()
        if selected_feature is None:
            self.ShowMsgBox(u'Выберите только одну точку в подгруппе Data сетевых данных')#('Select only one point feature in the group \"GNM network\"!')
            return         
        # Get point feature coordinates and feature's GFID, checking if the point has already some flag.
        gfid = selected_feature.attribute('gfid')
        if gfid == self.NETWORK_STARTFLAG_GFID:
            return # Just exit if this point is already a start point.
        if gfid == self.NETWORK_ENDFLAG_GFID:
            self.ShowMsgBox(u'Точка не может быть начальной и конечной одновременно. Задайте другую точку')#('The point can not be start and end at the same time, select another point!')
            return
        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            if bl_gfid == gfid:
                self.ShowMsgBox(u'Стартовая точка не может быть блокирована. Задайте другую точку')#('The start point can not be blocked, select another point!')
                return
        self.NETWORK_STARTFLAG_GFID = gfid
        # Remove old flag feature.
        ids = [f.id() for f in self.NETWORK_STARTFLAG_LAYER.getFeatures()]
        self.NETWORK_STARTFLAG_LAYER.dataProvider().deleteFeatures(ids)
        # Create new one.
        geom = selected_feature.geometry()
        point = geom.asPoint()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPoint(point))
        (res, outFeats) = self.NETWORK_STARTFLAG_LAYER.dataProvider().addFeatures([feat])
        ## update layer's extent when new features have been added
        ## because change of extent in provider is not propagated to the layer
        #self.NETWORK_STARTFLAG_LAYER.dataProvider().updateExtents()
        self.NETWORK_STARTFLAG_LAYER.triggerRepaint() # Otherwise point in this layer will not be moved.

        
        
        
    def OnEndFlagClicked(self):
    # This method is similar to OnStartFlagClicked
        selected_feature = self.GetSelectedPointFeature()
        if selected_feature is None:
            self.ShowMsgBox(u'Выберите только одну точку в подгруппе Data сетевых данных')#('Select only one point feature in the group \"GNM network data\"!')
            return
        gfid = selected_feature.attribute('gfid')
        if gfid == self.NETWORK_ENDFLAG_GFID:
            return         
        if gfid == self.NETWORK_STARTFLAG_GFID:
            self.ShowMsgBox(u'Точка не может быть начальной и конечной одновременно. Задайте другую точку')#('The point can not be start and end at the same time, select another point!')
            return
        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            if bl_gfid == gfid:
                self.ShowMsgBox(u'Конечная точка не может быть блокирована. Задайте другую точку')#('The end point can not be blocked, select another point!')
                return
        self.NETWORK_ENDFLAG_GFID = gfid
        ids = [f.id() for f in self.NETWORK_ENDFLAG_LAYER.getFeatures()]
        self.NETWORK_ENDFLAG_LAYER.dataProvider().deleteFeatures(ids)
        geom = selected_feature.geometry()
        point = geom.asPoint()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPoint(point))
        (res, outFeats) = self.NETWORK_ENDFLAG_LAYER.dataProvider().addFeatures([feat])
        self.NETWORK_ENDFLAG_LAYER.triggerRepaint() 

        
        
        
    def OnBlockFlagClicked(self):
    # This method is similar to OnStartFlagClicked
        for layer in self.NETWORK_CLASS_LAYERS:
            geom_type = layer.geometryType()
            if geom_type != QGis.Point:
                continue
            selection = layer.selectedFeatures()
            if selection is None:
                continue
            else:
                for feature in selection: 
                    layer.deselect(feature.id())
                    gfid = feature.attribute('gfid')
                    if gfid == self.NETWORK_STARTFLAG_GFID:
                        continue
                    if gfid == self.NETWORK_ENDFLAG_GFID:
                        continue
                    if gfid in self.NETWORK_BLOCKFLAG_GFIDS:
                        continue
                    self.NETWORK_BLOCKFLAG_GFIDS.append(gfid)
                    geom = feature.geometry()
                    point = geom.asPoint()
                    feat = QgsFeature()
                    feat.setGeometry(QgsGeometry.fromPoint(point))
                    (res, outFeats) = self.NETWORK_BLOCKFLAG_LAYER.dataProvider().addFeatures([feat])
                self.NETWORK_BLOCKFLAG_LAYER.triggerRepaint()   
           
    
    
    
    def OnRemoveFlagClicked(self):
        ids = [f.id() for f in self.NETWORK_STARTFLAG_LAYER.getFeatures()]
        self.NETWORK_STARTFLAG_LAYER.dataProvider().deleteFeatures(ids)    
        ids = [f.id() for f in self.NETWORK_ENDFLAG_LAYER.getFeatures()]
        self.NETWORK_ENDFLAG_LAYER.dataProvider().deleteFeatures(ids)
        ids = [f.id() for f in self.NETWORK_BLOCKFLAG_LAYER.getFeatures()]
        self.NETWORK_BLOCKFLAG_LAYER.dataProvider().deleteFeatures(ids)
        self.NETWORK_STARTFLAG_GFID = -1
        self.NETWORK_ENDTFLAG_GFID = -1
        self.NETWORK_BLOCKFLAG_GFIDS = []
        self.NETWORK_STARTFLAG_LAYER.triggerRepaint() 
        self.NETWORK_ENDFLAG_LAYER.triggerRepaint() 
        self.NETWORK_BLOCKFLAG_LAYER.triggerRepaint() 
    
    

    
    def OnPathClicked(self):
        if self.NETWORK_STARTFLAG_GFID == -1:
            self.ShowMsgBox(u'Начальная точка не была задана. Задайте её перед расчётами кратчайших путей')#('The start point has not been set! Set it before any calculations')
            return            
        if self.NETWORK_ENDFLAG_GFID == -1:
            self.ShowMsgBox(u'Конечная точка не была задана. Задайте её перед расчётами кратчайших путей')#('The end point has not been set! Set it before calculating shortest paths')
            return
            
        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            self.NETWORK_ANALYSER.BlockVertex(bl_gfid)
        
        path = self.NETWORK_ANALYSER.DijkstraShortestPath(self.NETWORK_STARTFLAG_GFID,self.NETWORK_ENDFLAG_GFID)
        if path is None:
            self.ShowMsgBox(u'Произошла ошибка в процессе расчёта кратчайшего пути')#('Some error occurs while calculating path!')
        elif len(path) <= 0:
            self.ShowMsgBox(u'Расчёт выполнен успешно, но пути между двумя точками не существует')#('OK, but there is no path between start and end points')   
        else:  
            #self.ShowMsgBox('Path found and displayed successfully. It contains {0} elements'.format(len(path))) 
            gfids = []
            for pair in path:
                #for p in pair:
                gfids.append(pair[1])
            self.UpdateResultLayer(gfids,self.NETWORK_RESULT_PATH_LAYER)
                    
        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            self.NETWORK_ANALYSER.UnblockVertex(bl_gfid)      
        
        
        
        
    def OnPathsClicked(self):
        if self.NETWORK_STARTFLAG_GFID == -1:
            self.ShowMsgBox(u'Начальная точка не была задана. Задайте её перед расчётами кратчайших путей')#('The start point has not been set! Set it before any calculations')
            return            
        if self.NETWORK_ENDFLAG_GFID == -1:
            self.ShowMsgBox(u'Конечная точка не была задана. Задайте её перед расчётами кратчайших путей')#('The end point has not been set! Set it before calculating shortest paths')
            return
            
        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            self.NETWORK_ANALYSER.BlockVertex(bl_gfid)
            
        paths = self.NETWORK_ANALYSER.YensShortestPaths(self.NETWORK_STARTFLAG_GFID,self.NETWORK_ENDFLAG_GFID,self.SETTING_K)    
        if paths is None:
            self.ShowMsgBox(u'Произошла ошибка в процессе расчёта кратчайшего пути')#('Some error occurs while calculating paths!')
        elif len(paths) <= 0:
            self.ShowMsgBox(u'Расчёт выполнен успешно, но пути между двумя точками не существует')#('OK, but there is no path between start and end points')  
# TEMP -------------------------------------------------------------------------------------------------
        #for path in paths:
        self.ShowMsgBox(u'Найдено {0} кратчайших путей'.format(len(paths)))
# ------------------------------------------------------------------------------------------------------
            
        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            self.NETWORK_ANALYSER.UnblockVertex(bl_gfid)             
            
            
            
        
    def OnConnectivityClicked(self):
        # Here we use rule parsing in order to determine the points, from which connectivity searching will be
        # started (actually rules had been parsed at the loading class layers step). But:
        # TODO: use the GdalStdAnalyser class for this reason, because all this work is already done inside it.

        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            self.NETWORK_ANALYSER.BlockVertex(bl_gfid)
        
        start_gfids = []
        for layer in self.NETWORK_CLASS_LAYERS:
            layer_name = layer.name()
            if layer_name in self.NETWORK_EMITTER_LAYER_NAMES:
                features = layer.getFeatures()
                for feature in features:
                    attrs = feature.attributes()
                    idx = layer.fieldNameIndex('gfid')
                    gfid = feature.attributes()[idx]
                    start_gfids.append(gfid)
        
        if len(start_gfids) == 0:
            self.ShowMsgBox(u'')#('OK, but there is no emitter features in the network')
        else:
            connectivity = self.NETWORK_ANALYSER.ConnectedComponents(start_gfids)
            self.UpdateResultLayer(connectivity,self.NETWORK_RESULT_CONNECTIVITY_LAYER)
 
        for bl_gfid in self.NETWORK_BLOCKFLAG_GFIDS:
            self.NETWORK_ANALYSER.UnblockVertex(bl_gfid)      
   
   
   
   
# *******************************************************************************************************************
# *                                      Work with project                                                          * 
# *******************************************************************************************************************     
            
            
    def EnableInterfaceForCurrentNetwork(self,ok):
        self.action_current_network.setEnabled(ok)
        self.action_start_flag.setEnabled(ok)
        self.action_end_flag.setEnabled(ok)
        self.action_block_flags.setEnabled(ok)
        self.action_remove_flags.setEnabled(ok) 
        self.action_path.setEnabled(ok)
        self.action_paths.setEnabled(ok)
        self.action_connectivity.setEnabled(ok)  
            
        
        
        
    def ClearCurrentNetworkProject(self):
        # Free main variables.
        self.NETWORK_ANALYSER = None
        self.NETWORK_FORMAT = ''
        self.NETWORK_PATH = ''
        self.NETWORK = None
        # Delete special GNM data from current project.
        # ...
        pass
        

        
        
    def ClearGNMNetworkLayersGroup (self):
    
        # Remove from map layer registry?
        # ...
        
        self.NETWORK_SYSTEM_LAYERS = []
        self.NETWORK_CLASS_LAYERS = [] 
        self.NETWORK_STARTFLAG_LAYER = None
        self.NETWORK_STARTFLAG_GFID = -1
        self.NETWORK_ENDFLAG_LAYER = None
        self.NETWORK_ENDFLAG_GFID = -1
        self.NETWORK_BLOCKFLAG_LAYER = None
        self.NETWORK_BLOCKFLAG_GFIDS = []
        self.NETWORK_RESULT_PATH_LAYER = None
        self.NETWORK_RESULT_PATHS_LAYERS = []
        self.NETWORK_RESULT_CONNECTIVITY_LAYER = None
        
        
        
        
    def CommonSteps (self,network,network_path,network_format):
        # Write initial GNM data into current project.
        # ...
        
        # Init main variables.
        self.NETWORK = network
        self.NETWORK_PATH = network_path
        self.NETWORK_FORMAT = network_format
        self.NETWORK_ANALYSER = gnm.CreateStdAnalyser()
        err = self.NETWORK_ANALYSER.PrepareGraph(self.NETWORK)
        if err != 0:
            self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось создать объект для сетевого анализа)')#('Error while initializing network in current project (unable to initialize graph analyser)!') 
            self.ClearCurrentNetworkProject() # Clear all initialized main variables.           
            return
            
        # Create GNM layers, based on data readed from project.
        ok = self.InitGNMNetworkLayersGroup()
        if not ok:
            self.ClearGNMNetworkLayersGroup() # Remove all already loaded GNM layers:
            self.ClearCurrentNetworkProject() # Clear all initialized main variables.
            return
            
        # Additional settings.
        self._temp_DefineEmitterLayers()

        # Enable interface.
        self.EnableInterfaceForCurrentNetwork(True)        

        
        
        
    def InitGNMNetworkLayersGroup (self):
    # Create all these GNM layers, only if they were not saved as spatial layers. Define this for each layer
    # separately using special data in the project file.
    
        # 0. Create common group and parameters.
        root_layer_tree = QgsProject.instance().layerTreeRoot()
        # TODO: add networks name to the name of the group.
        common_group = root_layer_tree.addGroup('GNM Network')
    
        # 1. Create flag layers.
        flags_group = common_group.addGroup('Flags')
# TEMP --------------------------------------------------------------------------------        
        uri_srs = 'epsg:4326' # Get network's SRS for creating system layers.
        #QgsCoordinateReferenceSystem::createFromString()
# -------------------------------------------------------------------------------------       
        uri_geom = 'Point'
        uri_layer = str('{0}?crs={1}').format(uri_geom,uri_srs)
        
        self.NETWORK_STARTFLAG_LAYER = QgsVectorLayer(uri_layer,'_gnm_start_flag',"memory")
        if self.NETWORK_STARTFLAG_LAYER is None:
            self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось создать системный слой флагов)')#('Error while initializing network in current project (unable to create flag memory layer)!') 
            return False
        self.NETWORK_STARTFLAG_LAYER.setReadOnly(True)
        QgsMapLayerRegistry.instance().addMapLayer(self.NETWORK_STARTFLAG_LAYER,False)
        flags_group.addLayer(self.NETWORK_STARTFLAG_LAYER) 
        
        self.NETWORK_ENDFLAG_LAYER = QgsVectorLayer(uri_layer,'_gnm_end_flag',"memory")
        if self.NETWORK_ENDFLAG_LAYER is None:
            self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось создать системный слой флагов)')#('Error while initializing network in current project (unable to create inner memory layer)!') 
            return False    
        self.NETWORK_ENDFLAG_LAYER.setReadOnly(True)
        QgsMapLayerRegistry.instance().addMapLayer(self.NETWORK_ENDFLAG_LAYER,False)
        flags_group.addLayer(self.NETWORK_ENDFLAG_LAYER) 
        
        self.NETWORK_BLOCKFLAG_LAYER = QgsVectorLayer(uri_layer,'_gnm_block_flags',"memory")
        if self.NETWORK_BLOCKFLAG_LAYER is None:
            self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось создать системный слой флагов)')#('Error while initializing network in current project (unable to create inner memory layer)!') 
            return False
        self.NETWORK_BLOCKFLAG_LAYER.setReadOnly(True)
        QgsMapLayerRegistry.instance().addMapLayer(self.NETWORK_BLOCKFLAG_LAYER,False)
        flags_group.addLayer(self.NETWORK_BLOCKFLAG_LAYER) 
        
        # Set layer default styles.
        #http://gis.stackexchange.com/questions/70058/how-to-change-the-color-of-a-vector-layer-in-pyqgis        
        
        # 2. Load class layers.
        class_group = common_group.addGroup('Data')
        # TODO: use function 'add layers' because of issue: http://qgis.org/api/classQgsMapLayerRegistry.html#a3d0d19c86467341bdd62471c5de61376
        classes_layer = self.LayerLoader('_gnm_classes','system')
        if not classes_layer.isValid():
            self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось загрузить системный слой класов)')#('Error while initializing network in current project (unable to load one of the system layers)!') 
            return False
        spatial_layers = []
        iter = classes_layer.getFeatures()
        for feature in iter:
            attrs = feature.attributes()
            idx = classes_layer.fieldNameIndex('layer_name')
            val = attrs[idx]
            if val == 'gnm_sysedges':
                continue
            lr = self.LayerLoader(val,'class')
            if not lr.isValid():
                self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось загрузить один из классовых слоёв сети)')#('Error while initializing network in current project (unable to load one of the class layers)!')
                return False
# TEMP ----------------------------------------------------------------------------------------------------
            lr.setReadOnly(True)
# ---------------------------------------------------------------------------------------------------------                
            QgsMapLayerRegistry.instance().addMapLayer(lr,False)
            class_group.addLayer(lr) 
            self.NETWORK_CLASS_LAYERS.append(lr) 
        
        # 3. Create result layers.
        results_group = common_group.addGroup('Results')
# TEMP --------------------------------------------------------------------------------        
        uri_srs = 'epsg:4326' 
# -------------------------------------------------------------------------------------       
        uri_geom = 'LineString'
        uri_layer = str('{0}?crs={1}').format(uri_geom,uri_srs)
        
        self.NETWORK_RESULT_PATH_LAYER = QgsVectorLayer(uri_layer,'_gnm_path_result',"memory")
        if self.NETWORK_RESULT_PATH_LAYER is None:
            self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось создать системный слой результатов)')#('Error while initializing network in current project (unable to create inner memory layer)!') 
            return False  
        self.NETWORK_RESULT_PATH_LAYER.setReadOnly(True)
        QgsMapLayerRegistry.instance().addMapLayer(self.NETWORK_RESULT_PATH_LAYER,False)
        results_group.addLayer(self.NETWORK_RESULT_PATH_LAYER)   
        
        self.NETWORK_RESULT_CONNECTIVITY_LAYER = QgsVectorLayer(uri_layer,'_gnm_con_result',"memory")
        if self.NETWORK_RESULT_CONNECTIVITY_LAYER is None:
            self.ShowMsgBox(u'Не удалось инициализировать сеть в текущем проекте! (не удалось создать системный слой результатов)')#('Error while initializing network in current project (unable to create inner memory layer)!') 
            return False 
        self.NETWORK_RESULT_CONNECTIVITY_LAYER.setReadOnly(True)
        QgsMapLayerRegistry.instance().addMapLayer(self.NETWORK_RESULT_CONNECTIVITY_LAYER,False)
        results_group.addLayer(self.NETWORK_RESULT_CONNECTIVITY_LAYER)              

        return True     
            

            
        
# *******************************************************************************************************************
# *                                             Additional                                                          * 
# *******************************************************************************************************************  
 

    def _temp_DefineEmitterLayers (self):
        rules_layer = self.LayerLoader('_gnm_rules','system')
        if not rules_layer.isValid():
            #self.ShowMsgBox('Error while initializing network in current project (unable to load one of the system layers)!') 
            return False
        iter = rules_layer.getFeatures()
        # See in each rule string the word 'EMITTER' and get the name of the layer after it.
        for feature in iter: 
            attrs = feature.attributes()
            idx = rules_layer.fieldNameIndex('rule_str')
            rule_str = feature.attributes()[idx]
            str_arr = rule_str.split(' ')
            if 'EMITTER' in str_arr:
                self.NETWORK_EMITTER_LAYER_NAMES.append(str_arr[1])
        return True
 
 


    def LayerLoader(self,str_name,type):
        if self.NETWORK is None:
            return None
        # TODO: remove this if statement and make the special classes (and class factory) for working 
        # with networks of different formats.
        if self.NETWORK_FORMAT == 'Shapefile':
            str_end = ''
            if type == 'system':
                str_end = '.dbf'
            elif type == 'class':
                str_end = '.shp'
            ret_layer = QgsVectorLayer(str(self.NETWORK_PATH) + '/' + str_name + str_end, str_name, "ogr")
            return ret_layer
        elif self.NETWORK_FORMAT == 'PostGIS':
            # ...
            return None
        else:
            return None


    
    
    def GetSelectedPointFeature(self):
        # Check weather only one point feature selected and only in class layers.
        count = 0
        selected_feature = None
        for layer in self.NETWORK_CLASS_LAYERS:
            geom_type = layer.geometryType()
            if geom_type != QGis.Point:
                continue
            selection = layer.selectedFeatures()
            if selection is None:
                continue
            else:
                for feature in selection:
                    layer.deselect(feature.id()) # Deselect feature that has been seen for user's convenience.
                    count = count + 1
                    if count > 1:
                        break
                    else:
                        selected_feature = feature
            if count > 1:
                break
        if (count == 0) or (count > 1):
            return None       
        return selected_feature
        
        

        
    def UpdateResultLayer (self,gfids,layer):
    # Clear and than fill the layer with line geometries.
    
        # Remove duplicates from gfids if occurs.
    
        # Clear layer.
        ids = [f.id() for f in layer.getFeatures()]
        layer.dataProvider().deleteFeatures(ids)   
        
        # Create all features by gfids (by coping geoms from OGR features).
        features_to_visualize = []
        for gfid in gfids:
            ogr_feature = self.NETWORK.GetFeatureByGFID(gfid)
            if ogr_feature is not None:
            
                ogr_geom = ogr_feature.GetGeometryRef() # We receive only line geometry!
                
                #buffer = []
                wkb = ogr_geom.ExportToWkb(ogr.wkbNDR)
                qgs_geom = QgsGeometry()
                qgs_geom.fromWkb(wkb)
                
                #qgs_points = []
                #point_count = ogr_geom.getNumPoints()
                #for point_num in range(0,point_count):
                #    point = None
                #    ogr_geom.getPoint(point_num,ogr_point)
                #    x = ogr_point.x()
                #    y = ogr_point.y()
                #    qgs_point = QgsPoint(x,y)
                #    qgs_points.append(qgs_point)
                
                #http://gdal.org/python/
                #qgs_points = []
                #ogr_points = ogr_geom.GetPoints() 
                #for ogr_point in ogr_points:
                #    x = ogr_point.GetX()
                #    y = ogr_point.GetY()
                #    qgs_point = QgsPoint(x,y)
                #    qgs_points.append(qgs_point)                    
                
                qgs_feature = QgsFeature()
                #qgs_feature.setGeometry(QgsGeometry.fromPolyline(QgsPolyline(qgs_points)))
                qgs_feature.setGeometry(qgs_geom)
                
                features_to_visualize.append(qgs_feature)
        
        # Add them to the layer at once.
        (res, outFeats) = layer.dataProvider().addFeatures(features_to_visualize)
        layer.triggerRepaint()     
    

    
           
    def ShowMsgBox(self,text):
        msg_box = QMessageBox()
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()  
        
        
        