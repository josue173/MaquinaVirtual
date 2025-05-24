import tkinter as tk
from tkinter import ttk, messagebox

class VMCreationDialog:
    def __init__(self, parent, vm_manager):
        self.vm_manager = vm_manager
        self.top = tk.Toplevel(parent)
        self.top.title("Crear Nueva Máquina Virtual")
        self.top.geometry("400x300")
        
        self.create_widgets()
    
    def create_widgets(self):
        self.main_frame = ttk.Frame(self.top, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nombre de la MV
        ttk.Label(self.main_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(self.main_frame)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # Memoria (MB)
        ttk.Label(self.main_frame, text="Memoria (MB):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.memory_entry = ttk.Entry(self.main_frame)
        self.memory_entry.insert(0, "1024")
        self.memory_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # vCPUs
        ttk.Label(self.main_frame, text="vCPUs:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.vcpus_entry = ttk.Entry(self.main_frame)
        self.vcpus_entry.insert(0, "1")
        self.vcpus_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        # Tamaño del disco
        ttk.Label(self.main_frame, text="Tamaño del disco (GB):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.disk_entry = ttk.Entry(self.main_frame)
        self.disk_entry.insert(0, "10")
        self.disk_entry.grid(row=3, column=1, sticky=tk.EW, pady=5)
        
        # Tipo de SO
        ttk.Label(self.main_frame, text="Tipo de SO:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.os_type = ttk.Combobox(self.main_frame, values=["linux", "windows"])
        self.os_type.current(0)
        self.os_type.grid(row=4, column=1, sticky=tk.EW, pady=5)
        
        # Ruta de la imagen ISO
        ttk.Label(self.main_frame, text="Imagen ISO:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.iso_entry = ttk.Entry(self.main_frame)
        self.iso_entry.grid(row=5, column=1, sticky=tk.EW, pady=5)
        
        # Botones
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        self.btn_create = ttk.Button(
            button_frame, 
            text="Crear", 
            command=self.create_vm
        )
        self.btn_create.pack(side=tk.LEFT, padx=5)
        
        self.btn_cancel = ttk.Button(
            button_frame, 
            text="Cancelar", 
            command=self.top.destroy
        )
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        
        # Configurar expansión de columnas
        self.main_frame.columnconfigure(1, weight=1)
    
    def create_vm(self):
        try:
            name = self.name_entry.get()
            memory = int(self.memory_entry.get())
            vcpus = int(self.vcpus_entry.get())
            disk_size = int(self.disk_entry.get())
            os_type = self.os_type.get()
            iso_path = self.iso_entry.get()
            
            if not name or not iso_path:
                messagebox.showwarning("Advertencia", "Nombre e imagen ISO son requeridos")
                return
                
            self.vm_manager.create_vm(name, memory, vcpus, disk_size, os_type, iso_path)
            messagebox.showinfo("Éxito", "Máquina virtual creada correctamente")
            self.top.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Valores numéricos inválidos")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la MV: {str(e)}")