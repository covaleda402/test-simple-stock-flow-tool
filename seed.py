#!/usr/bin/env python3
"""
Simple Stock Flow — Sembrador de Datos de Demostración (Tool)
Tarea T-24: Consume exclusivamente la API HTTP pública.
NO se conecta a la base de datos MySQL directamente.
"""

import json
import os
import sys
import urllib.error
import urllib.request

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@stockflow.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123456")


def http_request(method: str, path: str, data: dict = None, token: str = None) -> tuple[int, dict]:
    url = f"{API_BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            resp_body = resp.read().decode("utf-8")
            return status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        parsed = json.loads(resp_body) if resp_body else {}
        return e.code, parsed
    except Exception as e:
        print(f"Error de conexión con la API ({url}): {e}")
        return 0, {}


def main():
    print(f"=== Sembrador de Demostración Simple Stock Flow ===")
    print(f"Conectando a la API en: {API_BASE_URL}")

    # 1. Autenticación como Administrador
    print(f"Autenticando con usuario: {ADMIN_EMAIL}...")
    status, auth_res = http_request("POST", "/api/auth/login", {
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })

    if status != 200 or "accessToken" not in auth_res:
        print(f"Error de autenticación ({status}): {auth_res}")
        sys.exit(1)

    token = auth_res["accessToken"]
    print("[OK] Token de autenticación obtenido exitosamente.")

    # 2. Consultar Categorías
    print("Obteniendo categorías...")
    status, categories = http_request("GET", "/api/categories", token=token)
    if status != 200 or not isinstance(categories, list):
        print(f"Error obteniendo categorías ({status}): {categories}")
        sys.exit(1)

    cat_map = {c["name"]: c["id"] for c in categories}
    print(f"[OK] Categorías disponibles: {list(cat_map.keys())}")

    # 3. Crear Productos de Demostración
    demo_products = [
        {"name": "Martillo de Uña 16oz", "price": 28500, "stock": 25, "category": "Herramientas"},
        {"name": "Destornillador Phillips #2", "price": 14200, "stock": 40, "category": "Herramientas"},
        {"name": "Cable Eléctrico THHN #12", "price": 3500, "stock": 150, "category": "Electricidad"},
        {"name": "Interruptor Sencillo 10A", "price": 8900, "stock": 60, "category": "Electricidad"},
        {"name": "Tubo PVC Presión 1/2 pulgada", "price": 12000, "stock": 50, "category": "Fontanería"},
        {"name": "Llave de Paso 1/2 pulgada", "price": 22500, "stock": 30, "category": "Fontanería"},
        {"name": "Pintura Látex Blanco Galón", "price": 54000, "stock": 18, "category": "Pinturas"},
        {"name": "Brocha 3 pulgadas Profesional", "price": 11500, "stock": 35, "category": "Pinturas"},
        {"name": "Cinta Teflón 3/4 pulgada", "price": 2500, "stock": 100, "category": "General"},
    ]

    created_product_ids = []

    print("\nSembrando productos en el catálogo...")
    for p in demo_products:
        cat_id = cat_map.get(p["category"], list(cat_map.values())[0])
        status, prod_res = http_request("POST", "/api/products", {
            "name": p["name"],
            "price": p["price"],
            "stock": p["stock"],
            "categoryId": cat_id
        }, token=token)

        if status == 201:
            p_id = prod_res["id"]
            created_product_ids.append(p_id)
            print(f"  + Creado: {p['name']} (ID: {p_id})")
        else:
            print(f"  - No se pudo crear {p['name']} (Código {status}): {prod_res.get('detail', prod_res)}")

    # 4. Registrar Ventas de Demostración
    if created_product_ids:
        print("\nRegistrando ventas de prueba...")
        sale_lines = [
            {"productId": created_product_ids[0], "quantity": 2},
        ]
        if len(created_product_ids) > 1:
            sale_lines.append({"productId": created_product_ids[1], "quantity": 1})

        status, sale_res = http_request("POST", "/api/sales", {
            "lines": sale_lines
        }, token=token)

        if status == 201:
            print(f"  + Venta registrada exitosamente con ID: {sale_res.get('id')}")
        else:
            print(f"  - Error registrando venta: {sale_res}")

    print("\n=== Sembrado finalizado exitosamente ===")


if __name__ == "__main__":
    main()
