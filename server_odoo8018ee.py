from docker import DockerContainer
import os

ctnr = DockerContainer('odoo18mergal', 'odoo:18.1')
ctnr.set_localpath(os.path.abspath('.'))
ctnr.add_volume('odoo18ee.conf', '/etc/odoo/odoo.conf')
ctnr.add_volume('enterprise', '/mnt/enterprise')
ctnr.add_volume('extra-addons', '/mnt/extra-addons')
ctnr.add_volume('var_lib_odoo', '/var/lib/odoo')
ctnr.add_volume('odoo', '/mnt/odoo')
ctnr.add_port(8018, 8069)
ctnr.add_link("db5018", 'db')

# ctnr.add_extra_command("-u msp_customs_management")
# ctnr.add_extra_command("-u msp_account_payment_sheet")
# ctnr.add_extra_command("-u l10n_py_edi")
# ctnr.add_extra_command("-u msp_customs_management_analytic")
# ctnr.add_extra_command("-u account")
# ctnr.add_extra_command("-u l10n_py")

ctnr.run(stop_and_rebuild=True)
