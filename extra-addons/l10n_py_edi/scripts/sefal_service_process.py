import requests
import time

url = 'http://localhost:5080/facturacion-api/enviar_datos.php'
method = "GET"
try:
    print("Command", "enviar_datos")
    response = requests.request(method, url, timeout=15)
    print(response.content.decode())
except BaseException as errstr:
    print("Error 1: %s - %s - %s " % (url, method, errstr))

try:
    vlog = {}
    vlog['path'] = url
    vlog['method'] = method
    vlog['response'] = response.content.decode()
    vlog['type'] = 'outbound'
    vlog['tag'] = 'sefal.service.process.send.data'
    log = self.env['service.log']
    log.register(**vlog)
    # self.env.cr.commit()
except BaseException as errstr:
    print("Error 2: %s " % (errstr))

print("Waiting 5 seconds..")
time.sleep(5)

commands = ['consultaLote', 'recibeDE', 'envioLotes', 'consultaLote']
commands = []
delays = [3, 35, 20, 0]

for idx, cmd in enumerate(commands):
    print("=" * 30)
    print("Command", cmd)
    print("=" * 30)
    url = "http://localhost:5080/sifen/v2/%s.php" % (cmd)
    method = "GET"
    try:
        response = requests.request(method, url, timeout=15)
        print(response.content.decode())

        vlog = {}
        vlog['path'] = url
        vlog['method'] = method
        vlog['response'] = response.content.decode()
        vlog['type'] = 'outbound'
        vlog['tag'] = 'sefal.service.process.%s' % (cmd)
        log = self.env['service.log']
        log.register(**vlog)
        # self.env.cr.commit()

        time.sleep(delays[idx])
    except BaseException as errstr:
        print("Error 3: %s, %s, %s, %s" % (cmd, url, method, errstr))




