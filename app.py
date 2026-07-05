"""
Calculadora de Honorarios Profesionales - Consultora Técnica
==============================================================
Ingeniería de Costos | San Juan, Argentina

Cómo ejecutar:
    1. Instalar Streamlit una sola vez:  pip install streamlit
    2. Ejecutar desde la terminal:       streamlit run calculadora_honorarios.py

Cómo actualizar precios cuando cambian las sugerencias del CICSJ o la inflación:
    Editar ÚNICAMENTE el bloque "CONFIGURACIÓN DE PRECIOS" más abajo.
    No es necesario tocar el resto del código.
"""

import streamlit as st
import pandas as pd

# ============================================================
# CONFIGURACIÓN DE PRECIOS
# (Único bloque que se debe editar al actualizar valores)
# ============================================================

# Lista A: Porcentaje sobre el costo de obra (%)
# Clave = nombre del servicio | Valor = porcentaje (ej: 2 significa 2%)
PORCENTAJE_OBRA = {
    "Memoria de cálculo estructural": 1.1,
    "Plano de arquitectura": 0.75,
    "Plano estructural": 0.75,
    "Modelado 3D (BIM)": 1.1,
    "Renders": 0.25,
    "Videos de presentación": 0.3,
    "Cotizaciones (Cómputo y presupuesto)": 0.4,
    "Firma": 0.4,
}

# Lista B: Precio fijo por m² ($/m²)
PRECIO_POR_M2 = {
    "Memoria de cálculo estructural": 1100,
    "Plano de arquitectura": 800,
    "Plano estructural": 800,
    "Modelado 3D (BIM)": 1100,
    "Renders": 300,
    "Videos de presentación": 400,
    "Cotizaciones (Cómputo y presupuesto)": 400,
    "Firma": 300,
}

# Margen de beneficio profesional (%) aplicado sobre el subtotal de servicios
MARGEN_PROFESIONAL_PCT = 0

# Costo de equipo técnico / servicios subcontratados
# Puede ser un monto fijo, o un porcentaje del subtotal (ver CONFIGURACIÓN DE MODO abajo)
COSTO_SUBCONTRATADOS_FIJO = 0          # monto fijo en $ (usar si MODO_SUBCONTRATADOS = "fijo")
COSTO_SUBCONTRATADOS_PCT = 50.0        # % del subtotal (usar si MODO_SUBCONTRATADOS = "porcentaje")
MODO_SUBCONTRATADOS = "porcentaje"     # "fijo" o "porcentaje"

# ============================================================
# FIN DE LA CONFIGURACIÓN DE PRECIOS
# ============================================================


SERVICIOS = list(PORCENTAJE_OBRA.keys())


def calcular_costo_servicio(servicio: str, metodo: str, costo_obra: float, superficie: float,
                             porcentaje_obra: dict, precio_m2: dict) -> float:
    """Devuelve el costo de un servicio según el método elegido, usando las tarifas
    vigentes para este presupuesto (base o ajustadas en la sección 'Ajustar valores')."""
    if metodo == "% Precio de Obra":
        pct = porcentaje_obra.get(servicio, 0)
        return costo_obra * (pct / 100)
    else:  # $/m²
        precio = precio_m2.get(servicio, 0)
        return precio * superficie


def formatear_moneda(valor: float) -> str:
    return f"$ {valor:,.0f}".replace(",", ".")


# ============================================================
# INTERFAZ DE USUARIO (Streamlit)
# ============================================================

st.set_page_config(page_title="MAS Consultora", layout="centered")

st.title("MAS CONSULTORA")
st.caption("Consultora técnica de ingeniería y arquitectura · San Juan, Argentina")

st.divider()

# --- Datos del proyecto -------------------------------------------------
st.subheader("1. Datos del proyecto")

col1, col2 = st.columns(2)
with col1:
    costo_obra = st.number_input(
        "Costo total de la obra ($)",
        min_value=0.0,
        value=0.0,
        step=100_000.0,
        format="%.0f",
    )
with col2:
    superficie = st.number_input(
        "Superficie total (m²)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        format="%.1f",
    )

# --- Método de cálculo ----------------------------------------------------
st.subheader("2. Método de cálculo")
metodo = st.radio(
    "Elegí el método con el que se van a calcular los honorarios:",
    options=["% Precio de Obra", "$/m²"],
    horizontal=True,
)

# --- Subcontratados (ajustable en tiempo real) -----------------------------
st.subheader("2.1 Pago a subcontratados / equipo técnico")
modo_subcontratados_ui = st.radio(
    "¿Cómo se calcula el pago a subcontratados?",
    options=["Porcentaje del costo de cada servicio", "Monto fijo total"],
    horizontal=True,
    index=0 if MODO_SUBCONTRATADOS == "porcentaje" else 1,
)

if modo_subcontratados_ui == "Porcentaje del costo de cada servicio":
    pct_subcontratados_ui = st.slider(
        "Porcentaje a pagar a subcontratados (%)",
        min_value=0.0,
        max_value=100.0,
        value=float(COSTO_SUBCONTRATADOS_PCT),
        step=0.5,
    )
    fijo_subcontratados_ui = COSTO_SUBCONTRATADOS_FIJO
else:
    fijo_subcontratados_ui = st.number_input(
        "Monto fijo total para subcontratados ($)",
        min_value=0.0,
        value=float(COSTO_SUBCONTRATADOS_FIJO),
        step=10_000.0,
        format="%.0f",
    )
    pct_subcontratados_ui = COSTO_SUBCONTRATADOS_PCT

# --- Checklist de servicios -----------------------------------------------
st.subheader("3. Servicios incluidos")
st.caption("Tildá los servicios que forman parte de este presupuesto.")

servicios_seleccionados = []
cols = st.columns(2)
for i, servicio in enumerate(SERVICIOS):
    with cols[i % 2]:
        if st.checkbox(servicio, value=True, key=f"chk_{i}"):
            servicios_seleccionados.append(servicio)

st.divider()

# --- Ajuste fino de valores por servicio (opcional y discreto) -------------
with st.expander("⚙️ Ajustar valores de este presupuesto (opcional)"):
    st.caption(
        "Parten de la configuración base. Cambiá acá solo si este presupuesto "
        "puntual necesita una tarifa distinta."
    )

    margen_profesional_ui = st.number_input(
        "Margen profesional (%)",
        min_value=0.0,
        value=float(MARGEN_PROFESIONAL_PCT),
        step=1.0,
        format="%.1f",
        key="margen_ui",
    )

    st.markdown("---")

    porcentaje_obra_ui = {}
    precio_m2_ui = {}
    for servicio in SERVICIOS:
        c1, c2 = st.columns(2)
        with c1:
            porcentaje_obra_ui[servicio] = st.number_input(
                f"{servicio} · % obra",
                min_value=0.0,
                value=float(PORCENTAJE_OBRA[servicio]),
                step=0.05,
                format="%.2f",
                key=f"pct_ui_{servicio}",
            )
        with c2:
            precio_m2_ui[servicio] = st.number_input(
                f"{servicio} · $/m²",
                min_value=0.0,
                value=float(PRECIO_POR_M2[servicio]),
                step=50.0,
                format="%.0f",
                key=f"m2_ui_{servicio}",
            )

# ============================================================
# LÓGICA DE CÁLCULO
# ============================================================

filas = []
subtotal_servicios = 0.0

for servicio in servicios_seleccionados:
    costo = calcular_costo_servicio(servicio, metodo, costo_obra, superficie, porcentaje_obra_ui, precio_m2_ui)
    subtotal_servicios += costo
    tasa_aplicada = (
        f"{porcentaje_obra_ui[servicio]}% de la obra"
        if metodo == "% Precio de Obra"
        else f"{formatear_moneda(precio_m2_ui[servicio])} / m²"
    )
    filas.append({
        "Servicio": servicio,
        "Tasa aplicada": tasa_aplicada,
        "Costo": costo,
    })

# Margen profesional (usa lo elegido en el apartado de ajustes)
margen_valor = subtotal_servicios * (margen_profesional_ui / 100)

# Subcontratados (usa lo elegido en la interfaz, sección 2.1)
usar_modo_fijo = modo_subcontratados_ui == "Monto fijo total"

if usar_modo_fijo:
    subcontratados_valor = fijo_subcontratados_ui
else:
    subcontratados_valor = subtotal_servicios * (pct_subcontratados_ui / 100)

# Reparto del pago a subcontratados por servicio (columna nueva del desglose)
for fila in filas:
    if usar_modo_fijo:
        proporcion = (fila["Costo"] / subtotal_servicios) if subtotal_servicios > 0 else 0
        fila["Pago a subcontratados"] = subcontratados_valor * proporcion
    else:
        fila["Pago a subcontratados"] = fila["Costo"] * (pct_subcontratados_ui / 100)

total_final = subtotal_servicios + margen_valor + subcontratados_valor

# ============================================================
# SALIDA / RESUMEN PARA EL CLIENTE
# ============================================================

st.subheader("4. Resumen del presupuesto")

st.markdown(f"**Método utilizado:** {metodo}")

if filas:
    df = pd.DataFrame(filas)
    df["Costo"] = df["Costo"].apply(formatear_moneda)
    df["Pago a subcontratados"] = df["Pago a subcontratados"].apply(formatear_moneda)
    st.table(df.set_index("Servicio"))
else:
    st.warning("No hay servicios seleccionados. Tildá al menos uno en el checklist.")

st.markdown("---")

resumen_col1, resumen_col2 = st.columns(2)
with resumen_col1:
    st.metric("Subtotal servicios", formatear_moneda(subtotal_servicios))
    st.metric(f"Margen profesional ({margen_profesional_ui:.1f}%)", formatear_moneda(margen_valor))
with resumen_col2:
    etiqueta_subcontratados = (
        "Equipo técnico / subcontratados (monto fijo)"
        if usar_modo_fijo
        else f"Equipo técnico / subcontratados ({pct_subcontratados_ui:.1f}%)"
    )
    st.metric(etiqueta_subcontratados, formatear_moneda(subcontratados_valor))
    st.metric("💰 TOTAL FINAL", formatear_moneda(total_final))

st.divider()
st.caption(
    "Presupuesto generado automáticamente. Valores de referencia sujetos a "
    "actualización según sugerencias del Colegio de Ingenieros de San Juan (CICSJ) "
    "y variación del costo de la construcción."
)
