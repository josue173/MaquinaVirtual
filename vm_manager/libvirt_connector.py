import libvirt

class LibvirtConnector:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = libvirt.open('qemu:///system')
            if self.connection is None:
                raise Exception("No se pudo conectar a QEMU/KVM")
        except libvirt.libvirtError as e:
            raise Exception(f"Error de conexión Libvirt: {e}")
    
    def get_connection(self):
        if not self.connection or not self.connection.isAlive():
            self.connect()
        return self.connection
    
    def close(self):
        if self.connection:
            self.connection.close()