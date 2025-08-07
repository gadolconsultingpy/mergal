import re
import zipfile
import logging
from odoo import api, models, fields, _
import os

_logger = logging.getLogger(__name__)

class TaxPayerProcess(models.TransientModel):
    _name = 'tax.payer.process'
    _description = 'Tax Payer Process'

    def process_slow(self):
        root_path = "/mnt/input/ruc"
        for file_name in sorted(os.listdir(root_path)):
            if not file_name.endswith('.zip'):
                continue
            _logger.info(f"Extracting {file_name}")
            full_path = f"{root_path}/{file_name}"
            with zipfile.ZipFile(full_path, 'r') as zip_ref:
                zip_ref.extractall(root_path)
        for file_name in sorted(os.listdir(root_path)):
            pattern = r"ruc[0-9]\.txt"
            matched = re.match(pattern, file_name)
            if matched:
                full_path = f"{root_path}/{file_name}"
                _logger.info(f"Processing {full_path}")
                lines_tdx = 0
                lines_rdx = 0
                lines_edx = 0
                with open(full_path, 'r') as file_obj:
                    for line in file_obj:
                        lines_tdx += 1
                        data = line.split("|")
                        if len(data) != 6:
                            _logger.warning("Wrong line data: [%s]" %(data))
                            lines_edx += 1
                            continue
                        try:
                            self.env['tax.payer'].create(
                                {
                                    'code':data[0],
                                    'name':data[1],
                                    'digit':data[2],
                                    'legacy_code':data[3],
                                    'status':data[4],
                                }
                            )
                            lines_rdx += 1
                        except BaseException as errstr:
                            lines_edx += 1
                    self.env.cr.commit()
                    os.remove(full_path)
                _logger.info(f"End {full_path}")
                _logger.info(f"Total: {lines_tdx}, OK: {lines_rdx}, Error: {lines_edx}")

    def process(self):
        root_path = "/mnt/input/ruc"
        for file_name in sorted(os.listdir(root_path)):
            if not file_name.endswith('.zip'):
                continue
            _logger.info(f"Extracting {file_name}")
            full_path = f"{root_path}/{file_name}"
            with zipfile.ZipFile(full_path, 'r') as zip_ref:
                zip_ref.extractall(root_path)
        _logger.info("Truncating table tax_payer...")
        self.env.cr.execute('TRUNCATE TABLE tax_payer RESTART IDENTITY')
        for file_name in sorted(os.listdir(root_path)):
            pattern = r"ruc[0-9]\.txt"
            matched = re.match(pattern, file_name)
            if matched:
                full_path = f"{root_path}/{file_name}"
                data_file_name = file_name.replace(".txt","_data.txt")
                data_full_path = f"{root_path}/{data_file_name}"
                _logger.info(f"Processing {full_path}")
                lines_tdx = 0
                lines_rdx = 0
                lines_edx = 0
                header = ['code','name','digit','legacy_code','status']
                data_file_obj = open(data_full_path, "w")
                data_file_obj.write("|".join(header))
                data_file_obj.write("\n")
                with open(full_path, 'r') as file_obj:
                    for line in file_obj:
                        lines_tdx += 1
                        line = line.strip("\n").replace("\\","-")
                        data = line.split("|")
                        if len(data) != 6:
                            _logger.warning("Wrong line data: [%s]" %(data))
                            lines_edx += 1
                            continue
                        try:
                            data_file_obj.write("|".join(data[0:5]))
                            data_file_obj.write("\n")
                            lines_rdx += 1
                        except BaseException as errstr:
                            lines_edx += 1
                    self.env.cr.commit()
                    os.remove(full_path)
                data_file_obj.flush()
                data_file_obj.close()
                _logger.info(f"End {full_path}")
                _logger.info(f"Total: {lines_tdx}, OK: {lines_rdx}, Error: {lines_edx}")

                data_file_obj = open(os.path.abspath(data_full_path), 'r')

                # Leer la primera línea para obtener los nombres de columna
                header = data_file_obj.readline().strip()
                columns = [col.strip() for col in header.split('|')]

                # Copiar el contenido del archivo en la tabla
                with data_file_obj as data_file:
                    _logger.info(f"Importing File: {data_full_path}")
                    next(data_file)  # Saltar la primera línea (ya hemos leído los nombres de columna)
                    self.env.cr._cnx.cursor().copy_from(data_file, 'tax_payer', sep='|', columns=tuple(columns))
                    _logger.info(f"File imported: {data_full_path}")
                    os.remove(data_full_path)

                # Confirmar los cambios en la base de datos
                self.env.cr.commit()

#1000000|CAÑETE GONZALEZ, JUANA DEL CARMEN|3|CAGJ761720E|ACTIVO|
