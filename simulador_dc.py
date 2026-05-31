"""
SIMULADOR DE DESCANSOS COMPENSATORIOS
Recalculo automático al cambiar cualquier fecha
"""
import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="Simulador DC · Bodega",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

END_DATE = datetime.date(2026, 7, 12)
DATES    = [datetime.date(2026,6,1) + datetime.timedelta(days=i) for i in range(42)]
DI       = ['L','M','M','J','V','S','D']

DC_BG  = {'DC1':'#C00000','DC2':'#BF8F00','DC3':'#375623'}
DC_FG  = {'DC1':'white',  'DC2':'black',  'DC3':'white'}
ROL_C  = {
    'Lider de turno':'#1F3864','Líder Turno':'#1F3864','Lider Inventarios':'#1F3864',
    'Apoyo de Bodega':'#2E75B6','Apoyo Devolutivos':'#2E75B6','Apoyo inventarios':'#2E75B6',
    'Despachador':'#C55A11','Trazabilidad':'#BF8F00','Alistador':'#375623',
    'CASETA':'#31869B','CYD':'#548235','Montacarguista':'#7F6000',
    'Auxiliar Logística':'#4E6B30','Especialista Devolutivos':'#1F3864',
    'Aux admin Devolutivos':'#BF8F00','aux Devolutivos':'#4E6B30',
    'Facturador':'#2E75B6','Pedidos':'#C55A11',
    'aux inventarios':'#4E6B30','Aux admin':'#BF8F00',
}

# ── Ciclo DC ─────────────────────────────────────────────────────────────────
def gen_dc(fd):
    if not fd: return set()
    res=[fd]; gaps=[8,8,15,8,8]; c=fd
    for g in gaps:
        n=c+datetime.timedelta(days=g)
        if n.weekday()==6: n+=datetime.timedelta(days=1)
        if n>END_DATE: break
        res.append(n); c=n
    return set(res)

def gen_dc_list(fd):
    return sorted(gen_dc(fd))

# ── Datos ─────────────────────────────────────────────────────────────────────
J=lambda d: datetime.date(2026,6,d)

EQUIPOS = {
    'L1 — SECO':{'min':27,'n':32,'people':[
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
    ]},
    'L2 — SECO':{'min':27,'n':32,'people':[
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
    ]},
    'L3 — SECO':{'min':27,'n':32,'people':[
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
        (20,'VANEGAS TRASLAVIÑA W.A.','Montacarguista','DC2',J(12)),
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
    ]},
    'DASA — FRÍO':{'min':28,'n':35,'people':[
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
    ]},
    'Facturación':{'min':6,'n':7,'people':[
        (1,'GARAVITO DUARTE DIANA MILENA','Facturador','DC1',J(1)),
        (2,'GARCIA RINCON ANDRES JULIAN','Facturador','DC1',J(2)),
        (3,'GONZALEZ SALAMANCA JOSE HUMBERTO','Pedidos','DC1',J(3)),
        (4,'JUYO CHOCONTA GLORIA ESPERANZA','Pedidos','DC1',J(4)),
        (5,'PATARROYO GOMEZ OLGA LUCIA','Facturador','DC1',J(5)),
        (6,'RIOS RIOS CARLOS','Facturador','DC1',J(6)),
        (7,'RODRIGUEZ CASTAÑEDA WILMER ANDRES','Facturador','DC1',J(8)),
    ]},
    'Inventarios':{'min':6,'n':7,'people':[
        (1,'RONCANCIO BELLO PAULA LORENA','Lider Inventarios','DC1',J(1)),
        (2,'HORTUA HERRERA EDWIN','Apoyo inventarios','DC1',J(2)),
        (3,'LOPEZ POVEDA YULY ELIZABETH','Apoyo inventarios','DC1',J(3)),
        (4,'TRIVIÑO SANTAMARIA DAYANA','Apoyo inventarios','DC1',J(4)),
        (5,'CAMACHO MOLANO JAIME','aux inventarios','DC1',J(5)),
        (6,'RODRIGUEZ RUIZ RICARDO HUMBERTO','aux inventarios','DC1',J(6)),
        (7,'CASTRO OBANDO MARTHA INES','Aux admin','DC1',J(8)),
    ]},
    'Devolutivos':{'min':9,'n':11,'people':[
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
    ]},
}

# ── Session state ─────────────────────────────────────────────────────────────
if 'overrides' not in st.session_state:
    st.session_state.overrides = {}

def get_fd(eq, idx):
    return st.session_state.overrides.get((eq,idx), EQUIPOS[eq]['people'][idx][4])

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
.block-container{padding-top:1rem}
.rol-badge{padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;color:white}
.dc-pill{padding:2px 7px;border-radius:3px;font-size:11px;font-weight:bold;display:inline-block;margin:1px}
div[data-testid="metric-container"]{background:#f8f9fa;border-radius:8px;padding:8px}
</style>""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📅 Simulador DC")
    st.caption("Jun 1 – Jul 12, 2026 · Ciclo +8/+8/+15/+8/+8")
    st.divider()

    eq = st.selectbox("**Equipo:**", list(EQUIPOS.keys()))
    info = EQUIPOS[eq]
    people = info['people']

    st.markdown("---")
    st.markdown("### ✏️ Cambiar descanso")
    st.caption("El calendario recalcula automáticamente al seleccionar la fecha")

    nombres = [f"{p[0]}. {p[2][:26]}" for p in people]
    sel = st.selectbox("Persona:", range(len(nombres)),
                       format_func=lambda i: nombres[i])

    fd_actual = get_fd(eq, sel)

    # ── AUTO-RECALCULO: on_change actualiza overrides sin botón ──────────────
    def on_date_change():
        nueva = st.session_state[f'inp_{eq}_{sel}']
        st.session_state.overrides[(eq, sel)] = nueva

    nueva_fd = st.date_input(
        "📆 Nuevo 1er DC:",
        value=fd_actual,
        min_value=datetime.date(2026,6,1),
        max_value=datetime.date(2026,7,12),
        key=f'inp_{eq}_{sel}',
        on_change=on_date_change,
        help="Cambia la fecha y el calendario se actualiza automáticamente"
    )

    # Preview DCs
    dcs_prev = gen_dc_list(nueva_fd)
    st.markdown("**Descansos calculados:**")
    for i,d in enumerate(dcs_prev):
        cyc = f"DC{min(i+1,3)}"
        col = DC_BG.get(cyc,'#888')
        fg  = DC_FG.get(cyc,'white')
        st.markdown(
            f'<span class="dc-pill" style="background:{col};color:{fg}">DC{i+1}</span>'
            f' &nbsp; {d.strftime("%a %d/%b")}',
            unsafe_allow_html=True)

    st.divider()

    # Reset buttons
    n_mod = sum(1 for k in st.session_state.overrides if k[0]==eq)
    if n_mod:
        st.warning(f"**{n_mod} cambio(s)** aplicados en {eq}")
        if st.button("↺ Restaurar persona", use_container_width=True):
            st.session_state.overrides.pop((eq,sel), None)
            st.rerun()
        if st.button("↺ Restaurar TODO el equipo", use_container_width=True):
            for k in list(st.session_state.overrides):
                if k[0]==eq: del st.session_state.overrides[k]
            st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
info = EQUIPOS[eq]
people = info['people']
min_oper = info['min']
N = info['n']

# Calcular DC sets actuales (con overrides)
cur = [(p[0],p[1],p[2],p[3], get_fd(eq,i)) for i,p in enumerate(people)]
dc_sets = [gen_dc(p[4]) for p in cur]

# ── MÉTRICAS ──────────────────────────────────────────────────────────────────
work_days = [d for d in DATES if d.weekday()!=6]
oper_vals = [N - sum(1 for s in dc_sets if d in s) for d in work_days]
min_op = min(oper_vals)
alerts_list = []
for d,w in zip(work_days,oper_vals):
    if w < min_oper:
        alerts_list.append(f"⚠️ {d.strftime('%d/%b')}: {w} operando (mín {min_oper})")

c1,c2,c3,c4 = st.columns(4)
c1.metric("👥 Total", N)
c2.metric("✅ Mín. operando", f"{min_op}", delta=f"{min_op-min_oper:+d} vs req.",
          delta_color="normal" if min_op>=min_oper else "inverse")
c3.metric("📝 Requerido", min_oper)
c4.metric("⚠️ Alertas", len(alerts_list),
          delta="OK" if not alerts_list else "Revisar",
          delta_color="normal" if not alerts_list else "inverse")

# Alertas
if alerts_list:
    with st.expander(f"⚠️ {len(alerts_list)} alerta(s) — clic para ver", expanded=True):
        for a in alerts_list[:8]:
            st.error(a)
        if len(alerts_list)>8:
            st.caption(f"...y {len(alerts_list)-8} más")
else:
    st.success("✅ Todas las premisas cumplidas — operando mínimo garantizado en todo el período")

st.divider()

# ── CALENDARIO OPERANDO ───────────────────────────────────────────────────────
st.markdown("### 📊 Operando por día")

oper_html = '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:16px">'
for d, w in zip(work_days, oper_vals):
    if w >= min_oper: bg,fg='#C6EFCE','#276221'
    elif w >= min_oper-3: bg,fg='#FFEB9C','#9C5700'
    else: bg,fg='#FFC7CE','#9C0006'
    day_label = d.strftime('%d/%m')
    sat = '🟡' if d.weekday()==5 else ''
    oper_html += (f'<div style="background:{bg};color:{fg};border-radius:6px;'
                  f'padding:6px 8px;text-align:center;min-width:52px;font-size:12px">'
                  f'<div style="font-size:10px;opacity:.7">{day_label}{sat}</div>'
                  f'<div style="font-weight:bold;font-size:16px">{w}</div></div>')
oper_html += '</div>'
st.markdown(oper_html, unsafe_allow_html=True)

# ── TABLA PERSONAS ────────────────────────────────────────────────────────────
st.markdown("### 👥 Personal")

prev_cyc = None
for i, p in enumerate(cur):
    num,nom,rol,cyc,fd = p
    is_mod = (eq,i) in st.session_state.overrides
    is_sel = (i == sel)

    if cyc != prev_cyc:
        bg = DC_BG.get(cyc,'#888'); fg = DC_FG.get(cyc,'white')
        st.markdown(
            f'<div style="background:{bg};color:{fg};padding:5px 14px;'
            f'border-radius:6px;font-weight:bold;margin:10px 0 2px;font-size:13px">'
            f'▸ CICLO {cyc}</div>', unsafe_allow_html=True)
        prev_cyc = cyc

    dcs = gen_dc_list(fd)
    dc_str = '&nbsp;·&nbsp;'.join(
        [f'<span class="dc-pill" style="background:{DC_BG.get(cyc,"#888")};'
         f'color:{DC_FG.get(cyc,"white")}">{d.strftime("%d/%b")}</span>'
         for d in dcs])

    rol_col = ROL_C.get(rol,'#888')
    border = '2px solid #375623' if is_sel else ('1px solid #FFD700' if is_mod else '1px solid #eee')
    bg_row = '#F0FFF4' if is_sel else ('#FFFDE7' if is_mod else 'white')
    mod_ico = '✏️ ' if is_mod else ''
    is_pc = 'POR CONTRATAR' in nom
    nom_style = 'color:#999;font-style:italic' if is_pc else ''

    st.markdown(
        f'<div style="border:{border};background:{bg_row};border-radius:8px;'
        f'padding:6px 14px;margin:2px 0;display:flex;align-items:center;gap:12px">'
        f'<span style="font-size:11px;color:#888;min-width:20px">{num}</span>'
        f'<span style="font-size:12px;min-width:220px;{nom_style}">{mod_ico}{nom}</span>'
        f'<span class="rol-badge" style="background:{rol_col};font-size:10px">{rol}</span>'
        f'<span style="margin-left:auto;font-size:11px">{dc_str}</span>'
        f'</div>', unsafe_allow_html=True)

# ── CALENDARIO VISUAL ─────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📆 Calendario de descansos")

tab_jun, tab_jul = st.tabs(["📅 Junio 2026", "📅 Julio 2026"])

def render_cal(month):
    month_dates = [d for d in DATES if d.month==month]
    month_idx   = [i for i,d in enumerate(DATES) if d.month==month]

    rows = {}
    for i,p in enumerate(cur):
        num,nom,rol,cyc,fd = p
        dcs = dc_sets[i]
        row = []
        for j in month_idx:
            d = DATES[j]
            if d.weekday()==6:    row.append('Dom')
            elif d in dcs:        row.append(cyc)
            else:                 row.append('')
        short = f"{num}.{nom[:16]}"
        rows[short] = row

    cols = [f"{d.day}\n{DI[d.weekday()]}" for d in month_dates]
    df = pd.DataFrame(rows, index=cols).T

    def sty(v):
        if v=='DC1': return 'background:#C00000;color:white;font-weight:bold;text-align:center'
        if v=='DC2': return 'background:#BF8F00;color:black;font-weight:bold;text-align:center'
        if v=='DC3': return 'background:#375623;color:white;font-weight:bold;text-align:center'
        if v=='Dom': return 'background:#E0E0E0;color:#aaa;text-align:center'
        return 'background:#F5F5F5;text-align:center'

    st.dataframe(df.style.map(sty), use_container_width=True,
                 height=min(45+len(cur)*34, 900))

with tab_jun: render_cal(6)
with tab_jul: render_cal(7)

st.caption("Simulador DC · Jun–Jul 2026 · Ciclo 40-40-48h · Recálculo automático al cambiar fecha")
