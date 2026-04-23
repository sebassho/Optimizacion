# -*- coding: utf-8 -*-
from typing import List, Optional
from simplex import ejecutar_simplex, ejecutar_simplex_minimizacion, _formatear_numero


def imprimir_tabla(
    tabla: List[List[float]],
    nombres_var: List[str],
    base: List[str],
    j_entrante: Optional[int] = None,
    i_saliente: Optional[int] = None,
    elemento_pivote: Optional[float] = None,
) -> None:
    """Imprime la tabla simplex y resalta la variable entrante, saliente y pivote."""
    num_cols = len(tabla[0])
    headers = ["VB", "CR"] + nombres_var
    print("\n" + "  ".join(f"{h:>8}" for h in headers))
    print("-" * (10 * len(headers)))
    fila0 = ["z", _formatear_numero(tabla[0][-1])] + [_formatear_numero(tabla[0][j]) for j in range(num_cols - 1)]
    print("  ".join(f"{x:>8}" for x in fila0))
    for i in range(1, len(tabla)):
        fila = [base[i-1], _formatear_numero(tabla[i][-1])] + [_formatear_numero(tabla[i][j]) for j in range(num_cols - 1)]
        marcador = "  ← pivote" if i_saliente is not None and i == i_saliente else ""
        print("  ".join(f"{x:>8}" for x in fila) + marcador)
    if j_entrante is not None:
        print(f"\n  Entrante: {nombres_var[j_entrante]} | Saliente: {base[i_saliente-1] if i_saliente else 'N/A'} | Pivote: {_formatear_numero(elemento_pivote) if elemento_pivote else 'N/A'}")


def mostrar_resultado_final(resultado: dict, n: int) -> None:
    """Muestra los valores óptimos de las variables y de z."""
    es_min = resultado.get("minimizacion", False)
    tipo = "mín" if es_min else "máx"
    print("\n" + "=" * 60)
    print("                    RESULTADO FINAL")
    print("=" * 60)
    if resultado.get("optimo"):
        sol = resultado["solucion"]
        z = sol.get("z", 0)
        print(f"  Valor óptimo de la función objetivo: z_{tipo} = {_formatear_numero(z)}")
        print("\n  Valores óptimos de las variables de decisión:")
        for i in range(n):
            xi = f"x{i+1}"
            val = sol.get(xi, 0.0)
            print(f"    {xi} = {_formatear_numero(val)}")
        print("=" * 60)
    elif resultado.get("no_acotado"):
        print("  El problema es no acotado (sin solución óptima finita).")
        print("=" * 60)
    elif resultado.get("max_iter"):
        print("  Se alcanzó el número máximo de iteraciones.")
        print("=" * 60)



def main() -> None:
    try:
        from interfaz_simplex import main as main_gui
        main_gui()
    except ImportError:
        print("Error: Se requiere CustomTkinter. Instala con: pip install customtkinter")


if __name__ == "__main__":
    main()
