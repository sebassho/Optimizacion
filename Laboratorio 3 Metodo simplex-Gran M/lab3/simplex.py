# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import List, Tuple, Optional

# Coeficientes de la función objetivo (max): z = c1*x1 + c2*x2 + ...
# Restricciones: A @ x <= b (cada fila de A con término independiente en b)


def _formatear_numero(val: float) -> str:
    """Formatea un número para mostrar en tabla (evita -0.0)."""
    if abs(val) < 1e-10:
        return "0"
    if abs(val - round(val)) < 1e-10:
        return str(round(val))
    return f"{val:.4g}"


def construir_tabla_inicial(
    c: List[float],
    A: List[List[float]],
    b: List[float],
) -> Tuple[List[List[float]], List[str], List[str]]:
    """
    Construye la tabla simplex inicial en forma estándar.
    - c: coeficientes de la función objetivo (max z = c·x).
    - A: matriz de restricciones (una fila por restricción).
    - b: términos independientes (A·x <= b).
    Devuelve: (tabla, nombres_columnas, variables_base).
    """
    n = len(c)  # variables de decisión
    m = len(b)  # restricciones
    # Nombres: x1..xn, s1..sm
    nombres_var = [f"x{i+1}" for i in range(n)] + [f"s{i+1}" for i in range(m)]
    # Base inicial: holguras s1, s2, ...
    base = [f"s{i+1}" for i in range(m)]

    # Tabla: fila 0 = función objetivo (z - c·x = 0 => coeficientes -c para x, 0 para s)
    # Filas 1..m = restricciones con holguras
    # Columnas: n+m variables + CR
    tabla = []
    # Fila z: coeficientes -c1,-c2,...,-cn, 0,...,0, CR=0
    fila_z = [-c[j] for j in range(n)] + [0.0] * m + [0.0]
    tabla.append(fila_z)

    for i in range(m):
        fila = list(A[i]) + [1.0 if j == i else 0.0 for j in range(m)] + [b[i]]
        tabla.append(fila)

    return tabla, nombres_var, base


def encontrar_variable_entrante(tabla: List[List[float]], n: int, m: int) -> Optional[int]:
    """
    Encuentra la variable que entra (criterio de optimalidad para maximización):
    busca la variable con coeficiente más negativo en la fila z.
    Solo considera variables de decisión (primeras n columnas).
    """
    fila_z = tabla[0]
    min_val = 0.0
    j_entrante = None
    for j in range(n):
        if fila_z[j] < min_val:
            min_val = fila_z[j]
            j_entrante = j
    return j_entrante


def encontrar_variable_saliente(
    tabla: List[List[float]],
    j_entrante: int,
    m: int,
) -> Optional[int]:
    """
    Encuentra la variable que sale usando el criterio de razón mínima:
    divide los términos independientes (CR) entre los coeficientes de la variable entrante (solo si coef > 0).
    Devuelve el índice de fila (1..m) que sale.
    """
    i_saliente = None
    min_ratio = float("inf")
    for i in range(1, m + 1):
        coef = tabla[i][j_entrante]
        if coef <= 0:
            continue
        cr = tabla[i][-1]
        ratio = cr / coef
        if ratio < min_ratio:
            min_ratio = ratio
            i_saliente = i
    return i_saliente


def hacer_pivoteo(
    tabla: List[List[float]],
    i_pivote: int,
    j_pivote: int,
) -> None:
    """Realiza el pivoteo: normaliza la fila pivote y hace ceros en la columna pivote (modifica tabla in-place)."""
    ep = tabla[i_pivote][j_pivote]
    if abs(ep) < 1e-12:
        raise ValueError("Elemento pivote numéricamente cero.")
    # Normalizar fila pivote
    for j in range(len(tabla[0])):
        tabla[i_pivote][j] /= ep
    # Hacer ceros en la columna pivote (todas las demás filas)
    for i in range(len(tabla)):
        if i == i_pivote:
            continue
        factor = tabla[i][j_pivote]
        for j in range(len(tabla[0])):
            tabla[i][j] -= factor * tabla[i_pivote][j]


def construir_tabla_gran_m(
    c: List[float],
    A: List[List[float]],
    b: List[float],
    tipos: List[str],  # lista de "<=", ">=" o "=" por cada restricción
    M: float = 1e6,
) -> Tuple[List[List[float]], List[str], List[str]]:
    """
    Construye la tabla inicial para MINIMIZACIÓN por el método de la Gran M.

    Variables añadidas por tipo de restricción:
      "<=": variable de holgura  s_i  (coef objetivo = 0)
      ">=": variable de exceso   e_i  (coef objetivo = 0)  +  artificial  a_i  (coef = +M)
      "=" : solo artificial      a_i  (coef = +M)

    La fila z representa  z - c·x - M·(suma artificiales) = 0,
    almacenada con los coeficientes ya listos para pivoteo (la fila z
    se actualiza eliminando las artificiales que están en la base inicial).
    """
    n = len(c)
    m = len(b)

    nombres_var: List[str] = [f"x{i+1}" for i in range(n)]
    # índices dentro de la fila de cada tipo de variable auxiliar
    col_holgura: List[Optional[int]] = []   # columna de holgura/exceso para fila i
    col_artificial: List[Optional[int]] = []  # columna de artificial para fila i

    col_idx = n  # próxima columna disponible

    for i in range(m):
        t = tipos[i]
        if t == "<=":
            nombres_var.append(f"s{i+1}")
            col_holgura.append(col_idx)
            col_artificial.append(None)
            col_idx += 1
        elif t == ">=":
            nombres_var.append(f"S{i+1}")   # exceso
            col_holgura.append(col_idx)
            col_idx += 1
            nombres_var.append(f"A{i+1}")   # artificial
            col_artificial.append(col_idx)
            col_idx += 1
        elif t == "=":
            col_holgura.append(None)
            nombres_var.append(f"A{i+1}")   # artificial
            col_artificial.append(col_idx)
            col_idx += 1
        else:
            raise ValueError(f"Tipo de restricción desconocido: {t!r}. Use '<=', '>=' o '='.")

    total_cols = col_idx  # sin CR
    # Coeficientes de z en función objetivo (minimización):
    # variables de decisión: c_j
    # holguras/excesos: 0
    # artificiales: +M
    coef_z = [0.0] * total_cols
    for j in range(n):
        coef_z[j] = c[j]
    for i in range(m):
        if col_artificial[i] is not None:
            coef_z[col_artificial[i]] = M

    # Construir filas de restricciones
    filas_rest: List[List[float]] = []
    base: List[str] = []
    for i in range(m):
        fila = [0.0] * (total_cols + 1)  # +1 para CR
        # coeficientes de variables de decisión
        for j in range(n):
            fila[j] = A[i][j]
        # holgura o exceso
        if col_holgura[i] is not None:
            fila[col_holgura[i]] = 1.0 if tipos[i] == "<=" else -1.0
        # artificial
        if col_artificial[i] is not None:
            fila[col_artificial[i]] = 1.0
        fila[-1] = b[i]
        filas_rest.append(fila)
        # variable básica inicial: artificial si existe, holgura si <=
        if col_artificial[i] is not None:
            base.append(nombres_var[col_artificial[i]])
        else:
            base.append(nombres_var[col_holgura[i]])

    # Fila z: almacenamos z - (coef_z · x) = 0
    # En minimización la fila z se escribe como:  z = coef_z · variables
    # Para el tableau: fila_z[j] = coef_z[j] para variables de decisión/auxiliares, CR = 0
    # Pero las artificiales que están en la base deben eliminarse de la fila z
    # haciendo: fila_z <- fila_z - M * fila_restriccion  para cada artificial en base
    fila_z = coef_z + [0.0]  # CR = 0 inicialmente

    for i in range(m):
        if col_artificial[i] is not None:
            # eliminar artificial de la fila z
            for j in range(total_cols + 1):
                fila_z[j] -= M * filas_rest[i][j]

    tabla = [fila_z] + filas_rest
    return tabla, nombres_var, base


def ejecutar_simplex_minimizacion(
    c: List[float],
    A: List[List[float]],
    b: List[float],
    tipos: Optional[List[str]] = None,
    M: float = 1e6,
    max_iter: int = 100,
) -> Tuple[List[Tuple[List[List[float]], List[str], List[str], Optional[int], Optional[int], Optional[float]]], dict]:
    """
    Ejecuta el método Simplex de la Gran M para MINIMIZACIÓN.

    Parámetros:
      c     : coeficientes de la función objetivo (min z = c·x).
      A     : matriz de restricciones.
      b     : términos independientes.
      tipos : lista de '<=', '>=' o '=' para cada restricción.
              Si se omite, se asume '<=' para todas.
      M     : valor de la penalización (por defecto 1e6).
    """
    n = len(c)
    m = len(b)
    if tipos is None:
        tipos = ["<="] * m

    tabla, nombres_var, base = construir_tabla_gran_m(c, A, b, tipos, M)
    n_total = len(nombres_var)  # todas las columnas sin CR
    historial = []

    # Identificar columnas de variables artificiales para verificar factibilidad
    cols_artificiales = {
        j for j, nombre in enumerate(nombres_var) if nombre.startswith("A")
    }

    for _ in range(max_iter):
        # Mismo criterio que maximización: entra la columna con coef más negativo en fila z
        fila_z = tabla[0]
        min_val = 1e-8
        j_entrante = None
        for j in range(n_total):
            if fila_z[j] < -min_val:
                if j_entrante is None or fila_z[j] < fila_z[j_entrante]:
                    j_entrante = j

        if j_entrante is None:
            # Óptimo encontrado — verificar que no haya artificial en la base
            historial.append((copy.deepcopy(tabla), list(nombres_var), list(base), None, None, None))
            artificiales_en_base = [vb for vb in base if vb.startswith("A")]
            if artificiales_en_base:
                return historial, {"optimo": False, "infactible": True}

            sol = {f"x{i+1}": 0.0 for i in range(n)}
            # Reconstruir z real (sin penalización M)
            z_real = sum(c[j] * 0.0 for j in range(n))
            for i, vb in enumerate(base):
                if vb.startswith("x"):
                    idx = int(vb[1:]) - 1
                    sol[vb] = tabla[i + 1][-1]
                    z_real += c[idx] * tabla[i + 1][-1]
            sol["z"] = z_real
            return historial, {"optimo": True, "solucion": sol, "minimizacion": True}

        i_saliente = encontrar_variable_saliente(tabla, j_entrante, m)
        if i_saliente is None:
            historial.append((copy.deepcopy(tabla), list(nombres_var), list(base), j_entrante, None, None))
            return historial, {"optimo": False, "no_acotado": True}

        ep = tabla[i_saliente][j_entrante]
        historial.append((copy.deepcopy(tabla), list(nombres_var), list(base), j_entrante, i_saliente, ep))
        base[i_saliente - 1] = nombres_var[j_entrante]
        hacer_pivoteo(tabla, i_saliente, j_entrante)

    return historial, {"optimo": False, "max_iter": True}


def ejecutar_simplex(
    c: List[float],
    A: List[List[float]],
    b: List[float],
    max_iter: int = 100,
) -> Tuple[List[Tuple[List[List[float]], List[str], List[str], Optional[int], Optional[int], Optional[float]]], dict]:
    """Ejecuta el método simplex y devuelve el historial de tablas."""
    n, m = len(c), len(b)
    tabla, nombres_var, base = construir_tabla_inicial(list(c), A, b)
    historial = []

    for _ in range(max_iter):
        j_entrante = encontrar_variable_entrante(tabla, n, m)
        
        if j_entrante is None:
            historial.append((copy.deepcopy(tabla), list(nombres_var), list(base), None, None, None))
            sol = {f"x{i+1}": 0.0 for i in range(n)}
            sol["z"] = tabla[0][-1]
            for i, vb in enumerate(base):
                if vb.startswith("x"):
                    sol[vb] = tabla[i + 1][-1]
            return historial, {"optimo": True, "solucion": sol}
        
        i_saliente = encontrar_variable_saliente(tabla, j_entrante, m)
        if i_saliente is None:
            historial.append((copy.deepcopy(tabla), list(nombres_var), list(base), j_entrante, None, None))
            return historial, {"optimo": False, "no_acotado": True}
        
        ep = tabla[i_saliente][j_entrante]
        historial.append((copy.deepcopy(tabla), list(nombres_var), list(base), j_entrante, i_saliente, ep))
        base[i_saliente - 1] = nombres_var[j_entrante]
        hacer_pivoteo(tabla, i_saliente, j_entrante)

    return historial, {"optimo": False, "max_iter": True}
