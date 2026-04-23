import tkinter as tk
from tkinter import ttk
import math
from grafo import Grafo

# Colores
BG       = "#F5F4F2"
PANEL    = "#FFFFFF"
BORDE    = "#E2E0DC"
ACENTO   = "#4F46A8"
ACENTO2  = "#3B348A"
DIAG     = "#ECECEC"
TEXTO    = "#1A1A2E"
SUAVE    = "#6B6B80"
VERDE    = "#22C55E"
AMARILLO = "#F59E0B"
ROJO     = "#EF4444"
RESBG    = "#F8F8FF"

# Fuentes
FT = ("Georgia", 17, "bold")
FS = ("Georgia", 10)
FL = ("Helvetica", 10)
FB = ("Helvetica", 10, "bold")
FM = ("Courier", 9)
FN = ("Helvetica", 8)
FX = ("Helvetica", 18, "bold")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Teoria de Grafos - Practica N 04")
        self.configure(bg=BG)
        self.geometry("1200x750")
        self.minsize(900, 600)

        self.grafo = None
        self.n_var    = tk.StringVar(value="3")
        self.tipo_var = tk.StringVar(value="Dirigido")
        self.botones_matriz = []
        self.camino_nodos = []
        self.ciclo_nodos  = []

        self._header()
        self._paso1()
        # Frame que contiene todo el paso 2 (oculto al inicio)
        self.frame2 = tk.Frame(self, bg=BG)

    # ------------------------------------------------------------------
    def _header(self):
        h = tk.Frame(self, bg=ACENTO, pady=10)
        h.pack(fill="x")
        tk.Label(h, text="Teoria de Grafos - Practica N 04",
                 bg=ACENTO, fg="white", font=FT).pack(side="left", padx=18)
        tk.Label(h,
                 text="Universidad de Los Llanos | Ingenieria de Sistemas | Optimizacion",
                 bg=ACENTO, fg="#C8C5F5", font=FS).pack(side="left", padx=4)
        tk.Label(h, text="Interactivo", bg="#6C63D8", fg="white",
                 font=FN, padx=8, pady=3).pack(side="right", padx=18)

    # ------------------------------------------------------------------
    def _paso1(self):
        p = tk.Frame(self, bg=PANEL, bd=1, relief="solid", padx=14, pady=12)
        p.pack(fill="x", padx=16, pady=10)

        tk.Label(p, text="PASO 1 - CONFIGURAR EL GRAFO",
                 bg=PANEL, fg=SUAVE, font=FN).grid(row=0, column=0,
                 columnspan=6, sticky="w", pady=(0, 8))

        tk.Label(p, text="Tamano n x n:", bg=PANEL,
                 fg=TEXTO, font=FL).grid(row=1, column=0, padx=(0, 4))
        tk.Entry(p, textvariable=self.n_var, width=4,
                 font=FL, bd=1, relief="solid").grid(row=1, column=1, padx=(0, 14))

        tk.Label(p, text="Tipo:", bg=PANEL,
                 fg=TEXTO, font=FL).grid(row=1, column=2, padx=(0, 4))
        ttk.Combobox(p, textvariable=self.tipo_var, width=16,
                     values=["Dirigido", "No dirigido"],
                     state="readonly", font=FL).grid(row=1, column=3, padx=(0, 18))

        self._boton(p, "Crear matriz", self._crear).grid(row=1, column=4, padx=(0, 6))
        self._boton(p, "Limpiar", self._reset, sec=True).grid(row=1, column=5)

    # ------------------------------------------------------------------
    def _crear(self):
        try:
            n = int(self.n_var.get())
            assert 2 <= n <= 10
        except Exception:
            self._dlg_error("Ingresa un numero entre 2 y 10.")
            return

        dirigido = self.tipo_var.get() == "Dirigido"
        self.grafo = Grafo(n, dirigido)
        self.botones_matriz = []
        self.camino_nodos = []
        self.ciclo_nodos  = []

        # Destruir contenido anterior del frame2
        for w in self.frame2.winfo_children():
            w.destroy()
        self.frame2.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # ---- Layout: tres columnas con grid -------------------------
        self.frame2.columnconfigure(0, weight=0)  # matriz
        self.frame2.columnconfigure(1, weight=1)  # grafo
        self.frame2.columnconfigure(2, weight=0)  # resultados
        self.frame2.rowconfigure(0, weight=1)

        # Col 0: matriz
        col0 = tk.Frame(self.frame2, bg=PANEL, bd=1, relief="solid",
                        padx=10, pady=10)
        col0.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        tk.Label(col0, text="PASO 2 - ARISTAS  (clic=1, diagonal=0)",
                 bg=PANEL, fg=SUAVE, font=FN).pack(anchor="w", pady=(0, 6))
        self._build_matriz(col0)

        # Col 1: canvas grafo
        col1 = tk.Frame(self.frame2, bg=PANEL, bd=1, relief="solid",
                        padx=8, pady=8)
        col1.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
        tk.Label(col1, text="Grafo", bg=PANEL, fg=SUAVE, font=FN).pack(anchor="w")
        self.cv = tk.Canvas(col1, bg="#EEEDF8", highlightthickness=0)
        self.cv.pack(fill="both", expand=True, pady=4)
        self.cv.bind("<Configure>", lambda e: self._draw())

        # Col 2: resultados
        col2_container = tk.Frame(self.frame2, bg=PANEL, bd=1, relief="solid", width=300)
        col2_container.grid(row=0, column=2, sticky="ns")
        col2_container.pack_propagate(False)

        # Crear canvas y scrollbar
        self.canvas_res = tk.Canvas(col2_container, bg=PANEL, highlightthickness=0)
        self.canvas_res.bind_all("<MouseWheel>", lambda e: self.canvas_res.yview_scroll(int(-1*(e.delta/120)), "units"))
        scrollbar = ttk.Scrollbar(col2_container, orient="vertical", command=self.canvas_res.yview)
        
        # Este será el frame donde realmente se dibujarán los resultados
        self.col_res = tk.Frame(self.canvas_res, bg=PANEL)
        
        # Configurar el scroll
        self.col_res.bind(
            "<Configure>",
            lambda e: self.canvas_res.configure(scrollregion=self.canvas_res.bbox("all"))
        )

        self.canvas_res.create_window((0, 0), window=self.col_res, anchor="nw", width=280)
        self.canvas_res.configure(yscrollcommand=scrollbar.set)

        # Empaquetar elementos del scroll
        self.canvas_res.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(self.col_res, text="RESULTADOS", bg=PANEL, fg=SUAVE, font=FN).pack(
            anchor="w", pady=(0, 6))
        tk.Label(self.col_res, text="Presiona Calcular\npara ver los resultados.",
                 bg=PANEL, fg=SUAVE, font=FL, justify="center").pack(pady=20)

    # ------------------------------------------------------------------
    def _build_matriz(self, parent):
        n = self.grafo.n
        nms = self.grafo.nombres_vertices()

        g = tk.Frame(parent, bg=PANEL)
        g.pack()

        # Fila encabezado
        tk.Label(g, text="", bg=PANEL, width=3).grid(row=0, column=0)
        for j, nm in enumerate(nms):
            tk.Label(g, text=nm, bg=PANEL, fg=SUAVE,
                     font=FN, width=3).grid(row=0, column=j+1)

        for i in range(n):
            row_w = []
            tk.Label(g, text=nms[i], bg=PANEL, fg=SUAVE,
                     font=FN, width=3).grid(row=i+1, column=0)
            for j in range(n):
                lbl = tk.Label(g, width=2, font=FB,
                               cursor="hand2" if i != j else "arrow",
                               padx=6, pady=5)
                lbl.grid(row=i+1, column=j+1, padx=2, pady=2)
                self._estilo(lbl, i, j)
                if i != j:
                    lbl.bind("<Button-1>",
                             lambda e, r=i, c=j: self._toggle(r, c))
                row_w.append(lbl)
            self.botones_matriz.append(row_w)

        # Botones
        br = tk.Frame(parent, bg=PANEL)
        br.pack(pady=(10, 2))
        self._boton(br, "Calcular", self._calcular).pack(side="left", padx=(0, 6))
        self._boton(br, "Limpiar todo", self._limpiar_mat,
                    sec=True).pack(side="left")
        self.lbl_cnt = tk.Label(br, text="0 aristas",
                                bg=PANEL, fg=SUAVE, font=FN)
        self.lbl_cnt.pack(side="left", padx=8)

    def _estilo(self, lbl, i, j):
        if i == j:
            lbl.config(text="0", bg=DIAG, fg=SUAVE, relief="flat", bd=0)
        elif self.grafo.matriz[i][j]:
            lbl.config(text="1", bg=ACENTO, fg="white", relief="flat", bd=0)
        else:
            lbl.config(text="0", bg=PANEL, fg=SUAVE, relief="solid", bd=1)

    def _toggle(self, i, j):
        self.grafo.toggle_arista(i, j)
        self._estilo(self.botones_matriz[i][j], i, j)
        if not self.grafo.dirigido:
            self._estilo(self.botones_matriz[j][i], j, i)
        self.lbl_cnt.config(text=f"{self.grafo.num_aristas()} aristas")
        self.camino_nodos = []
        self.ciclo_nodos  = []
        self._draw()

    def _limpiar_mat(self):
        self.grafo.limpiar()
        self.camino_nodos = []
        self.ciclo_nodos  = []
        for i in range(self.grafo.n):
            for j in range(self.grafo.n):
                self._estilo(self.botones_matriz[i][j], i, j)
        self.lbl_cnt.config(text="0 aristas")
        self._clear_res()
        self._draw()

    # ------------------------------------------------------------------
    def _draw(self):
        if not self.grafo or not hasattr(self, "cv"):
            return
        cv = self.cv
        cv.delete("all")

        W = cv.winfo_width()  or 330
        H = cv.winfo_height() or 310
        if W < 10: W = 330
        if H < 10: H = 310

        g = self.grafo
        n = g.n
        nms = g.nombres_vertices()
        R = 22
        OFF = 8
        cx, cy = W // 2, H // 2
        r = min(W, H) // 2 - R - 16

        pos = [
            (cx + r*math.cos(math.radians(-90 + i*360/n)),
             cy + r*math.sin(math.radians(-90 + i*360/n)))
            for i in range(n)
        ]

        cam_set = set(zip(self.camino_nodos, self.camino_nodos[1:])) \
            if len(self.camino_nodos) > 1 else set()
        cic_set = set(zip(self.ciclo_nodos, self.ciclo_nodos[1:])) \
            if len(self.ciclo_nodos) > 1 else set()

        def ecol(i, j):
            ni, nj = nms[i], nms[j]
            if (ni, nj) in cic_set: return ROJO
            if (ni, nj) in cam_set: return AMARILLO
            return ACENTO

        for i in range(n):
            for j in range(n):
                if not g.matriz[i][j]: continue
                if not g.dirigido and j < i: continue
                x1, y1 = pos[i]; x2, y2 = pos[j]
                ang = math.atan2(y2-y1, x2-x1)
                sx = x1 + R*math.cos(ang); sy = y1 + R*math.sin(ang)
                ex = x2 - R*math.cos(ang); ey = y2 - R*math.sin(ang)
                col = ecol(i, j)
                lw = 2.5 if col != ACENTO else 1.5
                if g.dirigido and g.matriz[j][i]:
                    px = -math.sin(ang)*OFF; py = math.cos(ang)*OFF
                    sx+=px; sy+=py; ex+=px; ey+=py
                if g.dirigido:
                    cv.create_line(sx, sy, ex, ey, fill=col, width=lw,
                                   arrow=tk.LAST, arrowshape=(10, 12, 4))
                else:
                    cv.create_line(sx, sy, ex, ey, fill=col, width=lw)

        for i, (x, y) in enumerate(pos):
            cv.create_oval(x-R, y-R, x+R, y+R,
                           fill=ACENTO, outline="white", width=2)
            cv.create_text(x, y, text=nms[i], fill="white", font=FB)

    # ------------------------------------------------------------------
    def _calcular(self):
        if not self.grafo: return
        g = self.grafo
        nms = g.nombres_vertices()

        camino = g.encontrar_camino(0, 1) if g.n >= 2 else None
        ciclo  = g.encontrar_ciclo()
        self.camino_nodos = camino or []
        self.ciclo_nodos  = ciclo  or []
        self._draw()
        self._clear_res()
        res = self.col_res
        conexo = g.es_fuertemente_conexo()

        # Estadisticas
        sf = tk.Frame(res, bg=PANEL)
        sf.pack(fill="x", pady=(0, 8))
        for val, etq, col in [
            (str(g.num_vertices()), "vertices", ACENTO),
            (str(g.num_aristas()),  "aristas",  ACENTO),
            ("Si" if conexo else "No",
             "F.conexo" if g.dirigido else "Conexo",
             VERDE if conexo else ROJO),
        ]:
            f = tk.Frame(sf, bg=col, padx=10, pady=6)
            f.pack(side="left", padx=3)
            tk.Label(f, text=val, bg=col, fg="white", font=FX).pack()
            tk.Label(f, text=etq, bg=col, fg="white", font=FN).pack()

        self._bloque(res, "Representacion matematica",
                     g.representacion_V() + "\n" + g.representacion_A(), ACENTO)

        # --- Nueva lógica de alineación en interfaz.py ---

# 1. Creamos el encabezado empezando con 'M' y dándole 4 espacios a cada nombre de vértice
        encabezado = "M".ljust(4) + "".join(nm.ljust(4) for nm in nms)
        mat = encabezado + "\n"

        for i, nm in enumerate(nms):
        # 2. El nombre de la fila (v1, v2...) ocupa 4 espacios
            fila_texto = nm.ljust(4) 
    
    # 3. Cada valor (0 o 1) también ocupa 4 espacios para coincidir con el encabezado
            valores = "".join(str(self.grafo.matriz[i][k]).ljust(4) for k in range(self.grafo.n))
    
            mat += fila_texto + valores + "\n"

# Finalmente se envía al bloque de resultados
        self._bloque(res, "Matriz de adyacencia", mat.rstrip(), ACENTO)

        la = g.lista_adyacencia()
        la_txt = "\n".join(
            f"{v} -> {' '.join(ns) if ns else 'vacio'}"
            for v, ns in la.items())
        self._bloque(res, "Lista de adyacencia", la_txt, ACENTO)

        grd = g.grados()
        if g.dirigido:
            g_txt = "  ".join(f"{v} e:{d['entrada']} s:{d['salida']}"
                              for v, d in grd.items())
        else:
            g_txt = "  ".join(f"{v} g:{d['grado']}" for v, d in grd.items())
        self._bloque(res, "Grado de nodos", g_txt, AMARILLO)

        c_txt = (" -> ".join(camino) + f"\nlongitud: {len(camino)-1}"
                 if camino else
                 f"Sin camino entre {nms[0]} y {nms[1] if g.n>=2 else '?'}")
        self._bloque(res, "Camino (primero encontrado)", c_txt, AMARILLO)

        z_txt = (" -> ".join(ciclo) + f"\nlongitud: {len(ciclo)-1}"
                 if ciclo else "Sin ciclos detectados")
        self._bloque(res, "Ciclo", z_txt, ROJO)

    def _clear_res(self):
        if not hasattr(self, "col_res"): return
        for w in self.col_res.winfo_children():
            w.destroy()
        # Restaurar titulo
        tk.Label(self.col_res, text="RESULTADOS",
                 bg=PANEL, fg=SUAVE, font=FN).pack(anchor="w", pady=(0, 6))

    # ------------------------------------------------------------------
    def _boton(self, parent, txt, cmd, sec=False):
        bg = PANEL if sec else ACENTO
        fg = TEXTO if sec else "white"
        b = tk.Button(parent, text=txt, command=cmd,
                      bg=bg, fg=fg, font=FB,
                      bd=1, relief="solid", padx=10, pady=4,
                      cursor="hand2",
                      activebackground=ACENTO2, activeforeground="white")
        b.bind("<Enter>", lambda e: b.config(
            bg=ACENTO2 if not sec else BORDE, fg="white"))
        b.bind("<Leave>", lambda e: b.config(bg=bg, fg=fg))
        return b

    def _bloque(self, parent, titulo, txt, col):
        f = tk.Frame(parent, bg=PANEL, pady=2)
        f.pack(fill="x", pady=1)
        tk.Label(f, text=titulo, bg=PANEL, fg=col, font=FB).pack(anchor="w")
        tk.Label(f, text=txt, bg=RESBG, fg=TEXTO, font=FM,
                 justify="left", padx=6, pady=3,
                 wraplength=260).pack(anchor="w", fill="x")

    def _reset(self):
        self.grafo = None
        for w in self.frame2.winfo_children():
            w.destroy()
        self.frame2.pack_forget()

    def _dlg_error(self, msg):
        top = tk.Toplevel(self)
        top.title("Error")
        top.configure(bg=PANEL)
        top.resizable(False, False)
        tk.Label(top, text=msg, bg=PANEL, fg=ROJO,
                 font=FL, padx=20, pady=16).pack()
        tk.Button(top, text="OK", command=top.destroy,
                  bg=ACENTO, fg="white", font=FB,
                  bd=0, padx=12, pady=4).pack(pady=(0, 12))
        top.grab_set()