"""
SIMULADOR DE DESCANSOS COMPENSATORIOS
Equipos: SECO (L1-L2-L3), DASA, Facturación, Inventarios, Devolutivos
Ciclo: +8d / +8d / +15d / +8d / +8d | Domingo → Lunes
"""
import streamlit as st
import pandas as pd
import datetime
from copy import deepcopy

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Simulador DC",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

END_DATE = datetime.date(2026, 7, 12)
DATES = [datetime.date(2026, 6, 1) + datetime.timedelta(days=i) for i in range(42)]
DI = ['L','M','M','J','V','S','D']

DC_COLORS = {
    'DC1': ('#C00000', '#FFFFFF'),
    'DC2': ('#BF8F00', '#000000'),
    'DC3': ('#375623', '#FFFFFF'),
}
ROL_COLORS = {
    'Lider de turno': '#1F3864',
    'Líder Turno':    '#1F3864',
    'Apoyo de Bodega':'#2E75B6',
    'Apoyo Devolutivos':'#2E75B6',
    'Apoyo inventarios':'#2E75B6',
    'Despachador':    '#C55A11',
    'Trazabilidad':   '#BF8F00',
    'Alistador':      '#375623',
    'CASETA':         '#31869B',
    'CYD':            '#548235',
    'Montacarguista': '#7F6000',
    'Auxiliar Logística':'#4E6B30',
    'Especialista Devolutivos':'#1F3864',
    'Aux admin Devolutivos':'#BF8F00',
    'aux Devolutivos':'#4E6B30',
    'Facturador':     '#2E75B6',
    'Pedidos':        '#C55A11',
    'Lider Inventarios':'#1F3864',
    'aux inventarios':'#4E6B30',
    'Aux admin':      '#BF8F00',
}

# ─── ALGORITMO DC ────────────────────────────────────────────────────────────
def gen_dc(first_date: datetime.date) -> set:
    """Genera el set de fechas de descanso desde first_date"""
    if not first_date:
        return set()
    result = [first_date]
    gaps = [8, 8, 15, 8, 8]
    current = first_date
    for gap in gaps:
        nxt = current + datetime.timedelta(days=gap)
        if nxt.weekday() == 6:  # domingo → lunes
            nxt += datetime.timedelta(days=1)
        if nxt > END_DATE:
            break
        result.append(nxt)
        current = nxt
    return set(result)

def gen_dc_list(first_date: datetime.date) -> list:
    """Lista ordenada de DCs"""
    return sorted(gen_dc(first_date))

# ─── DATOS BASE ───────────────────────────────────────────────────────────────
def make_people():
    """Retorna dict con todos los equipos"""
    J = lambda d: datetime.date(2026, 6, d)
    return {
        'L1 — SECO': {
            'min_oper': 27, 'total': 32,
            'people': [
                (1,'BERNAL PARDO GERMAN LEONARDO','Lider de turno','DC1',J(3)),
                (2,'RODRIGUEZ AYALA MIGUEL ANTONIO','Apoyo de Bodega','DC1',J(5)),
                (3,'CAMELO URIBE SEBASTIAN','Despachador','DC1',J(1)),
                (4,'JAIMES DELGADO LINA MARCELA','Alistador','DC1',J(1)),
                (5,'BURGOS ZAMBRANO OSCAR YESID','Alistador','DC1',J(2)),
                (6,'RIAÑO SUSPES LUZ MIRIAM','CASETA','DC1',J(2)),
                (7,'BOLAÑOS CUELLAR JORGE ANDRES','CYD','DC1',J(2)),
                (8,'CANCHON ARENAS HELMER MAURICIO','Montacarguista','DC1',J(2)),
                (9,'DUARTE RODRIGUEZ PEDRO FABIAN','Montacarguista','DC1',J(3)),
                (10,'BARACALDO NAVARRETE MAURICIO','Montacarguista','DC1',J(3)),
                (11,'QUIMBAY SANTANA FABIO NELSON','Montacarguista','DC1',J(3)),
                (12,'MARTINEZ SANCHEZ JOSE ALEJANDRO','Apoyo de Bodega','DC2',J(8)),
                (13,'CHAPARRO PARRA WILLIAM FERNANDO','Despachador','DC2',J(8)),
                (14,'MALAGON SANCHEZ KEIVY NICOLAS','Alistador','DC2',J(8)),
                (15,'VIAFARA SUAREZ JOAN ALEXIS','Alistador','DC2',J(8)),
                (16,'PIZO PERDOMO DEIMAR ORLANDO','CYD','DC2',J(11)),
                (17,'URREGO FORERO EDISON ALEXANDER','CYD','DC2',J(12)),
                (18,'ROJAS ALBA JUAN CARLOS','Montacarguista','DC2',J(12)),
                (19,'RINCON SAAVEDRA MIYER JOAQUIN','Montacarguista','DC2',J(12)),
                (20,'ESCOBAR RINCON JOSE LUIS','Montacarguista','DC2',J(12)),
                (21,'SANCHEZ GARNICA CRISTIAN WILFREDO','Montacarguista','DC2',J(13)),
                (22,'POR CONTRATAR','CYD','DC2',J(13)),
                (23,'CARRANZA GUERRERO VICTOR HERNANDO','Trazabilidad','DC3',J(15)),
                (24,'SARMIENTO OLAYA FABIAN ERNESTO','Despachador','DC3',J(15)),
                (25,'ALARCON ORDOÑEZ DANIEL ESTEBAN','Alistador','DC3',J(15)),
                (26,'ROJAS ROJAS DIEGO ALEJANDRO','CYD','DC3',J(15)),
                (27,'BOLIVAR AMEZQUITA JOSE ANIBAL','Montacarguista','DC3',J(18)),
                (28,'GUTIERREZ GIRAL GILBERTO','Montacarguista','DC3',J(19)),
                (29,'JULIO CAMARGO GERMAN GUILLERMO','Montacarguista','DC3',J(19)),
                (30,'SANCHEZ RIAÑO DANIEL STIVEN','Montacarguista','DC3',J(19)),
                (31,'POR CONTRATAR','CYD','DC3',J(20)),
                (32,'POR CONTRATAR','CYD','DC3',J(16)),
            ]
        },
        'L2 — SECO': {
            'min_oper': 27, 'total': 32,
            'people': [
                (1,'CHARRIS TORRES YEISSON ALBERTO','Lider de turno','DC1',J(4)),
                (2,'CARRILLO GUACANEME JOSE LUIS','Apoyo de Bodega','DC1',J(5)),
                (3,'CHIA PARRA MICHAEL ANDRES','Despachador','DC1',J(1)),
                (4,'GUERRERO PINZON JEISON SMITH','Alistador','DC1',J(1)),
                (5,'CUERVO PALACIOS JORGE DANIEL','Alistador','DC1',J(2)),
                (6,'DIAZ MOLANO JUAN PABLO','CYD','DC1',J(2)),
                (7,'SALAMANCA MEDINA JASON BRAYAN','Montacarguista','DC1',J(2)),
                (8,'CARDENAS RIVERO NESTOR JOSE','Montacarguista','DC1',J(2)),
                (9,'CASTRO PACHON EDUARDO ELI','Montacarguista','DC1',J(3)),
                (10,'GUERRERO CORREDOR DAYER','Montacarguista','DC1',J(3)),
                (11,'POR CONTRATAR','CYD','DC1',J(3)),
                (12,'MOJICA MONTAÑO NELSON ORLANDO','Apoyo de Bodega','DC2',J(8)),
                (13,'GUZMAN HERNANDEZ JUAN CARLOS','Despachador','DC2',J(8)),
                (14,'ORJUELA CUBILLOS SERGIO ANDRES','Alistador','DC2',J(8)),
                (15,'GUTIERREZ CLAVIJO DIANA CAROLINA','Alistador','DC2',J(8)),
                (16,'ALAPE RINCON CRISTIAN ERNESTO','CYD','DC2',J(11)),
                (17,'GUERRERO BARCELO JESUS ELIAS','CYD','DC2',J(12)),
                (18,'SOLANO MORENO KEVIN RICARDO','Montacarguista','DC2',J(12)),
                (19,'LINARES LOPEZ JAIR ESTEBAN','Montacarguista','DC2',J(12)),
                (20,'MOYANO CHAVES JOSE LUIS','Montacarguista','DC2',J(12)),
                (21,'PACHON CANO ANDRU FERNEY','Montacarguista','DC2',J(13)),
                (22,'POR CONTRATAR','CYD','DC2',J(13)),
                (23,'BEJARANO MARTÍN JENI RUBIELA','Trazabilidad','DC3',J(15)),
                (24,'ESPEJO ORDOÑEZ DANIEL ALEJANDRO','Despachador','DC3',J(15)),
                (25,'URIANA EPIAYU PEDRO','Alistador','DC3',J(15)),
                (26,'RIOS GRANDE ROLLER STIVEN','CYD','DC3',J(15)),
                (27,'PINEDA RODRIGUEZ HECTOR JAVIER','Montacarguista','DC3',J(18)),
                (28,'RUBIANO FONSECA RODRIGO','Montacarguista','DC3',J(19)),
                (29,'RUBIANO RUBIANO JOSE MANUEL','Montacarguista','DC3',J(19)),
                (30,'TAPIA TAPIA FRANCISCO DAVID','Montacarguista','DC3',J(19)),
                (31,'POR CONTRATAR','Montacarguista','DC3',J(20)),
                (32,'POR CONTRATAR','CYD','DC3',J(16)),
            ]
        },
        'L3 — SECO': {
            'min_oper': 27, 'total': 32,
            'people': [
                (1,'AMAYA PINZON DAVID MAURICIO','Lider de turno','DC1',J(6)),
                (2,'ORTIZ MURCIA LEONARDO','Apoyo de Bodega','DC1',J(5)),
                (3,'BOLIVAR AMAYA RAUL ARMANDO','Despachador','DC1',J(1)),
                (4,'FARFAN QUIROGA LEIDY DAYHANNA','Alistador','DC1',J(1)),
                (5,'VARGAS ARIAS JUAN JOSE','Alistador','DC1',J(2)),
                (6,'RAMIREZ TENJICA BLANCA CECILIA','CASETA','DC1',J(2)),
                (7,'MOLINA SUAREZ MAICOL STEVEN','CYD','DC1',J(2)),
                (8,'VIRGÜEZ PEREZ CARLOS ALIRIO','Montacarguista','DC1',J(2)),
                (9,'CARDENAS MALAVER EDWIN ANDRES','Montacarguista','DC1',J(3)),
                (10,'FELICIANO RODRIGUEZ DAVID ALEJANDRO','Montacarguista','DC1',J(3)),
                (11,'JIMENEZ CORTES MIGUEL FERNANDO','Montacarguista','DC1',J(3)),
                (12,'BELLO CONTRERAS LADY CAROLINA','Apoyo de Bodega','DC2',J(8)),
                (13,'PAEZ ALVAREZ NANCY CONSUELO','Despachador','DC2',J(8)),
                (14,'MORA GUERRA BRAYAN STIVEN','Alistador','DC2',J(8)),
                (15,'MORENO SANCHEZ JHON FREDY','Alistador','DC2',J(8)),
                (16,'BEJARANO CANTOR IVAN FARID','Alistador','DC2',J(11)),
                (17,'BEDOYA VARGAS JUAN DAVID','CYD','DC2',J(12)),
                (18,'ACOSTA MENDEZ FANCIS GIOVANNI','CYD','DC2',J(12)),
                (19,'DIAZ ESTRADA LEONARDO','CYD','DC2',J(12)),
                (20,'VANEGAS TRASLAVIÑA W.','Montacarguista','DC2',J(12)),
                (21,'MENDIVELSO ABRIL RAFAEL ANTONIO','Montacarguista','DC2',J(13)),
                (22,'POR CONTRATAR','CYD','DC2',J(13)),
                (23,'OROZCO SANDOVAL JULIETH','Trazabilidad','DC3',J(15)),
                (24,'MARTINEZ GONZALEZ RAMON','Despachador','DC3',J(15)),
                (25,'OSPINO GARCES JHON EIDER','CYD','DC3',J(15)),
                (26,'MONTERO MONTAÑO WILLIAM EDUARDO','Montacarguista','DC3',J(15)),
                (27,'MOSQUERA MOSQUERA EULIDER','Montacarguista','DC3',J(18)),
                (28,'PALACIO FORERO JOHN FREDY','Montacarguista','DC3',J(19)),
                (29,'QUIROGA POVEDA JORGE ELIECER','Montacarguista','DC3',J(19)),
                (30,'POR CONTRATAR','Montacarguista','DC3',J(19)),
                (31,'POR CONTRATAR','Montacarguista','DC3',J(20)),
                (32,'POR CONTRATAR','CYD','DC3',J(17)),
            ]
        },
        'DASA — FRÍO': {
            'min_oper': 28, 'total': 35,
            'people': [
                (1,'Sanchez Perez Oscar Fabian','Líder Turno','DC1',J(1)),
                (2,'Jaramillo Sacantiva Diego Alexander','Montacarguista','DC1',J(2)),
                (3,'Tovar Muñoz Gustavo Adolfo','Montacarguista','DC1',J(3)),
                (4,'Tavera Sanchez Eleazar','Auxiliar Logística','DC1',J(1)),
                (5,'Sarmiento Forero Joan Stiven','Auxiliar Logística','DC1',J(2)),
                (6,'Rodriguez Gonzalez Kilian Sneider','Auxiliar Logística','DC1',J(3)),
                (7,'Castaño Jaramillo Oscar','Auxiliar Logística','DC1',J(4)),
                (8,'Malaver Pachon Wilson Raul','Auxiliar Logística','DC1',J(4)),
                (9,'Tapias Ninco Victor Duvian','Auxiliar Logística','DC1',J(5)),
                (10,'FERRER ORELLANO JESUS MANUEL','Auxiliar Logística','DC1',J(5)),
                (11,'Pachon Carrillo Cristhian David','Auxiliar Logística','DC1',J(6)),
                (12,'POR CONTRATAR','Auxiliar Logística','DC1',J(6)),
                (13,'POR CONTRATAR','Auxiliar Logística','DC1',J(6)),
                (14,'Gualteros Jamaica Ignacio','Líder Turno','DC2',J(8)),
                (15,'Fandiño Gracia Camilo Andres','Montacarguista','DC2',J(11)),
                (16,'Vargas Tellez Rodrigo','Montacarguista','DC2',J(10)),
                (17,'ROZO TIJO JULIAN ALEJANDRO','Auxiliar Logística','DC2',J(8)),
                (18,'Molina Garzon German Alonso','Auxiliar Logística','DC2',J(9)),
                (19,'Albornoz Buitrago Angie Karine','Auxiliar Logística','DC2',J(9)),
                (20,'Rodriguez Quintana Jhon Sebastian','Auxiliar Logística','DC2',J(10)),
                (21,'Perez Corro Julio David','Auxiliar Logística','DC2',J(10)),
                (22,'Garzon Calderon Juan David','Auxiliar Logística','DC2',J(11)),
                (23,'Rodriguez Cruz Luis Felipe','Auxiliar Logística','DC2',J(13)),
                (24,'POR CONTRATAR','Auxiliar Logística','DC2',J(12)),
                (25,'POR CONTRATAR','Auxiliar Logística','DC2',J(13)),
                (26,'Pulido Sanchez Edgar Esneider','Líder Turno','DC3',J(20)),
                (27,'Bulla Calderon William Dario','Montacarguista','DC3',J(15)),
                (28,'Montaño Capador Wilmar Alexander','Montacarguista','DC3',J(18)),
                (29,'Rayo Ceballos Elver Estith','Auxiliar Logística','DC3',J(15)),
                (30,'Gaita Espitia Johan Estevan','Auxiliar Logística','DC3',J(16)),
                (31,'Garnica Rincon Juan Camilo','Auxiliar Logística','DC3',J(17)),
                (32,'Alvarez Arcon Yamit','Auxiliar Logística','DC3',J(17)),
                (33,'Bustos Romero Jordi Jhonatan','Auxiliar Logística','DC3',J(18)),
                (34,'POR CONTRATAR','Auxiliar Logística','DC3',J(19)),
                (35,'POR CONTRATAR','Auxiliar Logística','DC3',J(20)),
            ]
        },
        'Facturación': {
            'min_oper': 6, 'total': 7,
            'people': [
                (1,'GARAVITO DUARTE DIANA MILENA','Facturador','DC1',J(1)),
                (2,'GARCIA RINCON ANDRES JULIAN','Facturador','DC1',J(2)),
                (3,'GONZALEZ SALAMANCA JOSE HUMBERTO','Pedidos','DC1',J(3)),
                (4,'JUYO CHOCONTA GLORIA ESPERANZA','Pedidos','DC1',J(4)),
                (5,'PATARROYO GOMEZ OLGA LUCIA','Facturador','DC1',J(5)),
                (6,'RIOS RIOS CARLOS','Facturador','DC1',J(6)),
                (7,'RODRIGUEZ CASTAÑEDA WILMER ANDRES','Facturador','DC1',J(8)),
            ]
        },
        'Inventarios': {
            'min_oper': 6, 'total': 7,
            'people': [
                (1,'RONCANCIO BELLO PAULA LORENA','Lider Inventarios','DC1',J(1)),
                (2,'HORTUA HERRERA EDWIN','Apoyo inventarios','DC1',J(2)),
                (3,'LOPEZ POVEDA YULY ELIZABETH','Apoyo inventarios','DC1',J(3)),
                (4,'TRIVIÑO SANTAMARIA DAYANA','Apoyo inventarios','DC1',J(4)),
                (5,'CAMACHO MOLANO JAIME','aux inventarios','DC1',J(5)),
                (6,'RODRIGUEZ RUIZ RICARDO HUMBERTO','aux inventarios','DC1',J(6)),
                (7,'CASTRO OBANDO MARTHA INES','Aux admin','DC1',J(8)),
            ]
        },
        'Devolutivos': {
            'min_oper': 9, 'total': 11,
            'people': [
                (1,'BONZA SABBAGH JAN ALEXANDER','Especialista Devolutivos','DC1',J(1)),
                (2,'ARDILA JEREZ YERSON ESTIBEN','Apoyo Devolutivos','DC1',J(2)),
                (3,'GOMEZ GUZMAN CRISTIAN RICARDO','Apoyo Devolutivos','DC1',J(3)),
                (4,'CORDOBA ANACONA LUIS HERNANDO','Aux admin Devolutivos','DC1',J(4)),
                (5,'BALLESTEROS RINCON JAIRO ORLANDO','aux Devolutivos','DC1',J(5)),
                (6,'CAMPOS DIAZ LUIS EDUARDO','aux Devolutivos','DC1',J(6)),
                (7,'CASTRO CARABUENA JONATHAN DAVID','aux Devolutivos','DC1',J(8)),
                (8,'MESIAS MUÑOZ DAVID ALEJANDRO','aux Devolutivos','DC2',J(9)),
                (9,'ROBERTO GUTIERREZ FELIX ALFONSO','aux Devolutivos','DC2',J(10)),
                (10,'SUAREZ RODRIGUEZ JONATHAN ESNEIDER','aux Devolutivos','DC2',J(11)),
                (11,'POR CONTRATAR','aux Devolutivos','DC3',J(15)),
            ]
        },
    }

# ─── STATE ───────────────────────────────────────────────────────────────────
if 'overrides' not in st.session_state:
    st.session_state.overrides = {}  # {(equipo, persona_idx): nueva_fecha}

if 'base_data' not in st.session_state:
    st.session_state.base_data = make_people()

def get_first_dc(equipo, idx):
    key = (equipo, idx)
    if key in st.session_state.overrides:
        return st.session_state.overrides[key]
    people = st.session_state.base_data[equipo]['people']
    return people[idx][4]

def validate_premises(equipo, people_with_dates):
    """Valida premisas y retorna lista de alertas"""
    alerts = []
    min_oper = st.session_state.base_data[equipo]['min_oper']
    n = len(people_with_dates)
    for d in DATES:
        if d.weekday() == 6: continue
        on_dc = sum(1 for _,_,_,_,fd in people_with_dates if d in gen_dc(fd))
        working = n - on_dc
        if working < min_oper:
            alerts.append(f"⚠ {d.strftime('%d/%b')}: solo {working} operando (mín {min_oper})")
    return alerts

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.dc1-badge {background:#C00000;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;}
.dc2-badge {background:#BF8F00;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;}
.dc3-badge {background:#375623;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;}
.oper-green {background:#C6EFCE;color:#276221;font-weight:bold;text-align:center;padding:4px;border-radius:4px;}
.oper-yellow {background:#FFEB9C;color:#9C5700;font-weight:bold;text-align:center;padding:4px;border-radius:4px;}
.oper-red {background:#FFC7CE;color:#9C0006;font-weight:bold;text-align:center;padding:4px;border-radius:4px;}
.cal-dc1 {background:#C00000;color:#fff;text-align:center;font-weight:bold;font-size:10px;border-radius:2px;padding:1px 3px;}
.cal-dc2 {background:#BF8F00;color:#000;text-align:center;font-weight:bold;font-size:10px;border-radius:2px;padding:1px 3px;}
.cal-dc3 {background:#375623;color:#fff;text-align:center;font-weight:bold;font-size:10px;border-radius:2px;padding:1px 3px;}
.cal-sun  {background:#E0E0E0;color:#999;text-align:center;font-size:9px;}
.cal-sat  {background:#FFF8E6;text-align:center;font-size:10px;}
.cal-norm {background:#F5F5F5;text-align:center;font-size:10px;}
div[data-testid="stExpander"] {border:1px solid #dee2e6;border-radius:8px;margin-bottom:8px;}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📅 Simulador DC")
    st.markdown("**Jun 1 – Jul 12, 2026**")
    st.markdown("Ciclo: `+8d / +8d / +15d / +8d / +8d`")
    st.divider()

    equipo = st.selectbox("**Selecciona equipo:**",
        list(st.session_state.base_data.keys()), index=0)

    st.divider()
    st.markdown("### ✏️ Cambiar 1er DC")

    people = st.session_state.base_data[equipo]['people']
    nombres = [f"{p[0]}. {p[2][:28]}" for p in people]
    sel_idx = st.selectbox("Persona:", range(len(nombres)),
                           format_func=lambda i: nombres[i])

    p = people[sel_idx]
    current_fd = get_first_dc(equipo, sel_idx)
    nueva_fecha = st.date_input(
        f"Nueva fecha 1er DC:",
        value=current_fd,
        min_value=datetime.date(2026,6,1),
        max_value=datetime.date(2026,7,12),
        key=f"date_{equipo}_{sel_idx}"
    )

    dcs_preview = gen_dc_list(nueva_fecha)
    st.markdown("**DCs calculados:**")
    for i, d in enumerate(dcs_preview):
        badge_cls = f"dc{i//2+1 if i < 2 else 3}-badge"
        st.markdown(
            f'<span class="dc1-badge">DC{i+1}</span> &nbsp; {d.strftime("%a %d/%b")}',
            unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Aplicar", use_container_width=True, type="primary"):
            st.session_state.overrides[(equipo, sel_idx)] = nueva_fecha
            st.success("¡Aplicado!")
            st.rerun()
    with col2:
        if st.button("↺ Reset", use_container_width=True):
            key = (equipo, sel_idx)
            if key in st.session_state.overrides:
                del st.session_state.overrides[key]
            st.rerun()

    st.divider()
    n_changes = len([k for k in st.session_state.overrides if k[0] == equipo])
    if n_changes:
        st.warning(f"**{n_changes} cambio(s)** en este equipo")
        if st.button("↺ Reset TODO el equipo"):
            for k in list(st.session_state.overrides.keys()):
                if k[0] == equipo:
                    del st.session_state.overrides[k]
            st.rerun()

# ─── MAIN ────────────────────────────────────────────────────────────────────
info = st.session_state.base_data[equipo]
people = info['people']
min_oper = info['min_oper']
N = info['total']

# Build current people with dates (applying overrides)
current_people = []
for i, p in enumerate(people):
    fd = get_first_dc(equipo, i)
    current_people.append((*p[:4], fd))

st.markdown(f"## 📋 {equipo} &nbsp; — &nbsp; {N} personas")

# ─── ALERTAS ─────────────────────────────────────────────────────────────────
alerts = validate_premises(equipo, current_people)
if alerts:
    with st.expander(f"⚠️ {len(alerts)} alerta(s) de premisas", expanded=True):
        for a in alerts[:10]:
            st.error(a)
        if len(alerts) > 10:
            st.warning(f"... y {len(alerts)-10} alertas más")
else:
    st.success("✅ Todas las premisas cumplidas — operando mínimo garantizado")

st.divider()

# ─── TABLA PERSONAS ──────────────────────────────────────────────────────────
st.markdown("### 👥 Personal y descansos")

prev_cyc = None
for i, p in enumerate(current_people):
    num, nom, rol, cyc, fd = p
    is_modified = (equipo, i) in st.session_state.overrides
    is_pc = 'POR CONTRATAR' in nom

    if cyc != prev_cyc:
        bg, fg = DC_COLORS[cyc]
        st.markdown(
            f'<div style="background:{bg};color:{fg};padding:6px 16px;'
            f'border-radius:6px;font-weight:bold;margin:12px 0 4px;">▸ CICLO {cyc}</div>',
            unsafe_allow_html=True)
        prev_cyc = cyc

    dcs = gen_dc_list(fd)
    dc_labels = " · ".join([f"**{d.strftime('%d/%b')}**" for d in dcs])

    rol_color = ROL_COLORS.get(rol, '#888888')
    mod_icon = "✏️ " if is_modified else ""

    with st.container():
        c1, c2, c3, c4 = st.columns([0.3, 2.5, 1.2, 3])
        with c1:
            st.markdown(f"**{num}**")
        with c2:
            style = "color:#888;font-style:italic" if is_pc else ""
            st.markdown(f'<span style="{style}">{mod_icon}{nom}</span>',
                        unsafe_allow_html=True)
        with c3:
            st.markdown(
                f'<span style="background:{rol_color};color:#fff;padding:2px 6px;'
                f'border-radius:3px;font-size:11px;">{rol}</span>',
                unsafe_allow_html=True)
        with c4:
            st.markdown(dc_labels)

st.divider()

# ─── CALENDARIO VISUAL ───────────────────────────────────────────────────────
st.markdown("### 📆 Calendario de descansos (Jun 1 – Jul 12, 2026)")

# Build calendar dataframe
all_dc_sets = [gen_dc(p[4]) for p in current_people]

# Header row
header_cols = [d.strftime('%d/%m') for d in DATES]
rows = []

# OPERANDO row
oper_row = []
for d in DATES:
    if d.weekday() == 6:
        oper_row.append("D")
    else:
        on_dc = sum(1 for s in all_dc_sets if d in s)
        oper_row.append(N - on_dc)

# Person rows for calendar
cal_data = {}
for i, (p, dcs) in enumerate(zip(current_people, all_dc_sets)):
    num, nom, rol, cyc, fd = p
    row = []
    for d in DATES:
        if d.weekday() == 6:
            row.append("D")
        elif d in dcs:
            row.append(cyc)
        else:
            row.append("")
    cal_data[f"{num}. {nom[:20]}"] = row

# Show calendar as dataframe with styling
# Filter to show only months with data
# Show Jun and Jul separately

tab_jun, tab_jul, tab_oper = st.tabs(["📅 Junio", "📅 Julio", "📊 OPERANDO"])

jun_dates = [d for d in DATES if d.month == 6]
jul_dates = [d for d in DATES if d.month == 7]
jun_idx = [i for i, d in enumerate(DATES) if d.month == 6]
jul_idx = [i for i, d in enumerate(DATES) if d.month == 7]

def render_calendar_tab(date_indices, dates_list, all_dc_sets, current_people, N):
    # Create df
    cols = [f"{d.strftime('%d')}\n{DI[d.weekday()]}" for d in dates_list]
    data = {}
    for i, p in enumerate(current_people):
        num, nom, rol, cyc, fd = p
        dcs = all_dc_sets[i]
        row_vals = []
        for j in date_indices:
            d = DATES[j]
            if d.weekday() == 6:
                row_vals.append("D")
            elif d in dcs:
                row_vals.append(cyc)
            else:
                row_vals.append("")
        data[f"{num}.{nom[:18]}"] = row_vals

    df = pd.DataFrame(data, index=cols).T

    def color_cell(val):
        if val == "DC1": return 'background-color:#C00000;color:white;font-weight:bold;text-align:center'
        if val == "DC2": return 'background-color:#BF8F00;color:black;font-weight:bold;text-align:center'
        if val == "DC3": return 'background-color:#375623;color:white;font-weight:bold;text-align:center'
        if val == "D":   return 'background-color:#E0E0E0;color:#999;text-align:center'
        return 'background-color:#F5F5F5;text-align:center'

    styled = df.style.map(color_cell)
    st.dataframe(styled, use_container_width=True, height=min(40+len(current_people)*35, 800))

with tab_jun:
    render_calendar_tab(jun_idx, jun_dates, all_dc_sets, current_people, N)

with tab_jul:
    render_calendar_tab(jul_idx, jul_dates, all_dc_sets, current_people, N)

with tab_oper:
    st.markdown("**Personas OPERANDO por día (verde ≥ mínimo · amarillo = límite · rojo = bajo mínimo)**")
    oper_dict = {}
    for j, d in enumerate(DATES):
        if d.weekday() == 6:
            oper_dict[d.strftime('%d/%m')] = ["D"]
        else:
            on_dc = sum(1 for s in all_dc_sets if d in s)
            oper_dict[d.strftime('%d/%m')] = [N - on_dc]

    oper_df = pd.DataFrame(oper_dict, index=['Operando'])

    def color_oper(val):
        if val == "D": return 'background-color:#E0E0E0;color:#999'
        if isinstance(val, int):
            if val >= min_oper: return 'background-color:#C6EFCE;color:#276221;font-weight:bold;text-align:center'
            if val >= min_oper-3: return 'background-color:#FFEB9C;color:#9C5700;font-weight:bold;text-align:center'
            return 'background-color:#FFC7CE;color:#9C0006;font-weight:bold;text-align:center'
        return ''

    st.dataframe(oper_df.style.map(color_oper), use_container_width=True, height=80)
    st.caption(f"Mínimo requerido: **{min_oper}** personas operando")

# ─── RESUMEN ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📊 Resumen")
c1, c2, c3, c4 = st.columns(4)
working_days = [d for d in DATES if d.weekday() != 6]
oper_vals = [N - sum(1 for s in all_dc_sets if d in s) for d in working_days]
c1.metric("👥 Total personas", N)
c2.metric("📅 Días del período", 36)
c3.metric("✅ Mínimo operando", f"{min(oper_vals)} / {min_oper}")
c4.metric("⚠️ Alertas activas", len(alerts))

st.caption("Simulador DC · Jun–Jul 2026 · Ciclo 40-40-48h · Todas las premisas activas")
