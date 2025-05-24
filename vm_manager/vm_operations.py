import os
import subprocess
import libvirt
from typing import List, Dict, Optional

class VMManager:
    def __init__(self, connector):
        self.connector = connector

    def list_vms(self) -> List[Dict]:
        """Lista todas las máquinas virtuales con su estado"""
        conn = self.connector.get_connection()
        domains = conn.listAllDomains(0)
        
        vms = []
        for domain in domains:
            try:
                info = domain.info()
                vms.append({
                    'id': domain.ID() if domain.ID() >= 0 else "N/A",
                    'name': domain.name(),
                    'state': "running" if info[0] == libvirt.VIR_DOMAIN_RUNNING else "shutoff",
                    'memory': info[1] // 1024,  # Convertir a MB
                    'vcpus': info[3]  # Número de vCPUs
                })
            except libvirt.libvirtError:
                vms.append({
                    'id': "N/A",
                    'name': domain.name(),
                    'state': "shutoff",
                    'memory': "N/A",
                    'vcpus': "N/A"
                })
        return vms

    def start_vm(self, vm_name: str) -> None:
        """Inicia una máquina virtual por nombre"""
        conn = self.connector.get_connection()
        try:
            domain = conn.lookupByName(vm_name)
            if domain.create() < 0:
                raise Exception("No se pudo iniciar la VM (código negativo)")
        except libvirt.libvirtError as e:
            raise Exception(f"Error de Libvirt: {e}")

    def stop_vm(self, vm_identifier: str) -> None:
        """Detiene una VM por ID o nombre"""
        conn = self.connector.get_connection()
        try:
            if vm_identifier.isdigit():
                domain = conn.lookupByID(int(vm_identifier))
            else:
                domain = conn.lookupByName(vm_identifier)
            
            if domain.destroy() < 0:
                raise Exception("No se pudo detener la VM")
        except libvirt.libvirtError as e:
            raise Exception(f"Error de Libvirt: {e}")

    def create_vm(self, name: str, memory: int, vcpus: int, 
                disk_size: int, os_type: str, iso_path: str) -> libvirt.virDomain:
        """Crea una nueva VM con manejo robusto de errores"""
        # Validaciones iniciales
        if not os.path.exists(iso_path):
            raise Exception(f"Archivo ISO no encontrado: {iso_path}")
        
        disk_name = f"{name.replace(' ', '_')}.qcow2"
        disk_path = f"/var/lib/libvirt/images/{disk_name}"
        
        try:
            # 1. Crear disco virtual
            self._create_disk_image(disk_path, disk_size)
            
            # 2. Generar configuración XML
            xml_config = self._generate_vm_xml(
                name=name,
                memory=memory,
                vcpus=vcpus,
                os_type=os_type,
                iso_path=iso_path,
                disk_path=disk_path
            )
            
            # 3. Definir la VM
            domain = self.connector.get_connection().defineXML(xml_config.strip())
            if not domain:
                raise Exception("Error al definir dominio")
            
            return domain
            
        except Exception as e:
            # Limpieza en caso de error
            if os.path.exists(disk_path):
                os.remove(disk_path)
            raise Exception(f"No se pudo crear la MV: {str(e)}")

    def _create_disk_image(self, disk_path: str, size_gb: int) -> None:
        """Crea un disco virtual con los permisos correctos"""
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(disk_path), exist_ok=True, mode=0o775)
            
            # Crear disco (con sudo para permisos)
            subprocess.run(
                ['sudo', 'qemu-img', 'create', '-f', 'qcow2', disk_path, f'{size_gb}G'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ajustar permisos
            subprocess.run(
                ['sudo', 'chown', 'libvirt-qemu:libvirt', disk_path],
                check=True
            )
            subprocess.run(
                ['sudo', 'chmod', '660', disk_path],
                check=True
            )
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error al crear disco: {e.stderr}")

    def _generate_vm_xml(self, name: str, memory: int, vcpus: int,
                       os_type: str, iso_path: str, disk_path: str) -> str:
        """Genera el XML de configuración para la VM"""
        return f"""
        <domain type='kvm'>
            <name>{name}</name>
            <memory unit='MB'>{memory}</memory>
            <vcpu>{vcpus}</vcpu>
            <os>
                <type arch='x86_64' machine='pc-q35-6.2'>hvm</type>
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
                    <source file='{disk_path}'/>
                    <target dev='vda' bus='virtio'/>
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
                </graphics>
                <video>
                    <model type='qxl' ram='65536' vram='65536' heads='1'/>
                </video>
                <memballoon model='virtio'/>
            </devices>
        </domain>
        """