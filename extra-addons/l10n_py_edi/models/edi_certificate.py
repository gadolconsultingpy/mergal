from OpenSSL import crypto
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from datetime import datetime
from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone
import OpenSSL
import OpenSSL.crypto
import base64
import contextlib
import logging
import ssl
import tempfile
import os

try:
    from . import signxml
except:
    _logger = logging.getLogger(__name__)
    _logger.warning("signxml Library can not import")


class EDICertificate(models.Model):
    _name = 'edi.certificate'
    _description = 'EDI Certificate'

    name = fields.Char('Name', compute="_compute_name", store=True)
    signature_filename = fields.Char('Signature File Name')
    signature_key_file = fields.Binary(string='Certificate Key', help='Certificate Key in PFX format', required=True)
    signature_pass_phrase = fields.Char(string='Certificate Passkey', help='Passphrase for the certificate key',
                                        copy=False)
    pem_file = fields.Binary('PEM File')
    pem_filename = fields.Char('PEM File Name')
    private_key = fields.Text(compute='_check_credentials', string='Private Key', store=True, copy=False,
                              groups='base.group_system')
    certificate = fields.Text(compute='_check_credentials', string='Certificate', store=True, copy=False)
    cert_expiration = fields.Datetime(
            compute='_check_credentials', string='Expiration date', help='The date on which the certificate expires',
            store=True)
    subject_serial_number = fields.Char(
            compute='_check_serial_number', string='Subject Serial Number', store=True, readonly=False, copy=False,
            help='This is the document of the owner of this certificate.'
                 'Some certificates does not provide this number and you must fill it by hand')
    cert_public_bytes = fields.Text("Certificate Public Bytes")
    company_id = fields.Many2one(
            'res.company', string='Company', default=lambda self: self.env.company.id, required=True, readonly=True)
    user_id = fields.Many2one('res.users', 'Certificate Owner',
                              help='If this certificate has an owner, he will be the only user authorized to use it, '
                                   'otherwise, the certificate will be shared with other users of the current company')
    last_token = fields.Char('Last Token')
    token_time = fields.Datetime('Token Time')
    l10n_py_is_there_shared_certificate = fields.Boolean("There is Shared Certificate")

    @api.depends('cert_expiration', 'signature_key_file', 'signature_pass_phrase')
    def _compute_name(self):
        for rec in self:
            if rec.signature_key_file and rec.signature_pass_phrase and rec.cert_expiration:
                cert_file = base64.b64decode(rec.signature_key_file)
                cert_pass = rec.signature_pass_phrase.encode()
                key, cert, add_cert = pkcs12.load_key_and_certificates(data=cert_file, password=cert_pass,
                                                                       backend=backends.default_backend())
                owner = cert.subject.get_attributes_for_oid(oid=NameOID.COMMON_NAME)  # OK
                rec.name = "%s - %s " % (owner[0].value, rec.cert_expiration.strftime("%d/%m/%Y"))
            else:
                rec.name = "/"

    def open_certificate(self):
        cert_file = base64.b64decode(self.signature_key_file)
        cert_pass = self.signature_pass_phrase.encode()

        key, cert, add_cert = pkcs12.load_key_and_certificates(data=cert_file, password=cert_pass,
                                                               backend=backends.default_backend())

        cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)  # OK
        # print("".join(cert_pem.decode().split("\n")[1:-2])) #OK
        self.cert_public_bytes = "".join(cert_pem.decode().split("\n")[1:-2])

        serial_number = cert.subject.get_attributes_for_oid(oid=NameOID.SERIAL_NUMBER)  # OK
        self.subject_serial_number = serial_number[0].value
        owner = cert.subject.get_attributes_for_oid(oid=NameOID.COMMON_NAME)  # OK

        if not self.company_id.tz:
            msg = _("Missing Timezone in Company")
            raise UserError(msg)
        country_tz = timezone(self.company_id.tz)
        country_current_dt = self._get_cl_current_datetime()
        date_format = '%Y-%m-%d %H:%M:%S'
        not_valid_after = str(cert.not_valid_after)
        cert_expiration = country_tz.localize(datetime.strptime(not_valid_after, date_format))
        self.cert_expiration = cert_expiration.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if country_current_dt > cert_expiration:
            msg = _("The certificate is expired since %s") % self.cert_expiration
            raise UserError(msg)
        return key, cert, add_cert

    def get_certificate_data(self):
        cert_file = base64.b64decode(self.signature_key_file)
        cert_pass = self.signature_pass_phrase.encode()

        key, cert, add_cert = pkcs12.load_key_and_certificates(data=cert_file, password=cert_pass,
                                                               backend=backends.default_backend())
        return key, cert, add_cert

    def get_pem(self):
        cert_file = base64.b64decode(self.signature_key_file)
        cert_pass = self.signature_pass_phrase.encode()

        key, cert, add_cert = pkcs12.load_key_and_certificates(data=cert_file, password=cert_pass,
                                                               backend=backends.default_backend())

        cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)  # OK
        return cert_pem

    def get_pem_file_name(self):
        ''' Decrypts the .pfx file to be used with requests. '''
        pem_file = ""
        with tempfile.NamedTemporaryFile(suffix='.pem') as f_pem:
            # f_pem = open("/mnt/output/450092-0.pem", 'wb')
            pfx = self.signature_key_file
            p12 = OpenSSL.crypto.load_pkcs12(pfx, self.signature_pass_phrase.encode())
            f_pem.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()))
            f_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, p12.get_certificate()))
            ca = p12.get_ca_certificates()
            if ca is not None:
                for cert in ca:
                    f_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
            # f_pem.close()
            pem_file = f_pem.name
            print(["PEM File", pem_file])
        return pem_file

    def get_pem_file(self):
        ''' Decrypts the .pfx file to be used with requests. '''
        pem_file = ""
        with tempfile.NamedTemporaryFile(suffix='.pem') as t_pem:
            p12 = OpenSSL.crypto.load_pkcs12(self.signature_key_file, self.signature_pass_phrase.encode())
            t_pem.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()))
            t_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, p12.get_certificate()))
            ca = p12.get_ca_certificates()
            if ca is not None:
                for cert in ca:
                    t_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
        return t_pem

    # @contextlib.contextmanager
    def pfx_to_pem(self):
        ''' Decrypts the .pfx file to be used with requests. '''
        with tempfile.NamedTemporaryFile(suffix='.pem') as t_pem:
            f_pem = open(t_pem.name, 'wb')
            pfx = self.signature_key_file
            p12 = OpenSSL.crypto.load_pkcs12(pfx, self.signature_pass_phrase.encode())
            f_pem.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()))
            f_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, p12.get_certificate()))
            ca = p12.get_ca_certificates()
            if ca is not None:
                for cert in ca:
                    f_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
            f_pem.close()
            yield t_pem.name

    def get_cert(self):
        # HOW TO USE:
        with self.pfx_to_pem() as cert:
            # requests.post(url, cert=cert, data=payload)
            return cert

    def create_digest_value(self, digest_data):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(digest_data.encode())
        res = digest.finalize()
        res_enc = base64.b64encode(res)
        return res_enc.decode('utf-8')

    def create_signature_value(self, digest_value):
        key, cert, add_cert = self.open_certificate()
        sv = key.sign(digest_value.encode(),
                      padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                      algorithm=hashes.SHA256())
        return base64.b64encode(sv).decode('utf-8')

    def get_public_bytes(self):
        key, cert, add_cert = self.open_certificate()
        cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)  # OK
        # print("".join(cert_pem.decode().split("\n")[1:-2])) #OK
        return "".join(cert_pem.decode().split("\n")[1:-2])

    def _get_data(self):
        """ Return the signature_key_file (b64 encoded) and the certificate decrypted """
        self.ensure_one()
        try:
            signature_pass_phrase = self.signature_pass_phrase.encode()
            signature_file = base64.b64decode(self.signature_key_file)
            p12 = crypto.load_pkcs12(signature_file, signature_pass_phrase)
        except Exception as error:
            raise UserError(error)
        certificate = p12.get_certificate()
        cer_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, certificate)
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
        for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
            cer_pem = cer_pem.replace(to_del.encode('UTF-8'), b'')
        return cer_pem, certificate, key

    def test_certificate(self):
        """ Return the signature_key_file (b64 encoded) and the certificate decrypted """
        self.ensure_one()
        try:
            signature_pass_phrase = self.signature_pass_phrase.encode()
            signature_file = base64.b64decode(self.signature_key_file)
            p12 = crypto.load_pkcs12(signature_file, signature_pass_phrase)
        except Exception as error:
            raise UserError(error)
        certificate = p12.get_certificate()
        cer_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, certificate)
        print(cer_pem)
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
        for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
            cer_pem = cer_pem.replace(to_del.encode('UTF-8'), b'')
        text = "cer_pem: %s\n" % (cer_pem)
        text += "certificate: %s\n" % (certificate)
        text += "key: %s\n" % (key)
        return self.env['generic.message.box'].message("Certificate Result", text)

        # return cer_pem, certificate, key

    @api.depends('signature_key_file', 'signature_pass_phrase')
    def _check_credentials(self):
        """
        Check the validity of signature_key_file/key/signature_pass_phrase and fill the fields
        with the certificate values.
        """
        return
        country_tz = timezone(self.company_id.tz)
        country_current_dt = self._get_cl_current_datetime()
        date_format = '%Y%m%d%H%M%SZ'
        for record in self:
            if not record.signature_key_file or not record.signature_pass_phrase:
                continue
            try:
                certificate = record._get_data()
                cert_expiration = country_tz.localize(
                        datetime.strptime(certificate[1].get_notAfter().decode('utf-8'), date_format))
            except Exception as e:
                msg = _("The certificate signature_key_file is invalid: %s.") % e
                raise UserError(msg)
            # Assign extracted values from the certificate
            record.cert_expiration = cert_expiration.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            record.certificate = certificate[0]
            record.private_key = certificate[2]
            if country_current_dt > cert_expiration:
                msg = _("The certificate is expired since %s") % record.cert_expiration
                raise UserError(msg)

    @api.depends('signature_key_file', 'signature_pass_phrase')
    def _check_serial_number(self):
        return
        """
        This method is only for the readonly false compute
        """
        for record in self:
            if not record.signature_key_file or not record.signature_pass_phrase:
                continue
            try:
                certificate = record._get_data()
            except Exception as e:
                raise UserError(_('The certificate signature_key_file is invalid: %s.') % e)
            record.subject_serial_number = certificate[1].get_subject().serialNumber

    def _get_cl_current_datetime(self):
        """ Get the current datetime with the Chilean timezone. """
        return fields.Datetime.context_timestamp(
                self.with_context(tz=self.company_id.tz), fields.Datetime.now())

    def sign_content(self, content_str, reference_uri="", id_attribute="Id"):
        key, cert, addcert = self.get_certificate_data()

        data_to_sign = content_str.encode().decode('utf-8')
        data_xml = etree.fromstring(data_to_sign)

        signer = signxml.XMLSigner(c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#",
                                   method=signxml.methods.enveloped)

        signer.namespaces = {None: signxml.namespaces.ds}
        data_signed = signer.sign(data_xml, key=key, cert=[cert], reference_uri=reference_uri, id_attribute="Id")

        # data_signed = XMLSigner().sign(data_xml, key=key, cert=[cert])
        data_signed_str = etree.tostring(data_signed).decode('utf-8')

        return data_signed_str

    def validate_schema(self, data_xml):
        xsd_path = "/mnt/input/WS_SiConsRUC_v141.xsd"
        xmlschema_doc = etree.parse(xsd_path)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        result = xmlschema.validate(data_xml)
        return result

    @api.model
    def prepare_cert_file(self, company_id, recreate=False):
        comp = self.env['res.company'].browse(company_id)
        if not comp:
            msg = _("Missing Company Preparing Certificate")
            raise UserError(msg)
        # print(comp.certificate_id.pem_filename)
        cert_file_path = "/tmp/%s" % (comp.certificate_id.pem_filename)
        if recreate:
            if os.path.exists(cert_file_path):
                os.remove(cert_file_path)
        if not os.path.exists(cert_file_path):
            cert_file = open(cert_file_path, "wb")
            cert_content = base64.b64decode(comp.certificate_id.pem_file)
            cert_file.write(cert_content)
            cert_file.close()
            # print("CONTENT", cert_content)
            # print("Cert. File Created: %s" % (cert_file_path))
        # else:
        #     print("Cert. File Exists: %s" % (cert_file_path))
        return cert_file_path
