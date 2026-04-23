from collections import deque
import heapq
from typing import Literal


class Grafo:
    """
    Representa un grafo dirigido o no dirigido mediante matriz de adyacencia con pesos.
    
    Características:
    - 0 significa sin arista
    - Soporta pesos positivos, negativos y cero
    - Validación de entrada para garantizar integridad
    
    Limitaciones:
    - Máximo 10 vértices (recomendado para UI)
    - Dijkstra requiere pesos > 0
    - Bellman-Ford detecta ciclos negativos
    """

    INF = float("inf")
    MAX_VERTICES = 10
    MIN_VERTICES = 2

    def __init__(self, n: int, dirigido: bool = True):
        """
        Inicializa el grafo.
        
        Args:
            n: Número de vértices (2-10)
            dirigido: True para dirigido, False para no dirigido
            
        Raises:
            ValueError: Si n está fuera del rango válido
        """
        if not isinstance(n, int) or n < self.MIN_VERTICES or n > self.MAX_VERTICES:
            raise ValueError(f"n debe ser entero entre {self.MIN_VERTICES} y {self.MAX_VERTICES}")
        
        self.n = n
        self.dirigido = dirigido
        # Matriz n×n inicializada en 0 (0 = sin arista)
        self.matriz = [[0] * n for _ in range(n)]

    # ------------------------------------------------------------------
    # Manipulación de aristas
    # ------------------------------------------------------------------

    def agregar_arista(self, i: int, j: int, peso: float = 1):
        """
        Agrega la arista (i, j) con el peso dado.
        
        Args:
            i: Vértice origen
            j: Vértice destino
            peso: Peso de la arista (por defecto 1)
            
        Raises:
            ValueError: Si los índices están fuera de rango
        """
        self._validar_indices(i, j)
        self.matriz[i][j] = peso
        if not self.dirigido:
            self.matriz[j][i] = peso

    def eliminar_arista(self, i: int, j: int):
        """
        Elimina la arista (i, j).
        
        Args:
            i: Vértice origen
            j: Vértice destino
            
        Raises:
            ValueError: Si los índices están fuera de rango
        """
        self._validar_indices(i, j)
        self.matriz[i][j] = 0
        if not self.dirigido:
            self.matriz[j][i] = 0

    def toggle_arista(self, i: int, j: int, peso: float = 1):
        """
        Alterna la existencia de la arista (i, j).
        
        Args:
            i: Vértice origen
            j: Vértice destino
            peso: Peso si se activa la arista
        """
        if self.matriz[i][j] == 0:
            self.agregar_arista(i, j, peso)
        else:
            self.eliminar_arista(i, j)

    def set_peso(self, i: int, j: int, peso: float):
        """
        Establece el peso de la arista (i, j).
        
        Args:
            i: Vértice origen
            j: Vértice destino
            peso: Nuevo peso
            
        Raises:
            ValueError: Si los índices están fuera de rango
        """
        self._validar_indices(i, j)
        if self.matriz[i][j] != 0 or peso != 0:
            self.matriz[i][j] = peso
            if not self.dirigido:
                self.matriz[j][i] = peso

    def limpiar(self):
        """Reinicia la matriz a todos los ceros."""
        self.matriz = [[0] * self.n for _ in range(self.n)]

    def _validar_indices(self, i: int, j: int):
        """Valida que los índices estén dentro del rango válido."""
        if not (0 <= i < self.n and 0 <= j < self.n):
            raise ValueError(f"Índices fuera de rango [0, {self.n-1}]")

    # ------------------------------------------------------------------
    # Propiedades básicas
    # ------------------------------------------------------------------

    def num_vertices(self) -> int:
        """Retorna el número de vértices."""
        return self.n

    def num_aristas(self) -> int:
        """
        Retorna el número de aristas.
        
        Para grafos no dirigidos, una arista se cuenta una sola vez.
        """
        total = sum(1 for i in range(self.n)
                      for j in range(self.n)
                      if self.matriz[i][j] != 0)
        return total if self.dirigido else total // 2

    def nombres_vertices(self) -> list[str]:
        """Retorna lista de nombres de vértices (v1, v2, ..., vn)."""
        return [f"v{i + 1}" for i in range(self.n)]

    # ------------------------------------------------------------------
    # Representación matemática
    # ------------------------------------------------------------------

    def representacion_V(self) -> str:
        """Retorna la representación matemática del conjunto de vértices."""
        nombres = self.nombres_vertices()
        return "V = {" + ", ".join(nombres) + "}"

    def representacion_A(self) -> str:
        """Retorna la representación matemática del conjunto de aristas."""
        nombres = self.nombres_vertices()
        aristas = []
        if self.dirigido:
            for i in range(self.n):
                for j in range(self.n):
                    if self.matriz[i][j] != 0:
                        w = self.matriz[i][j]
                        aristas.append(f"<{nombres[i]},{nombres[j]},{w}>")
        else:
            visitadas = set()
            for i in range(self.n):
                for j in range(self.n):
                    if self.matriz[i][j] != 0 and (j, i) not in visitadas:
                        w = self.matriz[i][j]
                        aristas.append(f"{{{nombres[i]},{nombres[j]},{w}}}")
                        visitadas.add((i, j))
        return "A = {" + ", ".join(aristas) + "}"

    # ------------------------------------------------------------------
    # Lista de adyacencia
    # ------------------------------------------------------------------

    def lista_adyacencia(self) -> dict[str, list[str]]:
        """Retorna la lista de adyacencia con pesos."""
        nombres = self.nombres_vertices()
        result = {}
        for i in range(self.n):
            vecinos = [f"{nombres[j]}({self.matriz[i][j]})"
                       for j in range(self.n) if self.matriz[i][j] != 0]
            result[nombres[i]] = vecinos
        return result

    # ------------------------------------------------------------------
    # Grados (CORREGIDO: los lazos cuentan como 2 en grafos no dirigidos)
    # ------------------------------------------------------------------

    def grados(self) -> dict[str, dict]:
        """
        Retorna el grado de cada vértice.
        
        Para grafos no dirigidos: los lazos cuentan como 2
        Para grafos dirigidos: grado de entrada y salida
        """
        nombres = self.nombres_vertices()
        result = {}
        for i in range(self.n):
            if self.dirigido:
                entrada = sum(1 for j in range(self.n) if self.matriz[j][i] != 0)
                salida  = sum(1 for j in range(self.n) if self.matriz[i][j] != 0)
                result[nombres[i]] = {"entrada": entrada, "salida": salida}
            else:
                # Para grafos no dirigidos: lazo cuenta como 2
                grado = sum(1 if i != j else 2 
                           for j in range(self.n) if self.matriz[i][j] != 0)
                result[nombres[i]] = {"grado": grado}
        return result

    # ------------------------------------------------------------------
    # Camino BFS (sin pesos — primer camino en saltos)
    # ------------------------------------------------------------------

    def encontrar_camino(self, origen: int = 0, destino: int = 1) -> list[str] | None:
        """
        Encuentra el primer camino entre dos vértices usando BFS.
        
        Args:
            origen: Índice del vértice origen
            destino: Índice del vértice destino
            
        Returns:
            Lista de vértices en el camino o None si no existe
        """
        if origen == destino:
            return [self.nombres_vertices()[origen]]
        
        self._validar_indices(origen, destino)
        
        visitado = [False] * self.n
        padre = [-1] * self.n
        cola = deque([origen])
        visitado[origen] = True
        
        while cola:
            actual = cola.popleft()
            for vecino in range(self.n):
                if self.matriz[actual][vecino] != 0 and not visitado[vecino]:
                    visitado[vecino] = True
                    padre[vecino] = actual
                    if vecino == destino:
                        return self._reconstruir_camino(padre, origen, destino)
                    cola.append(vecino)
        return None

    def _reconstruir_camino(self, padre: list[int], origen: int, destino: int) -> list[str]:
        """Reconstruye el camino desde los padres."""
        nombres = self.nombres_vertices()
        camino = []
        actual = destino
        while actual != -1:
            camino.append(nombres[actual])
            actual = padre[actual]
        return camino[::-1]

    # ------------------------------------------------------------------
    # Ciclo (DFS — primer ciclo encontrado)
    # ------------------------------------------------------------------

    def encontrar_ciclo(self) -> list[str] | None:
        """
        Encuentra el primer ciclo en el grafo usando DFS.
        
        Returns:
            Lista de vértices en el ciclo o None si no hay ciclos
        """
        color = [0] * self.n
        padre = [-1] * self.n
        ciclo_inicio = [None]
        ciclo_fin = [None]

        def dfs(u):
            color[u] = 1
            for v in range(self.n):
                if self.matriz[u][v] != 0:
                    if color[v] == 1:
                        ciclo_inicio[0] = v
                        ciclo_fin[0] = u
                        return True
                    if color[v] == 0:
                        padre[v] = u
                        if dfs(v):
                            return True
            color[u] = 2
            return False

        for s in range(self.n):
            if color[s] == 0:
                if dfs(s):
                    break

        if ciclo_inicio[0] is None:
            return None

        nombres = self.nombres_vertices()
        camino = []
        actual = ciclo_fin[0]
        while actual != ciclo_inicio[0]:
            camino.append(nombres[actual])
            actual = padre[actual]
        camino.append(nombres[ciclo_inicio[0]])
        camino.reverse()
        camino.append(nombres[ciclo_inicio[0]])
        return camino

    # ------------------------------------------------------------------
    # Conectividad
    # ------------------------------------------------------------------

    def es_fuertemente_conexo(self) -> bool:
        """
        Verifica si el grafo es fuertemente conexo.
        
        Para grafos no dirigidos: verifica conectividad
        Para grafos dirigidos: verifica si hay camino de cualquier vértice a cualquier otro
        """
        if self.n == 0:
            return True

        def alcanzables(src, mat):
            vis = [False] * self.n
            cola = deque([src])
            vis[src] = True
            while cola:
                u = cola.popleft()
                for v in range(self.n):
                    if mat[u][v] != 0 and not vis[v]:
                        vis[v] = True
                        cola.append(v)
            return all(vis)

        if not self.dirigido:
            return alcanzables(0, self.matriz)

        if not alcanzables(0, self.matriz):
            return False
        transpuesta = [[self.matriz[j][i] for j in range(self.n)] for i in range(self.n)]
        return alcanzables(0, transpuesta)

    # ------------------------------------------------------------------
    # Dijkstra (pesos positivos)
    # ------------------------------------------------------------------

    def dijkstra(self, origen: int, destino: int) -> tuple[list[str] | None, float]:
        """
        Calcula la ruta óptima usando algoritmo de Dijkstra.
        
        IMPORTANTE: Solo funciona con pesos > 0
        
        Args:
            origen: Índice del vértice origen
            destino: Índice del vértice destino
            
        Returns:
            Tupla (camino, costo_total) donde camino es None si no existe ruta
        """
        self._validar_indices(origen, destino)
        
        dist = [self.INF] * self.n
        padre = [-1] * self.n
        dist[origen] = 0
        # heap: (distancia, nodo)
        heap = [(0, origen)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            if u == destino:
                break
            for v in range(self.n):
                w = self.matriz[u][v]
                if w > 0:          # solo aristas con peso positivo
                    nd = dist[u] + w
                    if nd < dist[v]:
                        dist[v] = nd
                        padre[v] = u
                        heapq.heappush(heap, (nd, v))

        if dist[destino] == self.INF:
            return None, self.INF

        camino = []
        actual = destino
        while actual != -1:
            camino.append(self.nombres_vertices()[actual])
            actual = padre[actual]
        return camino[::-1], dist[destino]

    # ------------------------------------------------------------------
    # Bellman-Ford (admite pesos negativos, detecta ciclos negativos)
    # ------------------------------------------------------------------

    def bellman_ford(self, origen: int, destino: int) -> tuple[list[str] | None, float, bool]:
        """
        Calcula la ruta óptima usando algoritmo de Bellman-Ford.
        
        VENTAJAS: Funciona con pesos negativos
        DESVENTAJA: Más lento que Dijkstra
        
        Args:
            origen: Índice del vértice origen
            destino: Índice del vértice destino
            
        Returns:
            Tupla (camino, costo_total, ciclo_negativo)
            - ciclo_negativo=True si se detecta ciclo de peso negativo
        """
        self._validar_indices(origen, destino)
        
        dist = [self.INF] * self.n
        padre = [-1] * self.n
        dist[origen] = 0

        # Construir lista de aristas (i, j, peso) excluyendo ceros
        aristas = [
            (i, j, self.matriz[i][j])
            for i in range(self.n)
            for j in range(self.n)
            if self.matriz[i][j] != 0
        ]

        # Relajar |V|-1 veces
        for _ in range(self.n - 1):
            actualizado = False
            for u, v, w in aristas:
                if dist[u] != self.INF and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    padre[v] = u
                    actualizado = True
            if not actualizado:
                break

        # Detectar ciclos negativos
        ciclo_neg = False
        for u, v, w in aristas:
            if dist[u] != self.INF and dist[u] + w < dist[v]:
                ciclo_neg = True
                break

        if dist[destino] == self.INF:
            return None, self.INF, ciclo_neg

        camino = []
        actual = destino
        visitados = set()
        while actual != -1:
            if actual in visitados:
                return None, self.INF, True  # ciclo en reconstrucción
            visitados.add(actual)
            camino.append(self.nombres_vertices()[actual])
            actual = padre[actual]
        return camino[::-1], dist[destino], ciclo_neg