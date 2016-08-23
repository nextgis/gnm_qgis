# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QNetwork
                                 A QGIS plugin
 Manage and analyse networks via GDAL
                             -------------------
        begin                : 2016-08-23
        copyright            : (C) 2016 by NextGIS
        email                : info@nextgis.com
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
    """Load QNetwork class from file QNetwork.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gnm_manager import GNMManager
    return GNMManager(iface)
