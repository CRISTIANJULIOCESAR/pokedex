import sys
import subprocess
import pkg_resources
import os
import sqlite3

# Para usar estilos y widgets mejorados (ttk)
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from PIL import Image, ImageTk
from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ============================
# 1. Verificación e Instalación de Dependencias (opcional)
# ============================
def install_packages(packages):
    """
    Instala paquetes usando pip.
    """
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *packages])
    except subprocess.CalledProcessError as e:
        print(f"Error al instalar paquetes: {e}")
        sys.exit(1)

required_packages = {'pillow', 'matplotlib'}
installed_packages = {pkg.key for pkg in pkg_resources.working_set}
missing_packages = required_packages - installed_packages

# Descomenta si deseas instalación automática
# if missing_packages:
#     print(f"Instalando paquetes faltantes: {missing_packages}")
#     install_packages(missing_packages)

# ============================
# 2. Manejo de Rutas de Recursos
# ============================
def resource_path(relative_path):
    """
    Obtiene la ruta absoluta al recurso, funcionando tanto en desarrollo como en PyInstaller.
    """
    try:
        # PyInstaller crea una carpeta temporal y establece _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ============================
# 3. Gestión de la Base de Datos
# ============================
def conectar_db():
    """
    Conecta a la base de datos 'pokemon.db' y verifica que exista.
    """
    db_path = resource_path('pokemon.db')
    if not os.path.exists(db_path):
        messagebox.showerror("Error", f"No se encontró la base de datos 'pokemon.db' en {db_path}.")
        sys.exit(1)
    return sqlite3.connect(db_path)

def buscar_pokemon_en_db(nombre):
    """
    Busca el Pokémon por nombre en la base de datos.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pokemon WHERE nombre=?", (nombre,))
    pokemon = cursor.fetchone()
    conn.close()
    return pokemon

# ============================
# 4. Funciones de Lógica
# ============================
def buscar_pokemon():
    """
    Lógica para el botón 'Buscar'.
    """
    nombre = entry_nombre.get().strip().lower()
    if not nombre:
        messagebox.showwarning("Error", "Por favor, escribe un nombre de Pokémon.")
        return

    pokemon = buscar_pokemon_en_db(nombre)
    if not pokemon:
        messagebox.showerror("Error", f"No se encontró el Pokémon '{nombre}'.")
        return

    mostrar_pokemon(pokemon)

def mostrar_pokemon(pokemon):
    """
    Muestra datos y gráficos del Pokémon en la sección de resultados.
    """
    # Limpiar área de resultados
    for widget in frame_resultados.winfo_children():
        widget.destroy()

    # Desempaquetar los campos de la base de datos
    # Ejemplo: (ID, Nombre, Tipo1, Tipo2, HP, Ataque, Defensa, 
    # At.Especial, Def.Especial, Velocidad, Imagen)
    (pokemon_id, nombre, tipo1, tipo2, hp, ataque, defensa, atesp, defesp, velocidad, imagen_blob) = pokemon

    # Mostrar información
    lbl_id = ttk.Label(frame_resultados, text=f"ID: {pokemon_id}", font=("Arial", 12))
    lbl_nombre = ttk.Label(frame_resultados, text=f"Nombre: {nombre}", font=("Arial", 12))
    lbl_tipo1 = ttk.Label(frame_resultados, text=f"Tipo 1: {tipo1}", font=("Arial", 12))
    lbl_tipo2 = ttk.Label(frame_resultados, text=f"Tipo 2: {tipo2 if tipo2 else 'N/A'}", font=("Arial", 12))

    lbl_id.grid(row=0, column=0, sticky="w", padx=5, pady=2)
    lbl_nombre.grid(row=1, column=0, sticky="w", padx=5, pady=2)
    lbl_tipo1.grid(row=2, column=0, sticky="w", padx=5, pady=2)
    lbl_tipo2.grid(row=3, column=0, sticky="w", padx=5, pady=2)

    # Mostrar imagen
    if imagen_blob:
        try:
            imagen = Image.open(BytesIO(imagen_blob))
            imagen = imagen.resize((150, 150), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(imagen)
            lbl_imagen = ttk.Label(frame_resultados, image=img_tk)
            lbl_imagen.image = img_tk  # Evita que Python elimine la referencia
            lbl_imagen.grid(row=0, column=1, rowspan=4, padx=10, pady=10)
        except Exception as e:
            print(f"Error al procesar la imagen: {e}")
            lbl_error_imagen = ttk.Label(
                frame_resultados,
                text="Error al cargar la imagen.",
                font=("Arial", 12),
                foreground="red"
            )
            lbl_error_imagen.grid(row=0, column=1, rowspan=4, padx=10, pady=10)
    else:
        lbl_no_imagen = ttk.Label(
            frame_resultados,
            text="No hay imagen disponible.",
            font=("Arial", 12),
            foreground="red"
        )
        lbl_no_imagen.grid(row=0, column=1, rowspan=4, padx=10, pady=10)

    # Crear gráfico radial
    stats = [hp, ataque, defensa, atesp, defesp, velocidad]
    labels = ['HP', 'Ataque', 'Defensa', 'At. Especial', 'Def. Especial', 'Velocidad']

    figure = Figure(figsize=(4, 3), dpi=100)
    subplot = figure.add_subplot(111, polar=True)

    from math import pi
    angles = [n / float(len(labels)) * 2 * pi for n in range(len(labels))]
    angles += angles[:1]
    stats += stats[:1]

    subplot.fill(angles, stats, color='blue', alpha=0.25)
    subplot.plot(angles, stats, color='blue', linewidth=2)
    subplot.set_xticks(angles[:-1])
    subplot.set_xticklabels(labels, fontsize=10)
    subplot.set_yticks([20, 40, 60, 80, 100])
    subplot.set_yticklabels([20, 40, 60, 80, 100], fontsize=8)

    # Integrar el gráfico en Tkinter
    canvas = FigureCanvasTkAgg(figure, frame_resultados)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=4, column=0, columnspan=2, pady=10, sticky="n")

# ============================
# 5. Creación de la Interfaz Gráfica
# ============================
def main():
    root = tk.Tk()
    root.title("Pokédex Mejorada")

    # Ajustar tamaño de la ventana y permitir (o no) redimensionar
    root.geometry("600x500")
    root.minsize(600, 500)  # Tamaño mínimo para una mejor experiencia

    # -----------------------------
    # Configurar el estilo (ttk)
    # -----------------------------
    style = ttk.Style()
    # style.theme_use('clam')   # Puedes probar distintos temas: 'default', 'clam', 'alt', 'classic'
    style.configure("TLabel", font=("Arial", 10))
    style.configure("TButton", font=("Arial", 10), padding=5)

    # -----------------------------
    # Frame principal (usando grid)
    # -----------------------------
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=0)  # Buscador
    root.rowconfigure(1, weight=1)  # Resultados

    # FRAME BUSQUEDA
    frame_busqueda = ttk.Frame(root, padding="10 10 10 10")
    frame_busqueda.grid(row=0, column=0, sticky="ew")

    # Etiqueta y campo de entrada
    lbl_instruccion = ttk.Label(frame_busqueda, text="Escribe el nombre del Pokémon:", font=("Arial", 12))
    lbl_instruccion.grid(row=0, column=0, sticky="w")

    global entry_nombre
    entry_nombre = ttk.Entry(frame_busqueda, font=("Arial", 12), width=20)
    entry_nombre.grid(row=1, column=0, sticky="w", pady=5)

    btn_buscar = ttk.Button(frame_busqueda, text="Buscar", command=buscar_pokemon)
    btn_buscar.grid(row=1, column=1, padx=10, sticky="e")

    # FRAME RESULTADOS
    global frame_resultados
    frame_resultados = ttk.Frame(root, padding="10 10 10 10")
    frame_resultados.grid(row=1, column=0, sticky="nsew")

    # Expansión en ambas direcciones
    frame_resultados.columnconfigure(0, weight=1)
    frame_resultados.rowconfigure(4, weight=1)

    # Iniciar la aplicación
    root.mainloop()

if __name__ == "__main__":
    main()


"""
pyinstaller --onefile --windowed \
    --add-data "pokemon.db:." \
    --name "pokedex" \
    pokedex.py


"""