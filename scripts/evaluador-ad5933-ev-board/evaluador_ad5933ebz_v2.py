# -*- coding: utf-8 -*-
"""
Evaluador AD5933EBZ v2
======================

Analiza 5 mediciones repetidas de un mismo resistor tomadas con la placa
EVAL-AD5933EBZ entre 5 kHz y 100 kHz.

Está adaptado al formato REAL exportado por el software de la placa:

Frequency,Impedance,Phase,Real,Imaginary,Magnitude,
 5000 , 973,004836626529 , 1,32002869207781E-03 , 251 ,-10002 , 10005,1489244289

Nótese que:
- la coma se usa como separador decimal;
- el delimitador entre campos es una coma rodeada por espacios;
- por eso un lector CSV estándar puede interpretar mal el archivo.

Funciones principales:
- carga una carpeta con 5 CSV o selecciona 5 CSV manualmente;
- valida rango 5–100 kHz y paso esperado de 1 kHz;
- detecta frecuencias duplicadas / barridos concatenados;
- calcula precisión y repetibilidad frecuencia por frecuencia;
- si se ingresa un valor de referencia, calcula también exactitud;
- analiza la fase respecto de 0°;
- muestra tablas y gráficos;
- exporta resultados y gráficos.

Requisitos:
    pip install numpy pandas matplotlib
"""

from __future__ import annotations

import math
import os
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------
# Configuración experimental esperada
# ---------------------------------------------------------------------
N_REPETICIONES = 5
F_MIN_HZ = 5_000.0
F_MAX_HZ = 100_000.0
PASO_ESPERADO_HZ = 1_000.0
T95_DF4 = 2.7764451051977987  # t(0.975, gl=4)


# ---------------------------------------------------------------------
# Lectura del formato AD5933EBZ
# ---------------------------------------------------------------------
def _numero(texto: str) -> float:
    """Convierte un número del archivo AD5933: coma decimal -> punto."""
    t = texto.strip().strip('"').strip("'")
    t = t.replace(",", ".")
    return float(t)


def leer_ad5933_csv(ruta: str | Path) -> pd.DataFrame:
    """
    Lee el formato exportado por la EVAL-AD5933EBZ.

    El archivo usa coma decimal y los campos están delimitados por una coma
    precedida por espacios. Ejemplo:

      5000 , 973,0048 , 1,32E-03 , 251 ,-10002 , 10005,1489

    Devuelve columnas:
      Frequency_Hz, Impedance_Ohm, Phase_deg, Real, Imaginary, Magnitude
    """
    ruta = Path(ruta)
    filas = []

    with ruta.open("r", encoding="utf-8-sig", errors="replace") as f:
        for nro_linea, linea in enumerate(f, start=1):
            s = linea.strip()

            if not s:
                continue

            if s.lower().startswith("frequency"):
                continue

            # Delimitador real: coma precedida por al menos un espacio.
            # Así NO se separa la coma decimal.
            partes = re.split(r"\s+,\s*", s)
            partes = [p.strip().rstrip(",").strip() for p in partes if p.strip()]

            if len(partes) < 6:
                continue

            try:
                frecuencia = _numero(partes[0])
                impedancia = _numero(partes[1])
                fase = _numero(partes[2])
                real = _numero(partes[3])
                imaginaria = _numero(partes[4])
                magnitud = _numero(partes[5])
            except ValueError:
                continue

            filas.append(
                [frecuencia, impedancia, fase, real, imaginaria, magnitud]
            )

    if not filas:
        raise ValueError(
            f"No se pudieron leer datos válidos de '{ruta.name}'. "
            "Verifique que sea un archivo exportado por la AD5933EBZ."
        )

    df = pd.DataFrame(
        filas,
        columns=[
            "Frequency_Hz",
            "Impedance_Ohm",
            "Phase_deg",
            "Real",
            "Imaginary",
            "Magnitude",
        ],
    )

    # Normalización de fase a [-180, 180)
    df["Phase_deg"] = ((df["Phase_deg"] + 180.0) % 360.0) - 180.0

    return df


def preparar_medicion(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Valida y prepara una medición.

    Si hay frecuencias duplicadas (por ejemplo, dos barridos concatenados),
    conserva la PRIMERA aparición y genera una advertencia explícita.
    """
    avisos = []
    d = df.copy()

    duplicados = int(d["Frequency_Hz"].duplicated(keep="first").sum())
    if duplicados:
        avisos.append(
            f"Se detectaron {duplicados} filas con frecuencias repetidas. "
            "Para el análisis se conservó la primera aparición de cada frecuencia."
        )
        d = d.drop_duplicates(subset=["Frequency_Hz"], keep="first").copy()

    d = d.sort_values("Frequency_Hz").reset_index(drop=True)

    # Nos concentramos en el ancho de banda del ensayo.
    fuera = d[
        (d["Frequency_Hz"] < F_MIN_HZ) | (d["Frequency_Hz"] > F_MAX_HZ)
    ]
    if len(fuera):
        avisos.append(
            f"Se ignoraron {len(fuera)} puntos fuera de 5–100 kHz."
        )

    d = d[
        (d["Frequency_Hz"] >= F_MIN_HZ) &
        (d["Frequency_Hz"] <= F_MAX_HZ)
    ].copy()

    if d.empty:
        raise ValueError("El archivo no contiene datos entre 5 kHz y 100 kHz.")

    return d, avisos


# ---------------------------------------------------------------------
# Combinación y análisis
# ---------------------------------------------------------------------
def combinar_cinco_mediciones(
    rutas: list[str | Path],
) -> tuple[pd.DataFrame, list[str]]:
    if len(rutas) != N_REPETICIONES:
        raise ValueError("Deben cargarse exactamente 5 archivos CSV.")

    preparados = []
    avisos = []

    for i, ruta in enumerate(rutas, start=1):
        raw = leer_ad5933_csv(ruta)
        d, a = preparar_medicion(raw)
        preparados.append(d)
        for msg in a:
            avisos.append(f"{Path(ruta).name}: {msg}")

    combinado = None

    for i, d in enumerate(preparados, start=1):
        cols = d[
            [
                "Frequency_Hz",
                "Impedance_Ohm",
                "Phase_deg",
                "Real",
                "Imaginary",
                "Magnitude",
            ]
        ].copy()

        cols = cols.rename(
            columns={
                "Impedance_Ohm": f"Z_M{i}",
                "Phase_deg": f"Phase_M{i}",
                "Real": f"Real_M{i}",
                "Imaginary": f"Imag_M{i}",
                "Magnitude": f"Magnitude_M{i}",
            }
        )

        if combinado is None:
            combinado = cols
        else:
            combinado = pd.merge(
                combinado, cols, on="Frequency_Hz", how="inner"
            )

    if combinado is None or combinado.empty:
        raise ValueError(
            "No hay frecuencias comunes entre las cinco mediciones."
        )

    combinado = combinado.sort_values("Frequency_Hz").reset_index(drop=True)

    freqs = combinado["Frequency_Hz"].to_numpy(dtype=float)

    if freqs.min() != F_MIN_HZ or freqs.max() != F_MAX_HZ:
        avisos.append(
            f"El rango común encontrado es "
            f"{freqs.min()/1000:.1f}–{freqs.max()/1000:.1f} kHz."
        )

    if len(freqs) > 1:
        pasos = np.diff(freqs)
        if not np.allclose(pasos, PASO_ESPERADO_HZ, atol=1e-9):
            distintos = np.unique(np.round(pasos, 9))
            avisos.append(
                "El paso no es uniformemente 1 kHz. "
                f"Pasos encontrados: {distintos.tolist()} Hz."
            )

    esperado = int((F_MAX_HZ - F_MIN_HZ) / PASO_ESPERADO_HZ) + 1
    if len(freqs) != esperado:
        avisos.append(
            f"Se encontraron {len(freqs)} frecuencias comunes; "
            f"para 5–100 kHz con paso de 1 kHz se esperan {esperado}."
        )

    return combinado, avisos


def calcular_metricas(
    combinado: pd.DataFrame,
    r_referencia_ohm: float | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Calcula precisión/repetibilidad y, si hay referencia, exactitud.
    """
    d = combinado.copy()

    z_cols = [f"Z_M{i}" for i in range(1, N_REPETICIONES + 1)]
    p_cols = [f"Phase_M{i}" for i in range(1, N_REPETICIONES + 1)]

    Z = d[z_cols].to_numpy(dtype=float)
    P = d[p_cols].to_numpy(dtype=float)

    # -------- Precisión / repetibilidad --------
    z_media = np.mean(Z, axis=1)
    z_sd = np.std(Z, axis=1, ddof=1)
    z_sem = z_sd / math.sqrt(N_REPETICIONES)
    z_cv = np.where(
        z_media != 0,
        100.0 * z_sd / np.abs(z_media),
        np.nan,
    )
    z_min = np.min(Z, axis=1)
    z_max = np.max(Z, axis=1)
    z_rango = z_max - z_min

    ic_half = T95_DF4 * z_sem
    ic_low = z_media - ic_half
    ic_high = z_media + ic_half

    d["Z_mean_Ohm"] = z_media
    d["Z_SD_Ohm"] = z_sd
    d["Z_CV_pct"] = z_cv
    d["Z_min_Ohm"] = z_min
    d["Z_max_Ohm"] = z_max
    d["Z_range_Ohm"] = z_rango
    d["Z_SEM_Ohm"] = z_sem
    d["Z_CI95_low_Ohm"] = ic_low
    d["Z_CI95_high_Ohm"] = ic_high

    # -------- Fase --------
    fase_media = np.mean(P, axis=1)
    fase_sd = np.std(P, axis=1, ddof=1)

    d["Phase_mean_deg"] = fase_media
    d["Phase_SD_deg"] = fase_sd
    d["Phase_abs_error_from_0_deg"] = np.abs(fase_media)

    # -------- Exactitud (opcional) --------
    if r_referencia_ohm is not None:
        if r_referencia_ohm <= 0:
            raise ValueError("La resistencia de referencia debe ser positiva.")

        bias = z_media - r_referencia_ohm
        error_pct = 100.0 * bias / r_referencia_ohm
        abs_error_pct = np.abs(error_pct)

        rmse_por_f = np.sqrt(
            np.mean((Z - r_referencia_ohm) ** 2, axis=1)
        )
        rmse_pct = 100.0 * rmse_por_f / r_referencia_ohm

        d["Bias_Ohm"] = bias
        d["Error_pct"] = error_pct
        d["Abs_Error_pct"] = abs_error_pct
        d["RMSE_Ohm"] = rmse_por_f
        d["RMSE_pct"] = rmse_pct

    # -------- Resumen de banda --------
    freqs = d["Frequency_Hz"].to_numpy(dtype=float)

    resumen = {
        "n_repetitions": N_REPETICIONES,
        "n_frequencies": len(d),
        "f_min_kHz": float(freqs.min() / 1000.0),
        "f_max_kHz": float(freqs.max() / 1000.0),
        "Z_band_mean_Ohm": float(np.mean(z_media)),
        "Z_band_min_mean_Ohm": float(np.min(z_media)),
        "Z_band_max_mean_Ohm": float(np.max(z_media)),
        "Z_change_100k_minus_5k_Ohm": float(z_media[-1] - z_media[0]),
        "Z_change_100k_minus_5k_pct_of_band_mean": float(
            100.0 * (z_media[-1] - z_media[0]) / np.mean(z_media)
        ),
        "mean_SD_Ohm": float(np.mean(z_sd)),
        "max_SD_Ohm": float(np.max(z_sd)),
        "mean_CV_pct": float(np.mean(z_cv)),
        "max_CV_pct": float(np.max(z_cv)),
        "frequency_of_max_CV_kHz": float(
            freqs[int(np.nanargmax(z_cv))] / 1000.0
        ),
        "mean_phase_deg": float(np.mean(fase_media)),
        "mean_phase_SD_deg": float(np.mean(fase_sd)),
        "mean_abs_phase_error_deg": float(np.mean(np.abs(fase_media))),
        "max_abs_phase_error_deg": float(np.max(np.abs(fase_media))),
    }

    if r_referencia_ohm is not None:
        resumen.update(
            {
                "R_reference_Ohm": float(r_referencia_ohm),
                "mean_bias_Ohm": float(np.mean(d["Bias_Ohm"])),
                "mean_signed_error_pct": float(np.mean(d["Error_pct"])),
                "MARE_pct": float(np.mean(d["Abs_Error_pct"])),
                "max_abs_error_pct": float(np.max(d["Abs_Error_pct"])),
                "frequency_of_max_abs_error_kHz": float(
                    freqs[int(np.argmax(d["Abs_Error_pct"].to_numpy()))]
                    / 1000.0
                ),
                "global_RMSE_Ohm": float(
                    np.sqrt(np.mean((Z - r_referencia_ohm) ** 2))
                ),
                "global_RMSE_pct": float(
                    100.0
                    * np.sqrt(np.mean((Z - r_referencia_ohm) ** 2))
                    / r_referencia_ohm
                ),
            }
        )

    return d, resumen


# ---------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------
def crear_figuras(
    detalle: pd.DataFrame,
    r_referencia_ohm: float | None = None,
    etiqueta: str = "",
):
    f = detalle["Frequency_Hz"].to_numpy(dtype=float) / 1000.0
    figs = []

    # 1. Impedancia: cinco repeticiones + media ± SD
    fig, ax = plt.subplots(figsize=(10, 6))
    for i in range(1, N_REPETICIONES + 1):
        ax.plot(
            f,
            detalle[f"Z_M{i}"],
            linewidth=1.0,
            alpha=0.65,
            label=f"M{i}",
        )

    ax.plot(
        f,
        detalle["Z_mean_Ohm"],
        linewidth=2.4,
        label="Media de las 5",
    )

    ax.fill_between(
        f,
        detalle["Z_mean_Ohm"] - detalle["Z_SD_Ohm"],
        detalle["Z_mean_Ohm"] + detalle["Z_SD_Ohm"],
        alpha=0.18,
        label="±1 SD",
    )

    if r_referencia_ohm is not None:
        ax.axhline(
            r_referencia_ohm,
            linestyle="--",
            linewidth=1.4,
            label=f"Referencia = {r_referencia_ohm:g} Ω",
        )

    ax.set_xlabel("Frecuencia (kHz)")
    ax.set_ylabel("|Z| (Ω)")
    ax.set_title(f"Impedancia y repetibilidad {etiqueta}".strip())
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=2)
    fig.tight_layout()
    figs.append(("01_impedancia_repetibilidad", fig))

    # 2. Desviación estándar
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(f, detalle["Z_SD_Ohm"], linewidth=2.0)
    ax.set_xlabel("Frecuencia (kHz)")
    ax.set_ylabel("SD de |Z| (Ω)")
    ax.set_title(f"Precisión: desviación estándar {etiqueta}".strip())
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    figs.append(("02_sd_vs_frecuencia", fig))

    # 3. CV
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(f, detalle["Z_CV_pct"], linewidth=2.0)
    ax.set_xlabel("Frecuencia (kHz)")
    ax.set_ylabel("CV (%)")
    ax.set_title(f"Precisión: coeficiente de variación {etiqueta}".strip())
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    figs.append(("03_cv_vs_frecuencia", fig))

    # 4. Error relativo si hay referencia
    if r_referencia_ohm is not None:
        fig, ax = plt.subplots(figsize=(10, 5.4))
        ax.plot(f, detalle["Error_pct"], linewidth=2.0)
        ax.axhline(0.0, linestyle="--", linewidth=1.0)
        ax.set_xlabel("Frecuencia (kHz)")
        ax.set_ylabel("Error relativo (%)")
        ax.set_title(f"Exactitud: error relativo {etiqueta}".strip())
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        figs.append(("04_error_relativo_vs_frecuencia", fig))

    # 5. Fase
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i in range(1, N_REPETICIONES + 1):
        ax.plot(
            f,
            detalle[f"Phase_M{i}"],
            linewidth=0.9,
            alpha=0.50,
        )
    ax.plot(
        f,
        detalle["Phase_mean_deg"],
        linewidth=2.2,
        label="Fase media",
    )
    ax.axhline(
        0.0,
        linestyle="--",
        linewidth=1.2,
        label="Resistor ideal: 0°",
    )
    ax.set_xlabel("Frecuencia (kHz)")
    ax.set_ylabel("Fase (°)")
    ax.set_title(f"Fase de las cinco mediciones {etiqueta}".strip())
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    figs.append(("05_fase_vs_frecuencia", fig))

    return figs


# ---------------------------------------------------------------------
# Interfaz gráfica
# ---------------------------------------------------------------------
class EvaluadorAD5933(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Evaluador AD5933EBZ - 5 mediciones por resistor")
        self.geometry("1180x780")
        self.minsize(1000, 680)

        self.rutas: list[str] = []
        self.detalle: pd.DataFrame | None = None
        self.resumen: dict | None = None
        self.avisos: list[str] = []
        self.figuras = []

        self._crear_interfaz()

    def _crear_interfaz(self):
        cab = ttk.Frame(self, padding=12)
        cab.pack(fill="x")

        ttk.Label(
            cab,
            text="Evaluación de precisión y exactitud - AD5933EBZ",
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 10))

        ttk.Label(
            cab,
            text="Resistencia de referencia (Ω):"
        ).grid(row=1, column=0, sticky="w")

        self.ref_var = tk.StringVar()
        ttk.Entry(
            cab,
            textvariable=self.ref_var,
            width=18
        ).grid(row=1, column=1, sticky="w", padx=(8, 16))

        ttk.Label(
            cab,
            text="(opcional; dejar vacío para evaluar sólo precisión)"
        ).grid(row=1, column=2, sticky="w", padx=(0, 12))

        ttk.Button(
            cab,
            text="Cargar carpeta con 5 CSV",
            command=self.cargar_carpeta,
        ).grid(row=1, column=3, padx=4)

        ttk.Button(
            cab,
            text="Seleccionar 5 CSV",
            command=self.cargar_archivos,
        ).grid(row=1, column=4, padx=4)

        ttk.Button(
            cab,
            text="ANALIZAR",
            command=self.analizar,
        ).grid(row=2, column=4, sticky="e", padx=4, pady=(10, 0))

        self.archivos_label = ttk.Label(
            cab,
            text="No hay archivos cargados.",
            foreground="gray",
            wraplength=940,
        )
        self.archivos_label.grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(10, 0)
        )

        acciones = ttk.Frame(self, padding=(12, 0, 12, 8))
        acciones.pack(fill="x")

        ttk.Button(
            acciones,
            text="Mostrar gráficas",
            command=self.mostrar_graficas,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            acciones,
            text="Exportar resultados",
            command=self.exportar,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            acciones,
            text="Limpiar",
            command=self.limpiar,
        ).pack(side="left")

        # Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Pestaña resumen
        tab_res = ttk.Frame(notebook, padding=10)
        notebook.add(tab_res, text="Resumen")

        self.texto_resumen = tk.Text(
            tab_res,
            wrap="none",
            font=("Consolas", 10),
        )
        scroll_res_y = ttk.Scrollbar(
            tab_res, orient="vertical", command=self.texto_resumen.yview
        )
        scroll_res_x = ttk.Scrollbar(
            tab_res, orient="horizontal", command=self.texto_resumen.xview
        )
        self.texto_resumen.configure(
            yscrollcommand=scroll_res_y.set,
            xscrollcommand=scroll_res_x.set,
        )
        self.texto_resumen.grid(row=0, column=0, sticky="nsew")
        scroll_res_y.grid(row=0, column=1, sticky="ns")
        scroll_res_x.grid(row=1, column=0, sticky="ew")
        tab_res.rowconfigure(0, weight=1)
        tab_res.columnconfigure(0, weight=1)

        # Pestaña tabla
        tab_tabla = ttk.Frame(notebook, padding=10)
        notebook.add(tab_tabla, text="Resultados por frecuencia")

        cols = (
            "f",
            "mean",
            "sd",
            "cv",
            "ci_low",
            "ci_high",
            "phase",
            "phase_sd",
            "bias",
            "error",
            "abs_error",
        )

        self.tabla = ttk.Treeview(
            tab_tabla,
            columns=cols,
            show="headings",
            height=18,
        )

        titulos = {
            "f": "f (kHz)",
            "mean": "Media |Z| (Ω)",
            "sd": "SD (Ω)",
            "cv": "CV (%)",
            "ci_low": "IC95 inf. (Ω)",
            "ci_high": "IC95 sup. (Ω)",
            "phase": "Fase media (°)",
            "phase_sd": "SD fase (°)",
            "bias": "Bias (Ω)",
            "error": "Error (%)",
            "abs_error": "|Error| (%)",
        }

        anchos = {
            "f": 72,
            "mean": 115,
            "sd": 90,
            "cv": 82,
            "ci_low": 105,
            "ci_high": 105,
            "phase": 100,
            "phase_sd": 90,
            "bias": 90,
            "error": 90,
            "abs_error": 90,
        }

        for c in cols:
            self.tabla.heading(c, text=titulos[c])
            self.tabla.column(c, width=anchos[c], anchor="center")

        sy = ttk.Scrollbar(
            tab_tabla, orient="vertical", command=self.tabla.yview
        )
        sx = ttk.Scrollbar(
            tab_tabla, orient="horizontal", command=self.tabla.xview
        )
        self.tabla.configure(
            yscrollcommand=sy.set,
            xscrollcommand=sx.set,
        )

        self.tabla.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        tab_tabla.rowconfigure(0, weight=1)
        tab_tabla.columnconfigure(0, weight=1)

    # -----------------------------
    # Carga
    # -----------------------------
    def cargar_carpeta(self):
        carpeta = filedialog.askdirectory(
            title="Seleccione la carpeta que contiene las 5 mediciones"
        )
        if not carpeta:
            return

        archivos = sorted(
            [
                str(p)
                for p in Path(carpeta).iterdir()
                if p.is_file() and p.suffix.lower() == ".csv"
            ],
            key=self._clave_orden,
        )

        if len(archivos) != N_REPETICIONES:
            messagebox.showerror(
                "Cantidad incorrecta",
                f"La carpeta contiene {len(archivos)} CSV. "
                "Debe contener exactamente 5.",
            )
            return

        self._establecer_archivos(archivos)

    def cargar_archivos(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccione exactamente 5 archivos CSV",
            filetypes=[
                ("Archivos CSV", "*.csv"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not rutas:
            return

        if len(rutas) != N_REPETICIONES:
            messagebox.showerror(
                "Cantidad incorrecta",
                "Debe seleccionar exactamente 5 archivos CSV.",
            )
            return

        self._establecer_archivos(
            sorted(list(rutas), key=self._clave_orden)
        )

    @staticmethod
    def _clave_orden(ruta):
        nombre = Path(ruta).stem
        m = re.search(r"-M(\d+)$", nombre, flags=re.IGNORECASE)
        if m:
            return (0, int(m.group(1)))
        return (1, nombre.lower())

    def _establecer_archivos(self, archivos):
        self.rutas = list(archivos)
        nombres = [Path(x).name for x in self.rutas]
        self.archivos_label.config(
            text="Archivos: " + " | ".join(nombres),
            foreground="black",
        )

    # -----------------------------
    # Análisis
    # -----------------------------
    def _leer_referencia(self):
        texto = self.ref_var.get().strip()
        if not texto:
            return None

        try:
            valor = float(texto.replace(",", "."))
        except ValueError:
            raise ValueError(
                "La resistencia de referencia debe ser un número."
            )

        if valor <= 0:
            raise ValueError(
                "La resistencia de referencia debe ser positiva."
            )
        return valor

    def analizar(self):
        if len(self.rutas) != N_REPETICIONES:
            messagebox.showwarning(
                "Faltan mediciones",
                "Cargue primero exactamente 5 archivos CSV.",
            )
            return

        try:
            r_ref = self._leer_referencia()
            combinado, avisos = combinar_cinco_mediciones(self.rutas)
            detalle, resumen = calcular_metricas(combinado, r_ref)

            etiqueta = self._etiqueta_conjunto()
            figuras = crear_figuras(detalle, r_ref, etiqueta)

            # Cerrar figuras anteriores
            for _, fig in self.figuras:
                try:
                    plt.close(fig)
                except Exception:
                    pass

            self.detalle = detalle
            self.resumen = resumen
            self.avisos = avisos
            self.figuras = figuras

            self._mostrar_resumen()
            self._llenar_tabla()

            mensaje = (
                f"Análisis completo.\n\n"
                f"{len(detalle)} frecuencias comunes "
                f"entre {detalle['Frequency_Hz'].min()/1000:.1f} y "
                f"{detalle['Frequency_Hz'].max()/1000:.1f} kHz."
            )
            if avisos:
                mensaje += (
                    f"\n\nSe detectaron {len(avisos)} advertencia(s). "
                    "Revise la pestaña Resumen."
                )

            messagebox.showinfo("Análisis completo", mensaje)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _etiqueta_conjunto(self):
        nombres = [Path(x).stem for x in self.rutas]
        prefijos = []
        for n in nombres:
            m = re.match(r"(R\d+)-M\d+$", n, flags=re.IGNORECASE)
            if m:
                prefijos.append(m.group(1).upper())
        if prefijos and len(set(prefijos)) == 1:
            return f"- {prefijos[0]}"
        return ""

    def _mostrar_resumen(self):
        r = self.resumen
        lineas = []

        lineas += [
            "CONFIGURACIÓN DEL CONJUNTO",
            "--------------------------",
            f"Archivos:                    {', '.join(Path(x).name for x in self.rutas)}",
            f"Repeticiones:                {r['n_repetitions']}",
            f"Frecuencias comunes:         {r['n_frequencies']}",
            f"Rango analizado:             {r['f_min_kHz']:.1f}–{r['f_max_kHz']:.1f} kHz",
            "",
            "PRECISIÓN / REPETIBILIDAD",
            "-------------------------",
            f"Media de |Z| en la banda:    {r['Z_band_mean_Ohm']:.6f} Ω",
            f"SD media:                    {r['mean_SD_Ohm']:.6f} Ω",
            f"SD máxima:                   {r['max_SD_Ohm']:.6f} Ω",
            f"CV medio:                    {r['mean_CV_pct']:.6f} %",
            f"CV máximo:                   {r['max_CV_pct']:.6f} %",
            f"f del CV máximo:             {r['frequency_of_max_CV_kHz']:.1f} kHz",
            "",
            "DEPENDENCIA CON LA FRECUENCIA",
            "-----------------------------",
            f"|Z| media mínima:            {r['Z_band_min_mean_Ohm']:.6f} Ω",
            f"|Z| media máxima:            {r['Z_band_max_mean_Ohm']:.6f} Ω",
            f"Cambio 100 kHz - 5 kHz:      {r['Z_change_100k_minus_5k_Ohm']:.6f} Ω",
            f"Cambio relativo a media:     {r['Z_change_100k_minus_5k_pct_of_band_mean']:.6f} %",
            "",
            "FASE",
            "----",
            f"Fase media:                  {r['mean_phase_deg']:.6f} °",
            f"SD media de fase:            {r['mean_phase_SD_deg']:.6f} °",
            f"|fase| media respecto a 0°:  {r['mean_abs_phase_error_deg']:.6f} °",
            f"|fase| máxima respecto a 0°: {r['max_abs_phase_error_deg']:.6f} °",
        ]

        if "R_reference_Ohm" in r:
            lineas += [
                "",
                "EXACTITUD",
                "---------",
                f"Referencia:                  {r['R_reference_Ohm']:.6f} Ω",
                f"Bias medio:                  {r['mean_bias_Ohm']:.6f} Ω",
                f"Error medio con signo:       {r['mean_signed_error_pct']:.6f} %",
                f"MARE:                        {r['MARE_pct']:.6f} %",
                f"Error absoluto máximo:       {r['max_abs_error_pct']:.6f} %",
                f"f del error abs. máximo:     {r['frequency_of_max_abs_error_kHz']:.1f} kHz",
                f"RMSE global:                 {r['global_RMSE_Ohm']:.6f} Ω",
                f"RMSE global relativo:        {r['global_RMSE_pct']:.6f} %",
            ]
        else:
            lineas += [
                "",
                "EXACTITUD",
                "---------",
                "No se ingresó un valor de referencia.",
                "Por lo tanto no se calculan Bias, Error %, MARE ni RMSE.",
            ]

        if self.avisos:
            lineas += ["", "ADVERTENCIAS", "------------"]
            lineas += [f"- {a}" for a in self.avisos]

        self.texto_resumen.configure(state="normal")
        self.texto_resumen.delete("1.0", "end")
        self.texto_resumen.insert("1.0", "\n".join(lineas))
        self.texto_resumen.configure(state="disabled")

    def _llenar_tabla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        exactitud = "Bias_Ohm" in self.detalle.columns

        for _, row in self.detalle.iterrows():
            valores = [
                f"{row['Frequency_Hz']/1000:.1f}",
                f"{row['Z_mean_Ohm']:.6f}",
                f"{row['Z_SD_Ohm']:.6f}",
                f"{row['Z_CV_pct']:.6f}",
                f"{row['Z_CI95_low_Ohm']:.6f}",
                f"{row['Z_CI95_high_Ohm']:.6f}",
                f"{row['Phase_mean_deg']:.6f}",
                f"{row['Phase_SD_deg']:.6f}",
            ]

            if exactitud:
                valores += [
                    f"{row['Bias_Ohm']:.6f}",
                    f"{row['Error_pct']:.6f}",
                    f"{row['Abs_Error_pct']:.6f}",
                ]
            else:
                valores += ["", "", ""]

            self.tabla.insert("", "end", values=valores)

    # -----------------------------
    # Gráficos / exportación
    # -----------------------------
    def mostrar_graficas(self):
        if not self.figuras:
            messagebox.showwarning(
                "Sin análisis",
                "Primero realice el análisis.",
            )
            return
        plt.show()

    def exportar(self):
        if self.detalle is None or self.resumen is None:
            messagebox.showwarning(
                "Sin análisis",
                "Primero realice el análisis.",
            )
            return

        carpeta = filedialog.askdirectory(
            title="Seleccione la carpeta de salida"
        )
        if not carpeta:
            return

        carpeta = Path(carpeta)

        etiqueta = self._etiqueta_conjunto().replace("-", "").strip()
        if not etiqueta:
            etiqueta = "AD5933"
        base = etiqueta.replace(" ", "_")

        try:
            detalle_path = carpeta / f"{base}_resultados_por_frecuencia.csv"
            resumen_path = carpeta / f"{base}_resumen.csv"
            original_path = carpeta / f"{base}_datos_5_mediciones.csv"

            self.detalle.to_csv(
                detalle_path,
                index=False,
                decimal=".",
            )

            pd.DataFrame([self.resumen]).to_csv(
                resumen_path,
                index=False,
                decimal=".",
            )

            # Sólo columnas originales combinadas
            originales = [
                c
                for c in self.detalle.columns
                if re.match(
                    r"^(Frequency_Hz|Z_M\d+|Phase_M\d+|Real_M\d+|Imag_M\d+|Magnitude_M\d+)$",
                    c,
                )
            ]
            self.detalle[originales].to_csv(
                original_path,
                index=False,
                decimal=".",
            )

            for nombre, fig in self.figuras:
                fig.savefig(
                    carpeta / f"{base}_{nombre}.png",
                    dpi=200,
                    bbox_inches="tight",
                )

            # Archivo de advertencias, si las hay
            if self.avisos:
                (carpeta / f"{base}_advertencias.txt").write_text(
                    "\n".join(self.avisos),
                    encoding="utf-8",
                )

            messagebox.showinfo(
                "Exportación completa",
                "Se exportaron los resultados CSV y las gráficas PNG.",
            )

        except Exception as e:
            messagebox.showerror(
                "Error de exportación",
                str(e),
            )

    def limpiar(self):
        self.rutas = []
        self.detalle = None
        self.resumen = None
        self.avisos = []

        for _, fig in self.figuras:
            try:
                plt.close(fig)
            except Exception:
                pass
        self.figuras = []

        self.archivos_label.config(
            text="No hay archivos cargados.",
            foreground="gray",
        )

        self.texto_resumen.configure(state="normal")
        self.texto_resumen.delete("1.0", "end")
        self.texto_resumen.configure(state="disabled")

        for item in self.tabla.get_children():
            self.tabla.delete(item)


if __name__ == "__main__":
    app = EvaluadorAD5933()
    app.mainloop()
