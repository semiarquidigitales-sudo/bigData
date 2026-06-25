# ============================================================
# FASE 2 — VERIFICAR EL DATASET DESCARGADO
# Cambia RUTA_DATASET a la ruta real de tu archivo
# ============================================================

import pandas as pd
import os

# ── Cambia esta ruta al archivo que descargaste ──────────────────
RUTA_DATASET = 'datos/crudos/ventas_colombia_2022_2024.csv'
# Otros ejemplos:
# RUTA_DATASET = 'datos/crudos/olist_order_items_dataset.csv'
# RUTA_DATASET = 'datos/crudos/year_2010_2011.csv'
# RUTA_DATASET = 'datos/crudos/yellow_tripdata_2023-01.csv'

if not os.path.exists(RUTA_DATASET):
    print(f'⚠️  Archivo no encontrado: {RUTA_DATASET}')
    print('   Verifica con: ls datos/crudos/')
else:
    # Cargar solo las primeras 200K filas para la verificación
    df = pd.read_csv(RUTA_DATASET, low_memory=False, nrows=200_000)

    print('=' * 55)
    print('VERIFICACIÓN DEL DATASET')
    print('=' * 55)
    print(f'  Archivo:   {os.path.basename(RUTA_DATASET)}')
    print(f'  Disco:     {os.path.getsize(RUTA_DATASET)/1024**2:.1f} MB')
    print(f'  Filas:     {len(df):,} (muestra de 200K)')
    print(f'  Columnas:  {df.shape[1]}')
    print(f'  RAM:       {df.memory_usage(deep=True).sum()/1024**2:.1f} MB')
    print()
    print('COLUMNAS Y TIPOS:')
    for col in df.columns:
        nulos = df[col].isna().sum()
        pct   = nulos / len(df) * 100
        print(f'  {col:<30} {str(df[col].dtype):<12} {nulos:>6} nulos ({pct:.1f}%)')
    print()
    if len(df) >= 100_000:
        print('✅ Cumple el mínimo de 100.000 filas')
    else:
        print('⚠️  Menos de 100K en la muestra — puede que el archivo completo tenga más')
    print()
    print('VISTA PREVIA (3 filas):')
    print(df.head(3).to_string())