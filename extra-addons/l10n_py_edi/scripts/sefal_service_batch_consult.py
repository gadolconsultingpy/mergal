import requests
import xmltodict

sequence = self.env['ir.sequence'].search([('code', '=', 'rEnviConsLoteDe')])

batch_control = self.env['lote.control'].search([("lote_num_sifen", ">", 0)])
for bc in batch_control:
    vals = {}
    vals['batch_consult_sequence'] = int(sequence.next_by_id())
    vals['batch_number'] = int(bc.lote_num_sifen)

    rEnviConsLoteDe_template = "l10n_py_edi.rEnviConsLoteDe"
    rEnviConsLoteDe = self.env['ir.qweb']._render(rEnviConsLoteDe_template, vals)
    # print("RESULTADO", rEnviConsLoteDe.decode())

    url = "https://sifen-test.set.gov.py/de/ws/consultas/consulta-lote.wsdl"
    headers = {}
    headers['Content-Type'] = "application/soap+xml"
    headers['SOAPAction'] = '"#%s"' % ("SiConsDE")

    response = requests.post(url=url, headers=headers, data=rEnviConsLoteDe, cert="/mnt/input/F1T_15401.pem")
    # print("RESPONSE", response.content.decode())
    xmltree = xmltodict.parse(response.content)
    # print(xmltree.keys())
    # print(xmltree.get("env:Envelope",{}).get("env:Body",{}).get("ns2:rRetEnviDe",{}).get("ns2:rProtDe",{}).keys())
    rProtDe = xmltree.get("env:Envelope", {}).get("env:Body", {}).get("ns2:rRetEnviDe", {}).get("ns2:rProtDe", {})
    dFecProc = rProtDe.get("ns2:dFecProc")
    dEstRes = rProtDe.get("ns2:dEstRes")
    gResProc = rProtDe.get("ns2:gResProc")
    dCodRes = gResProc.get("ns2:dCodRes")
    dMsgRes = gResProc.get("ns2:dMsgRes")
    print("=" * 30)
    print(bc.lote_num_sifen)
    print("dFecProc", dFecProc)
    print("dEstRes", dEstRes)
    print("dCodRes", dCodRes)
    print("dMsgRes", dMsgRes)
