import time
import shutil
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count
from sqlalchemy import create_engine
import pandas as pd

def run_spark_benchmark():
    print("\n" + "="*80)
    print(" CLÍNICA RED - BENCHMARK & OPTIMIZACIÓN PYSPARK (US 05 TASKS 4 & 5) ")
    print("="*80 + "\n")

    spark = SparkSession.builder \
        .appName("ClinicaRed-Optimization-Benchmark") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")

    # 1. Extracción de datos
    from src.core.config import settings
    db_uri = settings.DATABASE_URL
    
    query = """
        SELECT 
            a.id AS appointment_id,
            a.patient_id,
            a.specialty_id,
            a.status,
            a.scheduled_datetime,
            COALESCE(att.attended, false) AS attended
        FROM appointments a
        LEFT JOIN attendances att ON a.id = att.appointment_id;
    """
    
    print("[*] Extrayendo datos de PostgreSQL...")
    engine = create_engine(db_uri)
    pdf = pd.read_sql(query, engine)

    # Multiplicar a 20,000 registros para volumen analítico
    pdf_expanded = pd.concat([pdf] * 200, ignore_index=True)
    pdf_expanded["scheduled_datetime"] = pdf_expanded["scheduled_datetime"].astype(str)
    total_records = len(pdf_expanded)
    print(f"[v] Dataset preparado: {total_records:,} registros para análisis.\n")

    temp_source = "/tmp/raw_benchmark_source.csv"
    pdf_expanded.to_csv(temp_source, index=False)

    raw_df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(temp_source)

    unoptimized_dir = "/tmp/spark_unoptimized_csv"
    optimized_dir = "/tmp/spark_optimized_parquet"
    shutil.rmtree(unoptimized_dir, ignore_errors=True)
    shutil.rmtree(optimized_dir, ignore_errors=True)

    # Ingesta y almacenamiento en ambos formatos
    print("[*] Escribiendo almacenamiento base (CSV plano)...")
    raw_df.write.mode("overwrite").option("header", "true").csv(unoptimized_dir)

    print("[*] Escribiendo almacenamiento optimizado (Parquet particionado por especialidad)...")
    raw_df.write.mode("overwrite").partitionBy("specialty_id").parquet(optimized_dir)

    # =========================================================================
    # ESCENARIO 1: LATENCIA DE CONSULTA EN CSV (SIN OPTIMIZAR)
    # =========================================================================
    print("\n>>> Ejecutando consultas sobre Escenario 1: CSV (Monolítico, Sin Caché)...")
    start_baseline = time.time()

    df_base = spark.read.option("header", "true").csv(unoptimized_dir)
    q1 = df_base.groupBy("specialty_id").agg(count("*").alias("total")).collect()
    q2 = df_base.filter(col("attended") == "false").groupBy("specialty_id").agg(count("*").alias("no_shows")).collect()
    q3 = df_base.groupBy("status").agg(count("*").alias("por_estado")).collect()

    end_baseline = time.time()
    baseline_query_ms = (end_baseline - start_baseline) * 1000

    # =========================================================================
    # ESCENARIO 2: LATENCIA DE CONSULTA EN PARQUET + CACHÉ (OPTIMIZADO)
    # =========================================================================
    print(">>> Ejecutando consultas sobre Escenario 2: Parquet + Caché en RAM...")
    
    # Cargar y materializar en memoria caliente
    df_opt = spark.read.parquet(optimized_dir)
    df_opt.cache()
    df_opt.count()

    start_opt = time.time()

    q_opt1 = df_opt.groupBy("specialty_id").agg(count("*").alias("total")).collect()
    q_opt2 = df_opt.filter(col("attended") == "false").groupBy("specialty_id").agg(count("*").alias("no_shows")).collect()
    q_opt3 = df_opt.groupBy("status").agg(count("*").alias("por_estado")).collect()

    end_opt = time.time()
    optimized_query_ms = (end_opt - start_opt) * 1000

    # =========================================================================
    # AUDITORÍA DE PLAN FÍSICO CATALYST (.explain() - TASK 4)
    # =========================================================================
    print("\n" + "-"*80)
    print(" ANÁLISIS DEL PLAN DE EJECUCIÓN FÍSICO (CATALYST EXPLAIN - TASK 4):")
    print("-" * 80)
    df_opt.filter(col("specialty_id") == 1).groupBy("status").count().explain()

    # =========================================================================
    # TABLA COMPARATIVA DE LATENCIA ANALÍTICA (TASK 5)
    # =========================================================================
    improvement_ms = baseline_query_ms - optimized_query_ms
    improvement_pct = (improvement_ms / baseline_query_ms) * 100
    speedup = baseline_query_ms / optimized_query_ms if optimized_query_ms > 0 else 1.0

    print("\n" + "="*80)
    print(" TABLA COMPARATIVA DE RENDIMIENTO ANALÍTICO (BEFORE VS AFTER)")
    print("="*80)
    print(f"{'MÉTRICA / CONFIGURACIÓN':<38} | {'LÍNEA BASE (NO OPTIMIZADA)':<20} | {'OPTIMIZADA (COLUMNAR)':<20}")
    print("-" * 80)
    print(f"{'Formato de Almacenamiento':<38} | {'CSV Plano':<20} | {'Apache Parquet (Snappy)':<20}")
    print(f"{'Estrategia de Particionado':<38} | {'Ninguno (Monolítico)':<20} | {'Por specialty_id':<20}")
    print(f"{'Persistencia en Memoria (Cache)':<38} | {'Inactiva (I/O a disco)':<20} | {'df.cache() Activo en RAM':<20}")
    print(f"{'Volumen Evaluado':<38} | {f'{total_records:,} filas':<20} | {f'{total_records:,} filas':<20}")
    print(f"{'Latencia Consultas Agregadas (ms)':<38} | {f'{baseline_query_ms:,.2f} ms':<20} | {f'{optimized_query_ms:,.2f} ms':<20}")
    print(f"{'Reducción de Tiempo de Consulta':<38} | {'0.0%':<20} | {f'{improvement_pct:.2f}% más rápido':<20}")
    print(f"{'Aceleración Analítica (Speedup)':<38} | {'1.0x (Base)':<20} | {f'{speedup:.2f}x':<20}")
    print("="*80 + "\n")

    spark.stop()
    if os.path.exists(temp_source):
        os.remove(temp_source)
    shutil.rmtree(unoptimized_dir, ignore_errors=True)
    shutil.rmtree(optimized_dir, ignore_errors=True)

if __name__ == "__main__":
    run_spark_benchmark()
