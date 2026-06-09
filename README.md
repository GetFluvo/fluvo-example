This is a demonstration for the usage of [fluvo](https://github.com/GetFluvo/fluvo) and https://github.com/GetFluvo/addons

Choosing the right branch (one branch per Odoo version)
=======================================================
This repository is organised with **one branch per Odoo major version**. Check
out the branch that matches the version of the Odoo server you are importing
into:

| Branch            | Odoo version | Notes                                            |
|-------------------|--------------|--------------------------------------------------|
| `11.0`            | Odoo 11      | Legacy example (uses `ProductProcessorV10`).     |
| `18.0` (default)  | Odoo 18      | **You are here.**                                |
| `19.0`            | Odoo 19      | Uses the `json2` protocol with an API key.       |

```sh
git checkout 18.0   # for an Odoo 18 server (default)
git checkout 11.0   # for an Odoo 11 server
git checkout 19.0   # for an Odoo 19 server
```

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

`transform.sh` runs the Python transform scripts, which generate the data CSVs
into `data/` and (re)generate `load.sh` with the `fluvo import` commands.
`load.sh` then loads everything into your Odoo database.

You've all your data into your database
