import os
import logging

_logger = logging.getLogger(__name__)


class DockerContainer:

    def __init__(self, name, template=''):
        self.name = name
        self.volumes = []
        self.ports = []
        self.links = []
        self.template = template
        self.local_path = ""  # Añadimos un atributo local_path
        self.extra_command = ""

    # Métodos para los atributos name y template
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_template(self, template):
        self.template = template

    def get_template(self):
        return self.template

    def set_localpath(self, local_path):
        self.local_path = local_path

    # Métodos para el atributo volumes
    def add_volume(self, host_src, cont_dest):
        host_src = os.path.join(self.local_path, host_src)  # Concatenamos local_path y host_src
        self.volumes.append((host_src, cont_dest))

    def get_volumes(self):
        return self.volumes

    # Métodos para el atributo ports
    def add_port(self, host_src, cont_dest):
        self.ports.append((host_src, cont_dest))

    def get_ports(self):
        return self.ports

    # Métodos para el atributo links
    def add_link(self, cont_src, cont_dest):
        self.links.append((cont_src, cont_dest))

    def get_links(self):
        return self.links

    def add_extra_command(self, extra_command):
        self.extra_command = extra_command  # Método para establecer el comando extra

    def prepare_command(self):
        command = f"docker run --name {self.name}"

        # Agregar volúmenes
        for host_src, cont_dest in self.volumes:
            command += f" -v {host_src}:{cont_dest}"

        # Agregar puertos
        for host_src, cont_dest in self.ports:
            command += f" -p {host_src}:{cont_dest}"

        # Agregar enlaces
        for cont_src, cont_dest in self.links:
            command += f" --link {cont_src}:{cont_dest}"

        # Agregar plantilla
        if self.template:
            command += f" -t {self.template}"

        if self.extra_command:
            command += f" {self.extra_command}"  # Agregar el comando extra al final
        return command

    # Método para ejecutar el contenedor
    def run(self, stop_and_rebuild=False):
        if stop_and_rebuild:
            _logger.info("STOP DOCKER CONTAINER")
            os.system(f"docker stop {self.name}")
            _logger.info("REMOVE DOCKER CONTAINER")
            os.system(f"docker rm {self.name}")

        command = self.prepare_command()
        _logger.info(command)
        # Ejecutar el comando
        os.system(command)

    def __repr__(self):
        return self.prepare_command()

#
# # Ejemplo de uso:
# container = DockerContainer(name='mi_contenedor', template='nginx')
# container.add_volume('/host/source', '/container/destination')
# container.add_port('8080', '80')
# container.add_link('mi_otro_contenedor', 'other_service')
#
# # Ejecutar el contenedor, deteniendo y reconstruyendo si es necesario
# container.run(stop_and_rebuild=True)
