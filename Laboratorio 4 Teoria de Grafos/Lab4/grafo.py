from collections import deque


class Grafo:
    """
    Representa un grafo dirigido o no dirigido mediante
    matriz de adyacencia.
    """

    def __init__(self, n: int, dirigido: bool = True):
        self.n = n
        self.dirigido = dirigido
        # Matriz n×n inicializada en 0
        self.matriz = [[0] * n for _ in range(n)]

    # ------------------------------------------------------------------
    # Manipulación de aristas
    # ------------------------------------------------------------------

    def agregar_arista(self, i: int, j: int):
        """Agrega la arista (i, j). Si no es dirigido, también (j, i)."""
        if i == j:
            return  # La diagonal siempre queda en 0
        self.matriz[i][j] = 1
        if not self.dirigido:
            self.matriz[j][i] = 1

    def eliminar_arista(self, i: int, j: int):
        """Elimina la arista (i, j). Si no es dirigido, también (j, i)."""
        self.matriz[i][j] = 0
        if not self.dirigido:
            self.matriz[j][i] = 0

    def toggle_arista(self, i: int, j: int):
        """Alterna la existencia de la arista (i, j)."""
        if i == j:
            return
        if self.matriz[i][j] == 0:
            self.agregar_arista(i, j)
        else:
            self.eliminar_arista(i, j)

    def limpiar(self):
        """Pone toda la matriz en 0."""
        self.matriz = [[0] * self.n for _ in range(self.n)]

    # ------------------------------------------------------------------
    # Propiedades básicas
    # ------------------------------------------------------------------

    def num_vertices(self) -> int:
        return self.n

    def num_aristas(self) -> int:
        total = sum(self.matriz[i][j]
                    for i in range(self.n)
                    for j in range(self.n))
        # En grafos no dirigidos cada arista se cuenta dos veces
        return total if self.dirigido else total // 2

    def nombres_vertices(self) -> list[str]:
        return [f"v{i + 1}" for i in range(self.n)]

    # ------------------------------------------------------------------
    # Representación matemática
    # ------------------------------------------------------------------

    def representacion_V(self) -> str:
        nombres = self.nombres_vertices()
        return "V = {" + ", ".join(nombres) + "}"

    def representacion_A(self) -> str:
        nombres = self.nombres_vertices()
        aristas = []
        if self.dirigido:
            for i in range(self.n):
                for j in range(self.n):
                    if self.matriz[i][j]:
                        aristas.append(f"<{nombres[i]},{nombres[j]}>")
        else:
            visitadas = set()
            for i in range(self.n):
                for j in range(self.n):
                    if self.matriz[i][j] and (j, i) not in visitadas:
                        aristas.append(f"{{{nombres[i]},{nombres[j]}}}")
                        visitadas.add((i, j))
        return "A = {" + ", ".join(aristas) + "}"

    # ------------------------------------------------------------------
    # Lista de adyacencia
    # ------------------------------------------------------------------

    def lista_adyacencia(self) -> dict[str, list[str]]:
        nombres = self.nombres_vertices()
        result = {}
        for i in range(self.n):
            vecinos = [nombres[j] for j in range(self.n) if self.matriz[i][j]]
            result[nombres[i]] = vecinos
        return result

    # ------------------------------------------------------------------
    # Grados
    # ------------------------------------------------------------------

    def grados(self) -> dict[str, dict]:
        """
        Para grafos dirigidos devuelve grado de entrada y salida.
        Para no dirigidos devuelve grado total.
        """
        nombres = self.nombres_vertices()
        result = {}
        for i in range(self.n):
            if self.dirigido:
                entrada = sum(self.matriz[j][i] for j in range(self.n))
                salida = sum(self.matriz[i][j] for j in range(self.n))
                result[nombres[i]] = {"entrada": entrada, "salida": salida}
            else:
                grado = sum(self.matriz[i][j] for j in range(self.n))
                result[nombres[i]] = {"grado": grado}
        return result

    # ------------------------------------------------------------------
    # Camino (BFS — primer camino encontrado entre v1 y v2)
    # ------------------------------------------------------------------

    def encontrar_camino(self, origen: int = 0, destino: int = 1) -> list[str] | None:
        """
        BFS desde `origen` hasta `destino`.
        Devuelve la lista de nombres de vértices o None si no existe camino.
        """
        if origen == destino:
            return [self.nombres_vertices()[origen]]

        visitado = [False] * self.n
        padre = [-1] * self.n
        cola = deque([origen])
        visitado[origen] = True

        while cola:
            actual = cola.popleft()
            for vecino in range(self.n):
                if self.matriz[actual][vecino] and not visitado[vecino]:
                    visitado[vecino] = True
                    padre[vecino] = actual
                    if vecino == destino:
                        return self._reconstruir_camino(padre, origen, destino)
                    cola.append(vecino)
        return None

    def _reconstruir_camino(self, padre: list[int], origen: int, destino: int) -> list[str]:
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
        DFS para detectar el primer ciclo.
        Devuelve la lista de nombres de vértices que forman el ciclo o None.
        """
        color = [0] * self.n   # 0=blanco, 1=gris, 2=negro
        padre = [-1] * self.n
        ciclo_inicio = [None]
        ciclo_fin = [None]

        def dfs(u):
            color[u] = 1
            for v in range(self.n):
                if self.matriz[u][v]:
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
        Para grafos dirigidos: DFS desde cada vértice alcanza todos los demás.
        Para no dirigidos: BFS/DFS desde el vértice 0 alcanza todos.
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
                    if mat[u][v] and not vis[v]:
                        vis[v] = True
                        cola.append(v)
            return all(vis)

        if not self.dirigido:
            return alcanzables(0, self.matriz)

        # Dirigido: alcanzable en dirección original
        if not alcanzables(0, self.matriz):
            return False
        # Transpuesta
        transpuesta = [[self.matriz[j][i] for j in range(self.n)] for i in range(self.n)]
        return alcanzables(0, transpuesta)
