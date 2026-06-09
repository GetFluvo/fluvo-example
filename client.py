# -*- coding: utf-8 -*-
import os
import polars as pl
from fluvo.lib import mapper
from fluvo.lib.transform import Processor
from datetime import datetime
from prefix import *

CONFIG = 'conf%sconnection.conf' % os.sep
SOURCE = 'origin%scontact.csv' % os.sep

# Force the date column to be read as a string so Polars does not try to
# infer a date type and reject the '%d/%m/%y' values during schema inference.
SCHEMA_OVERRIDES = {'Create ON': pl.String}

##STEP 1 : Define the mapping for every object to import
mapping = {
    'id' : mapper.m2o_map(CLIENT_PREFIX, mapper.concat('_', 'Client Name','zip code')),
    'name' : mapper.val('Client Name', skip=True),
    'phone' : mapper.val('Phone'),
    'street' : mapper.val('address1'),
    'city' : mapper.val('city'),
    'zip' : mapper.val('zip code'),
    'country_id/id' : mapper.map_val(country_map, 'country'),
    'lang' : mapper.map_val(lang_map, 'Language'),
    'image_1920' : mapper.binary("Image", "origin/img/"),
    'create_uid': mapper.val('Create BY'),
    'create_date': mapper.val('Create ON',
        postprocess=lambda x: datetime.strptime(x, "%d/%m/%y").strftime("%Y-%m-%d 00:00:00")),
    'category_id/id': mapper.m2m(PARTNER_CATEGORY_PREFIX, 'Tag', 'Fidelity Grade'),
}

# Categories ('Tag' column) and grades ('Fidelity Grade' column) are stored as
# comma-separated values, so they are exploded with process_m2m to create one
# res.partner.category record per value.
tag_mapping = {
   'id' : mapper.m2o(PARTNER_CATEGORY_PREFIX, 'Tag'),
   'name' :  mapper.val('Tag'),
}

grade_mapping = {
   'id' : mapper.m2o(PARTNER_CATEGORY_PREFIX, 'Fidelity Grade'),
   'name' :  mapper.val('Fidelity Grade'),
}

#STEP 2 : Read the source file once and process every mapping.
# The tags and grades (res.partner.category) must be imported BEFORE the
# partners that reference them, so they are written to the load script first.
tag_processor = Processor(tag_mapping, source_filename=SOURCE,
                          config_file=CONFIG, schema_overrides=SCHEMA_OVERRIDES)
tag_processor.process_m2m(id_column='Tag', m2m_columns=['Tag'],
                          filename_out='data%sres.partner.category.csv' % os.sep,
                          params={'model': 'res.partner.category'})
tag_processor.write_to_file("load.sh", python_exe='', path='')

# Reuse the already-loaded dataframe to avoid re-reading the CSV.
grade_processor = Processor(grade_mapping, dataframe=tag_processor.dataframe,
                            config_file=CONFIG)
grade_processor.process_m2m(id_column='Fidelity Grade', m2m_columns=['Fidelity Grade'],
                            filename_out='data%sres.partner.category.grade.csv' % os.sep,
                            params={'model': 'res.partner.category'})
grade_processor.write_to_file("load.sh", python_exe='', path='', append=True)

partner_processor = Processor(mapping, dataframe=tag_processor.dataframe,
                              config_file=CONFIG)
partner_processor.process('data%sres.partner.csv' % os.sep,
                          {'model': 'res.partner', 'worker': 2, 'batch_size': 20,
                           'context': {'write_metadata': True}})
partner_processor.write_to_file("load.sh", python_exe='', path='', append=True)

print('Client Done')
