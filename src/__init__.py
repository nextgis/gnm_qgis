# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GNMManager
                                 A QGIS plugin
 Manages GDAL GNM networks
                             -------------------
        begin                : 2015-02-03
        copyright            : (C) 2015 by NextGIS
        email                : gusevmihs@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GNMManager class from file GNMManager.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gnm_manager import GNMManager
    return GNMManager(iface)
