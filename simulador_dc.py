"""
SIMULADOR DC v4 — Fondo claro, auto-solver corregido, recalculo automatico
"""
import streamlit as st
import pandas as pd
import datetime
import io
try:
    import openpyxl
    HAS_OPENPYXL = True
except:
    HAS_OPENPYXL = False

st.set_page_config(page_title="Simulador DC",page_icon="📅",
                   layout="wide",initial_sidebar_state="expanded")

END_DATE = datetime.date(2026,7,12)
DATES    = [datetime.date(2026,6,1)+datetime.timedelta(days=i) for i in range(42)]
WORK     = [d for d in DATES if d.weekday()!=6]
DI       = ['L','M','M','J','V','S','D']
DC_BG    = {'DC1':'#C00000','DC2':'#BF8F00','DC3':'#375623'}
DC_FG    = {'DC1':'#FFFFFF','DC2':'#000000','DC3':'#FFFFFF'}
ROL_C    = {
    'Lider de turno':'#1F3864','Líder Turno':'#1F3864','Lider Inventarios':'#1F3864',
    'Apoyo de Bodega':'#2E75B6','Apoyo Devolutivos':'#2E75B6','Apoyo inventarios':'#2E75B6',
    'Despachador':'#C55A11','Trazabilidad':'#BF8F00','Alistador':'#375623',
    'CASETA':'#31869B','CYD':'#548235','Montacarguista':'#7F6000',
    'Auxiliar Logística':'#4E6B30','Especialista Devolutivos':'#1F3864',
    'Aux admin Devolutivos':'#BF8F00','aux Devolutivos':'#4E6B30',
    'Facturador':'#2E75B6','Pedidos':'#C55A11',
    'aux inventarios':'#4E6B30','Aux admin':'#BF8F00',
}

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


def parse_upload(file_bytes, eq):
    """
    Parse uploaded Excel/CSV and return list of people tuples.
    Expected columns: N°, Nombre, Rol, Ciclo, 1er_DC
    """
    import io
    results = []
    errors  = []
    try:
        if HAS_OPENPYXL:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
        else:
            import csv
            rows = list(csv.reader(io.StringIO(file_bytes.decode('utf-8'))))
    except Exception as e:
        return None, [f"Error leyendo archivo: {e}"]

    # Find header row (look for 'Nombre' in first 3 rows)
    header_row = None
    for i, row in enumerate(rows[:3]):
        if row and any(str(c).lower().strip() in ['nombre','name'] for c in row if c):
            header_row = i; break
    if header_row is None:
        return None, ["No se encontró encabezado. Columnas requeridas: N°, Nombre, Rol, Ciclo, 1er_DC"]

    headers = [str(c).strip().lower() if c else '' for c in rows[header_row]]
    col_map = {}
    for i, h in enumerate(headers):
        if 'nombre' in h or 'name' in h:   col_map['nombre'] = i
        if 'rol' in h:                      col_map['rol']    = i
        if 'ciclo' in h:                    col_map['ciclo']  = i
        if '1er' in h or 'dc' in h or 'fecha' in h or 'date' in h: col_map['fecha'] = i
        if h == 'n°' or h == 'n' or h == '#': col_map['num'] = i

    missing = [k for k in ['nombre','rol','ciclo','fecha'] if k not in col_map]
    if missing:
        return None, [f"Faltan columnas: {', '.join(missing)}. Encontradas: {', '.join(h for h in headers if h)}"]

    for r_idx, row in enumerate(rows[header_row+1:], 1):
        if not row or not any(c for c in row if c):
            continue
        try:
            num    = row[col_map['num']] if 'num' in col_map else r_idx
            nombre = str(row[col_map['nombre']]).strip() if row[col_map['nombre']] else ''
            rol    = str(row[col_map['rol']]).strip()    if row[col_map['rol']]    else ''
            ciclo  = str(row[col_map['ciclo']]).strip()  if row[col_map['ciclo']]  else ''
            fecha_raw = row[col_map['fecha']]

            if not nombre: continue

            # Parse date
            if isinstance(fecha_raw, datetime.datetime):
                fd = fecha_raw.date()
            elif isinstance(fecha_raw, datetime.date):
                fd = fecha_raw
            elif fecha_raw:
                s = str(fecha_raw).strip()
                for fmt in ['%d/%m/%Y','%Y-%m-%d','%d-%m-%Y','%d/%m/%y','%m/%d/%Y']:
                    try: fd = datetime.datetime.strptime(s, fmt).date(); break
                    except: pass
                else:
                    errors.append(f"Fila {r_idx}: fecha '{fecha_raw}' no reconocida"); continue
            else:
                errors.append(f"Fila {r_idx}: {nombre} no tiene fecha"); continue

            # Validate date range
            if fd < datetime.date(2026,6,1) or fd > datetime.date(2026,7,12):
                errors.append(f"Fila {r_idx}: {nombre} — fecha {fd} fuera del rango Jun1-Jul12/2026")
                continue

            if ciclo not in ('DC1','DC2','DC3'):
                ciclo = 'DC1'  # default

            results.append((int(num) if str(num).isdigit() else r_idx,
                            nombre, rol, ciclo, fd))
        except Exception as e:
            errors.append(f"Fila {r_idx}: error — {e}")

    return results if results else None, errors

J=lambda d:datetime.date(2026,6,d)

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

# ── Solver ────────────────────────────────────────────────────────────────────
def count_violations(dc_sets, N, min_oper):
    return sum(1 for d in WORK if N - sum(1 for s in dc_sets if d in s) < min_oper)

def best_move_for(idx, p, dc_sets, N, min_oper):
    """Mejor fecha para mover a la persona idx"""
    base = count_violations(dc_sets, N, min_oper)
    best = None
    for delta in list(range(-10, 0)) + list(range(1, 11)):
        new_fd = p[4] + datetime.timedelta(days=delta)
        if new_fd < datetime.date(2026,6,1) or new_fd > datetime.date(2026,7,5): continue
        if new_fd.weekday() == 6: continue
        ns = dc_sets.copy(); ns[idx] = gen_dc(new_fd)
        nv = count_violations(ns, N, min_oper)
        if best is None or nv < best[0] or (nv == best[0] and abs(delta) < best[2]):
            best = (nv, new_fd, abs(delta))
    return best

def apply_moves(dc_sets, moves):
    """Apply a list of (idx, new_fd) moves to dc_sets and return new list"""
    tmp = list(dc_sets)
    for idx, new_fd in moves:
        tmp[idx] = gen_dc(new_fd)
    return tmp

def auto_solve_full(eq, cur, dc_sets):
    """
    Smart solver that tries 1, 2 and 3-person combinations.
    Focuses on people who are in DC on the most violated days.
    """
    N = len(cur)
    min_oper = EQUIPOS[eq]['min_oper']
    base_viol = count_violations(dc_sets, N, min_oper)
    if base_viol == 0:
        return []

    # Identify which people are causing violations (in DC on violated days)
    viol_days = [d for d in WORK if N - sum(1 for s in dc_sets if d in s) < min_oper]
    guilty = {}  # idx -> count of violated days they're in DC
    for d in viol_days:
        for i, s in enumerate(dc_sets):
            if d in s and 'POR CONTRATAR' not in cur[i][1]:
                guilty[i] = guilty.get(i, 0) + 1
    # Sort candidates by how many violated days they contribute to
    candidates = sorted(guilty.keys(), key=lambda i: -guilty[i])
    if not candidates:
        candidates = [i for i,p in enumerate(cur) if 'POR CONTRATAR' not in p[1]]
    candidates = candidates[:12]  # top 12 most guilty

    def best_delta(idx, base_sets):
        p = cur[idx]
        best = None
        for delta in list(range(-10,0)) + list(range(1,11)):
            nf = p[4] + datetime.timedelta(days=delta)
            if nf < datetime.date(2026,6,1) or nf > datetime.date(2026,7,5): continue
            if nf.weekday() == 6: continue
            nv = count_violations(apply_moves(base_sets, [(idx,nf)]), N, min_oper)
            if best is None or nv < best[0] or (nv==best[0] and abs(delta)<best[2]):
                best = (nv, nf, abs(delta))
        return best

    results = []

    # ── 1 persona ──────────────────────────────────────────────────────────────
    for idx in candidates:
        r = best_delta(idx, dc_sets)
        if r and r[0] < base_viol:
            nom = ' '.join(cur[idx][1].split()[:2])
            results.append({
                'tipo':'1 persona','idx':idx,'idx2':None,'idx3':None,
                'nombre':nom,'nombre2':None,'nombre3':None,
                'fd_orig':cur[idx][4],'fd_new':r[1],
                'fd_orig2':None,'fd_new2':None,'fd_orig3':None,'fd_new3':None,
                'mejora':base_viol-r[0],'new_viol':r[0],
            })
    results.sort(key=lambda x:(-x['mejora'],abs((x['fd_new']-x['fd_orig']).days)))
    seen1={s['idx'] for s in results}
    top1=[s for i,s in enumerate(results) if s['idx'] not in list(seen1)[:i]]
    # deduplicate by idx
    seen1=set(); top1u=[]
    for s in results:
        if s['idx'] not in seen1: seen1.add(s['idx']); top1u.append(s)
    top1=top1u[:5]

    perfect1 = [s for s in top1 if s['new_viol']==0]
    if perfect1: return perfect1

    # ── 2 personas ─────────────────────────────────────────────────────────────
    pairs=[]
    cands2 = candidates[:8]
    for ia in range(len(cands2)):
        for ib in range(ia+1, len(cands2)):
            idxA=cands2[ia]; idxB=cands2[ib]
            rA = best_delta(idxA, dc_sets)
            if not rA: continue
            ns_a = apply_moves(dc_sets, [(idxA, rA[1])])
            rB = best_delta(idxB, ns_a)
            if not rB: continue
            tmp = apply_moves(dc_sets, [(idxA,rA[1]),(idxB,rB[1])])
            nv2 = count_violations(tmp, N, min_oper)
            if nv2 < base_viol:
                nomA=' '.join(cur[idxA][1].split()[:2])
                nomB=' '.join(cur[idxB][1].split()[:2])
                pairs.append({
                    'tipo':'2 personas','idx':idxA,'idx2':idxB,'idx3':None,
                    'nombre':nomA,'nombre2':nomB,'nombre3':None,
                    'fd_orig':cur[idxA][4],'fd_new':rA[1],
                    'fd_orig2':cur[idxB][4],'fd_new2':rB[1],
                    'fd_orig3':None,'fd_new3':None,
                    'mejora':base_viol-nv2,'new_viol':nv2,
                })
    pairs.sort(key=lambda x:(-x['mejora'],0))
    perfect2=[s for s in pairs if s['new_viol']==0]
    if perfect2: return (top1+perfect2)[:6]

    # ── 3 personas (si el deficit sigue alto) ──────────────────────────────────
    trios=[]
    cands3 = candidates[:6]
    for ia in range(len(cands3)):
        for ib in range(ia+1, len(cands3)):
            for ic in range(ib+1, len(cands3)):
                idxA=cands3[ia]; idxB=cands3[ib]; idxC=cands3[ic]
                rA=best_delta(idxA, dc_sets)
                if not rA: continue
                ns_a=apply_moves(dc_sets,[(idxA,rA[1])])
                rB=best_delta(idxB, ns_a)
                if not rB: continue
                ns_ab=apply_moves(ns_a,[(idxB,rB[1])])
                rC=best_delta(idxC, ns_ab)
                if not rC: continue
                tmp=apply_moves(dc_sets,[(idxA,rA[1]),(idxB,rB[1]),(idxC,rC[1])])
                nv3=count_violations(tmp,N,min_oper)
                if nv3 < base_viol:
                    nomA=' '.join(cur[idxA][1].split()[:2])
                    nomB=' '.join(cur[idxB][1].split()[:2])
                    nomC=' '.join(cur[idxC][1].split()[:2])
                    trios.append({
                        'tipo':'3 personas','idx':idxA,'idx2':idxB,'idx3':idxC,
                        'nombre':nomA,'nombre2':nomB,'nombre3':nomC,
                        'fd_orig':cur[idxA][4],'fd_new':rA[1],
                        'fd_orig2':cur[idxB][4],'fd_new2':rB[1],
                        'fd_orig3':cur[idxC][4],'fd_new3':rC[1],
                        'mejora':base_viol-nv3,'new_viol':nv3,
                    })
    trios.sort(key=lambda x:(-x['mejora'],0))

    combined = top1 + pairs[:3] + trios[:3]
    combined.sort(key=lambda x:(-x['mejora'],len(x['tipo'])))
    return combined[:6] if combined else []

# ── State ─────────────────────────────────────────────────────────────────────
if 'ov' not in st.session_state:
    st.session_state.ov = {}

def get_fd(eq, i):
    return st.session_state.ov.get((eq, i), EQUIPOS[eq]['people'][i][4])

# ── CSS: fondo BLANCO forzado ─────────────────────────────────────────────────
st.markdown("""
<style>
/* ═══ FONDO BLANCO TOTAL ═══ */
html, body, .stApp, .main, .block-container,
[data-testid="stAppViewContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
section.main > div { background-color: #FFFFFF !important; }

[data-testid="stSidebar"],
[data-testid="stSidebarContent"] { background-color: #F4F6F9 !important; }

/* ═══ TEXTO OSCURO EN TODO ═══ */
*, *::before, *::after { color: #1a1a1a !important; }
p, span, div, label, li, td, th, h1,h2,h3,h4,h5 { color: #1a1a1a !important; }

/* ═══ TABS ═══ */
.stTabs [data-baseweb="tab-list"] {
    background: #e8edf3 !important; border-radius: 8px; padding: 3px;
    border: 1px solid #dee2e6 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #333 !important;
    font-weight: 600 !important; font-size: 14px !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important; color: #1F3864 !important;
    border-radius: 6px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.1) !important;
}
.stTabs [data-baseweb="tab-panel"],
.stTabs [data-baseweb="tab-panel"] * { background: #FFFFFF !important; color: #1a1a1a !important; }

/* ═══ EXPANDERS ═══ */
.stExpander, [data-testid="stExpander"],
[data-testid="stExpander"] > div,
details, summary { background: #FFFFFF !important; color: #1a1a1a !important; }
details summary { color: #1a1a1a !important; font-weight: 600; }

/* ═══ FILE UPLOADER ═══ */
[data-testid="stFileUploader"],
[data-testid="stFileUploader"] * ,
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploaderDropzone"] * { background: #FFFFFF !important; color: #1a1a1a !important; }
[data-testid="stFileUploaderDropzone"] { border: 2px dashed #aaa !important; border-radius: 8px !important; }

/* ═══ SELECTBOX ═══ */
[data-testid="stSelectbox"] *, [data-testid="stDateInput"] * { color: #1a1a1a !important; }

/* ═══ MÉTRICAS ═══ */
[data-testid="metric-container"] {
    background: #f0f4f8 !important; border: 1px solid #d0d7de;
    border-radius: 8px !important; padding: 10px !important;
}
[data-testid="metric-container"] * { color: #1a1a1a !important; }

/* ═══ ALERTAS STREAMLIT ═══ */
[data-testid="stAlert"] { background: #fff5f5 !important; }
[data-testid="stAlert"] * { color: #9C0006 !important; }

/* ═══ CUSTOM CLASSES ═══ */
.dc-p { padding:2px 8px; border-radius:3px; font-size:11px; font-weight:bold; display:inline-block; margin:1px; }
.prem-ok  { border-left:4px solid #375623; background:#f0fff4; padding:7px 12px; border-radius:4px; margin:3px 0; font-size:13px; }
.prem-bad { border-left:4px solid #C00000; background:#fff5f5; padding:7px 12px; border-radius:4px; margin:3px 0; font-size:13px; }
.sug-box  { border:1px solid #375623; background:#f0fff4; padding:10px 14px; border-radius:6px; margin:4px 0; }
.sug-box2 { border:1px solid #2E75B6; background:#EFF6FF; padding:10px 14px; border-radius:6px; margin:4px 0; }
.panel-prem { background:#F8FBFF; border:1px solid #C7DCEF; border-radius:8px; padding:14px 18px; margin:4px 0; }
.rol-row  { display:flex; align-items:center; gap:8px; padding:3px 0; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📅 Simulador DC")
    st.caption("Jun 1 – Jul 12, 2026  ·  +8d/+8d/+15d/+8d/+8d")
    st.divider()

    eq = st.selectbox("**Equipo:**", list(EQUIPOS.keys()))

    # ── Carga de personal ────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📂 Cargar personal desde Excel/CSV", expanded=False):
        st.caption("Sube un archivo con columnas: N°, Nombre, Rol, Ciclo, 1er_DC")
        uploaded = st.file_uploader(
            "Selecciona archivo:", type=["xlsx","csv"],
            key=f"upload_{eq}",
            label_visibility="collapsed"
        )
        if uploaded:
            file_bytes = uploaded.read()
            parsed, errs = parse_upload(file_bytes, eq)
            if parsed:
                if st.button(f"✅ Cargar {len(parsed)} personas en {eq}",
                             use_container_width=True, type="primary"):
                    st.session_state[f'custom_{eq}'] = parsed
                    st.session_state.ov = {k:v for k,v in st.session_state.ov.items()
                                           if k[0]!=eq}
                    st.success(f"✓ {len(parsed)} personas cargadas")
                    st.rerun()
                st.caption(f"Vista previa: {len(parsed)} personas encontradas")
                prev_df = pd.DataFrame(
                    [(p[0],p[1][:28],p[2],p[3],p[4].strftime('%d/%m/%Y'))
                     for p in parsed[:8]],
                    columns=['N°','Nombre','Rol','Ciclo','1er DC'])
                st.dataframe(prev_df, hide_index=True, use_container_width=True)
            if errs:
                for e in errs[:5]:
                    st.warning(e)
        if f'custom_{eq}' in st.session_state:
            n_custom = len(st.session_state[f'custom_{eq}'])
            st.success(f"✓ Datos propios cargados: {n_custom} personas")
            if st.button("🗑 Volver a datos originales", use_container_width=True):
                del st.session_state[f'custom_{eq}']
                st.session_state.ov = {k:v for k,v in st.session_state.ov.items()
                                       if k[0]!=eq}
                st.rerun()

    info = EQUIPOS[eq]
    people = info['people']
    min_oper = info['min_oper']

    st.markdown("---")
    st.markdown("### ✏️ Cambiar 1er DC")
    st.caption("El simulador recalcula automáticamente al cambiar la fecha")

    nombres = [f"{p[0]}. {p[2][:26]}" for p in people]
    sel = st.selectbox("Persona:", range(len(nombres)),
                       format_func=lambda i: nombres[i])

    def on_date():
        val = st.session_state[f'dp_{eq}_{sel}']
        st.session_state.ov[(eq, sel)] = val

    st.date_input(
        "📆 1er DC:", value=get_fd(eq, sel),
        min_value=datetime.date(2026,6,1),
        max_value=datetime.date(2026,7,12),
        key=f'dp_{eq}_{sel}',
        on_change=on_date,
        help="Cambia la fecha → todo recalcula solo"
    )

    # Preview DCs
    dcs_p = gen_dc_list(get_fd(eq, sel))
    st.markdown("**Descansos calculados:**")
    for i, d in enumerate(dcs_p):
        idx_cyc = min(i, 2)
        cyc_key = ['DC1','DC2','DC3'][idx_cyc]
        bg = DC_BG[cyc_key]; fg = DC_FG[cyc_key]
        st.markdown(
            f'<span class="dc-p" style="background:{bg};color:{fg}">DC{i+1}</span>'
            f' &nbsp; <span style="color:#333">{d.strftime("%a %d/%b")}</span>',
            unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📋 Premisas")
    PREM_TXT = {
        'L1 — SECO':  [f'Min operando: {min_oper}','Min montacarguistas: 9','Líderes SECO/FRÍO no coinciden','Domingo → lunes','Ciclo 40-40-48h'],
        'L2 — SECO':  [f'Min operando: {min_oper}','Min montacarguistas: 9','Líderes SECO/FRÍO no coinciden','Domingo → lunes','Ciclo 40-40-48h'],
        'L3 — SECO':  [f'Min operando: {min_oper}','Min montacarguistas: 9','Líderes SECO/FRÍO no coinciden','Domingo → lunes','Ciclo 40-40-48h'],
        'DASA — FRÍO':[f'Min operando: {min_oper}','Min montacarguistas: 1','Min auxiliares: 7','MCs no coinciden con Líderes','Domingo → lunes','Ciclo 40-40-48h'],
        'Facturación':[f'Min operando: {min_oper}','Domingo → lunes','Ciclo 40-40-48h'],
        'Inventarios': [f'Min operando: {min_oper}','Domingo → lunes','Ciclo 40-40-48h'],
        'Devolutivos': [f'Min operando: {min_oper}','Domingo → lunes','Ciclo 40-40-48h'],
    }
    for txt in PREM_TXT.get(eq, []):
        st.markdown(f'<div class="prem-ok">✅ {txt}</div>', unsafe_allow_html=True)

    st.divider()
    n_mod = sum(1 for k in st.session_state.ov if k[0]==eq)
    if n_mod:
        st.info(f"**{n_mod}** cambio(s) activo(s)")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("↺ Persona", use_container_width=True):
                st.session_state.ov.pop((eq, sel), None)
                st.rerun()
        with c2:
            if st.button("↺ Equipo", use_container_width=True):
                [st.session_state.ov.pop(k) for k in list(st.session_state.ov) if k[0]==eq]
                st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────────
info = EQUIPOS[eq]
# Use custom uploaded data if available
if f'custom_{eq}' in st.session_state:
    people = st.session_state[f'custom_{eq}']
    N = len(people)
    min_oper = info['min_oper']
else:
    people = info['people']
    N = info['n']; min_oper = info['min_oper']
cur = [(p[0],p[1],p[2],p[3],get_fd(eq,i)) for i,p in enumerate(people)]
dc_sets = [gen_dc(p[4]) for p in cur]

# Calcular operando
oper_vals = [N - sum(1 for s in dc_sets if d in s) for d in WORK]
min_op = min(oper_vals)

# Detectar violaciones
viol_days = [(d,w) for d,w in zip(WORK,oper_vals) if w < min_oper]

st.markdown(f"## 📋 {eq} &nbsp;·&nbsp; {N} personas")

# Métricas
c1,c2,c3,c4 = st.columns(4)
c1.metric("👥 Total personas", N)
c2.metric("📉 Mín. operando real", min_op,
          delta=f"{min_op-min_oper:+d} vs req.",
          delta_color="normal" if min_op>=min_oper else "inverse")
c3.metric("📋 Mínimo requerido", min_oper)
c4.metric("⚠️ Días con alerta", len(viol_days),
          delta="OK ✓" if not viol_days else f"{len(viol_days)} días",
          delta_color="normal" if not viol_days else "inverse")

st.markdown("---")

# ── ALERTAS + SOLVER ──────────────────────────────────────────────────────────
if viol_days:
    st.markdown(f"### ⚠️ Alertas — {len(viol_days)} día(s) bajo el mínimo")

    # Mostrar días en alerta
    alert_html = '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px">'
    for d, w in viol_days:
        alert_html += (f'<div style="background:#FFC7CE;color:#9C0006;border-radius:5px;'
                       f'padding:4px 8px;font-size:12px;font-weight:bold">'
                       f'{d.strftime("%d/%b")}: {w} op</div>')
    alert_html += '</div>'
    st.markdown(alert_html, unsafe_allow_html=True)

    # SOLVER
    col_a, col_b = st.columns([2,1])
    with col_a:
        st.markdown(
            f'<div class="prem-bad">🔴 Hay <b>{len(viol_days)} día(s)</b> con menos de '
            f'<b>{min_oper}</b> personas operando. El solver buscará '
            f'automáticamente la mejor fecha para cada persona afectada.</div>',
            unsafe_allow_html=True)
    with col_b:
        run_solver = st.button("🔧 Buscar solución automática",
                               use_container_width=True, type="primary")

    if run_solver:
        with st.spinner("Analizando todas las combinaciones..."):
            solutions = auto_solve_full(eq, cur, dc_sets)
        if solutions:
            st.session_state[f'sol_{eq}'] = solutions
        else:
            st.warning("No se encontró una solución simple moviendo una persona. "
                       "Prueba mover manualmente varias personas.")

    # Mostrar soluciones encontradas
    sol_key = f'sol_{eq}'
    if sol_key in st.session_state and st.session_state[sol_key]:
        st.markdown("#### 💡 Soluciones encontradas")
        for s in st.session_state[sol_key]:
            delta_d = (s['fd_new'] - s['fd_orig']).days
            signo = "+" if delta_d > 0 else ""
            res_txt = "✅ resuelve todo" if s['new_viol']==0 else f"reduce a {s['new_viol']} alerta(s)"
            tipo_badge = f"<b style='color:#375623'>[{s['tipo']}]</b>"

            if s['tipo'] == '2 personas' and s['idx2'] is not None:
                delta_d2 = (s['fd_new2'] - s['fd_orig2']).days
                signo2 = "+" if delta_d2 > 0 else ""
                box_class = "sug-box2"
                txt = (f'{tipo_badge} &nbsp;'
                       f'👤 <b>{s["nombre"]}</b>: {s["fd_orig"].strftime("%d/%b")} → <b>{s["fd_new"].strftime("%d/%b")}</b> ({signo}{delta_d}d)'
                       f' &nbsp;+&nbsp; '
                       f'👤 <b>{s["nombre2"]}</b>: {s["fd_orig2"].strftime("%d/%b")} → <b>{s["fd_new2"].strftime("%d/%b")}</b> ({signo2}{delta_d2}d)'
                       f' &nbsp;|&nbsp; {res_txt}')
            else:
                box_class = "sug-box"
                txt = (f'{tipo_badge} &nbsp;'
                       f'👤 <b>{s["nombre"]}</b>: {s["fd_orig"].strftime("%d/%b")} → <b>{s["fd_new"].strftime("%d/%b")}</b> ({signo}{delta_d}d)'
                       f' &nbsp;|&nbsp; {res_txt}')

            st.markdown(f'<div class="{box_class}">{txt}</div>', unsafe_allow_html=True)

            btn_key=f"apl_{s['idx']}_{s.get('idx2','x')}_{s.get('idx3','x')}_{s['fd_new']}"
            if s['tipo']=='3 personas':
                if st.button(f"✅ Aplicar 3 movimientos",key=btn_key):
                    st.session_state.ov[(eq,s['idx'])]=s['fd_new']
                    st.session_state.ov[(eq,s['idx2'])]=s['fd_new2']
                    st.session_state.ov[(eq,s['idx3'])]=s['fd_new3']
                    st.session_state.pop(sol_key,None); st.rerun()
            elif s['tipo']=='2 personas':
                if st.button(f"✅ Aplicar 2 movimientos",key=btn_key):
                    st.session_state.ov[(eq,s['idx'])]=s['fd_new']
                    st.session_state.ov[(eq,s['idx2'])]=s['fd_new2']
                    st.session_state.pop(sol_key,None); st.rerun()
            else:
                if st.button(f"✅ Aplicar",key=btn_key):
                    st.session_state.ov[(eq,s['idx'])]=s['fd_new']
                    st.session_state.pop(sol_key,None); st.rerun()
else:
    st.success("✅ **Todas las premisas cumplidas** — operando mínimo garantizado en todo el período Jun–Jul 2026")

# ── OPERANDO VISUAL ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Personas operando por día")
html = '<div style="display:flex;flex-wrap:wrap;gap:3px">'
for d, w in zip(WORK, oper_vals):
    if w >= min_oper:   bg,fg='#C6EFCE','#276221'
    elif w >= min_oper-3: bg,fg='#FFEB9C','#9C5700'
    else:               bg,fg='#FFC7CE','#9C0006'
    sat = '🟡' if d.weekday()==5 else ''
    html += (f'<div style="background:{bg};color:{fg};border-radius:5px;'
             f'padding:5px 6px;text-align:center;min-width:46px">'
             f'<div style="opacity:.7;font-size:9px">{d.strftime("%d/%m")}{sat}</div>'
             f'<b style="font-size:15px">{w}</b></div>')
html += '</div>'
st.markdown(html, unsafe_allow_html=True)
st.caption(f"Verde ≥{min_oper} · Amarillo ={min_oper-3}–{min_oper-1} · Rojo <{min_oper-3}")

# ── TABLA PERSONAS ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 👥 Personal y descansos")
prev_cyc = None
for i, p in enumerate(cur):
    num,nom,rol,cyc,fd = p
    is_mod = (eq,i) in st.session_state.ov
    is_sel = (i == sel)
    if cyc != prev_cyc:
        bg=DC_BG.get(cyc,'#888'); fg=DC_FG.get(cyc,'white')
        st.markdown(
            f'<div style="background:{bg};color:{fg};padding:5px 14px;border-radius:6px;'
            f'font-weight:bold;margin:10px 0 2px;font-size:13px">▸ CICLO {cyc}</div>',
            unsafe_allow_html=True)
        prev_cyc = cyc

    dcs = gen_dc_list(fd)
    dc_str = '&nbsp;'.join([
        f'<span class="dc-p" style="background:{DC_BG.get(cyc,"#888")};'
        f'color:{DC_FG.get(cyc,"white")}">{d.strftime("%d/%b")}</span>'
        for d in dcs])
    rc = ROL_C.get(rol,'#888')
    border = '2px solid #375623' if is_sel else ('1px solid #FFD700' if is_mod else '1px solid #eee')
    bg_r = '#F0FFF4' if is_sel else ('#FFFDE7' if is_mod else 'white')
    is_pc = 'POR CONTRATAR' in nom
    ns = 'color:#999;font-style:italic' if is_pc else 'color:#1a1a1a'
    mi = '✏️ ' if is_mod else ''
    st.markdown(
        f'<div style="border:{border};background:{bg_r};border-radius:7px;'
        f'padding:5px 12px;margin:2px 0;display:flex;align-items:center;gap:10px">'
        f'<span style="font-size:11px;color:#888;min-width:18px">{num}</span>'
        f'<span style="font-size:12px;min-width:210px;{ns}">{mi}{nom}</span>'
        f'<span style="background:{rc};color:white;padding:1px 7px;border-radius:3px;'
        f'font-size:10px;font-weight:bold">{rol}</span>'
        f'<span style="margin-left:auto">{dc_str}</span>'
        f'</div>', unsafe_allow_html=True)

# ── CALENDARIO + PREMISAS ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📆 Calendario de descansos")
tab1, tab2, tab_prem = st.tabs(["📅 Junio 2026", "📅 Julio 2026", "📋 Premisas y Roles"])

def render_cal(month):
    md = [d for d in DATES if d.month==month]
    mi = [i for i,d in enumerate(DATES) if d.month==month]
    rows = {}
    for i,p in enumerate(cur):
        num,nom,rol,cyc,fd = p
        dcs_i = dc_sets[i]
        rows[f"{num}.{nom[:15]}"] = [
            cyc if DATES[j] in dcs_i else ('D' if DATES[j].weekday()==6 else '')
            for j in mi]
    df = pd.DataFrame(rows, index=[f"{d.day}\n{DI[d.weekday()]}" for d in md]).T
    def sty(v):
        if v=='DC1': return 'background:#C00000;color:white;font-weight:bold;text-align:center'
        if v=='DC2': return 'background:#BF8F00;color:black;font-weight:bold;text-align:center'
        if v=='DC3': return 'background:#375623;color:white;font-weight:bold;text-align:center'
        if v=='D':   return 'background:#E0E0E0;color:#aaa;text-align:center'
        return 'background:#F5F5F5;color:#333;text-align:center'
    st.dataframe(df.style.map(sty), use_container_width=True,
                 height=min(45+len(cur)*34, 900))

with tab1: render_cal(6)
with tab2: render_cal(7)
with tab_prem:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("#### ⚙️ Reglas del ciclo")
        ciclo_rows = [
            ("DC1 → DC2", "+8 días"),("DC2 → DC3", "+8 días"),
            ("DC3 → DC4", "+15 días (ciclo 48h)"),
            ("DC4 → DC5", "+8 días"),("DC5 → DC6", "+8 días"),
            ("Domingo", "→ se mueve al lunes siguiente"),
            ("Período", "Jun 1 – Jul 12, 2026 (42 días)"),
            ("Ciclos","DC1 = 40h · DC2 = 40h · DC3 = 48h"),
        ]
        df_ciclo = pd.DataFrame(ciclo_rows, columns=["Paso","Regla"])
        st.dataframe(df_ciclo, hide_index=True, use_container_width=True)

        st.markdown("#### 👥 Mínimos operacionales")
        min_rows = [
            ("L1 SECO","32","27","9 montacarguistas"),
            ("L2 SECO","32","27","9 montacarguistas"),
            ("L3 SECO","32","27","9 montacarguistas"),
            ("DASA FRÍO","35","28","1 MC + 7 auxiliares"),
            ("Facturación","7","6","—"),
            ("Inventarios","7","6","—"),
            ("Devolutivos","11","9","—"),
        ]
        df_min = pd.DataFrame(min_rows, columns=["Equipo","Total","Mín operando","Obs"])
        st.dataframe(df_min, hide_index=True, use_container_width=True)

    with col_p2:
        st.markdown("#### 🏷️ Roles y colores")
        roles_data = [
            ("Lider de turno","#1F3864","Líder del equipo SECO"),
            ("Líder Turno","#1F3864","Líder del equipo DASA"),
            ("Apoyo de Bodega","#2E75B6","Soporte operativo"),
            ("Despachador","#C55A11","Despacho de mercancía"),
            ("Alistador","#375623","Alistamiento de pedidos"),
            ("CYD","#548235","Cargue y descargue"),
            ("Montacarguista","#7F6000","Operación de montacargas"),
            ("Trazabilidad","#BF8F00","Control y trazabilidad"),
            ("CASETA","#31869B","Control de acceso"),
            ("Auxiliar Logística","#4E6B30","Auxiliar DASA Frío"),
            ("Facturador","#2E75B6","Área de facturación"),
            ("Pedidos","#C55A11","Gestión de pedidos"),
            ("aux Devolutivos","#4E6B30","Área devolutivos"),
        ]
        roles_html = ""
        for rol, color, desc in roles_data:
            roles_html += (f'<div class="rol-row">' 
                f'<span style="background:{color};color:white;padding:2px 8px;'
                f'border-radius:3px;font-size:11px;font-weight:bold;min-width:150px'
                f';display:inline-block">{rol}</span>'
                f'<span style="font-size:12px;color:#555">{desc}</span></div>')
        st.markdown(roles_html, unsafe_allow_html=True)

        st.markdown("#### ⚠️ Reglas especiales")
        especiales = [
            "Líderes SECO y FRÍO no pueden descansar el mismo día",
            "MCs de DASA no descansan cuando descansa el Líder DASA",
            "Mínimo 1 MC operando en DASA en todo momento",
            "Mínimo 7 auxiliares operando en DASA en todo momento",
        ]
        for e in especiales:
            st.markdown(f'<div class="prem-ok">📌 {e}</div>', unsafe_allow_html=True)

st.caption("Simulador DC · Jun–Jul 2026 · Ciclo 40-40-48h · Auto-solver integrado · Todas las premisas activas")
