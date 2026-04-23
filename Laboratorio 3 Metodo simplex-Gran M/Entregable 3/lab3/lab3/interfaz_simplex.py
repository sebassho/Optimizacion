# -*- coding: utf-8 -*-
from fractions import Fraction
from typing import List, Optional, Tuple
import customtkinter as ctk
from simplex import ejecutar_simplex, ejecutar_simplex_minimizacion, _formatear_numero


# Apariencia
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

def convertir_entrada_usuario_a_numero(texto: str) -> float:
    """
    Convierte la entrada del usuario en un número.
    Acepta números en formato decimal o fracción.
    Ejemplos válidos: 2, -3.5, 1/3, -5/2, 0,  7 / 4
    También acepta coma decimal: 3,5 -> 3.5
    """
    s = (texto or "").strip()
    if not s:
        return 0.0
    s = s.replace(",", ".")
    # Fracción simple a/b
    if "/" in s:
        parts = [p.strip() for p in s.split("/", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            num = Fraction(parts[0])
            den = Fraction(parts[1])
            if den == 0:
                raise ValueError("División por cero en fracción.")
            return float(num / den)
    # Decimal / entero (Fraction soporta strings tipo "3.5" también)
    return float(Fraction(s))


def tabla_a_texto_minimizacion_coloreado(
    tabla: List[List[float]],
    nombres_var: List[str],
    base: List[str],
    c: List[float],
    j_entrante: Optional[int] = None,
    i_saliente: Optional[int] = None,
    elemento_pivote: Optional[float] = None,
) -> List:
    """
    Genera tabla simplex GRAN M con colores para columna entrante, fila saliente y pivote.
    """

    def fmt(val: float, show_m=False) -> str:
        if show_m and abs(val - 1e6) < 1e3:
            return "M"
        if show_m and abs(val + 1e6) < 1e3:
            return "-M"
        if show_m and abs(val) < 1e-10:
            return "0"
        if show_m and abs(val) > 1e4:
            mult = val / 1e6
            if abs(mult - round(mult)) < 1e-6:
                return f"{int(round(mult))}M"
        if abs(val) < 1e-10:
            return "0"
        f = Fraction(val).limit_denominator(60)
        if abs(float(f) - float(val)) < 1e-10 and f.denominator != 1:
            return f"{f.numerator}/{f.denominator}"
        return _formatear_numero(val)

    num_cols = len(tabla[0])
    n_vars = len(nombres_var)
    ancho = 10
    resultado: List = []
    
    # Encabezado Cj
    cj_row = ["Cj", ""]
    for j in range(n_vars):
        var_name = nombres_var[j]
        if var_name.startswith("x"):
            idx = int(var_name[1:]) - 1
            if idx < len(c):
                cj_row.append(fmt(c[idx]))
            else:
                cj_row.append("0")
        else:
            cj_row.append("M" if var_name.startswith("A") else "0")
    cj_row.append("")
    linea = "  ".join(f"{x:^{ancho}}" for x in cj_row) + "\n"
    resultado.append((linea, "normal"))
    
    # Encabezado variables
    headers_display = ["VB"] + nombres_var + ["CR"]
    linea_header = ""
    for col_idx, h in enumerate(headers_display):
        if col_idx == 0:
            linea_header += f"{h:^{ancho}}"
        elif col_idx - 1 == j_entrante:
            linea_header += "  " + f"{h:^{ancho}}"  # Columna entrante
            resultado.append((linea_header, "normal"))
            resultado.append((" " * len(linea_header), "entrante"))  # Fondo
            linea_header = ""
        else:
            linea_header += "  " + f"{h:^{ancho}}"
    if linea_header:
        linea_header += "\n"
        resultado.append((linea_header, "normal"))
    
    sep = "  ".join("-" * ancho for _ in range(len(headers_display))) + "\n"
    resultado.append((sep, "normal"))

    # Restricciones - línea por línea con colores por celda
    for i in range(1, len(tabla)):
        vb = base[i - 1]
        fila_vals = [fmt(tabla[i][j], show_m=True) for j in range(num_cols - 1)]
        
        if vb.startswith("x"):
            idx = int(vb[1:]) - 1
            cj_base = c[idx] if idx < len(c) else 0.0
            cj_display = fmt(cj_base)
        else:
            cj_display = "M" if vb.startswith("A") else "0"
        
        # VB (columna 0)
        vb_display = f"{vb:^{ancho}}"
        if i == i_saliente:
            resultado.append((vb_display, "saliente"))
        else:
            resultado.append((vb_display, "normal"))
        
        # Columnas de variables
        for j in range(n_vars):
            val_str = fila_vals[j]
            es_pivote = (i == i_saliente and j == j_entrante)
            es_columna_entrante = (j == j_entrante)
            es_fila_saliente = (i == i_saliente)
            
            val_formato = f"{val_str:^{ancho}}"
            
            if es_pivote:
                resultado.append(("  ", "normal"))
                resultado.append((val_formato, "pivote"))
            elif es_columna_entrante:
                resultado.append(("  ", "normal"))
                resultado.append((val_formato, "entrante"))
            elif es_fila_saliente:
                resultado.append(("  ", "normal"))
                resultado.append((val_formato, "saliente"))
            else:
                resultado.append(("  " + val_formato, "normal"))
        
        # CR (último)
        cr_str = fmt(tabla[i][-1], show_m=True)
        cr_formato = f"{cr_str:^{ancho}}"
        if es_fila_saliente:
            resultado.append(("  ", "normal"))
            resultado.append((cr_formato, "saliente"))
        else:
            resultado.append(("  " + cr_formato, "normal"))
        
        resultado.append(("\n", "normal"))

    resultado.append((sep, "normal"))

    # Calcular Zj
    zj_row = ["Zj"]
    for j in range(n_vars):
        zj = 0.0
        for i in range(1, len(tabla)):
            vb = base[i - 1]
            if vb.startswith("x"):
                idx = int(vb[1:]) - 1
                cb = c[idx] if idx < len(c) else 0.0
            else:
                cb = 1e6 if vb.startswith("A") else 0.0
            zj += cb * tabla[i][j]
        if j == j_entrante:
            zj_row.append(f"{fmt(zj, show_m=True):^{ancho}}")
        else:
            zj_row.append(fmt(zj, show_m=True))
    
    zj_cr = 0.0
    for i in range(1, len(tabla)):
        vb = base[i - 1]
        if vb.startswith("x"):
            idx = int(vb[1:]) - 1
            cb = c[idx] if idx < len(c) else 0.0
        else:
            cb = 1e6 if vb.startswith("A") else 0.0
        zj_cr += cb * tabla[i][-1]
    zj_row.append(fmt(zj_cr, show_m=True))
    
    # Mostrar fila Zj con colores
    resultado.append((f"{zj_row[0]:^{ancho}}", "normal"))
    for j in range(1, len(zj_row) - 1):
        if j - 1 == j_entrante:
            resultado.append(("  ", "normal"))
            resultado.append((f"{zj_row[j]:^{ancho}}", "entrante"))
        else:
            resultado.append(("  " + f"{zj_row[j]:^{ancho}}", "normal"))
    resultado.append(("  " + f"{zj_row[-1]:^{ancho}}\n", "normal"))

    # Calcular Cj - Zj
    cj_zj_row = ["Cj-Zj"]
    for j in range(n_vars):
        var_name = nombres_var[j]
        if var_name.startswith("x"):
            idx = int(var_name[1:]) - 1
            cj_val = c[idx] if idx < len(c) else 0.0
        else:
            cj_val = 0.0 if not var_name.startswith("A") else 1e6
        
        zj = 0.0
        for i in range(1, len(tabla)):
            vb = base[i - 1]
            if vb.startswith("x"):
                idx_b = int(vb[1:]) - 1
                cb = c[idx_b] if idx_b < len(c) else 0.0
            else:
                cb = 1e6 if vb.startswith("A") else 0.0
            zj += cb * tabla[i][j]
        
        if j == j_entrante:
            cj_zj_row.append(f"{fmt(cj_val - zj, show_m=True):^{ancho}}")
        else:
            cj_zj_row.append(fmt(cj_val - zj, show_m=True))
    
    # Mostrar fila Cj-Zj con colores
    resultado.append((f"{cj_zj_row[0]:^{ancho}}", "normal"))
    for j in range(1, len(cj_zj_row)):
        if j - 1 == j_entrante:
            resultado.append(("  ", "normal"))
            resultado.append((f"{cj_zj_row[j]:^{ancho}}", "entrante"))
        else:
            resultado.append(("  " + f"{cj_zj_row[j]:^{ancho}}", "normal"))
    resultado.append(("\n", "normal"))

    # Información de pivoteo
    if j_entrante is not None and j_entrante < len(nombres_var):
        resultado.append((f"\n  ↓ Entrante: {nombres_var[j_entrante]}\n", "entrante"))
    if i_saliente is not None and 1 <= i_saliente <= len(base):
        resultado.append((f"  → Saliente: {base[i_saliente - 1]}\n", "saliente"))
    if elemento_pivote is not None:
        resultado.append((f"  ◆ Pivote: {fmt(elemento_pivote, show_m=True)}\n", "normal"))

    return resultado


def tabla_a_texto_minimizacion(
    tabla: List[List[float]],
    nombres_var: List[str],
    base: List[str],
    c: List[float],
    j_entrante: Optional[int] = None,
    i_saliente: Optional[int] = None,
    elemento_pivote: Optional[float] = None,
) -> str:
    """
    Convierte una tabla simplex GRAN M con formato exacto de las fotos:
    VB | x1 x2 ... | s1 A1 s2 A2 ... | CR
    Incluye filas: Zj (costo de oportunidad) y Cj-Zj (criterio de optimalidad)
    """

    def fmt(val: float, show_m=False) -> str:
        # Si es cercano a M
        if show_m and abs(val - 1e6) < 1e3:
            return "M"
        if show_m and abs(val + 1e6) < 1e3:
            return "-M"
        if show_m and abs(val) < 1e-10:
            return "0"
        
        # Expresiones con M (como "2M", "3-2M", etc.)
        if show_m and abs(val) > 1e4:
            mult = val / 1e6
            if abs(mult - round(mult)) < 1e-6:
                return f"{int(round(mult))}M"
        
        if abs(val) < 1e-10:
            return "0"
        f = Fraction(val).limit_denominator(60)
        if abs(float(f) - float(val)) < 1e-10 and f.denominator != 1:
            return f"{f.numerator}/{f.denominator}"
        return _formatear_numero(val)

    num_cols = len(tabla[0])
    n_vars = len(nombres_var)
    
    # Encabezado: VB | x1 x2 ... | s1 A1 s2 A2 ... | CR
    ancho = 9
    lineas: List[str] = []
    
    # Fila de encabezado Cj (coeficientes de la función objetivo)
    cj_row = ["Cj", ""]
    for j in range(n_vars):
        var_name = nombres_var[j]
        if var_name.startswith("x"):
            idx = int(var_name[1:]) - 1
            if idx < len(c):
                cj_row.append(fmt(c[idx]))
            else:
                cj_row.append("0")
        else:
            cj_row.append("M" if var_name.startswith("A") else "0")
    cj_row.append("")
    lineas.append("  ".join(f"{x:^{ancho}}" for x in cj_row))
    
    # Encabezado de variables: VB | x1 x2 ... | s1 A1 s2 A2 ... | CR
    headers_display = ["VB"] + nombres_var + ["CR"]
    lineas.append("  ".join(f"{h:^{ancho}}" for h in headers_display))
    
    sep = "  ".join("-" * ancho for _ in range(len(headers_display)))
    lineas.append(sep)

    # Restricciones (filas 1..m)
    for i in range(1, len(tabla)):
        vb = base[i - 1]
        fila_vals = [fmt(tabla[i][j], show_m=True) for j in range(num_cols - 1)]
        
        # Obtener Cj para la variable base
        if vb.startswith("x"):
            idx = int(vb[1:]) - 1
            cj_base = c[idx] if idx < len(c) else 0.0
            cj_display = fmt(cj_base)
        else:
            cj_display = "M" if vb.startswith("A") else "0"
        
        fila = [vb] + fila_vals + [fmt(tabla[i][-1], show_m=True)]
        marcador = "  ← pivote" if i_saliente is not None and i == i_saliente else ""
        lineas.append("  ".join(f"{x:^{ancho}}" for x in fila) + marcador)

    lineas.append(sep)

    # Calcular Zj (costo de oportunidad para cada columna)
    zj_row = ["Zj"]
    for j in range(n_vars):
        zj = 0.0
        for i in range(1, len(tabla)):
            vb = base[i - 1]
            if vb.startswith("x"):
                idx = int(vb[1:]) - 1
                cb = c[idx] if idx < len(c) else 0.0
            else:
                cb = 1e6 if vb.startswith("A") else 0.0
            zj += cb * tabla[i][j]
        zj_row.append(fmt(zj, show_m=True))
    
    # CR para Zj (valor de la función objetivo)
    zj_cr = 0.0
    for i in range(1, len(tabla)):
        vb = base[i - 1]
        if vb.startswith("x"):
            idx = int(vb[1:]) - 1
            cb = c[idx] if idx < len(c) else 0.0
        else:
            cb = 1e6 if vb.startswith("A") else 0.0
        zj_cr += cb * tabla[i][-1]
    zj_row.append(fmt(zj_cr, show_m=True))
    lineas.append("  ".join(f"{x:^{ancho}}" for x in zj_row))

    # Calcular Cj - Zj (criterio de optimalidad)
    cj_zj_row = ["Cj-Zj"]
    for j in range(n_vars):
        var_name = nombres_var[j]
        if var_name.startswith("x"):
            idx = int(var_name[1:]) - 1
            cj_val = c[idx] if idx < len(c) else 0.0
        else:
            cj_val = 0.0 if not var_name.startswith("A") else 1e6
        
        zj = 0.0
        for i in range(1, len(tabla)):
            vb = base[i - 1]
            if vb.startswith("x"):
                idx_b = int(vb[1:]) - 1
                cb = c[idx_b] if idx_b < len(c) else 0.0
            else:
                cb = 1e6 if vb.startswith("A") else 0.0
            zj += cb * tabla[i][j]
        
        cj_zj_row.append(fmt(cj_val - zj, show_m=True))
    cj_zj_row.append("")
    lineas.append("  ".join(f"{x:^{ancho}}" for x in cj_zj_row))

    if j_entrante is not None and j_entrante < len(nombres_var):
        lineas.append(f"\n  Entrante: {nombres_var[j_entrante]}")
    if i_saliente is not None and 1 <= i_saliente <= len(base):
        lineas.append(f"  Saliente: {base[i_saliente - 1]}")
    if elemento_pivote is not None:
        lineas.append(f"  Pivote: {fmt(elemento_pivote, show_m=True)}")

    return "\n".join(lineas)



def tabla_a_texto(
    tabla: List[List[float]],
    nombres_var: List[str],
    base: List[str],
    j_entrante: Optional[int] = None,
    i_saliente: Optional[int] = None,
    elemento_pivote: Optional[float] = None,
) -> str:
    """
    Convierte una tabla simplex MAXIMIZACIÓN en texto con el formato tipo cuaderno:
    VB | z | x1..xn | s1..sm | CR
    (restricciones primero, fila z al final).
    """

    def fmt(val: float) -> str:
        # Mostrar fracciones cuando sea razonable (p.ej. 0.3333 -> 1/3)
        if abs(val) < 1e-10:
            return "0"
        f = Fraction(val).limit_denominator(60)
        if abs(float(f) - float(val)) < 1e-10 and f.denominator != 1:
            return f"{f.numerator}/{f.denominator}"
        return _formatear_numero(val)

    num_cols = len(tabla[0])  # n + m + CR
    headers = ["VB", "z"] + nombres_var + ["CR"]
    ancho = 10
    lineas: List[str] = []
    sep = "  ".join("-" * ancho for _ in headers)
    lineas.append("  ".join(f"{h:^{ancho}}" for h in headers))
    lineas.append(sep)

    # Restricciones (filas 1..m): z=0
    for i in range(1, len(tabla)):
        fila_vals = [fmt(tabla[i][j]) for j in range(num_cols - 1)]
        fila = [base[i - 1], "0"] + fila_vals + [fmt(tabla[i][-1])]
        marcador = "  ← fila pivote" if i_saliente is not None and i == i_saliente else ""
        lineas.append("  ".join(f"{x:^{ancho}}" for x in fila) + marcador)

    # Fila z al final: z=1
    fila_z_vals = [fmt(tabla[0][j]) for j in range(num_cols - 1)]
    fila_z = ["z", "1"] + fila_z_vals + [fmt(tabla[0][-1])]
    lineas.append(sep)
    lineas.append("  ".join(f"{x:^{ancho}}" for x in fila_z))

    if j_entrante is not None and j_entrante < len(nombres_var):
        lineas.append(f"\n  Variable entrante (columna pivote): {nombres_var[j_entrante]}")
    if i_saliente is not None and 1 <= i_saliente <= len(base):
        lineas.append(f"  Variable saliente (fila pivote): {base[i_saliente - 1]}")
    if elemento_pivote is not None:
        lineas.append(f"  Elemento pivote: {fmt(elemento_pivote)}")

    return "\n".join(lineas)


def resultado_final_a_texto(resultado: dict, n: int) -> str:
    """Genera el texto del resultado final."""
    es_min = resultado.get("minimizacion", False)
    tipo = "mín" if es_min else "máx"
    lineas = ["═══════════════════════════════════════", "         RESULTADO FINAL", "═══════════════════════════════════════"]
    if resultado.get("optimo"):
        sol = resultado["solucion"]
        z = sol.get("z", 0)
        lineas.append(f"  Valor óptimo: z_{tipo} = {_formatear_numero(z)}")
        lineas.append("  Variables de decisión:")
        for i in range(n):
            xi = f"x{i+1}"
            val = sol.get(xi, 0.0)
            lineas.append(f"    {xi} = {_formatear_numero(val)}")
    elif resultado.get("no_acotado"):
        lineas.append("  El problema es no acotado (sin solución óptima finita).")
    elif resultado.get("max_iter"):
        lineas.append("  Se alcanzó el número máximo de iteraciones.")
    lineas.append("═══════════════════════════════════════")
    return "\n".join(lineas)


class AppSimplex(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Método Simplex - Programación Lineal")
        self.geometry("1200x750")
        self.minsize(900, 550)

        self.n_var = 2
        self.m_rest = 2
        self.modo_minimizar = True  # Por defecto minimización (Gran M)
        self.entries_objetivo: List[ctk.CTkEntry] = []
        self.entries_A: List[List[ctk.CTkEntry]] = []
        self.entries_b: List[ctk.CTkEntry] = []
        self.entries_tipos: List[ctk.CTkOptionMenu] = []  # tipo de restricción por fila
        self.frame_objetivo: Optional[ctk.CTkFrame] = None
        self.frame_restricciones: Optional[ctk.CTkFrame] = None
        self.frame_resultados: Optional[ctk.CTkFrame] = None
        self.text_resultados: Optional[ctk.CTkTextbox] = None

        self.construir_interfaz()

    def construir_interfaz(self):
        # Panel izquierdo: datos del problema
        panel_izq = ctk.CTkFrame(self, width=420, fg_color="gray15", corner_radius=10)
        panel_izq.pack(side="left", fill="y", padx=15, pady=15)

        # Título principal
        titulo = ctk.CTkLabel(panel_izq, text="Configurar Problema", font=("Courier", 16, "bold"))
        titulo.pack(anchor="w", padx=15, pady=(12, 15))

        # Configuración n y m
        config_frame = ctk.CTkFrame(panel_izq, fg_color="gray20", corner_radius=8)
        config_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        config_inner = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_inner.pack(fill="x", padx=12, pady=10)
        
        ctk.CTkLabel(config_inner, text="Nº variables:", font=("Courier", 13)).pack(side="left", padx=(0, 5))
        self.spin_n = ctk.CTkEntry(config_inner, width=60, font=("Courier", 13))
        self.spin_n.insert(0, "2")
        self.spin_n.pack(side="left", padx=5)
        
        ctk.CTkLabel(config_inner, text="  Nº restricciones:", font=("Courier", 13)).pack(side="left", padx=(15, 5))
        self.spin_m = ctk.CTkEntry(config_inner, width=60, font=("Courier", 13))
        self.spin_m.insert(0, "2")
        self.spin_m.pack(side="left", padx=5)
        
        ctk.CTkButton(config_frame, text="Generar formulario", command=self.generar_formulario, width=160, 
                     font=("Courier", 12), fg_color="#2E7D32", hover_color="#1B5E20", corner_radius=8).pack(
            side="right", padx=12, pady=10
        )

        # Función objetivo
        obj_label_frame = ctk.CTkFrame(panel_izq, fg_color="transparent")
        obj_label_frame.pack(fill="x", padx=10, pady=(15, 8))
        ctk.CTkLabel(obj_label_frame, text="📊 FUNCIÓN OBJETIVO", font=("Courier", 14, "bold")).pack(side="left", padx=5)

        # Selector Maximizar / Minimizar
        self.btn_modo = ctk.CTkButton(
            obj_label_frame,
            text="� MINIMIZAR",
            width=140,
            font=("Courier", 11, "bold"),
            fg_color="#7B1FA2",
            hover_color="#4A148C",
            corner_radius=8,
            command=self.toggle_modo,
        )
        self.btn_modo.pack(side="right", padx=5)

        self.frame_objetivo = ctk.CTkFrame(panel_izq, fg_color="gray20", corner_radius=8)
        self.frame_objetivo.pack(fill="x", padx=10, pady=(0, 12))
        self.generar_campos_funcion_objetivo()

        # Restricciones
        res_label = ctk.CTkLabel(
            panel_izq,
            text="🗐 RESTRICCIONES",
            font=("Courier", 14, "bold")
        )
        res_label.pack(anchor="w", padx=15, pady=(15, 8))
        self.frame_restricciones = ctk.CTkScrollableFrame(panel_izq, height=220, fg_color="transparent", corner_radius=8)
        self.frame_restricciones.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        self.generar_campos_restricciones()

        ctk.CTkButton(self, text="▶ RESOLVER", command=self.resolver_problema, height=50, 
                     font=("Courier", 13, "bold"), fg_color="#1565C0", hover_color="#0D47A1", corner_radius=10).pack(
            fill="x", padx=20, pady=15
        )

        # Panel derecho: resultados
        panel_der = ctk.CTkFrame(self, fg_color="gray15", corner_radius=10)
        panel_der.pack(side="right", fill="both", expand=True, padx=15, pady=15)
        ctk.CTkLabel(panel_der, text="📈 ITERACIONES Y RESULTADO", font=("Courier", 14, "bold")).pack(anchor="w", padx=15, pady=(12, 10))
        self.text_resultados = ctk.CTkTextbox(panel_der, font=("Courier", 12), wrap="word", fg_color="gray20", corner_radius=8)
        self.text_resultados.pack(fill="both", expand=True, pady=5)
        self.text_resultados.insert("1.0", "1. Ingresa el número de variables y restricciones\n2. Presiona 'Generar formulario'\n3. Completa los campos\n4. Presiona 'RESOLVER CON SIMPLEX'")

    def toggle_modo(self):
        self.modo_minimizar = not self.modo_minimizar
        if self.modo_minimizar:
            self.btn_modo.configure(text="🔽 MINIMIZAR", fg_color="#7B1FA2", hover_color="#4A148C")
        else:
            self.btn_modo.configure(text="🔼 MAXIMIZAR", fg_color="#1565C0", hover_color="#0D47A1")

    def generar_campos_funcion_objetivo(self):
        self._limpiar_frame(self.frame_objetivo)
        self.entries_objetivo.clear()
        n = self._obtener_numero(self.spin_n, 2, 1, 12)
        # Mostrar fórmula de referencia
        formula = " + ".join([f"[ ]·x{i+1}" for i in range(n)])
        ctk.CTkLabel(self.frame_objetivo, text=f"z = {formula}", font=("Courier", 13, "bold")).pack(anchor="w", padx=10, pady=8)
        
        # Campos de entrada
        entrada_frame = ctk.CTkFrame(self.frame_objetivo, fg_color="transparent")
        entrada_frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(entrada_frame, text="Ingresa los coeficientes:", font=("Courier", 12)).pack(anchor="w", pady=(0, 5))
        
        campos_frame = ctk.CTkFrame(self.frame_objetivo, fg_color="transparent")
        campos_frame.pack(fill="x", padx=10, pady=(0, 10))
        # Valores por defecto: Min Z = 3x1 + 8x2
        valores_defecto = [3, 8, 5, 4, 1, 2, 3, 4, 5, 6, 7, 8]
        for i in range(n):
            inner = ctk.CTkFrame(campos_frame, fg_color="transparent")
            inner.pack(side="left", padx=3, pady=3)
            ctk.CTkLabel(inner, text=f"x{i+1}:", font=("Courier", 12, "bold")).pack(side="left", padx=2)
            e = ctk.CTkEntry(inner, width=65, placeholder_text="0", font=("Courier", 12))
            e.insert(0, str(valores_defecto[i]))
            e.pack(side="left", padx=2)
            self.entries_objetivo.append(e)

    def generar_campos_restricciones(self):
        self._limpiar_frame(self.frame_restricciones)
        self.entries_A.clear()
        self.entries_b.clear()
        self.entries_tipos.clear()
        n = self._obtener_numero(self.spin_n, 2, 1, 12)
        m = self._obtener_numero(self.spin_m, 2, 1, 20)
        self.n_var, self.m_rest = n, m
        
        # Mostrar fórmula de referencia
        formula = " + ".join([f"[ ]·x{i+1}" for i in range(n)])
        ctk.CTkLabel(self.frame_restricciones, text=f"Plantilla: {formula} ≤/≥/= [ ]", font=("Courier", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 12))
        
        # Valores por defecto para las restricciones
        # x1 + 4x2 >= 3/2
        # x1 + 2x2 >= 1/2
        coef_default = [
            [1, 4, 2, 1, 3, 2],
            [1, 2, 1, 2, 1, 3],
            [1, 2, 3, 1, 2, 1],
        ]
        b_default = [1.5, 0.5, 3]
        tipos_default = [">=", ">=", "<="]
        
        for i in range(m):
            restriccion_frame = ctk.CTkFrame(self.frame_restricciones, fg_color="gray25", corner_radius=6)
            restriccion_frame.pack(fill="x", pady=5, padx=5)
            
            # Encabezado de restricción
            header = ctk.CTkLabel(restriccion_frame, text=f"Restricción {i+1}", font=("Courier", 12, "bold"))
            header.pack(anchor="w", padx=10, pady=(8, 8))
            
            # Campos de coeficientes
            coef_frame = ctk.CTkFrame(restriccion_frame, fg_color="transparent")
            coef_frame.pack(fill="x", padx=10, pady=(0, 8))
            
            fila_entries = []
            for j in range(n):
                campo_frame = ctk.CTkFrame(coef_frame, fg_color="transparent")
                campo_frame.pack(side="left", padx=2, pady=2)
                ctk.CTkLabel(campo_frame, text=f"x{j+1}:", font=("Courier", 11, "bold")).pack(side="left", padx=1)
                e = ctk.CTkEntry(campo_frame, width=50, placeholder_text="0", font=("Courier", 11))
                val = coef_default[i][j] if i < len(coef_default) and j < len(coef_default[i]) else 0
                e.insert(0, str(val))
                e.pack(side="left", padx=1)
                fila_entries.append(e)
            
            # Tipo de restricción + término independiente
            derecha_frame = ctk.CTkFrame(restriccion_frame, fg_color="transparent")
            derecha_frame.pack(fill="x", padx=10, pady=(0, 8))
            tipo_menu = ctk.CTkOptionMenu(
                derecha_frame,
                values=["<=", ">=", "="],
                width=70,
                font=("Courier", 11, "bold"),
                fg_color="gray35",
                button_color="gray40",
                dropdown_fg_color="gray30",
            )
            tipo_defecto = tipos_default[i] if i < len(tipos_default) else "<="
            tipo_menu.set(tipo_defecto)
            tipo_menu.pack(side="left", padx=(0, 4))
            ctk.CTkLabel(derecha_frame, text="b:", font=("Courier", 11, "bold")).pack(side="left", padx=2)
            eb = ctk.CTkEntry(derecha_frame, width=65, placeholder_text="0", font=("Courier", 11))
            val_b = b_default[i] if i < len(b_default) else 0
            eb.insert(0, str(val_b))
            eb.pack(side="left", padx=2)
            
            self.entries_A.append(fila_entries)
            self.entries_b.append(eb)
            self.entries_tipos.append(tipo_menu)

    def _limpiar_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _obtener_numero(self, entry, default=2, min_val=1, max_val=12):
        try:
            n = int(entry.get())
        except ValueError:
            n = default
        n = max(min_val, min(n, max_val))
        entry.delete(0, "end")
        entry.insert(0, str(n))
        return n

    def generar_formulario(self):
        self.generar_campos_funcion_objetivo()
        self.generar_campos_restricciones()

    def leer_datos_del_usuario(self) -> Tuple[List[float], List[List[float]], List[float], List[str]]:
        c = [self._parse_safe(e) for e in self.entries_objetivo]
        A = [[self._parse_safe(e) for e in fila] for fila in self.entries_A]
        b = [self._parse_safe(e) for e in self.entries_b]
        tipos = [m.get() for m in self.entries_tipos]
        return c, A, b, tipos

    def _parse_safe(self, entry):
        try:
            return convertir_entrada_usuario_a_numero(entry.get())
        except ValueError:
            return 0.0

    def resolver_problema(self):
        c, A, b, tipos = self.leer_datos_del_usuario()
        n, m = len(c), len(b)
        
        if not n or not m:
            self._mostrar_error("Error: indica al menos 1 variable y 1 restricción.")
            return
        if len(A) != m or any(len(fila) != n for fila in A):
            self._mostrar_error("Error: dimensiones incorrectas.")
            return

        try:
            if self.modo_minimizar:
                historial, resultado = ejecutar_simplex_minimizacion(c, A, b, tipos)
                tipo_str = "MINIMIZACIÓN (Gran M)"
            else:
                historial, resultado = ejecutar_simplex(c, A, b)
                tipo_str = "MAXIMIZACIÓN"
        except Exception as ex:
            self._mostrar_error(f"Error al ejecutar Simplex:\n{ex}")
            return

        salida = [f"MÉTODO SIMPLEX - {tipo_str}", ""]
        for it, (tabla, nombres_var, base, j_entrante, i_saliente, ep) in enumerate(historial):
            salida.append(f"——— Iteración {it + 1} ———")
            if self.modo_minimizar:
                salida.append(tabla_a_texto_minimizacion(tabla, nombres_var, base, c, j_entrante, i_saliente, ep))
            else:
                salida.append(tabla_a_texto(tabla, nombres_var, base, j_entrante, i_saliente, ep))
            salida.append("")

        if resultado.get("infactible"):
            salida.append("═══════════════════════════════════════")
            salida.append("  PROBLEMA INFACTIBLE")
            salida.append("  (variable artificial permaneció en la base)")
            salida.append("═══════════════════════════════════════")
        else:
            salida.append(resultado_final_a_texto(resultado, n))

        self.text_resultados.delete("1.0", "end")
        self.text_resultados.insert("1.0", "\n".join(salida))

    def _mostrar_error(self, msg):
        self.text_resultados.delete("1.0", "end")
        self.text_resultados.insert("1.0", msg)


def main():
    app = AppSimplex()
    app.mainloop()


if __name__ == "__main__":
    main()
