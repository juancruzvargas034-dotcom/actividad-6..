import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# CONFIGURACIÓN
st.set_page_config(
    page_title="COINK | Análisis de depósitos",
    page_icon="🐷",
    layout="wide"
)

st.title("🐷 COINK — Panel de análisis")
st.caption("Análisis de datos de depósitos en Oinks")

# CARGAR DATOS
@st.cache_data
def cargar_datos(archivo):
    df = pd.read_csv(archivo)

    columnas = {
        "user_id",
        "operation_value",
        "operation_date",
        "maplocation_name"
    }

    faltantes = columnas - set(df.columns)
    if faltantes:
        raise ValueError(
            "Faltan columnas: " + ", ".join(faltantes)
        )

    df["operation_value"] = pd.to_numeric(
        df["operation_value"], errors="coerce"
    )
    df["operation_date"] = pd.to_datetime(
        df["operation_date"], errors="coerce"
    )

    df = df.dropna(subset=[
        "user_id",
        "operation_value",
        "operation_date",
        "maplocation_name"
    ])

    df = df[df["operation_value"] >= 0].copy()
    return df


# ARCHIVO CSV
ruta = Path(__file__).parent / "depositos_oink.csv"

archivo = st.sidebar.file_uploader(
    "📂 Cargar archivo CSV",
    type=["csv"]
)

try:
    if archivo is not None:
        df = cargar_datos(archivo)
    elif ruta.exists():
        df = cargar_datos(ruta)
    else:
        st.warning(
            "Carga el archivo depositos_oink.csv "
            "desde el menú lateral."
        )
        st.stop()

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.stop()


# FILTROS
st.sidebar.header("🔎 Filtros")

fecha_min = df["operation_date"].min().date()
fecha_max = df["operation_date"].max().date()

rango = st.sidebar.date_input(
    "Seleccionar periodo",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

if isinstance(rango, (tuple, list)) and len(rango) == 2:
    inicio, fin = rango
else:
    inicio, fin = fecha_min, fecha_max

lugares = sorted(
    df["maplocation_name"].dropna().unique().tolist()
)

seleccion = st.sidebar.multiselect(
    "Seleccionar ubicación",
    lugares,
    default=lugares
)

filtrado = df[
    df["operation_date"].dt.date.between(inicio, fin)
    & df["maplocation_name"].isin(seleccion)
].copy()

if filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()


# MÉTRICAS PRINCIPALES
total_depositos = len(filtrado)
total_dinero = filtrado["operation_value"].sum()
usuarios = filtrado["user_id"].nunique()
promedio = filtrado["operation_value"].mean()
mediana = filtrado["operation_value"].median()

recurrentes = (
    filtrado.groupby("user_id").size() > 1
).sum()

porcentaje = (
    recurrentes / usuarios * 100 if usuarios > 0 else 0
)

st.header("📊 Métricas generales")

col1, col2, col3 = st.columns(3)

col1.metric(
    "💰 Total de depósitos",
    f"{total_depositos:,}"
)

col2.metric(
    "💵 Dinero recaudado",
    f"${total_dinero:,.0f}"
)

col3.metric(
    "👥 Usuarios únicos",
    f"{usuarios:,}"
)

col4, col5, col6 = st.columns(3)

col4.metric(
    "📈 Promedio por depósito",
    f"${promedio:,.0f}"
)

col5.metric(
    "📊 Mediana por depósito",
    f"${mediana:,.0f}"
)

col6.metric(
    "🔁 Usuarios recurrentes",
    f"{porcentaje:.1f}%"
)


# GRÁFICAS POR UBICACIÓN
st.divider()
st.header("📍 Análisis por ubicación")

izquierda, derecha = st.columns(2)

with izquierda:
    st.subheader("Cantidad de depósitos")

    por_lugar = (
        filtrado.groupby("maplocation_name")
        .size()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots()

    por_lugar.plot(
        kind="bar",
        ax=ax
    )

    ax.set_xlabel("Ubicación")
    ax.set_ylabel("Número de depósitos")
    ax.tick_params(axis="x", rotation=25)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


with derecha:
    st.subheader("Dinero por ubicación")

    dinero_lugar = (
        filtrado.groupby("maplocation_name")[
            "operation_value"
        ].sum().sort_values(ascending=False)
    )

    fig, ax = plt.subplots()

    dinero_lugar.plot(
        kind="bar",
        ax=ax
    )

    ax.set_xlabel("Ubicación")
    ax.set_ylabel("Dinero depositado ($)")
    ax.tick_params(axis="x", rotation=25)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# EVOLUCIÓN MENSUAL
st.divider()
st.header("📅 Evolución mensual")

mensual = (
    filtrado.set_index("operation_date")
    .resample("MS")
    .agg(
        depositos=("operation_value", "size"),
        dinero=("operation_value", "sum")
    )
    .reset_index()
)

fig, ax = plt.subplots()

ax.plot(
    mensual["operation_date"],
    mensual["depositos"],
    marker="o"
)

ax.set_xlabel("Mes")
ax.set_ylabel("Número de depósitos")
ax.set_title("Depósitos realizados por mes")

fig.autofmt_xdate()
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# FRECUENCIA DE USUARIOS
st.divider()
st.header("👥 Frecuencia de depósitos por usuario")

frecuencia = filtrado.groupby("user_id").size()

distribucion = (
    frecuencia.value_counts()
    .sort_index()
)

tabla_frecuencia = (
    distribucion.rename_axis("Número de depósitos")
    .reset_index(name="Usuarios")
)

st.bar_chart(
    tabla_frecuencia.set_index("Número de depósitos")["Usuarios"]
)


# TABLA RESUMEN
st.divider()
st.header("📋 Resumen de ubicaciones")

resumen = (
    filtrado.groupby("maplocation_name")
    .agg(
        Depositos=("operation_value", "size"),
        Dinero_total=("operation_value", "sum"),
        Promedio=("operation_value", "mean"),
        Usuarios_unicos=("user_id", "nunique")
    )
    .sort_values("Depositos", ascending=False)
)

resumen["Dinero_total"] = resumen["Dinero_total"].round(0)
resumen["Promedio"] = resumen["Promedio"].round(0)

st.dataframe(
    resumen,
    use_container_width=True
)


# INTERPRETACIÓN
st.divider()
st.header("🧠 Interpretación de resultados")

st.markdown("""
- **Total de depósitos:** cantidad de operaciones registradas.
- **Dinero recaudado:** suma de los valores de los depósitos.
- **Usuarios únicos:** cantidad de usuarios diferentes.
- **Promedio:** valor medio de los depósitos.
- **Mediana:** valor central de los depósitos.
- **Usuarios recurrentes:** porcentaje de usuarios que
  realizaron más de un depósito en el periodo seleccionado.
- **Ubicación más utilizada:** lugar con mayor cantidad
  de depósitos registrados.

Estas métricas permiten analizar el comportamiento de los
depósitos, comparar ubicaciones y observar los hábitos
de ahorro de los usuarios.
""")

st.caption(
    "COINK | Proyecto de análisis de datos con Python, "
    "Pandas, Matplotlib y Streamlit."
)