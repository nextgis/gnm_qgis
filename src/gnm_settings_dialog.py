# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMSettingsDialog
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

from osgeo import ogr
from osgeo import gnm

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'gnm_settings_dialog_base.ui'))


class GNMSettingsDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(GNMSettingsDialog, self).__init__(parent)
        self.setupUi(self)
