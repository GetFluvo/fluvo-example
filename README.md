This is a demonstration for the usage of [fluvo](https://github.com/GetFluvo/fluvo) and https://github.com/GetFluvo/addons

Installation
============
0) Install fluvo: `pip install fluvo` (or `uv pip install fluvo`)
1) Create an odoo 18 database named "load" with sale_management, purchase and [product_template_attribute_value_xmlid](https://github.com/GetFluvo/addons/tree/18.0/product_template_attribute_value_xmlid) installed
2) Check the settings in conf/connection.conf
3) Create users with name and login Thibault and Francois
4) activate the following lang French (BE) / Français (BE), English, Dutch / Nederlands

Your are good to go

Test
====
 
sh transform.sh
sh load.sh

You've all your data into your database
