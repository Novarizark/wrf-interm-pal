#/usr/bin/env python3
"""Build PGW_HANDLER Objects"""

import datetime
import pandas as pd 
import numpy as np
import xarray as xr
from scipy.io import FortranFile, FortranEOFError
from utils import utils
import lib.wrf_interm_pal as pal

print_prefix='lib.pgw_handler>>'



class PGWHandler(object):

    '''
    Construct PGW Handler 

    Methods
    -----------
    __init__:   initialize PGW Handler with config and loading data
    interp_data: interpolate data to common mesh
    write_wrfinterm: write wrfinterm file

    '''
    
    def __init__(self, cfg):
        '''
        Initialize PGW Handler with config and loading data
        '''
        
        cfg=cfg['PGW']

        self.interm_path=cfg['interm_path']
        self.interm_prefix=cfg['interm_prefix']
        self.pgw_strt_ts=datetime.datetime.strptime(
            cfg['pgw_start_ts'], utils.CONST['YMDH'])
        self.pgw_end_ts=datetime.datetime.strptime(
            cfg['pgw_end_ts'], utils.CONST['YMDH'])
        self.pgw_frq=cfg['pgw_frq']
        self.pgw_diff_file=cfg['pgw_diff_file']
        self.out_root=cfg['output_path']
        self.out_prefix=self.interm_prefix+'_'+cfg['output_add_prefix']

        dt=datetime.timedelta(hours=int(self.pgw_frq))
        self.in_time_series=pd.date_range(
            start=self.pgw_strt_ts, end=self.pgw_end_ts, freq=dt)

    def load_interm_meta(self):
        '''
        load meta data according to single interm file 
        '''
        tf=self.in_time_series[0]
        in_fn=self.interm_path+'/'+self.interm_prefix+':'+tf.strftime('%Y-%m-%d_%H')
        self.slab_temp=pal.gen_wrf_mid_template()
        utils.write_log(print_prefix+'Processing meta...')

        # NOTE: dtype='>u4' for header (big-endian, unsigned int)
        
        wrf_mid = FortranFile(in_fn, 'r', header_dtype=np.dtype('>u4'))        
        self.slab_temp=pal.read_record(wrf_mid)
        wrf_mid.close()
        
        slab_rec=self.slab_temp

        # construct lat lon mesh
        self.lat1d=np.arange(
            slab_rec['STARTLAT'], 
            slab_rec['STARTLAT']+slab_rec['DELTLAT']*slab_rec['NY'], 
            slab_rec['DELTLAT'])

        self.lon1d=np.arange(
            slab_rec['STARTLON'], 
            slab_rec['STARTLON']+slab_rec['DELTLON']*slab_rec['NX'], 
            slab_rec['DELTLON'])
        

    def prep_delta(self):
        '''
        prepare delta data for interpolation
        '''
        ds_diff=xr.open_dataset(self.pgw_diff_file)
        
        # Below can be changed for different delta file
        dta=ds_diff['dta']
        dtas=ds_diff['dtas']
        
        self.dta=dta.sel(month=slice(7,9)).mean(dim='month')
        self.dta = self.dta.interp(
            lon=self.lon1d, lat=self.lat1d,
            method='linear')
        
        self.dtas=dtas.sel(month=slice(7,9)).mean(dim='month')
        self.dtas = self.dtas.interp(
            lon=self.lon1d, lat=self.lat1d,
            method='linear')
        
        ds_diff.close()
    
    
    def pgw_pipeline(self, tf):
        '''
        PGW pipeline
        '''
        in_fn=self.interm_path+'/'+self.interm_prefix+':'+tf.strftime('%Y-%m-%d_%H')
        out_fn=self.out_root+'/'+self.out_prefix+':'+tf.strftime('%Y-%m-%d_%H')
        self.slab_temp=pal.gen_wrf_mid_template()
        utils.write_log(print_prefix+'Reading %s...' % in_fn)
        # NOTE: dtype='>u4' for header (big-endian, unsigned int)
        wrf_mid_in = FortranFile(in_fn, 'r', header_dtype=np.dtype('>u4'))
        wrf_mid_out = FortranFile(out_fn, 'w', header_dtype=np.dtype('>u4'))
        
        while True:
            try: 
                self.slab_temp=pal.read_record(wrf_mid_in)
            except FortranEOFError:
                break
            
            slab_dic=self.slab_temp
            fld,lvl=slab_dic['FIELD'],slab_dic['XLVL']
            if fld =='TT' and lvl<=100000.0:
                slab_dic['SLAB']=slab_dic['SLAB']+self.dta.sel(
                    plev=lvl, method='nearest').values
            elif fld in ['TT', 'SST','SKINTEMP','ST0000007'] and lvl==200100.0:
                slab_dic['SLAB']=slab_dic['SLAB']+self.dtas.values
            ecode=pal.write_record(wrf_mid_out, slab_dic)

        wrf_mid_in.close()
        wrf_mid_out.close()

 
if __name__ == "__main__":
    pass
