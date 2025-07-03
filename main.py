from fastapi import FastAPI
import pyodbc
import os

app = FastAPI()

# Conexión usando variables de entorno
server = os.getenv('SERVER')
database = os.getenv('DB')
username = os.getenv('USER')
password = os.getenv('PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'

conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'

@app.get("/op")
def get_op_data(op: str):
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # 1. Consulta PEDIDOS
        cursor.execute("""
            SELECT [Cliente], [Referencia_Articulo], [Descripcion_Articulo], [OP], [Estado_OP], [OPA],
                   [Estado_Articulo], [Fecha_Creacción_OP], [Fecha_Aprobacion_OP], [Fecha_Aprob_AAFF],
                   [Fecha_Entrada_Planificacion], [Ultima_Operacion_Realizada], [Fecha_Fin_Ultimo_Proceso],
                   [Cantidad_Teorica_OP_Pliegos], [Fecha_Solicitada_Cliente], [Fecha_Pendiente_Aprobacion],
                   [Fecha_Produccion], [Ancho], [Largo]
            FROM [SistradeERP].[dbo].[00GG_PEDIDOS]
            WHERE OP = ? AND Estado_OP NOT IN ('(F)Cerrada','(P)Producción','(A)Anulada')
        """, op)
        pedido = cursor.fetchone()

        if not pedido:
            return {"error": "OP no encontrada o ya cerrada"}

        pedido_data = dict(zip([column[0] for column in cursor.description], pedido))

        # 2. Consulta CONSUMOS
        cursor.execute("""
            SELECT T0.OT, T0.Codigo_Recurso, T0.Fecha, T0.Cantidad_Requerida, T0.Cantidad_Consumida, 
                   T0.Descripcion_Seccion, T0.Codigo_Articulo, T0.Descripcion_Articulo,
                   T1.Cliente, T1.Troquel, T1.Referencia_Articulo, T1.Descripcion_Articulo
            FROM [SistradeERP].[dbo].[00GG_CONTROL_CONSUMOS] AS T0
            LEFT JOIN (
                SELECT OP, Cliente, Fecha_pedido, Troquel, Referencia_Articulo, Descripcion_Articulo 
                FROM [SistradeERP].[dbo].[00GG_SOP_OPS]
            ) AS T1 ON T0.OT = T1.OP
            WHERE T0.OT = ? AND Descripcion_Seccion IN ('Impresión','Guillotina')
              AND SUBSTRING(T0.Codigo_Articulo,1,2) = '10'
              AND T0.OT IS NOT NULL
        """, op)
        consumos = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

        # 3. Consulta DISPONIBILIDAD de materiales usados
        codigos_articulos = list({row['Codigo_Articulo'] for row in consumos})
        disponibilidad = []
        if codigos_articulos:
            placeholders = ','.join(['?'] * len(codigos_articulos))
            query_disponible = f"""
                SELECT T0.[Codigo_Articulo], T0.[Descripcion_Articulo], T0.[STK_Disponivel], T0.[STK_Actual],
                       T0.[STK_Reservado], T0.[STK_Encomendado], T0.[STK_Requisitado], T0.[Codigo_Unidad],
                       T0.[Descripcion_Unidad], T0.[STK_Min], T0.[Ponto_Encomienda], T0.[STK_Seguridad], 
                       T0.[STK_a_producir], T1.SubFamilia, T1.Familia
                FROM [SistradeERP].[dbo].[00GG_CONSULTA_DISPONIBLE] AS T0
                LEFT JOIN (
                    SELECT [SubFamilia], Codigo, [Familia], [Marca]
                    FROM [SistradeERP].[dbo].[00GG_Listado_Articulos_Detalle]
                ) AS T1 ON T0.[Codigo_Articulo] = T1.[Codigo]
                WHERE Familia IN ('MATERIAL CLIENTE','CARTULINA GRAFICA','CARTONCILLOS','OTROS PAPELES','ONDULADOS')
                  AND T0.Codigo_Articulo IN ({placeholders})
            """
            cursor.execute(query_disponible, *codigos_articulos)
            disponibilidad = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

        # 4. Consulta GESTIÓN DE RESERVAS
        cursor.execute("""
            SELECT *
            FROM [SistradeERP].[dbo].[00GG_Gestion_Reservas]
            WHERE OP = ? AND SUBSTRING(articulo,1,2) IN ('10','15','20','25','27')
        """, op)
        reservas = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

        return {
            "pedido": pedido_data,
            "consumos": consumos,
            "disponibilidad": disponibilidad,
            "reservas": reservas
        }

    except Exception as e:
        return {"error": str(e)}
