import sys 
import time
import tkinter as tk
from tkinter import ttk, messagebox
from vm_manager.libvirt_connector import LibvirtConnector
from vm_manager.vm_operations import VMManager
from gui.vm_creation_dialog import VMCreationDialog
import subprocess  # Añadir esta línea con las otras importaciones
import shutil      # Para verificar ejecutables

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    required = ['virt-viewer', 'virsh', 'qemu-system-x86_64']
    missing = [cmd for cmd in required if not shutil.which(cmd)]
    
    if missing:
        messagebox.showerror(
            "Dependencias faltantes",
            f"Componentes requeridos no encontrados:\n{', '.join(missing)}\n\n"
            "Instale con:\n"
            "sudo apt-get install virt-viewer libvirt-clients qemu-system-x86"
        )
        sys.exit(1)  # Sale del programa con código de error
    return True

class VirtualizationManagerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Gestor de Máquinas Virtuales - UMG SO2")
        self.master.geometry("800x600")
        
        # Conexión con Libvirt
        self.connector = LibvirtConnector()
        self.vm_manager = VMManager(self.connector)
        
        self.create_widgets()
        self.refresh_vm_list()
        
    def create_widgets(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de herramientas
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, pady=5)
        
        self.btn_create = ttk.Button(
            self.toolbar, 
            text="Crear MV", 
            command=self.show_create_vm_dialog
        )
        self.btn_create.pack(side=tk.LEFT, padx=2)
        
        self.btn_start = ttk.Button(
            self.toolbar, 
            text="Iniciar", 
            command=self.start_selected_vm
        )
        self.btn_start.pack(side=tk.LEFT, padx=2)
        
        self.btn_stop = ttk.Button(
            self.toolbar, 
            text="Detener", 
            command=self.stop_selected_vm
        )
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        
        self.btn_refresh = ttk.Button(
            self.toolbar, 
            text="Actualizar", 
            command=self.refresh_vm_list
        )
        self.btn_refresh.pack(side=tk.LEFT, padx=2)
        
        # Lista de máquinas virtuales
        self.vm_tree = ttk.Treeview(
            self.main_frame, 
            columns=('name', 'state', 'memory', 'vcpus'), 
            selectmode='browse'
        )
        
        self.vm_tree.heading('#0', text='ID')
        self.vm_tree.heading('name', text='Nombre')
        self.vm_tree.heading('state', text='Estado')
        self.vm_tree.heading('memory', text='Memoria (MB)')
        self.vm_tree.heading('vcpus', text='vCPUs')
        
        self.vm_tree.column('#0', width=50)
        self.vm_tree.column('name', width=150)
        self.vm_tree.column('state', width=100)
        self.vm_tree.column('memory', width=100)
        self.vm_tree.column('vcpus', width=80)
        
        self.vm_tree.pack(fill=tk.BOTH, expand=True)
        
        # Barra de estado
        self.status_bar = ttk.Label(
            self.main_frame, 
            text="Conectado a Libvirt", 
            relief=tk.SUNKEN
        )
        self.status_bar.pack(fill=tk.X, pady=5)
    
    def refresh_vm_list(self):
        for item in self.vm_tree.get_children():
            self.vm_tree.delete(item)
            
        try:
            vms = self.vm_manager.list_vms()
            for vm in vms:
                state = "Encendida" if vm['state'] == "running" else "Apagada"
                memory = vm['memory'] if vm['memory'] != "N/A" else "N/A"
                vcpus = vm['vcpus'] if vm['vcpus'] != "N/A" else "N/A"
                
                self.vm_tree.insert(
                    '', 'end', 
                    text=vm['id'], 
                    values=(vm['name'], state, memory, vcpus)
                )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron listar las VMs: {str(e)}")
    
    def show_create_vm_dialog(self):
        dialog = VMCreationDialog(self.master, self.vm_manager)
        self.master.wait_window(dialog.top)
        self.refresh_vm_list()
    
    def start_selected_vm(self):
        selected_item = self.vm_tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione una máquina virtual")
            return
            
        vm_name = self.vm_tree.item(selected_item)['values'][0]
        
        try:
            # Iniciar la VM
            self.vm_manager.start_vm(vm_name)
            
            # Lanzar el visor automáticamente
            self.launch_viewer(vm_name)
            
            self.refresh_vm_list()
            messagebox.showinfo("Éxito", f"MV {vm_name} iniciada y visor lanzado")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar la MV: {str(e)}")
    
    def launch_viewer(self, vm_name):
        """Versión mejorada con más opciones y depuración"""
        viewers = [
            ["virt-viewer", "-f", "--connect", "qemu:///system", vm_name],
            ["remote-viewer", "-f", "spice://localhost"],
            ["virt-manager", "--show-domain-console", vm_name],
            ["gtk3-vncviewer", "localhost"]
        ]
        
        for viewer_cmd in viewers:
            try:
                print(f"Intentando lanzar: {' '.join(viewer_cmd)}")  # Depuración
                process = subprocess.Popen(
                    viewer_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True  # Importante para GUI
                )
                # Esperar 2 segundos para ver si aparece
                time.sleep(2)
                if process.poll() is None:
                    return  # Éxito
            except FileNotFoundError:
                continue
            
        # Si llegamos aquí, todos fallaron
        error_msg = (
            "No se pudo abrir el visor automático.\n\n"
            "Pruebe manualmente con:\n"
            f"virt-viewer --connect qemu:///system {vm_name}\n\n"
            "O instale un visor con:\n"
            "sudo apt install virt-viewer virt-manager"
        )
        messagebox.showerror("Error de visualización", error_msg)    
    
    def stop_selected_vm(self):
        selected_item = self.vm_tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Seleccione una VM")
            return
        
        # Obtener solo el NOMBRE (no usar el ID)
        vm_name = self.vm_tree.item(selected_item, 'values')[0]  # Primera columna es el nombre
        
        try:
            self.vm_manager.stop_vm(vm_name)  # Siempre pasar el nombre como string
            self.refresh_vm_list()
            messagebox.showinfo("Éxito", f"VM {vm_name} detenida")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo detener: {str(e)}")