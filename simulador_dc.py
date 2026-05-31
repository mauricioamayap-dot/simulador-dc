"""
SIMULADOR DC v3 — Recálculo automático + Auto-solver + Premisas completas
"""
import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Simulador DC · Bodega",page_icon="📅",
                   layout="wide",initial_sidebar_state="expanded")

END_DATE=datetime.date(2026,7,12)
DATES=[datetime.date(2026,6,1)+datetime.timedelta(days=i) for i in range(42)]
WORK_DAYS=[d for d in DATES if d.weekday()!=6]
DI=['L','M','M','J','V','S','D']

DC_BG={'DC1':'#C00000','DC2':'#BF8F00','DC3':'#375623'}
DC_FG={'DC1':'white','DC2':'black','DC3':'white'}
ROL_C={'Lider de turno':'#1F3864','Líder Turno':'#1F3864','Lider Inventarios':'#1F3864',
       'Apoyo de Bodega':'#2E75B6','Apoyo Devolutivos':'#2E75B6','Apoyo inventarios':'#2E75B6',
       'Despachador':'#C55A11','Trazabilidad':'#BF8F00','Alistador':'#375623',
       'CASETA':'#31869B','CYD':'#548235','Montacarguista':'#7F6000',
       'Auxiliar Logística':'#4E6B30','Especialista Devolutivos':'#1F3864',
       'Aux admin Devolutivos':'#BF8F00','aux Devolutivos':'#4E6B30',
       'Facturador':'#2E75B6','Pedidos':'#C55A11','aux inventarios':'#4E6B30','Aux admin':'#BF8F00'}

# ── Algoritmo ciclo DC ────────────────────────────────────────────────────────
def gen_dc(fd):
    if not fd: return set()
    res=[fd]; gaps=[8,8,15,8,8]; c=fd
    for g in gaps:
        n=c+datetime.timedelta(days=g)
        if n.weekday()==6: n+=datetime.timedelta(days=1)
        if n>END_DATE: break
        res.append(n); c=n
    return set(res)

def gen_dc_list(fd): return sorted(gen_dc(fd))

J=lambda d: datetime.date(2026,6,d)

# ── PREMISAS ──────────────────────────────────────────────────────────────────
PREMISAS = {
    'L1 — SECO':  {'min_oper':27,'min_mc':9,'lideres':[0]},
    'L2 — SECO':  {'min_oper':27,'min_mc':9,'lideres':[0]},
    'L3 — SECO':  {'min_oper':27,'min_mc':9,'lideres':[0]},
    'DASA — FRÍO':{'min_oper':28,'min_mc':1,'min_aux':7,'lideres':[0,13,25]},
    'Facturación':{'min_oper':6},
    'Inventarios':{'min_oper':6},
    'Devolutivos':{'min_oper':9},
}

def validate_all(eq, cur, dc_sets):
    """Valida TODAS las premisas y retorna lista de alertas"""
    alerts=[]
    prem=PREMISAS[eq]
    min_oper=prem['min_oper']
    N=len(cur)

    for d in WORK_DAYS:
        on_dc=[i for i,s in enumerate(dc_sets) if d in s]
        working=N-len(on_dc)

        # P1: Mínimo operando
        if working < min_oper:
            alerts.append({
                'tipo':'min_oper','dia':d,'valor':working,'req':min_oper,
                'on_dc':on_dc,
                'msg':f"⚠️ **{d.strftime('%d/%b')}**: {working} operando (mín {min_oper})"
            })

        # P2: Montacarguistas mínimo
        if 'min_mc' in prem:
            mc_idx=[i for i,p in enumerate(cur) if p[2]=='Montacarguista']
            mc_on_dc=sum(1 for i in mc_idx if i in on_dc)
            mc_working=len(mc_idx)-mc_on_dc
            if mc_working < prem['min_mc']:
                alerts.append({
                    'tipo':'min_mc','dia':d,'valor':mc_working,'req':prem['min_mc'],
                    'on_dc':[i for i in mc_idx if i in on_dc],
                    'msg':f"🚛 **{d.strftime('%d/%b')}**: solo {mc_working} montacarguistas (mín {prem['min_mc']})"
                })

        # P3: Auxiliares DASA mínimo
        if 'min_aux' in prem:
            aux_idx=[i for i,p in enumerate(cur) if p[2]=='Auxiliar Logística']
            aux_dc=sum(1 for i in aux_idx if i in on_dc)
            aux_w=len(aux_idx)-aux_dc
            if aux_w < prem['min_aux']:
                alerts.append({
                    'tipo':'min_aux','dia':d,'valor':aux_w,'req':prem['min_aux'],
                    'on_dc':[i for i in aux_idx if i in on_dc],
                    'msg':f"👷 **{d.strftime('%d/%b')}**: solo {aux_w} auxiliares DASA (mín {prem['min_aux']})"
                })

    # P4: Líderes no comparten descanso
    if 'lideres' in prem and len(prem['lideres'])>1:
        lids=prem['lideres']
        for ia in range(len(lids)):
            for ib in range(ia+1,len(lids)):
                shared=dc_sets[lids[ia]] & dc_sets[lids[ib]] & set(WORK_DAYS)
                for d in sorted(shared):
                    nom_a=cur[lids[ia]][1].split()[0]
                    nom_b=cur[lids[ib]][1].split()[0]
                    alerts.append({
                        'tipo':'lideres','dia':d,'valor':0,'req':0,'on_dc':[],
                        'msg':f"👔 **{d.strftime('%d/%b')}**: Líderes {nom_a} y {nom_b} coinciden en DC"
                    })

    return alerts

# ── AUTO-SOLVER ───────────────────────────────────────────────────────────────
def auto_solve(eq, cur, dc_sets, alert):
    """Para una alerta, sugiere qué persona mover y a qué fecha"""
    suggestions=[]
    N=len(cur)
    prem=PREMISAS[eq]
    min_oper=prem.get('min_oper',1)

    candidates=alert['on_dc']  # personas en DC ese día
    if not candidates: return []

    for idx in candidates[:5]:  # probar los primeros 5
        fd_orig=cur[idx][4]
        nom=cur[idx][1].split()[0]

        for delta in [1,-1,2,-2,3,-3,4,-4,5,-5]:
            new_fd=fd_orig+datetime.timedelta(days=delta)
            if new_fd < datetime.date(2026,6,1): continue
            if new_fd > datetime.date(2026,7,5): continue
            if new_fd.weekday()==6: continue

            # Simular con esta nueva fecha
            new_sets=dc_sets.copy()
            new_sets[idx]=gen_dc(new_fd)

            # Verificar que resuelve el problema y no crea otros
            new_alerts=validate_all(eq,
                [(p[0],p[1],p[2],p[3],new_fd if i==idx else cur[i][4])
                 for i,p in enumerate(cur)],
                new_sets)

            # Filtrar alertas graves (mínimo operando)
            critical=[a for a in new_alerts if a['tipo']=='min_oper' and a['valor']<min_oper]
            if len(critical) < sum(1 for a in validate_all(eq,cur,dc_sets) if a['tipo']=='min_oper'):
                suggestions.append({
                    'idx':idx,'nom':nom,'fd_orig':fd_orig,
                    'fd_new':new_fd,'mejora':True,
                    'label':f"Mover **{nom}** de {fd_orig.strftime('%d/%b')} → {new_fd.strftime('%d/%b')}"
                })
                break

    return suggestions[:3]

# ── DATOS ─────────────────────────────────────────────────────────────────────
EQUIPOS={'L1 — SECO':{'min_oper':27,'n':32,'people':[
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
]},'L2 — SECO':{'min_oper':27,'n':32,'people':[
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
]},'L3 — SECO':{'min_oper':27,'n':32,'people':[
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
]},'DASA — FRÍO':{'min_oper':28,'n':35,'people':[
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
]},'Facturación':{'min_oper':6,'n':7,'people':[
    (1,'GARAVITO DUARTE DIANA MILENA','Facturador','DC1',J(1)),
    (2,'GARCIA RINCON ANDRES JULIAN','Facturador','DC1',J(2)),
    (3,'GONZALEZ SALAMANCA JOSE HUMBERTO','Pedidos','DC1',J(3)),
    (4,'JUYO CHOCONTA GLORIA ESPERANZA','Pedidos','DC1',J(4)),
    (5,'PATARROYO GOMEZ OLGA LUCIA','Facturador','DC1',J(5)),
    (6,'RIOS RIOS CARLOS','Facturador','DC1',J(6)),
    (7,'RODRIGUEZ CASTAÑEDA WILMER ANDRES','Facturador','DC1',J(8)),
]},'Inventarios':{'min_oper':6,'n':7,'people':[
    (1,'RONCANCIO BELLO PAULA LORENA','Lider Inventarios','DC1',J(1)),
    (2,'HORTUA HERRERA EDWIN','Apoyo inventarios','DC1',J(2)),
    (3,'LOPEZ POVEDA YULY ELIZABETH','Apoyo inventarios','DC1',J(3)),
    (4,'TRIVIÑO SANTAMARIA DAYANA','Apoyo inventarios','DC1',J(4)),
    (5,'CAMACHO MOLANO JAIME','aux inventarios','DC1',J(5)),
    (6,'RODRIGUEZ RUIZ RICARDO HUMBERTO','aux inventarios','DC1',J(6)),
    (7,'CASTRO OBANDO MARTHA INES','Aux admin','DC1',J(8)),
]},'Devolutivos':{'min_oper':9,'n':11,'people':[
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
]}}

# ── State ─────────────────────────────────────────────────────────────────────
if 'ov' not in st.session_state: st.session_state.ov={}
def get_fd(eq,i): return st.session_state.ov.get((eq,i),EQUIPOS[eq]['people'][i][4])

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
.block-container{padding-top:.5rem}
.dc-p{padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold;display:inline-block;margin:1px}
.prem-box{border-left:4px solid #375623;background:#f0fff4;padding:8px 14px;border-radius:4px;margin:4px 0;font-size:13px}
.prem-box-warn{border-left:4px solid #C00000;background:#fff5f5;padding:8px 14px;border-radius:4px;margin:4px 0;font-size:13px}
</style>""",unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📅 Simulador DC")
    st.caption("Jun 1 – Jul 12, 2026 · +8/+8/+15/+8/+8")
    st.divider()

    eq=st.selectbox("**Equipo:**",list(EQUIPOS.keys()))
    info=EQUIPOS[eq]; people=info['people']
    prem=PREMISAS[eq]

    st.markdown("---")
    st.markdown("### ✏️ Cambiar descanso")
    st.caption("Recalcula automáticamente al cambiar la fecha")

    nombres=[f"{p[0]}. {p[2][:26]}" for p in people]
    sel=st.selectbox("Persona:",range(len(nombres)),format_func=lambda i:nombres[i])

    def on_date():
        st.session_state.ov[(eq,sel)]=st.session_state[f'dp_{eq}_{sel}']

    st.date_input("📆 1er DC:",value=get_fd(eq,sel),
        min_value=datetime.date(2026,6,1),max_value=datetime.date(2026,7,12),
        key=f'dp_{eq}_{sel}',on_change=on_date,
        help="Cambia aquí → todo se actualiza solo")

    dcs_p=gen_dc_list(get_fd(eq,sel))
    for i,d in enumerate(dcs_p):
        cyc=f"DC{i+1}"; bg=DC_BG.get('DC1' if i==0 else 'DC2' if i<2 else 'DC3','#888')
        fg=DC_FG.get('DC1' if i==0 else 'DC2' if i<2 else 'DC3','white')
        st.markdown(f'<span class="dc-p" style="background:{bg};color:{fg}">DC{i+1}</span> '
                    f'{d.strftime("%a %d/%b")}',unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📋 Premisas activas")
    st.markdown(f'<div class="prem-box">✅ Min operando: <b>{prem["min_oper"]}</b></div>',unsafe_allow_html=True)
    if 'min_mc' in prem:
        st.markdown(f'<div class="prem-box">✅ Min montacarguistas: <b>{prem["min_mc"]}</b></div>',unsafe_allow_html=True)
    if 'min_aux' in prem:
        st.markdown(f'<div class="prem-box">✅ Min auxiliares DASA: <b>{prem["min_aux"]}</b></div>',unsafe_allow_html=True)
    if 'lideres' in prem and len(prem['lideres'])>1:
        st.markdown(f'<div class="prem-box">✅ Líderes no comparten DC</div>',unsafe_allow_html=True)
    st.markdown('<div class="prem-box">✅ Domingo → lunes automático</div>',unsafe_allow_html=True)
    st.markdown('<div class="prem-box">✅ Ciclo 40-40-48h (+8/+8/+15)</div>',unsafe_allow_html=True)

    st.divider()
    n_mod=sum(1 for k in st.session_state.ov if k[0]==eq)
    if n_mod:
        st.warning(f"**{n_mod}** cambio(s) en {eq}")
        if st.button("↺ Reset persona",use_container_width=True):
            st.session_state.ov.pop((eq,sel),None); st.rerun()
        if st.button("↺ Reset equipo",use_container_width=True):
            [st.session_state.ov.pop(k) for k in list(st.session_state.ov) if k[0]==eq]; st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
info=EQUIPOS[eq]; people=info['people']; N=info['n']; min_oper=info['min_oper']
cur=[(p[0],p[1],p[2],p[3],get_fd(eq,i)) for i,p in enumerate(people)]
dc_sets=[gen_dc(p[4]) for p in cur]
alerts=validate_all(eq,cur,dc_sets)

st.markdown(f"## 📋 {eq} — {N} personas")

# ── MÉTRICAS ──────────────────────────────────────────────────────────────────
oper_vals=[N-sum(1 for s in dc_sets if d in s) for d in WORK_DAYS]
min_op=min(oper_vals)
c1,c2,c3,c4=st.columns(4)
c1.metric("👥 Total",N)
c2.metric("✅ Mín operando real",min_op,
          delta=f"{min_op-min_oper:+d}",
          delta_color="normal" if min_op>=min_oper else "inverse")
c3.metric("📋 Requerido",min_oper)
c4.metric("⚠️ Alertas",len(alerts),
          delta="OK" if not alerts else "Revisar",
          delta_color="normal" if not alerts else "inverse")

# ── ALERTAS + AUTO-SOLVER ─────────────────────────────────────────────────────
if alerts:
    st.markdown("---")
    st.markdown(f"### ⚠️ {len(alerts)} alerta(s) detectada(s)")
    for a in alerts[:6]:
        col1,col2=st.columns([3,1])
        with col1:
            st.markdown(
                f'<div class="prem-box-warn">{a["msg"]}</div>',
                unsafe_allow_html=True)
        with col2:
            if a['on_dc'] and st.button(f"🔧 Sugerir fix",key=f"fix_{a['dia']}_{a['tipo']}"):
                sugs=auto_solve(eq,cur,dc_sets,a)
                if sugs:
                    st.session_state[f'sugs_{a["dia"]}_{a["tipo"]}']=sugs
                else:
                    st.warning("No se encontró corrección automática — ajusta manualmente")

        # Mostrar sugerencias si existen
        sug_key=f'sugs_{a["dia"]}_{a["tipo"]}'
        if sug_key in st.session_state:
            for s in st.session_state[sug_key]:
                btn_label=f"✅ Aplicar: {s['label']}"
                if st.button(btn_label,key=f"apl_{s['idx']}_{a['dia']}"):
                    st.session_state.ov[(eq,s['idx'])]=s['fd_new']
                    del st.session_state[sug_key]
                    st.rerun()
    if len(alerts)>6:
        st.caption(f"...y {len(alerts)-6} alertas más")
else:
    st.success("✅ Todas las premisas cumplidas — operando mínimo garantizado en todo el período")

# ── OPERANDO VISUAL ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Operando por día")
html='<div style="display:flex;flex-wrap:wrap;gap:3px">'
for d,w in zip(WORK_DAYS,oper_vals):
    bg,fg=('#C6EFCE','#276221') if w>=min_oper else ('#FFEB9C','#9C5700') if w>=min_oper-3 else ('#FFC7CE','#9C0006')
    sat='🟡' if d.weekday()==5 else ''
    html+=(f'<div style="background:{bg};color:{fg};border-radius:5px;padding:5px 6px;'
           f'text-align:center;min-width:46px;font-size:11px">'
           f'<div style="opacity:.7;font-size:9px">{d.strftime("%d/%m")}{sat}</div>'
           f'<b style="font-size:15px">{w}</b></div>')
html+='</div>'
st.markdown(html,unsafe_allow_html=True)

# ── TABLA PERSONAS ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 👥 Personal y descansos")
prev_cyc=None
for i,p in enumerate(cur):
    num,nom,rol,cyc,fd=p
    is_mod=(eq,i) in st.session_state.ov; is_sel=(i==sel)
    if cyc!=prev_cyc:
        bg=DC_BG.get(cyc,'#888'); fg=DC_FG.get(cyc,'white')
        st.markdown(f'<div style="background:{bg};color:{fg};padding:5px 14px;border-radius:6px;'
                    f'font-weight:bold;margin:10px 0 2px;font-size:13px">▸ CICLO {cyc}</div>',unsafe_allow_html=True)
        prev_cyc=cyc
    dcs=gen_dc_list(fd)
    dc_str='&nbsp;'.join([f'<span class="dc-p" style="background:{DC_BG.get(cyc,"#888")};color:{DC_FG.get(cyc,"white")}">{d.strftime("%d/%b")}</span>' for d in dcs])
    rc=ROL_C.get(rol,'#888')
    border='2px solid #375623' if is_sel else ('1px solid #FFD700' if is_mod else '1px solid #eee')
    bg_r='#F0FFF4' if is_sel else ('#FFFDE7' if is_mod else 'white')
    is_pc='POR CONTRATAR' in nom
    ns='color:#999;font-style:italic' if is_pc else ''
    mi='✏️ ' if is_mod else ''
    st.markdown(
        f'<div style="border:{border};background:{bg_r};border-radius:7px;padding:5px 12px;'
        f'margin:2px 0;display:flex;align-items:center;gap:10px">'
        f'<span style="font-size:11px;color:#888;min-width:18px">{num}</span>'
        f'<span style="font-size:12px;min-width:210px;{ns}">{mi}{nom}</span>'
        f'<span style="background:{rc};color:white;padding:1px 7px;border-radius:3px;font-size:10px;font-weight:bold">{rol}</span>'
        f'<span style="margin-left:auto">{dc_str}</span>'
        f'</div>',unsafe_allow_html=True)

# ── CALENDARIO ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📆 Calendario")
tab1,tab2=st.tabs(["📅 Junio","📅 Julio"])

def render_cal(month):
    md=[d for d in DATES if d.month==month]
    mi=[i for i,d in enumerate(DATES) if d.month==month]
    rows={}
    for i,p in enumerate(cur):
        num,nom,rol,cyc,fd=p
        dcs=dc_sets[i]
        rows[f"{num}.{nom[:15]}"]=[cyc if DATES[j] in dcs else ('D' if DATES[j].weekday()==6 else '') for j in mi]
    df=pd.DataFrame(rows,index=[f"{d.day}\n{DI[d.weekday()]}" for d in md]).T
    def sty(v):
        if v=='DC1': return 'background:#C00000;color:white;font-weight:bold;text-align:center'
        if v=='DC2': return 'background:#BF8F00;color:black;font-weight:bold;text-align:center'
        if v=='DC3': return 'background:#375623;color:white;font-weight:bold;text-align:center'
        if v=='D':   return 'background:#E0E0E0;color:#aaa;text-align:center'
        return 'background:#F5F5F5;text-align:center'
    st.dataframe(df.style.map(sty),use_container_width=True,height=min(45+len(cur)*34,850))

with tab1: render_cal(6)
with tab2: render_cal(7)
st.caption("Simulador DC · Jun–Jul 2026 · Todas las premisas activas · Auto-solver integrado")
