#!/usr/bin/env python
# coding=utf-8

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
 
class IdentifyGeometry(QgsMapToolIdentify):

    layers_to_search = []

    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolIdentify.__init__(self, canvas)
        
    def updateLayersToSearch(self,new_list_of_layers):
        self.layers_to_search = new_list_of_layers
 
    #https://3nids.wordpress.com/2013/02/14/identify-feature-on-map/
    def canvasReleaseEvent(self, mouseEvent):
        results = self.identify(mouseEvent.x(),mouseEvent.y(), self.TopDownStopAtFirst, self.layers_to_search, self.VectorLayer)
        if len(results) > 0:
            self.emit( SIGNAL( "geomIdentified" ), results[0].mLayer, results[0].mFeature)