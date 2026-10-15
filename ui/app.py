
import csv
import queue
import shutil
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from validators.engine import load_contract, validate_csv
import sys

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent

class ValidatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Data Contract Validator")
        self.geometry("1000x700")
        self.configure(bg="#f4f6f9")
        self.products = {}
        self.contract = None
        self.file = None
        self.events = queue.Queue()
        self.running = False
        self.product_var = tk.StringVar()
        self.file_var = tk.StringVar(value="Ningún archivo seleccionado")
        self.status_var = tk.StringVar(value="Pendiente")
        self.progress_var = tk.DoubleVar(value=0)
        self.create_ui()
        self.load_products()
        self.after(100, self.check_events)
    def create_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=7)
        style.configure("Treeview", rowheight=25)
        style.configure("Green.Horizontal.TProgressbar", background="#23995c")
        style.configure("Red.Horizontal.TProgressbar", background="#dc5252")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main = ttk.Frame(self, padding=15)
        main.grid(sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=3)
        main.rowconfigure(4, weight=2)
        ttk.Label(main, text="Data Contract Validator", font=("Arial", 18, "bold")).grid(row=0, sticky="w", pady=(0, 15))
        product_frame = ttk.LabelFrame(main, text="1. Producto de datos", padding=10)
        product_frame.grid(row=1, sticky="ew", pady=5)
        product_frame.columnconfigure(0, weight=1)
        self.product_combo = ttk.Combobox(product_frame, textvariable=self.product_var, state="readonly")
        self.product_combo.grid(row=0, column=0, sticky="ew")
        self.product_combo.bind("<<ComboboxSelected>>", self.change_product)
        ttk.Button(product_frame, text="Actualizar", command=self.load_products).grid(row=0, column=1, padx=5)
        file_frame = ttk.LabelFrame(main, text="2. Archivo de entrada", padding=10)
        file_frame.grid(row=2, sticky="ew", pady=5)
        file_frame.columnconfigure(0, weight=1)
        ttk.Label(file_frame, textvariable=self.file_var).grid(row=0, column=0, sticky="w")
        self.search_button = ttk.Button(file_frame, text="Buscar CSV", command=self.select_file)
        self.search_button.grid(row=0, column=1, padx=5)
        preview_frame = ttk.LabelFrame(main, text="3. Vista previa - Primeras 10 filas", padding=10)
        preview_frame.grid(row=3, sticky="nsew", pady=5)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(preview_frame, show="headings")
        self.table.grid(row=0, column=0, sticky="nsew")
        scroll_y = ttk.Scrollbar(preview_frame, orient="vertical", command=self.table.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.table.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
        self.table.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        result_frame = ttk.LabelFrame(main, text="4. Validación", padding=10)
        result_frame.grid(row=4, sticky="nsew", pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(2, weight=1)
        controls = ttk.Frame(result_frame)
        controls.grid(row=0, sticky="ew", pady=5)
        controls.columnconfigure(1, weight=1)
        self.validate_button = ttk.Button(controls, text="Validar archivo", command=self.start_validation, state="disabled")
        self.validate_button.grid(row=0, column=0)
        ttk.Label(controls, textvariable=self.status_var).grid(row=0, column=1, sticky="e")
        self.progress = ttk.Progressbar(result_frame, variable=self.progress_var, maximum=100, style="Green.Horizontal.TProgressbar")
        self.progress.grid(row=1, sticky="ew", pady=5)
        self.logs = tk.Text(result_frame, bg="#17212d", fg="white", wrap="word", state="disabled")
        self.logs.grid(row=2, sticky="nsew")
        self.logs.tag_configure("OK", foreground="#71d59a")
        self.logs.tag_configure("ERROR", foreground="#ff8989")
    def load_products(self):
        self.products = {}
        for path in sorted((ROOT / "contracts").rglob("*.yaml")):
            try:
                data = load_contract(path)
                label = f"{path.parent.name} / {data['contract']['name']}"
                self.products[label] = path
            except Exception as e:
                self.log(f"Contrato ignorado: {path.name} - {e}", "ERROR")
        self.product_combo["values"] = list(self.products)
        if self.products:
            self.product_combo.current(0)
            self.change_product()
        else:
            self.contract = None
            self.file = None
            self.product_var.set("")
            self.file_var.set("Ningún archivo seleccionado")
            self.validate_button.config(state="disabled")
            self.status_var.set("Sin contratos disponibles")
    def change_product(self, event=None):
        self.contract = self.products.get(self.product_var.get())
        self.file = None
        self.file_var.set("Ningún archivo seleccionado")
        self.validate_button.config(state="disabled")
        self.table.delete(*self.table.get_children())
        self.table["columns"] = ()
        self.progress_var.set(0)
        self.status_var.set("Pendiente")
    def select_file(self):
        if not self.contract:
            return messagebox.showwarning("Aviso", "Selecciona un producto de datos")
        source = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not source:
            return
        try:
            now = datetime.now()
            folder = ROOT / "input" / self.contract.parent.name / now.strftime("%Y/%m/%d/%H%M%S_%f")
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / Path(source).name
            shutil.copy2(source, destination)
            self.preview_file(destination)
            self.file = destination
            self.file_var.set(str(destination.relative_to(ROOT)))
            self.progress_var.set(0)
            self.status_var.set("Pendiente")
            self.validate_button.config(state="normal")
            self.log(f"Archivo cargado: {destination.name}")
        except Exception as e:
            self.file = None
            self.validate_button.config(state="disabled")
            messagebox.showerror("Error", str(e))
    def preview_file(self, path):
        self.table.delete(*self.table.get_children())
        self.table["columns"] = ()
        config = load_contract(self.contract)["file"]
        with open(path, encoding=config.get("encoding", "utf-8"), newline="") as f:
            reader = csv.reader(f, delimiter=config.get("delimiter", ","))
            columns = next(reader, [])
            ids = [str(i) for i in range(len(columns))]
            self.table["columns"] = ids
            for i, name in zip(ids, columns):
                self.table.heading(i, text=name)
                self.table.column(i, width=140, minwidth=60, stretch=True)
            for index, row in enumerate(reader):
                if index == 10:
                    break
                self.table.insert("", "end", values=(row + [""] * len(columns))[:len(columns)])
    def start_validation(self):
        if self.running or not self.file:
            return
        self.running = True
        self.validate_button.config(state="disabled")
        self.search_button.config(state="disabled")
        self.product_combo.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("Validando...")
        self.log("Iniciando validación")
        threading.Thread(target=self.run_validation, args=(self.file, self.contract), daemon=True).start()
    def run_validation(self, path, contract):
        try:
            config = load_contract(contract)["file"]
            with open(path, encoding=config.get("encoding", "utf-8"), newline="") as f:
                reader = csv.reader(f, delimiter=config.get("delimiter", ","), strict=True)
                next(reader, None)
                total = sum(1 for _ in reader)
            def progress(rows):
                percent = min(rows / total * 100, 99.9) if total else 99.9
                self.events.put(("progress", percent))
            result = validate_csv(path, contract, progress_callback=progress)
            self.events.put(("result", result))
        except Exception as e:
            self.events.put(("error", str(e)))
    def check_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress":
                    self.progress_var.set(event[1])
                    self.status_var.set(f"Validando {event[1]:.1f}%")
                elif event[0] == "result":
                    self.show_result(event[1])
                    self.finish_validation()
                elif event[0] == "error":
                    self.log(event[1], "ERROR")
                    self.status_var.set("Error de ejecución")
                    self.finish_validation()
        except queue.Empty:
            pass
        self.after(100, self.check_events)
    def show_result(self, result):
        self.progress_var.set(100)
        self.log(f"Registros: {result['total_rows']} | Válidos: {result['valid_rows']} | Inválidos: {result['invalid_rows']}")
        self.log(f"Total de errores: {result['error_count']}")
        if result["status"] == "APPROVED":
            self.status_var.set("APTO PARA INGESTA")
            self.progress.config(style="Green.Horizontal.TProgressbar")
            self.log("Archivo aprobado para ingesta", "OK")
        else:
            self.status_var.set("INGESTA BLOQUEADA")
            self.progress.config(style="Red.Horizontal.TProgressbar")
            for error in result["errors"]:
                self.log(f"Línea {error['row']} | {error['column']} | {error['message']} | {error['value']}", "ERROR")
            if result["errors_truncated"]:
                self.log("Se alcanzó el límite de errores mostrados", "ERROR")
            self.log("Archivo rechazado", "ERROR")
    def finish_validation(self):
        self.running = False
        self.validate_button.config(state="normal")
        self.search_button.config(state="normal")
        self.product_combo.config(state="readonly")
    def log(self, message, level="INFO"):
        now = datetime.now().strftime("%H:%M:%S")
        self.logs.config(state="normal")
        self.logs.insert("end", f"[{now}] [{level}] {message}\n", level)
        self.logs.see("end")
        self.logs.config(state="disabled")
