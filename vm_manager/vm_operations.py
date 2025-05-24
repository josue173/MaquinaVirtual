import libvirt
import os

class VMManager:
    def __init__(self, connector):
        self.connector = connector
    
    def list_vms(self):
        conn = self.connector.get_connection()
        domains = conn.listAllDomains(0)

        vms = []
        for domain in domains:
            try:
                vms.append({
                    'id': domain.ID() if domain.ID() >= 0 else "N/A",
                    'name': domain.name(),
                    'state': "running" if domain.isActive() else "shutoff",
                    'memory': domain.info()[1] // 1024,  # Memoria en MB
                    'vcpus': domain.info()[3]  # vCPUs
                })
            except libvirt.libvirtError:
                # Si falla, usar valores por defecto
                vms.append({
                    'id': "N/A",
                    'name': domain.name(),
                    'state': "shutoff",
                    'memory': "N/A",
                    'vcpus': "N/A"
                })
        return vms
    
    def start_vm(self, vm_name):
        conn = self.connector.get_connection()
        try:
            domain = conn.lookupByName(vm_name)  # Buscar por nombre
            if domain.create() < 0:  # Iniciar VM
                raise Exception("Error al iniciar la VM (código de retorno negativo)")
        except libvirt.libvirtError as e:
            raise Exception(f"Error de Libvirt: {e}")
    
    def stop_vm(self, vm_id):
        conn = self.connector.get_connection()
        try:
            vm_id = int(vm_id)
            domain = conn.lookupByID(vm_id)
        except:
            domain = conn.lookupByName(vm_id)
        
        if domain.destroy() < 0:
            raise Exception("No se pudo detener la máquina virtual")
    
    def create_vm(self, name, memory, vcpus, disk_size, os_type, iso_path):
        # Eliminar espacios del nombre para el archivo de disco
        disk_name = name.replace(" ", "_") + ".qcow2"
        disk_path = f"/var/lib/libvirt/images/{disk_name}"

        # Verificar si el directorio existe
        if not os.path.exists('/var/lib/libvirt/images'):
            os.makedirs('/var/lib/libvirt/images', mode=0o775)
            os.chown('/var/lib/libvirt/images', 0, 109)  # root:libvirt

        # Crear el disco (manejar espacios en la ruta)
        os.system(f"qemu-img create -f qcow2 '{disk_path}' {disk_size}G")
        os.chown(disk_path, 64055, 109)  # libvirt-qemu:libvirt
        os.chmod(disk_path, 0o660)

        # Crear el XML de definición de la máquina virtual
        xml_template = f"""
        <domain type='kvm'>
            <name>{name}</name>
            <memory unit='MB'>{memory}</memory>
            <vcpu>{vcpus}</vcpu>
            <os>
                <type arch='x86_64' machine='pc-q35-6.2'>hvm</type>
                <boot dev='cdrom'/>
            </os>
            <features>
                <acpi/>
                <apic/>
                <vmport state='off'/>
            </features>
            <devices>
                <emulator>/usr/bin/qemu-system-x86_64</emulator>
                <disk type='file' device='cdrom'>
                    <driver name='qemu' type='raw'/>
                    <source file='{iso_path}'/>
                    <target dev='sda' bus='sata'/>
                    <readonly/>
                    <boot order='1'/>
                </disk>
                <disk type='file' device='disk'>
                    <driver name='qemu' type='qcow2'/>
                    <source file='/var/lib/libvirt/images/{name}.qcow2'/>
                    <target dev='vda' bus='virtio'/>
                    <boot order='2'/>
                </disk>
                <controller type='usb' index='0' model='qemu-xhci' ports='15'/>
                <controller type='sata' index='0'/>
                <controller type='virtio-serial' index='0'/>
                <interface type='network'>
                    <source network='default'/>
                    <model type='virtio'/>
                </interface>
                <graphics type='spice' autoport='yes'>
                    <listen type='address'/>
                    <image compression='off'/>
                </graphics>
                <video>
                    <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='1'/>
                </video>
                <memballoon model='virtio'/>
            </devices>
        </domain>
        """

        graphics_xml = """
        <devices>
            <graphics type='spice' autoport='yes'>
                <listen type='address'/>
            </graphics>
            <video>
                <model type='qxl' ram='65536' vram='65536' vgamem='16384' heads='1'/>
            </video>
        </devices>
        """
        
        xml_template = f"""
        <domain type='kvm'>
            <!-- Configuración existente -->
            {graphics_xml}
        </domain>
        """
        
        # Crear el disco virtual
        disk_path = f"/var/lib/libvirt/images/{name}.qcow2"
        if os.path.exists(disk_path):
            raise Exception(f"El disco {disk_path} ya existe")
        
        # Crear el disco con qemu-img (requiere qemu-utils instalado)
        os.system(f"qemu-img create -f qcow2 {disk_path} {disk_size}G")
        
        # Definir la máquina virtual
        domain = conn.defineXML(xml_template.strip())
        if domain is None:
            raise Exception("No se pudo definir la máquina virtual")
        
        return domain