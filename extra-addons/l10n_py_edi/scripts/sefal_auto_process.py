import requests
import time

url = 'http://localhost:5080/facturacion-api/enviar_datos.php'
method = "GET"
try:
    # print("Command", "enviar_datos")
    response = requests.request(method, url, timeout=15)
    # print(response.content.decode())

    vlog = {}
    vlog['path'] = url
    vlog['method'] = method
    vlog['response'] = response.content.decode()
    vlog['type'] = 'outbound'
    vlog['tag'] = 'sefal.service.process'
    log.register(**vlog)
    self.env.cr.commit()

except BaseException as errstr:
    print("Error: %s - %s - %s " % (url, method, errstr))

commands = ['consultaLote', 'recibeDE', 'envioLotes', 'consultaLote']
delays = [3, 35, 20, 0]

log = self.env['service.log']

for idx, cmd in enumerate(commands):
    # print("Command", cmd)
    url = "http://localhost:5080/sifen/v2/%s.php" % (cmd)
    method = "GET"
    try:
        response = requests.request(method, url, timeout=15)
        # print(response.content.decode())

        vlog = {}
        vlog['path'] = url
        vlog['method'] = method
        vlog['response'] = response.content.decode()
        vlog['type'] = 'outbound'
        vlog['tag'] = 'sefal.service.process'
        log.register(**vlog)
        self.env.cr.commit()

        time.sleep(delays[idx])
    except BaseException as errstr:
        print("Error: %s - %s - %s " % (url, method, errstr))




