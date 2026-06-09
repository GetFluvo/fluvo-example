# -*- coding: utf-8 -*-
import os
import polars as pl
from fluvo.lib import mapper
from fluvo.lib.transform import ProductProcessorV10
from prefix import *

CONFIG = 'conf%stest_connection.conf' % os.sep
SOURCE = 'origin%sproduct.csv' % os.sep

context = {'create_product_product' : False, 'tracking_disable' : True}

#STEP 1 : Category and Parent Category
categ_parent_map = {
    'id' : mapper.m2o(CATEGORY_PREFIX, 'categoy'),
    'name' : mapper.val('categoy'),
}

categ_map = {
    'id' : mapper.m2o(CATEGORY_PREFIX, 'Sub Category'),
    'parent_id/id' : mapper.m2o(CATEGORY_PREFIX, 'categoy'),
    'name' : mapper.val('Sub Category'),
}

# Read the comma-separated source file once; every other processor reuses the
# loaded dataframe to avoid re-reading the CSV. All commands accumulate in the
# single load.sh created earlier in this run (append=True everywhere).
categ_parent_processor = ProductProcessorV10(categ_parent_map, source_filename=SOURCE,
                                             separator=',', config_file=CONFIG)
categ_parent_processor.process('data%sproduct.category.parent.csv' % os.sep,
                               {'model': 'product.category'}, 'set')
categ_parent_processor.write_to_file("load.sh", python_exe='', path='', append=True)

dataframe = categ_parent_processor.dataframe

categ_processor = ProductProcessorV10(categ_map, dataframe=dataframe, config_file=CONFIG)
categ_processor.process('data%sproduct.category.csv' % os.sep, {}, 'set')
categ_processor.write_to_file("load.sh", python_exe='', path='', append=True)

#STEP 2 : Product Template mapping
template_map = {
 'id' : mapper.m2o(TEMPLATE_PREFIX, 'ref'),
 'categ_id/id': mapper.m2o(CATEGORY_PREFIX, 'Sub Category'),
 'standard_price': mapper.num('cost'),
 'list_price': mapper.num('public_price'),
 'default_code': mapper.val('ref'),
 'name': mapper.val('name'),
}
template_processor = ProductProcessorV10(template_map, dataframe=dataframe, config_file=CONFIG)
template_processor.process('data%sproduct.template.csv' % os.sep,
                           {'worker': 4, 'batch_size': 10, 'context': context}, 'set')
template_processor.write_to_file("load.sh", python_exe='', path='', append=True)

vendor_map = {
    'id': mapper.m2o(SUPPLIER_INFO_PREFIX, 'ref'),
    'partner_id/id': mapper.m2o(SUPPLIER_PREFIX, 'vendor'),
    'price': mapper.num('public_price'),
    'product_tmpl_id/id':  mapper.m2o(TEMPLATE_PREFIX, 'ref'),
}
vendor_processor = ProductProcessorV10(vendor_map, dataframe=dataframe, config_file=CONFIG)
vendor_processor.process('data%sproduct.supplierinfo.csv' % os.sep,
                         {'worker': 4, 'batch_size': 10, 'groupby': 'product_tmpl_id/id',
                          'context': context}, 'set')
vendor_processor.write_to_file("load.sh", python_exe='', path='', append=True)

#STEP 3: Attribute List
attribute_list = ['Color', 'Gender', 'Size_H', 'Size_W']

#Generate a csv with the id, name for attribute based on the column
attribute_processor = ProductProcessorV10({}, dataframe=dataframe, config_file=CONFIG)
attribute_processor.process_attribute_data(attribute_list, ATTRIBUTE_PREFIX,
    'data%sproduct.attribute.csv' % os.sep,
    {'worker': 4, 'batch_size': 10, 'context': context})
attribute_processor.write_to_file("load.sh", python_exe='', path='', append=True)

#STEP 4: Attribute Value
# process_attribute_value_data unpivots the attribute columns and collects the
# unique (attribute, value) pairs into product.attribute.value records. The
# generated XML ids use "<value_prefix>.<attribute>_<value>", which the
# attribute lines below reference.
attribute_value_processor = ProductProcessorV10({}, dataframe=dataframe, config_file=CONFIG)
attribute_value_processor.process_attribute_value_data(attribute_list,
    ATTRIBUTE_VALUE_PREFIX, ATTRIBUTE_PREFIX,
    'data%sproduct.attribute.value.csv' % os.sep,
    {'worker': 3, 'batch_size': 50, 'context': context, 'groupby': 'attribute_id/id'})
attribute_value_processor.write_to_file("load.sh", python_exe='', path='', append=True)

#STEP 5: Attribute Value Line
# One product.template.attribute.line per (product template, attribute). The
# source attribute columns are unpivoted (m2m=True) so that 'm2m_source_column'
# holds the attribute name and 'm2m_source_value' the attribute value.
context['update_many2many'] = True
line_mapping = {
   #XML_ID is product external_id (ref) + attribute name
   'id' : mapper.m2o_map(ATTRIBUTE_LINE_PREFIX, mapper.concat_mapper_all('_', mapper.val('m2m_source_column'), mapper.val('ref'))),
   'product_tmpl_id/id' :  mapper.m2o(TEMPLATE_PREFIX, 'ref'),
   'attribute_id/id' : mapper.m2o(ATTRIBUTE_PREFIX, 'm2m_source_column'),
   'value_ids/id' : mapper.m2o_map(ATTRIBUTE_VALUE_PREFIX, mapper.concat('_', 'm2m_source_column', 'm2m_source_value')),
}

line_processor = ProductProcessorV10(line_mapping, dataframe=dataframe, config_file=CONFIG)
line_processor.process('data%sproduct.template.attribute.line.csv' % os.sep,
    {'worker': 1, 'batch_size': 25, 'context': dict(context), 'groupby': 'product_tmpl_id/id'},
    'set', m2m=True, m2m_columns=attribute_list)
line_processor.write_to_file("load.sh", python_exe='', path='', append=True)
context.pop('update_many2many')

#STEP 6: Product Variant
product_mapping = {
   'id' : mapper.m2o_map(PRODUCT_PREFIX, mapper.concat('_', 'ref', 'Color', 'Gender', 'Size_H', 'Size_W'), skip=True),
   'barcode' : mapper.val('barcode'),
   'product_tmpl_id/id' : mapper.m2o(TEMPLATE_PREFIX, 'ref'),
   # Modern (V13+) attribute system: Odoo matches the variant by the attribute
   # value *names*. The mapper only emits a value when a 'template_id' column is
   # present, so we expose 'ref' as 'template_id' below.
   'product_template_attribute_value_ids/id': mapper.m2m_template_attribute_value(
           PT_ATTRIBUTE_VALUE_PREFIX, 'Color', 'Gender', 'Size_H', 'Size_W'
       ),
   'default_code': mapper.val('ref'),
   'standard_price': mapper.num('cost'),
}
# Expose 'ref' as 'template_id' so m2m_template_attribute_value emits values.
product_processor = ProductProcessorV10(product_mapping, dataframe=dataframe,
    config_file=CONFIG, preprocess=lambda df: df.with_columns(pl.col('ref').alias('template_id')))
product_processor.process('data%sproduct.product.csv' % os.sep,
    {'worker': 3, 'batch_size': 25, 'groupby': 'product_tmpl_id/id', 'context': context}, 'set')
product_processor.write_to_file("load.sh", python_exe='', path='', append=True)

print('Product Done')
