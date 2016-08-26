#!/usr/bin/env python
# coding=utf-8

def haveGnm ():
    import imp
    try:
        module_osgeo_info = imp.find_module('osgeo')
        module_osgeo = imp.load_module('osgeo', *module_osgeo_info)
        imp.find_module('_gnm', module_osgeo.__path__) # __path__ is already a list
        found = True
    except:
        found = False
    return found
 
