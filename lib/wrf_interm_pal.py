#/usr/bin/env python3
"""Build WRF intermediate file template"""

import datetime
import struct
import pandas as pd 
import xarray as xr
import numpy as np
from scipy.io import FortranFile
from utils import utils


print_prefix='lib.wrf_interm_pal>>'

def gen_wrf_mid_template():
    # init the dictionary
    NLAT,NLON=181,360
    slab_dict={
        'IFV':5, 'HDATE':'0000-00-00_00:00:00:0000',
        'XFCST':0.0, 'MAP_SOURCE':'CMIP6',
        'FIELD':'', 'UNIT':'', 'DESC':'', 
        'XLVL':0.0, 'NX':NLON, 'NY':NLAT,
        'IPROJ':0,'STARTLOC':'SWCORNER',
        'STARTLAT':-90.0, 'STARTLON':0.0,
        'DELTLAT':1.0, 'DELTLON':1.0, 'EARTH_RAD':6371.229,
        'IS_WIND_EARTH_REL': 0, 
        'SLAB':np.array(np.zeros((NLAT,NLON)), dtype=np.float32),
        'key_lst':['IFV', 'HDATE', 'XFCST', 'MAP_SOURCE', 'FIELD', 'UNIT', 
        'DESC', 'XLVL', 'NX', 'NY', 'IPROJ', 'STARTLOC', 
        'STARTLAT', 'STARTLON', 'DELTLAT', 'DELTLON', 
        'EARTH_RAD', 'IS_WIND_EARTH_REL', 'SLAB']
    }
    return slab_dict

def read_record(in_file):
    '''
    Read a record from a WRF intermediate file
    '''
    # IFV header
    slab=gen_wrf_mid_template()
    rec=in_file.read_record('>I')
    slab['IFV']=rec[0]

    # HDATE header
    rec=in_file.read_record('>156c')
    (
        slab['HDATE'], slab['XFCST'],
        slab['MAP_SOURCE'], slab['FIELD'],
        slab['UNIT'], slab['DESC'],
        slab['XLVL'], slab['NX'], slab['NY'],
        slab['IPROJ']
    )=struct.unpack('>24sf32s9s25s46sfIII', rec)
    
    # STARTLOC header
    rec=in_file.read_record('>28c')
    (
        slab['STARTLOC'], slab['STARTLAT'],
        slab['STARTLON'], slab['DELTLAT'], slab['DELTLON'],
        slab['EARTH_RAD']
    )=struct.unpack('>8sfffff', rec)
    
    # IS_WIND_EARTH_REL header
    rec=in_file.read_record('>I')
    slab['IS_WIND_EARTH_REL']=rec[0]
    
    # Let's play with the SLAB
    rec=in_file.read_record(
        '(%d,%d)>f' % (slab['NY'], slab['NX']))
    slab['SLAB']=np.array(rec)
    
    # convert to string
    for key in [
        'HDATE', 'MAP_SOURCE', 'FIELD', 
        'UNIT', 'DESC', 'STARTLOC']:
        slab[key]=slab[key].decode('utf-8').strip()

    return slab

def write_record(out_file, slab_dic):
    '''
    Write a record to a WRF intermediate file
    '''
    slab_dic['MAP_SOURCE']=slab_dic['MAP_SOURCE'].ljust(32)
    slab_dic['FIELD']=slab_dic['FIELD'].ljust(9)
    slab_dic['UNIT']=slab_dic['UNIT'].ljust(25)
    slab_dic['DESC']=slab_dic['DESC'].ljust(46)
    
    # IFV header
    out_file.write_record(struct.pack('>I',slab_dic['IFV']))
    
    # HDATE header
    pack=struct.pack('>24sf32s9s25s46sfIII', 
        slab_dic['HDATE'].encode(), slab_dic['XFCST'],
        slab_dic['MAP_SOURCE'].encode(), slab_dic['FIELD'].encode(),
        slab_dic['UNIT'].encode(), slab_dic['DESC'].encode(),
        slab_dic['XLVL'], slab_dic['NX'], slab_dic['NY'],
        slab_dic['IPROJ'])
    out_file.write_record(pack)

    # STARTLOC header
    pack=struct.pack('>8sfffff',
        slab_dic['STARTLOC'].encode(), slab_dic['STARTLAT'],
        slab_dic['STARTLON'], slab_dic['DELTLAT'], slab_dic['DELTLON'],
        slab_dic['EARTH_RAD'])
    out_file.write_record(pack)

    # IS_WIND_EARTH_REL header
    pack=struct.pack('>I', slab_dic['IS_WIND_EARTH_REL'])
    out_file.write_record(pack)

    # Let's play with the SLAB
    out_file.write_record(
        slab_dic['SLAB'].astype('>f'))
    
    return 0
