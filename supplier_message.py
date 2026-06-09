# -*- coding: utf-8 -*-
import os
import polars as pl
from fluvo.lib import mapper
from fluvo.lib.transform import Processor
from datetime import datetime
from prefix import SUPPLIER_PREFIX, MESSAGE_PREFIX, SUPPLIER_CONTACT_PREFIX

CONFIG = 'conf%sconnection.conf' % os.sep
SOURCE = 'origin%smessage.csv' % os.sep

# Force the date column to a string so Polars does not reject the
# '%d/%m/%y %H:%M:%S' values (e.g. '02/03/17 12:05:00') during schema inference.
SCHEMA_OVERRIDES = {'Date': pl.String}

##STEP 1 : Define the mapping for every object to import
mapping = {
    # External ID is not allowed to be imported
    # 'id' : mapper.m2o_map(MESSAGE_PREFIX, mapper.concat("_", 'Company_ID', 'Date')),
    # 'res_external_id' : mapper.m2o(SUPPLIER_PREFIX, 'Company_ID'),
    'message_type': mapper.const('email'),
    'author_id/id': mapper.m2o(SUPPLIER_CONTACT_PREFIX, 'from'),
    'email_from': mapper.val('from'),
    'subject': mapper.val('subject'),
    'body': mapper.val('body'),
    'date': mapper.val('Date',
       postprocess=lambda x: datetime.strptime(x, "%d/%m/%y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")),
}

#STEP 2 : Process data (append to the load script created earlier in this run).
processor = Processor(mapping, source_filename=SOURCE, config_file=CONFIG,
                      schema_overrides=SCHEMA_OVERRIDES)
processor.process('data%smail.message.csv' % os.sep, {})
processor.write_to_file("load.sh", python_exe='', path='', append=True)

print('Supplier Message Done')
