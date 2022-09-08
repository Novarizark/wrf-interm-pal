#/usr/bin/env python3
'''
Date: Sep 6, 2022

This is a script to merge pseudo global warming (PGW) delta 
values into the pre-existed WRF interm files. 
PGW values should be provided in advance.

Revision:
Sep 6, 2022 --- New 

Zhenning LI
'''

import logging, logging.config
import lib 
from utils import utils

def main_run():

    # logging manager
    logging.config.fileConfig('./conf/logging_config.ini')
    
    utils.write_log('Read Config...')
    cfg_hdl=lib.cfgparser.read_cfg('./conf/config.ini')
 
    utils.write_log('Construct PGWHandler...')
    pgw_hdl=lib.pgw_handler.PGWHandler(cfg_hdl)

    pgw_hdl.load_interm_meta()
    # prep delta data according to interm meta
    pgw_hdl.prep_delta()

    for time_frm in pgw_hdl.in_time_series:
        utils.write_log('Processing time: '+str(time_frm))
        pgw_hdl.pgw_pipeline(time_frm)
        #utils.write_log('Writing time: '+str(time_frm))
        #pgw_hdl.read_wrfinterm(time_frm)
 


'''
'''

if __name__=='__main__':
    main_run()
