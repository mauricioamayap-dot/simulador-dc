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

def auto_solve_full(eq, cur, dc_sets):
    """
    1) Prueba mover 1 persona → todas las combinaciones persona × delta
    2) Si nadie resuelve solo, prueba 2 personas en combinación
    Devuelve lista de sugerencias ordenadas por mejora
    """
    N = len(cur)
    min_oper = EQUIPOS[eq]['min_oper']
    base_viol = count_violations(dc_sets, N, min_oper)
    if base_viol == 0: return []

    # ── Paso 1: 1 persona ─────────────────────────────────────────────────────
    singles = []
    for idx, p in enumerate(cur):
        if 'POR CONTRATAR' in p[1]: continue
        result = best_move_for(idx, p, dc_sets, N, min_oper)
        if result and result[0] < base_viol:
            nom = ' '.join(p[1].split()[:2])
            singles.append({
                'tipo': '1 persona', 'idx': idx, 'idx2': None,
                'nombre': nom, 'nombre2': None,
                'fd_orig': p[4], 'fd_new': result[1],
                'fd_orig2': None, 'fd_new2': None,
                'mejora': base_viol - result[0], 'new_viol': result[0],
            })

    singles.sort(key=lambda x: (-x['mejora'], abs((x['fd_new']-x['fd_orig']).days)))
    seen = set()
    top_singles = []
    for s in singles:
        if s['idx'] not in seen:
            seen.add(s['idx']); top_singles.append(s)
    top_singles = top_singles[:5]

    # Si alguno resuelve completamente, retornar solo esos
    perfect = [s for s in top_singles if s['new_viol'] == 0]
    if perfect: return perfect

    # ── Paso 2: 2 personas (solo si el deficit es ≤3 y hay pocas alertas) ────
    if base_viol <= 5:
        # Tomar las 8 mejores personas del paso 1
        candidates = [s['idx'] for s in top_singles[:8]] if top_singles else \
                     [i for i,p in enumerate(cur) if 'POR CONTRATAR' not in p[1]][:8]

        pairs = []
        for ia in range(len(candidates)):
            for ib in range(ia+1, len(candidates)):
                idxA = candidates[ia]; idxB = candidates[ib]
                pA = cur[idxA]; pB = cur[idxB]
                rA = best_move_for(idxA, pA, dc_sets, N, min_oper)
                if not rA: continue
                # Aplicar movimiento A y buscar mejor B
                ns_a = dc_sets.copy(); ns_a[idxA] = gen_dc(rA[1])
                rB = best_move_for(idxB, pB, ns_a, N, min_oper)
                if not rB: continue
                nv = count_violations(
                    {**{i:s for i,s in enumerate(dc_sets)},
                     idxA:gen_dc(rA[1]), idxB:gen_dc(rB[1])}.values().__iter__(),
                    N, min_oper)
                # recompute properly
                tmp = list(dc_sets)
                tmp[idxA] = gen_dc(rA[1]); tmp[idxB] = gen_dc(rB[1])
                nv2 = count_violations(tmp, N, min_oper)
                if nv2 < base_viol:
                    nomA = ' '.join(pA[1].split()[:2])
                    nomB = ' '.join(pB[1].split()[:2])
                    pairs.append({
                        'tipo': '2 personas', 'idx': idxA, 'idx2': idxB,
                        'nombre': nomA, 'nombre2': nomB,
                        'fd_orig': pA[4], 'fd_new': rA[1],
                        'fd_orig2': pB[4], 'fd_new2': rB[1],
                        'mejora': base_viol-nv2, 'new_viol': nv2,
                    })
        pairs.sort(key=lambda x: (-x['mejora'], 0))
        # Combinar resultados
        result = top_singles + [p for p in pairs if p['new_viol'] < base_viol]
        result.sort(key=lambda x: (-x['mejora'], x['tipo']))
        return result[:6]

    return top_singles

# ── State ─────────────────────────────────────────────────────────────────────
if 'ov' not in st.session_state:
    st.session_state.ov = {}

def get_fd(eq, i):
    return st.session_state.ov.get((eq, i), EQUIPOS[eq]['people'][i][4])

# ── CSS: fondo BLANCO forzado ─────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fondo blanco en toda la app ── */
.stApp, .main, .block-container { background-color: #FFFFFF !important; }
[data-testid="stSidebar"] { background-color: #F8F9FA !important; }
.block-container { padding-top: .8rem; }

/* ── Texto siempre oscuro ── */
body, p, li, label, span, div, h1, h2, h3, h4, h5,
.stMarkdown, .stText { color: #1a1a1a !important; }

/* ── Tabs: fondo blanco, texto negro ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #f0f4f8 !important;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #1a1a1a !important;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #1F3864 !important;
    border-radius: 6px;
}
.stTabs [data-baseweb="tab-panel"] {
    background-color: #FFFFFF !important;
    color: #1a1a1a !important;
}
/* ── Selectbox y inputs ── */
[data-testid="stSelectbox"] label,
[data-testid="stDateInput"] label { color: #1a1a1a !important; }

/* ── Métricas ── */
[data-testid="metric-container"] {
    background: #f0f4f8 !important;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 8px;
    color: #1a1a1a !important;
}
[data-testid="metric-container"] * { color: #1a1a1a !important; }

/* ── Clases custom ── */
.dc-p { padding:2px 8px; border-radius:3px; font-size:11px;
        font-weight:bold; display:inline-block; margin:1px; }
.prem-ok  { border-left:4px solid #375623; background:#f0fff4;
            padding:7px 12px; border-radius:4px; margin:3px 0;
            font-size:13px; color:#1a1a1a !important; }
.prem-bad { border-left:4px solid #C00000; background:#fff5f5;
            padding:7px 12px; border-radius:4px; margin:3px 0;
            font-size:13px; color:#1a1a1a !important; }
.sug-box  { border:1px solid #375623; background:#f0fff4;
            padding:10px 14px; border-radius:6px; margin:4px 0;
            color:#1a1a1a !important; }
.sug-box2 { border:1px solid #2E75B6; background:#EFF6FF;
            padding:10px 14px; border-radius:6px; margin:4px 0;
            color:#1a1a1a !important; }
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

            if s['tipo'] == '2 personas' and s['idx2'] is not None:
                if st.button(f"✅ Aplicar ambos cambios — {s['nombre']} + {s['nombre2']}",
                             key=f"apl2_{s['idx']}_{s['idx2']}_{s['fd_new']}"):
                    st.session_state.ov[(eq, s['idx'])]  = s['fd_new']
                    st.session_state.ov[(eq, s['idx2'])] = s['fd_new2']
                    st.session_state.pop(sol_key, None)
                    st.rerun()
            else:
                if st.button(f"✅ Aplicar — mover {s['nombre']} al {s['fd_new'].strftime('%d/%b')}",
                             key=f"apl1_{s['idx']}_{s['fd_new']}"):
                    st.session_state.ov[(eq, s['idx'])] = s['fd_new']
                    st.session_state.pop(sol_key, None)
                    st.rerun()
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

# ── CALENDARIO ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📆 Calendario de descansos")
tab1, tab2 = st.tabs(["📅 Junio 2026", "📅 Julio 2026"])

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

st.caption("Simulador DC · Jun–Jul 2026 · Ciclo 40-40-48h · Auto-solver integrado · Todas las premisas activas")
