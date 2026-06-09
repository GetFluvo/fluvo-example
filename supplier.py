# -*- coding: utf-8 -*-
import os
from fluvo.lib import mapper
from fluvo.lib.transform import Processor
from datetime import datetime
from prefix import *

CONFIG = 'conf%stest_connection.conf' % os.sep
SOURCE = 'origin%ssupplier.csv' % os.sep

##STEP 1 : Define the mapping for every object to import
mapping = {
    'id' : mapper.m2o(SUPPLIER_PREFIX, 'Company_ID'),
    'name' : mapper.val('Company_Name'),
    'phone' : mapper.val('Phone'),
    'street' : mapper.val('address1'),
    'city' : mapper.val('city'),
    'zip' : mapper.val('zip code'),
    'country_id/id' : mapper.map_val(country_map, 'country'),
    'user_id': mapper.val('Account_Manager'),
}

contact_mapping = {
    'id': mapper.m2o(SUPPLIER_CONTACT_PREFIX, 'Contact Email'),
    'parent_id/id': mapper.m2o(SUPPLIER_PREFIX, 'Company_ID'),
    'email': mapper.val('Contact Email'),
    'name': mapper.concat(' ',  'Contact First Name', 'Contact Last Name'),
    'title/id': mapper.m2o(TITLE_PREFIX, 'Contact Title'),
}

title_map = {
    'id': mapper.m2o(TITLE_PREFIX, 'Contact Title'),
    'name': mapper.val('Contact Title', skip=True),
    'shortcut': mapper.val('Contact Title')
}

#STEP 2 : Read the source file once and process every mapping.
# Titles and supplier companies are referenced by the contacts, so they are
# written to the load script before the contacts (append=True everywhere
# because client.py already created load.sh in this run).
title_processor = Processor(title_map, source_filename=SOURCE, config_file=CONFIG)
title_processor.process('data%sres.partner.title.csv' % os.sep, {}, 'set')
title_processor.write_to_file("load.sh", python_exe='', path='', append=True)

supplier_processor = Processor(mapping, dataframe=title_processor.dataframe,
                               config_file=CONFIG)
supplier_processor.process('data%sres.partner.supplier.csv' % os.sep,
                           {'model': 'res.partner'})
supplier_processor.write_to_file("load.sh", python_exe='', path='', append=True)

contact_processor = Processor(contact_mapping, dataframe=title_processor.dataframe,
                              config_file=CONFIG)
contact_processor.process('data%sres.partner.supplier.contact.csv' % os.sep,
                          {'model': 'res.partner'})
contact_processor.write_to_file("load.sh", python_exe='', path='', append=True)

print('Supplier Done')
