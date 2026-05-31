"""
SIMULADOR DC v5 — COMPLETO
Auto-scheduler + Solver 3 personas + Premisas editables + Carga Excel
Jun 1 – Jul 12, 2026 | Ciclo +8/+8/+15/+8/+8
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

st.set_page_config(page_title="Simulador DC", page_icon="📅",
                   layout="wide", initial_sidebar_state="expanded")

# ── Constantes ────────────────────────────────────────────────────────────────
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
EQ_NUM = {'L1 — SECO':1,'L2 — SECO':2,'L3 — SECO':3,
           'DASA — FRÍO':4,'Facturación':5,'Inventarios':6,'Devolutivos':7}

# ── Session state ─────────────────────────────────────────────────────────────
def default_config():
    return {
        'inicio': datetime.date(2026,6,1),
        'fin':    datetime.date(2026,7,12),
        'ciclo':  [8,8,15,8,8],
        'equipos':{
            'L1 — SECO':  {'min_oper':27,'min_mc':9,  'regla_lideres':True},
            'L2 — SECO':  {'min_oper':27,'min_mc':9,  'regla_lideres':True},
            'L3 — SECO':  {'min_oper':27,'min_mc':9,  'regla_lideres':True},
            'DASA — FRÍO':{'min_oper':28,'min_mc':1,  'min_aux':7,'regla_mc_lider':True},
            'Facturación':{'min_oper':6},
            'Inventarios':{'min_oper':6},
            'Devolutivos':{'min_oper':9},
        }
    }

if 'ov'    not in st.session_state: st.session_state.ov    = {}
if 'cfg'   not in st.session_state: st.session_state.cfg   = default_config()
if 'rules' not in st.session_state: st.session_state.rules = {}

RULE_TYPES = {
    'rol_rol':      '🔴 Dos roles no comparten DC el mismo día',
    'cobertura':    '👷 Mínimo N de un rol activos por día',
    'persona_dia':  '📅 Persona solo descansa en días específicos',
    'exclusion':    '🚫 Persona NO descansa en fecha concreta',
    'inter_equipo': '🔗 Regla entre dos equipos',
    'min_rol':      '🔢 Mínimo N personas de un rol activas',
}

def default_rules_for(eq):
    base=[]
    if 'SECO' in eq:
        base.append({'id':f'r_lmc_{eq[:2]}','tipo':'rol_rol','activa':True,'equipo':eq,
                     'rol1':'Lider de turno','rol2':'Montacarguista',
                     'desc':'Líder y Montacarguista no comparten DC'})
        base.append({'id':f'r_mc9_{eq[:2]}','tipo':'min_rol','activa':True,'equipo':eq,
                     'rol':'Montacarguista','min_n':9,
                     'desc':'Mínimo 9 Montacarguistas activos'})
    if 'DASA' in eq:
        base.append({'id':'r_lmc_dasa','tipo':'rol_rol','activa':True,'equipo':eq,
                     'rol1':'Líder Turno','rol2':'Montacarguista',
                     'desc':'Líder DASA y MC no comparten DC'})
        base.append({'id':'r_aux_dasa','tipo':'min_rol','activa':True,'equipo':eq,
                     'rol':'Auxiliar Logística','min_n':7,
                     'desc':'Mínimo 7 auxiliares activos'})
        base.append({'id':'r_mc_dasa','tipo':'min_rol','activa':True,'equipo':eq,
                     'rol':'Montacarguista','min_n':1,
                     'desc':'Mínimo 1 Montacarguista activo en DASA'})
    return base

def get_rules(eq):
    if eq not in st.session_state.rules:
        st.session_state.rules[eq]=default_rules_for(eq)
    return st.session_state.rules[eq]

def cfg(): return st.session_state.cfg
def get_fd(eq,i): return st.session_state.ov.get((eq,i), _people(eq)[i][4])
def _people(eq):
    k = f'custom_{eq}'
    return st.session_state[k] if k in st.session_state else EQUIPOS[eq]['people']

# ── Algoritmo ciclo DC ────────────────────────────────────────────────────────
def gen_dc(fd):
    if not fd: return set()
    end=cfg()['fin']; gaps=cfg()['ciclo']
    res=[fd]; c=fd
    for g in gaps:
        n=c+datetime.timedelta(days=g)
        if n.weekday()==6: n+=datetime.timedelta(days=1)
        if n>end: break
        res.append(n); c=n
    return set(res)

def gen_dc_list(fd): return sorted(gen_dc(fd))

def get_work_days():
    s=cfg()['inicio']; e=cfg()['fin']
    return [s+datetime.timedelta(days=i)
            for i in range((e-s).days+1)
            if (s+datetime.timedelta(days=i)).weekday()!=6]

def count_viol(dc_sets_list, N, min_oper):
    wk=get_work_days()
    return sum(1 for d in wk if N-sum(1 for s in dc_sets_list if d in s)<min_oper)

# ── Motor de reglas ─────────────────────────────────────────────────────────
def validate_rules(eq, cur, dc_sets):
    rules=get_rules(eq); violations=[]; wk=get_work_days()
    for rule in rules:
        if not rule.get('activa',True): continue
        rid=rule['id']; tipo=rule['tipo']

        if tipo=='rol_rol':
            r1,r2=rule.get('rol1',''),rule.get('rol2','')
            i1=[i for i,p in enumerate(cur) if p[2]==r1]
            i2=[i for i,p in enumerate(cur) if p[2]==r2]
            for d in wk:
                on1=[i for i in i1 if d in dc_sets[i]]
                on2=[i for i in i2 if d in dc_sets[i]]
                if on1 and on2:
                    violations.append({'regla':rule,'dia':d,'personas':on1+on2,'tipo':'rol_rol',
                        'msg':f"🔴 {d.strftime('%d/%b')}: **{r1}** y **{r2}** coinciden en DC"})

        elif tipo=='cobertura':
            rol=rule.get('rol',''); mn=rule.get('min_n',1)
            ri=[i for i,p in enumerate(cur) if p[2]==rol]; nr=len(ri)
            for d in wk:
                w=nr-sum(1 for i in ri if d in dc_sets[i])
                if w<mn:
                    violations.append({'regla':rule,'dia':d,'personas':[i for i in ri if d in dc_sets[i]],
                        'tipo':'cobertura','msg':f"👷 {d.strftime('%d/%b')}: {w} **{rol}** activos (mín {mn})"})

        elif tipo=='persona_dia':
            nom=rule.get('nombre',''); dias_s=rule.get('dias_permitidos',[])
            dias_ok=[]
            for ds in dias_s:
                try: dias_ok.append(datetime.datetime.strptime(ds,'%Y-%m-%d').date())
                except: pass
            for i,p in enumerate(cur):
                if p[1]==nom and dias_ok:
                    bad=[d for d in dc_sets[i] if d in wk and d not in dias_ok]
                    for d in bad:
                        violations.append({'regla':rule,'dia':d,'personas':[i],'tipo':'persona_dia',
                            'msg':f"📅 {d.strftime('%d/%b')}: **{nom.split()[0]}** descansa fuera de días permitidos"})

        elif tipo=='min_rol':
            rol=rule.get('rol',''); mn=rule.get('min_n',1)
            ri=[i for i,p in enumerate(cur) if p[2]==rol]; nr=len(ri)
            for d in wk:
                w=nr-sum(1 for i in ri if d in dc_sets[i])
                if w<mn:
                    violations.append({'regla':rule,'dia':d,
                        'personas':[i for i in ri if d in dc_sets[i]],'tipo':'min_rol',
                        'msg':f"🔢 {d.strftime('%d/%b')}: {w} **{rol}** activos (mín {mn})"})

        elif tipo=='exclusion':

            nom=rule.get('nombre',''); fs=rule.get('fecha','')
            try: fe=datetime.datetime.strptime(fs,'%Y-%m-%d').date()
            except: continue
            for i,p in enumerate(cur):
                if p[1]==nom and fe in dc_sets[i]:
                    violations.append({'regla':rule,'dia':fe,'personas':[i],'tipo':'exclusion',
                        'msg':f"🚫 {fe.strftime('%d/%b')}: **{nom.split()[0]}** tiene DC en fecha excluida"})

    return violations

def suggest_scenarios(eq, cur, dc_sets, violations):
    N=len(cur); min_oper=cfg()['equipos'].get(eq,{}).get('min_oper',6); scenarios=[]
    wk=get_work_days()
    deficit_rol={}
    for v in violations:
        if v['tipo'] in ('cobertura','min_rol'):
            rol=v['regla'].get('rol',''); mn=v['regla'].get('min_n',1)
            ri=[i for i,p in enumerate(cur) if p[2]==rol]
            w=len(ri)-sum(1 for i in ri if v['dia'] in dc_sets[i])
            d=mn-w
            if d>0: deficit_rol[rol]=max(deficit_rol.get(rol,0),d)
    for rol,d in deficit_rol.items():
        scenarios.append({'tipo':'personal','rol':rol,'cant':d,
            'desc':f"➕ Agregar **{d}** persona(s) con rol **{rol}**",
            'impacto':f"Cumpliría la cobertura mínima de {rol}"})
    rr=[v for v in violations if v['tipo']=='rol_rol']
    if rr:
        nd=len(set(v['dia'] for v in rr))
        scenarios.append({'tipo':'redistribuir','desc':f"↔️ Redistribuir ciclos en {nd} día(s) conflictivos",
            'impacto':"El solver puede separar los roles automáticamente"})
    vd=[d for d in wk if N-sum(1 for s in dc_sets if d in s)<min_oper]
    if vd:
        dm=max(min_oper-(N-sum(1 for s in dc_sets if d in s)) for d in vd)
        if dm>0:
            scenarios.append({'tipo':'personal_general','cant':dm,
                'desc':f"➕ Agregar **{dm}** persona(s) al equipo {eq}",
                'impacto':f"Garantizaría mínimo {min_oper} operando en todos los días"})
    return scenarios

def render_rules_panel(eq, cur, dc_sets):
    rules=get_rules(eq); violations=validate_rules(eq,cur,dc_sets)
    uniq_viol=len(set(v['regla']['id'] for v in violations)) if violations else 0
    label=f"📏 Reglas {'⚠️ '+str(uniq_viol)+' conflicto(s)' if uniq_viol else '✅ sin conflictos'}"

    with st.expander(label, expanded=(uniq_viol>0)):
        # Reglas activas
        if rules:
            st.markdown("**Reglas activas:**")
            for i,rule in enumerate(rules):
                ca,cb,cc=st.columns([0.5,4,0.5])
                act=ca.checkbox("",rule.get('activa',True),
                    key=f"ract_{eq}_{i}",label_visibility="collapsed")
                if act!=rule.get('activa',True):
                    st.session_state.rules[eq][i]['activa']=act
                nv=sum(1 for v in violations if v['regla']['id']==rule['id'])
                ico="🔴" if nv>0 and act else ("✅" if act else "⬜")
                cb.markdown(f"{ico} {rule['desc']}" + (f" *({nv}×)*" if nv else ""))
                if cc.button("✕",key=f"rdel_{eq}_{i}"):
                    st.session_state.rules[eq].pop(i); st.rerun()
        else:
            st.caption("Sin reglas — agrega la primera ↓")

        st.markdown("---")
        st.markdown("**➕ Nueva regla:**")
        tipo_sel=st.selectbox("Tipo:",list(RULE_TYPES.keys()),
            format_func=lambda k:RULE_TYPES[k],key=f"nrt_{eq}")
        roles_eq=sorted(set(p[2] for p in cur))
        noms_eq=sorted(set(p[1] for p in cur if 'POR CONTRATAR' not in p[1]))
        nr={'id':f"r{len(rules)}_{eq[:2]}_{tipo_sel[:3]}",'tipo':tipo_sel,'activa':True,'equipo':eq}

        if tipo_sel=='rol_rol':
            ca,cb=st.columns(2)
            r1=ca.selectbox("Rol 1:",roles_eq,key=f"nr1_{eq}")
            r2=cb.selectbox("Rol 2:",[r for r in roles_eq if r!=r1],key=f"nr2_{eq}")
            nr.update({'rol1':r1,'rol2':r2,'desc':f"{r1} ≠ {r2} mismo día DC"})
        elif tipo_sel=='cobertura':
            ca,cb=st.columns(2)
            rl=ca.selectbox("Rol:",roles_eq,key=f"ncrol_{eq}")
            mn=cb.number_input("Mín activos:",1,20,1,key=f"ncmin_{eq}")
            nr.update({'rol':rl,'min_n':mn,'desc':f"Mín {mn} {rl} activos"})
        elif tipo_sel=='persona_dia':
            nom=st.selectbox("Persona:",noms_eq,key=f"npdn_{eq}")
            dias=st.multiselect("Días permitidos:",
                [d.strftime('%Y-%m-%d') for d in get_work_days()],
                format_func=lambda s:datetime.datetime.strptime(s,'%Y-%m-%d').strftime('%a %d/%b'),
                key=f"npdias_{eq}")
            nr.update({'nombre':nom,'dias_permitidos':dias,
                'desc':f"{nom.split()[0]}: solo descansa en {len(dias)} día(s) específicos"})
        elif tipo_sel=='exclusion':
            nom=st.selectbox("Persona:",noms_eq,key=f"nexn_{eq}")
            fex=st.date_input("Fecha excluida:",cfg()['inicio'],
                cfg()['inicio'],cfg()['fin'],key=f"nexf_{eq}")
            nr.update({'nombre':nom,'fecha':fex.strftime('%Y-%m-%d'),
                'desc':f"{nom.split()[0]}: NO descansa el {fex.strftime('%d/%b')}"})
        elif tipo_sel=='min_rol':
            ca,cb=st.columns([3,1])
            rl=ca.selectbox("Rol:",roles_eq,key=f"nmrol_{eq}")
            mn=cb.number_input("Mínimo:",1,50,1,key=f"nmmin_{eq}")
            nr.update({'rol':rl,'min_n':mn,
                'desc':f"Mínimo {mn} {rl} activos por día"})

        elif tipo_sel=='inter_equipo':

            eq2=st.selectbox("Equipo 2:",[e for e in EQUIPOS.keys() if e!=eq],key=f"nie2_{eq}")
            ca,cb=st.columns(2)
            r1=ca.selectbox(f"Rol {eq[:4]}:",roles_eq,key=f"nier1_{eq}")
            r2e2=sorted(set(p[2] for p in _people(eq2)))
            r2=cb.selectbox(f"Rol {eq2[:4]}:",r2e2,key=f"nier2_{eq}")
            nr.update({'equipo2':eq2,'rol1':r1,'rol2':r2,
                'desc':f"{r1} ({eq[:4]}) ≠ {r2} ({eq2[:4]})"})

        if st.button("➕ Agregar",use_container_width=True,type="primary",key=f"addr_{eq}"):
            get_rules(eq).append(nr)
            st.success(f"✓ {nr['desc']}"); st.rerun()

        # Conflictos y escenarios
        if violations:
            st.markdown("---")
            st.markdown(f"**⚠️ Conflictos:**")
            shown=set()
            for v in violations[:6]:
                k=(v['regla']['id'],v['dia'])
                if k not in shown: shown.add(k); st.markdown(v['msg'])

            scens=suggest_scenarios(eq,cur,dc_sets,violations)
            if scens:
                st.markdown("**💡 Para resolver:**")
                for s in scens:
                    bg='#EFF6FF' if 'redistribuir' in s['tipo'] else '#FFF5EC'
                    bc='#2E75B6' if 'redistribuir' in s['tipo'] else '#C55A11'
                    st.markdown(
                        f'<div style="border-left:3px solid {bc};background:{bg};'
                        f'padding:7px 11px;border-radius:4px;margin:3px 0;font-size:12px">'
                        f'{s["desc"]}<br>'
                        f'<span style="color:var(--color-text-secondary);font-size:11px">{s["impacto"]}</span>'
                        f'</div>',unsafe_allow_html=True)
                    if 'redistribuir' in s['tipo']:
                        if st.button("⚙️ Solver automático",key=f"solvr_{eq}",use_container_width=True):
                            with st.spinner("Resolviendo..."):
                                sols=auto_solve(eq,cur,dc_sets)
                            st.session_state[f'sol_{eq}']=sols or []; st.rerun()

# ── Auto-scheduler ────────────────────────────────────────────────────────────
def auto_schedule(people_input, eq, min_oper=27):
    N=len(people_input)
    start=cfg()['inicio']; end=cfg()['fin']; gaps=cfg()['ciclo']

    def dc_set(fd):
        if not fd: return set()
        res=[fd]; c=fd
        for g in gaps:
            n=c+datetime.timedelta(days=g)
            if n.weekday()==6: n+=datetime.timedelta(days=1)
            if n>end: break
            res.append(n); c=n
        return set(res)

    def c_viol(sched):
        wk=get_work_days()
        sets=[dc_set(f) for f in sched]
        return sum(1 for d in wk if N-sum(1 for s in sets if d in s)<min_oper)

    n1=(N+2)//3; n2=(N+1)//3; n3=N-n1-n2
    LIDER={'Lider de turno','Líder Turno','Lider Inventarios'}
    MC={'Montacarguista'}

    lideres=[i for i,p in enumerate(people_input) if p[2] in LIDER]
    mcs    =[i for i,p in enumerate(people_input) if p[2] in MC]
    otros  =[i for i,p in enumerate(people_input) if p[2] not in LIDER|MC]

    ciclo_a=[None]*N; grupos={'DC1':[],'DC2':[],'DC3':[]}
    tam={'DC1':n1,'DC2':n2,'DC3':n3}
    def esp(g): return tam[g]-len(grupos[g])
    def asgn(idx,g): ciclo_a[idx]=g; grupos[g].append(idx)

    for k,i in enumerate(lideres): asgn(i,['DC1','DC2','DC3'][k%3])
    for i in mcs:
        if ciclo_a[i] is None:
            for g in sorted(['DC1','DC2','DC3'],key=esp,reverse=True):
                if esp(g)>0: asgn(i,g); break
    for i in otros:
        if ciclo_a[i] is None:
            for g in sorted(['DC1','DC2','DC3'],key=esp,reverse=True):
                if esp(g)>0: asgn(i,g); break
    for i in range(N):
        if ciclo_a[i] is None:
            for g in ['DC1','DC2','DC3']: asgn(i,g); break

    def ventana(offset, days=7):
        v=[]
        for i in range(days):
            d=start+datetime.timedelta(days=offset+i)
            if d.weekday()!=6 and d<=end: v.append(d)
        return v

    vnt={'DC1':ventana(0),'DC2':ventana(7),'DC3':ventana(14)}
    fechas=[None]*N; sched=[None]*N

    for ciclo in ['DC1','DC2','DC3']:
        pers=grupos[ciclo]; vv=vnt[ciclo] or [start]
        mx=max(1,len(pers)//len(vv)+1)
        for k,idx in enumerate(pers):
            best_fd=None; best_v=9999
            for fd in vv:
                ya=sum(1 for j in pers[:k] if fechas[j]==fd)
                if ya>=mx: continue
                t=list(sched); t[idx]=fd; v=c_viol(t)
                if v<best_v or best_fd is None: best_v=v; best_fd=fd
            if best_fd is None: best_fd=vv[k%len(vv)]
            fechas[idx]=best_fd; sched[idx]=best_fd

    result=[(p[0],p[1],p[2],ciclo_a[i] or 'DC1',fechas[i] or start)
            for i,p in enumerate(people_input)]
    return result, c_viol([r[4] for r in result])

# ── Solver ────────────────────────────────────────────────────────────────────
def apply_moves(dc_sets,moves):
    tmp=list(dc_sets)
    for idx,fd in moves: tmp[idx]=gen_dc(fd)
    return tmp

def best_move(idx,p,dc_sets,N,min_oper):
    best=None
    for d in list(range(-10,0))+list(range(1,11)):
        nf=p[4]+datetime.timedelta(days=d)
        if nf<datetime.date(2026,6,1) or nf>datetime.date(2026,7,5): continue
        if nf.weekday()==6: continue
        nv=count_viol(apply_moves(dc_sets,[(idx,nf)]),N,min_oper)
        if best is None or nv<best[0] or (nv==best[0] and abs(d)<best[2]):
            best=(nv,nf,abs(d))
    return best

def auto_solve(eq,cur,dc_sets):
    N=len(cur); min_oper=cfg()['equipos'].get(eq,{}).get('min_oper',27)
    base=count_viol(dc_sets,N,min_oper)
    if base==0: return []

    viol_days=[d for d in get_work_days() if N-sum(1 for s in dc_sets if d in s)<min_oper]
    guilty={}
    for d in viol_days:
        for i,s in enumerate(dc_sets):
            if d in s and 'POR CONTRATAR' not in cur[i][1]:
                guilty[i]=guilty.get(i,0)+1
    cands=sorted(guilty.keys(),key=lambda i:-guilty[i])
    if not cands: cands=[i for i,p in enumerate(cur) if 'POR CONTRATAR' not in p[1]]
    cands=cands[:12]

    res=[]
    # 1 persona
    for idx in cands:
        r=best_move(idx,cur[idx],dc_sets,N,min_oper)
        if r and r[0]<base:
            nom=' '.join(cur[idx][1].split()[:2])
            res.append({'tipo':'1 persona','idx':idx,'idx2':None,'idx3':None,
                        'nombre':nom,'nombre2':None,'nombre3':None,
                        'fd_orig':cur[idx][4],'fd_new':r[1],
                        'fd_orig2':None,'fd_new2':None,'fd_orig3':None,'fd_new3':None,
                        'mejora':base-r[0],'new_viol':r[0]})
    res.sort(key=lambda x:(-x['mejora'],abs((x['fd_new']-x['fd_orig']).days)))
    seen=set(); top1=[]
    for s in res:
        if s['idx'] not in seen: seen.add(s['idx']); top1.append(s)
    top1=top1[:5]
    if any(s['new_viol']==0 for s in top1): return [s for s in top1 if s['new_viol']==0]

    # 2 personas
    pairs=[]
    for ia in range(len(cands[:8])):
        for ib in range(ia+1,len(cands[:8])):
            idxA=cands[ia]; idxB=cands[ib]
            rA=best_move(idxA,cur[idxA],dc_sets,N,min_oper)
            if not rA: continue
            ns_a=apply_moves(dc_sets,[(idxA,rA[1])])
            rB=best_move(idxB,cur[idxB],ns_a,N,min_oper)
            if not rB: continue
            tmp=apply_moves(dc_sets,[(idxA,rA[1]),(idxB,rB[1])])
            nv=count_viol(tmp,N,min_oper)
            if nv<base:
                pairs.append({'tipo':'2 personas','idx':idxA,'idx2':idxB,'idx3':None,
                              'nombre':' '.join(cur[idxA][1].split()[:2]),
                              'nombre2':' '.join(cur[idxB][1].split()[:2]),'nombre3':None,
                              'fd_orig':cur[idxA][4],'fd_new':rA[1],
                              'fd_orig2':cur[idxB][4],'fd_new2':rB[1],
                              'fd_orig3':None,'fd_new3':None,
                              'mejora':base-nv,'new_viol':nv})
    pairs.sort(key=lambda x:-x['mejora'])
    if any(s['new_viol']==0 for s in pairs):
        return (top1+[s for s in pairs if s['new_viol']==0])[:6]

    # 3 personas
    trios=[]
    c3=cands[:6]
    for ia in range(len(c3)):
        for ib in range(ia+1,len(c3)):
            for ic in range(ib+1,len(c3)):
                idxA=c3[ia]; idxB=c3[ib]; idxC=c3[ic]
                rA=best_move(idxA,cur[idxA],dc_sets,N,min_oper)
                if not rA: continue
                ns_a=apply_moves(dc_sets,[(idxA,rA[1])])
                rB=best_move(idxB,cur[idxB],ns_a,N,min_oper)
                if not rB: continue
                ns_ab=apply_moves(ns_a,[(idxB,rB[1])])
                rC=best_move(idxC,cur[idxC],ns_ab,N,min_oper)
                if not rC: continue
                tmp=apply_moves(dc_sets,[(idxA,rA[1]),(idxB,rB[1]),(idxC,rC[1])])
                nv=count_viol(tmp,N,min_oper)
                if nv<base:
                    trios.append({'tipo':'3 personas','idx':idxA,'idx2':idxB,'idx3':idxC,
                                  'nombre':' '.join(cur[idxA][1].split()[:2]),
                                  'nombre2':' '.join(cur[idxB][1].split()[:2]),
                                  'nombre3':' '.join(cur[idxC][1].split()[:2]),
                                  'fd_orig':cur[idxA][4],'fd_new':rA[1],
                                  'fd_orig2':cur[idxB][4],'fd_new2':rB[1],
                                  'fd_orig3':cur[idxC][4],'fd_new3':rC[1],
                                  'mejora':base-nv,'new_viol':nv})
    trios.sort(key=lambda x:-x['mejora'])
    combined=top1+pairs[:3]+trios[:3]
    combined.sort(key=lambda x:(-x['mejora'],len(x['tipo'])))
    return combined[:6]

# ── Parser Excel/CSV ──────────────────────────────────────────────────────────
def parse_upload(file_bytes):
    results=[]; errors=[]
    try:
        if HAS_OPENPYXL:
            wb=openpyxl.load_workbook(io.BytesIO(file_bytes),data_only=True)
            ws=wb.active
            rows=list(ws.iter_rows(values_only=True))
        else:
            import csv
            rows=list(csv.reader(io.StringIO(file_bytes.decode('utf-8'))))
    except Exception as e:
        return None,["Error leyendo archivo: "+str(e)]

    # Find header row
    header_row=None
    for i,row in enumerate(rows[:4]):
        if row and any(str(c).lower().strip() in ['nombre','name'] for c in row if c):
            header_row=i; break
    if header_row is None:
        return None,["No se encontró encabezado. Columnas: N°, Nombre, Rol, EQUIPO"]

    headers=[str(c).strip().lower() if c else '' for c in rows[header_row]]
    col={}
    for i,h in enumerate(headers):
        if 'nombre' in h or 'name' in h: col['nombre']=i
        if 'rol' in h and 'equipo' not in h: col['rol']=i
        if 'ciclo' in h: col['ciclo']=i
        if '1er' in h or ('dc' in h and 'ciclo' not in h) or 'fecha' in h: col['fecha']=i
        if h in ('n°','n','#','num','número'): col['num']=i
        if 'equipo' in h or 'team' in h or 'lote' in h: col['equipo']=i

    missing=[k for k in ['nombre','rol'] if k not in col]
    if missing: return None,["Faltan columnas: "+', '.join(missing)]

    for r_idx,row in enumerate(rows[header_row+1:],1):
        if not row or not any(c for c in row if c): continue
        try:
            num   = row[col['num']] if 'num' in col and col['num']<len(row) else r_idx
            nom   = str(row[col['nombre']]).strip() if row[col['nombre']] else ''
            rol   = str(row[col['rol']]).strip()    if 'rol' in col and col['rol']<len(row) and row[col['rol']] else ''
            if not nom: continue

            ciclo=None
            if 'ciclo' in col and col['ciclo']<len(row) and row[col['ciclo']]:
                cr=str(row[col['ciclo']]).strip()
                if cr in ('DC1','DC2','DC3'): ciclo=cr

            fd=None
            if 'fecha' in col and col['fecha']<len(row):
                fv=row[col['fecha']]
                if isinstance(fv,datetime.datetime): fd=fv.date()
                elif isinstance(fv,datetime.date):   fd=fv
                elif fv:
                    for fmt in ['%d/%m/%Y','%Y-%m-%d','%d-%m-%Y','%d/%m/%y']:
                        try: fd=datetime.datetime.strptime(str(fv).strip(),fmt).date(); break
                        except: pass

            eq_val=None
            if 'equipo' in col and col['equipo']<len(row) and row[col['equipo']]:
                try: eq_val=int(float(str(row[col['equipo']]).strip()))
                except: pass

            results.append((int(num) if str(num).isdigit() else r_idx,
                            nom, rol, ciclo, fd, eq_val))
        except Exception as e:
            errors.append(f"Fila {r_idx}: {e}")
    return (results if results else None), errors

# ── Datos hardcoded ───────────────────────────────────────────────────────────
J=lambda d:datetime.date(2026,6,d)
EQUIPOS={
'L1 — SECO':{'min_oper':27,'n':32,'people':[
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
'L2 — SECO':{'min_oper':27,'n':32,'people':[
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
'L3 — SECO':{'min_oper':27,'n':32,'people':[
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
'DASA — FRÍO':{'min_oper':28,'n':35,'people':[
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
'Facturación':{'min_oper':6,'n':7,'people':[
    (1,'GARAVITO DUARTE DIANA MILENA','Facturador','DC1',J(1)),
    (2,'GARCIA RINCON ANDRES JULIAN','Facturador','DC1',J(2)),
    (3,'GONZALEZ SALAMANCA JOSE HUMBERTO','Pedidos','DC1',J(3)),
    (4,'JUYO CHOCONTA GLORIA ESPERANZA','Pedidos','DC1',J(4)),
    (5,'PATARROYO GOMEZ OLGA LUCIA','Facturador','DC1',J(5)),
    (6,'RIOS RIOS CARLOS','Facturador','DC1',J(6)),
    (7,'RODRIGUEZ CASTAÑEDA WILMER ANDRES','Facturador','DC1',J(8)),
]},
'Inventarios':{'min_oper':6,'n':7,'people':[
    (1,'RONCANCIO BELLO PAULA LORENA','Lider Inventarios','DC1',J(1)),
    (2,'HORTUA HERRERA EDWIN','Apoyo inventarios','DC1',J(2)),
    (3,'LOPEZ POVEDA YULY ELIZABETH','Apoyo inventarios','DC1',J(3)),
    (4,'TRIVIÑO SANTAMARIA DAYANA','Apoyo inventarios','DC1',J(4)),
    (5,'CAMACHO MOLANO JAIME','aux inventarios','DC1',J(5)),
    (6,'RODRIGUEZ RUIZ RICARDO HUMBERTO','aux inventarios','DC1',J(6)),
    (7,'CASTRO OBANDO MARTHA INES','Aux admin','DC1',J(8)),
]},
'Devolutivos':{'min_oper':9,'n':11,'people':[
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

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
html,body,.stApp,.main,.block-container,[data-testid="stAppViewContainer"],
[data-testid="stVerticalBlock"],section.main>div{background:#FFFFFF!important}
[data-testid="stSidebar"],[data-testid="stSidebarContent"]{background:#F4F6F9!important}
body,p,span,div,label,h1,h2,h3,li,td,th,.stMarkdown,.stText{color:#000000!important}
[data-baseweb="select"]>div,[data-baseweb="option"],[data-baseweb="menu"]{background:#FFFFFF!important;color:#000000!important}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#FFFFFF!important;color:#000000!important}
[data-baseweb="select"] svg{fill:#000000!important}
.stTabs [data-baseweb="tab-list"]{background:#1F3864!important;border-radius:8px;padding:3px}
.stTabs [data-baseweb="tab"]{color:#FFFFFF!important;font-weight:600!important;background:transparent!important}
.stTabs [aria-selected="true"]{background:#FFFFFF!important;color:#000000!important;border-radius:6px!important}
.stTabs [data-baseweb="tab-panel"],.stTabs [data-baseweb="tab-panel"] *{background:#FFFFFF!important;color:#000000!important}
.stExpander,details{background:#FFFFFF!important}
details summary{background:#1F3864!important;border-radius:6px;padding:6px 12px!important;font-weight:600}
details summary,details summary *,details summary p,details summary span{color:#FFFFFF!important}
[data-testid="stSidebar"] details summary{background:#2E4A7A!important}
[data-testid="stSidebar"] details>div{background:#F4F6F9!important}
[data-testid="stSidebar"] details>div *{color:#000000!important}
[data-testid="stFileUploader"],[data-testid="stFileUploader"] *{background:#FFFFFF!important;color:#000000!important}
[data-testid="stFileUploaderDropzone"]{border:2px dashed #2E75B6!important;border-radius:8px!important;background:#F0F4FF!important}
[data-testid="metric-container"]{background:#1F3864!important;border-radius:8px!important;padding:10px!important}
[data-testid="metric-container"],[data-testid="metric-container"] *{color:#FFFFFF!important}
.stButton>button{background:#1F3864!important;color:#FFFFFF!important;border-radius:6px!important;border:none!important}
.stButton>button *,.stButton>button span{color:#FFFFFF!important}
.stButton>button:hover{background:#2E4A7A!important}
[data-testid="stBaseButton-primary"]{background:#C00000!important}
[data-testid="stBaseButton-primary"]:hover{background:#9C0000!important}
[data-testid="stCheckbox"] label,[data-testid="stCheckbox"] *{color:#000000!important}
[data-testid="stSelectbox"] label,[data-testid="stDateInput"] label{color:#000000!important}
.dc-p{padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold;display:inline-block;margin:1px}
.sug-box{border-left:3px solid #375623;background:#f0fff4;padding:10px 14px;border-radius:4px;margin:4px 0}
.sug-box{color:#000000!important}
.sug-box2{border-left:3px solid #2E75B6;background:#EFF6FF;padding:10px 14px;border-radius:4px;margin:4px 0;color:#000000!important}
.sug-box3{border-left:3px solid #C55A11;background:#FFF5EC;padding:10px 14px;border-radius:4px;margin:4px 0;color:#000000!important}
.prem-ok{border-left:4px solid #375623;background:#f0fff4;padding:7px 12px;border-radius:4px;margin:3px 0;font-size:13px;color:#000000!important}
.rule-conflict{border-left:3px solid #C00000;background:#FFF0F0;padding:7px 12px;border-radius:4px;margin:3px 0;font-size:13px;color:#000000!important}
/* calendario HTML */
.cal-table{border-collapse:collapse;width:100%;font-size:11px}
.cal-table th{background:#1F3864;color:#FFFFFF;padding:3px 4px;text-align:center;font-weight:600;white-space:nowrap}
.cal-table td{padding:2px 3px;text-align:center;border:1px solid #dee2e6;white-space:nowrap}
.cal-dc1{background:#C00000;color:#FFFFFF!important;font-weight:bold}
.cal-dc2{background:#BF8F00;color:#000000!important;font-weight:bold}
.cal-dc3{background:#375623;color:#FFFFFF!important;font-weight:bold}
.cal-sun{background:#E0E0E0;color:#999999!important}
.cal-sat{background:#FFF8E6;color:#000000!important}
.cal-nom{background:#F0F4F8;color:#1F3864!important;font-weight:600;text-align:left;padding:3px 6px;font-size:10px;max-width:120px;overflow:hidden;text-overflow:ellipsis}
.cal-empty{background:#F5F5F5;color:#cccccc!important}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📅 Simulador DC")
    st.caption("Jun 1 – Jul 12, 2026  ·  Ciclo +8/+8/+15/+8/+8")
    st.divider()

    eq = st.selectbox("**Equipo:**", list(EQUIPOS.keys()))
    people = _people(eq)
    min_oper = cfg()['equipos'].get(eq,{}).get('min_oper', EQUIPOS[eq]['min_oper'])

    # ── Carga de personal ────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📂 Cargar personal desde Excel", expanded=False):
        st.caption("Columnas: N°, Nombre, Rol, EQUIPO")
        uploaded = st.file_uploader("", type=["xlsx","csv"],
                                    key=f"up_{eq}", label_visibility="collapsed")
        if uploaded:
            parsed, errs = parse_upload(uploaded.read())
            if parsed:
                eq_num = EQ_NUM.get(eq)
                has_eq_col = any(len(p)>5 and p[5] for p in parsed)
                filtered = [p for p in parsed if len(p)>5 and p[5]==eq_num] if (has_eq_col and eq_num) else parsed
                if not filtered: filtered = parsed

                st.caption(f"{len(filtered)} personas para {eq}")
                prev = pd.DataFrame(
                    [(p[0],p[1][:25],p[2],
                      p[3] or '⚙️','p[4].strftime("%d/%m") if p[4] else "⚙️"')
                     for p in filtered[:6]],
                    columns=['N°','Nombre','Rol','Ciclo','1erDC'])
                # Fix: proper date formatting
                prev = pd.DataFrame(
                    [(p[0],p[1][:25],p[2],
                      p[3] if p[3] else '⚙️ auto',
                      p[4].strftime('%d/%m/%Y') if p[4] else '⚙️ auto')
                     for p in filtered[:6]],
                    columns=['N°','Nombre','Rol','Ciclo','1er DC'])
                st.dataframe(prev, hide_index=True, use_container_width=True)

                needs_auto = any(p[3] is None or p[4] is None for p in filtered)
                if needs_auto:
                    st.info("Sin Ciclo/Fecha → el solver asignará automáticamente")
                    if st.button("⚙️ Calcular ciclos automáticamente",
                                 use_container_width=True, type="primary"):
                        only_roles = [(p[0],p[1],p[2]) for p in filtered]
                        scheduled, viol = auto_schedule(only_roles, eq, min_oper)
                        st.session_state[f'custom_{eq}'] = scheduled
                        st.session_state.ov = {k:v for k,v in st.session_state.ov.items() if k[0]!=eq}
                        msg = f"✓ Ciclos asignados" + (f" — {viol} días con alerta, ajusta manualmente" if viol else " sin violaciones")
                        st.success(msg) if not viol else st.warning(msg)
                        st.rerun()
                else:
                    if st.button(f"✅ Cargar {len(filtered)} personas",
                                 use_container_width=True, type="primary"):
                        st.session_state[f'custom_{eq}'] = [(p[0],p[1],p[2],p[3],p[4]) for p in filtered]
                        st.session_state.ov = {k:v for k,v in st.session_state.ov.items() if k[0]!=eq}
                        st.rerun()
            for e in errs[:3]: st.warning(e)

        if f'custom_{eq}' in st.session_state:
            nc = len(st.session_state[f'custom_{eq}'])
            st.success(f"✓ Datos propios: {nc} personas")
            if st.button("🗑 Volver a datos originales", use_container_width=True):
                del st.session_state[f'custom_{eq}']
                st.session_state.ov = {k:v for k,v in st.session_state.ov.items() if k[0]!=eq}
                st.rerun()

    # ── Cambiar 1er DC ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✏️ Cambiar 1er DC")
    st.caption("Recalcula automáticamente al cambiar la fecha")

    people_cur = _people(eq)
    nombres = [f"{p[0]}. {p[2][:26]}" for p in people_cur]
    sel = st.selectbox("Persona:", range(len(nombres)), format_func=lambda i: nombres[i])

    def on_date():
        st.session_state.ov[(eq,sel)] = st.session_state[f'dp_{eq}_{sel}']

    st.date_input("📆 1er DC:", value=get_fd(eq,sel),
        min_value=cfg()['inicio'], max_value=cfg()['fin'],
        key=f'dp_{eq}_{sel}', on_change=on_date)

    dcs_p = gen_dc_list(get_fd(eq,sel))
    for i,d in enumerate(dcs_p):
        ck = ['DC1','DC2','DC3'][min(i,2)]
        st.markdown(f'<span class="dc-p" style="background:{DC_BG[ck]};color:{DC_FG[ck]}">DC{i+1}</span>'
                    f' <span style="color:#333">{d.strftime("%a %d/%b")}</span>',
                    unsafe_allow_html=True)

    # ── Premisas editables ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("⚙️ Configurar Premisas", expanded=False):
        st.markdown("**📅 Período**")
        c1,c2 = st.columns(2)
        ni = c1.date_input("Inicio", cfg()['inicio'], key="cfg_ini")
        nf = c2.date_input("Fin",    cfg()['fin'],    key="cfg_fin")
        if ni!=cfg()['inicio']: st.session_state.cfg['inicio']=ni
        if nf!=cfg()['fin']:    st.session_state.cfg['fin']=nf

        st.markdown("**🔄 Ciclo (días)**")
        cc = st.columns(5); labels=["→DC2","→DC3","→DC4","→DC5","→DC6"]
        nc = [cc[i].number_input(labels[i],1,30,cfg()['ciclo'][i],1,key=f"cc{i}") for i in range(5)]
        if nc!=cfg()['ciclo']: st.session_state.cfg['ciclo']=nc

        st.markdown("**👥 Mínimo operando**")
        for eq_n, eq_c in cfg()['equipos'].items():
            ca,cb = st.columns([3,1])
            ca.caption(eq_n)
            nm = cb.number_input("",1,50,int(eq_c.get('min_oper',1)),1,
                                  key=f"mn_{eq_n}", label_visibility="collapsed")
            if nm!=eq_c.get('min_oper'): st.session_state.cfg['equipos'][eq_n]['min_oper']=nm

        eq_cc = cfg()['equipos'].get(eq,{})
        if 'min_mc' in eq_cc:
            nm2=st.number_input("Mín. montacarguistas",1,20,int(eq_cc['min_mc']),1,key=f"mc_{eq}")
            if nm2!=eq_cc['min_mc']: st.session_state.cfg['equipos'][eq]['min_mc']=nm2
        if 'min_aux' in eq_cc:
            nm3=st.number_input("Mín. auxiliares",1,20,int(eq_cc['min_aux']),1,key=f"ax_{eq}")
            if nm3!=eq_cc['min_aux']: st.session_state.cfg['equipos'][eq]['min_aux']=nm3
        if 'regla_lideres' in eq_cc:
            rl=st.checkbox("Líderes no coinciden",eq_cc['regla_lideres'],key=f"rl_{eq}")
            if rl!=eq_cc['regla_lideres']: st.session_state.cfg['equipos'][eq]['regla_lideres']=rl

        ca,cb=st.columns(2)
        if ca.button("💾 Guardar",use_container_width=True,type="primary"): st.rerun()
        if cb.button("↺ Reset",use_container_width=True):
            st.session_state.cfg=default_config(); st.rerun()

    # ── Panel de reglas ──────────────────────────────────────────────────────
    st.markdown("---")
    # Render rules panel (uses cur/dc_sets from main area - pass current state)
    _cur_sidebar = [(p[0],p[1],p[2],p[3],get_fd(eq,i)) for i,p in enumerate(_people(eq))]
    _dcs_sidebar = [gen_dc(p[4]) for p in _cur_sidebar]
    render_rules_panel(eq, _cur_sidebar, _dcs_sidebar)

    st.divider()
    n_mod=sum(1 for k in st.session_state.ov if k[0]==eq)
    if n_mod:
        st.info(f"**{n_mod}** cambio(s)")
        ca,cb=st.columns(2)
        if ca.button("↺ Persona",use_container_width=True):
            st.session_state.ov.pop((eq,sel),None); st.rerun()
        if cb.button("↺ Equipo",use_container_width=True):
            [st.session_state.ov.pop(k) for k in list(st.session_state.ov) if k[0]==eq]; st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════
people = _people(eq)
N = len(people)
min_oper = cfg()['equipos'].get(eq,{}).get('min_oper', EQUIPOS[eq]['min_oper'])
cur = [(p[0],p[1],p[2],p[3],get_fd(eq,i)) for i,p in enumerate(people)]
dc_sets = [gen_dc(p[4]) for p in cur]
WORK_NOW = get_work_days()
oper_vals = [N-sum(1 for s in dc_sets if d in s) for d in WORK_NOW]
viol_days = [(d,w) for d,w in zip(WORK_NOW,oper_vals) if w<min_oper]

st.markdown(f"## 📋 {eq} &nbsp;·&nbsp; {N} personas")

# Métricas
min_op=min(oper_vals) if oper_vals else N
c1,c2,c3,c4=st.columns(4)
c1.metric("👥 Total",N)
c2.metric("📉 Mín. operando real",min_op,
          delta=f"{min_op-min_oper:+d}",
          delta_color="normal" if min_op>=min_oper else "inverse")
c3.metric("📋 Requerido",min_oper)
c4.metric("⚠️ Alertas",len(viol_days),
          delta="OK ✓" if not viol_days else f"{len(viol_days)} días",
          delta_color="normal" if not viol_days else "inverse")

# ── Alertas + Solver ──────────────────────────────────────────────────────────
st.markdown("---")
if viol_days:
    st.markdown(f"### ⚠️ {len(viol_days)} día(s) bajo el mínimo operacional")
    alert_html='<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px">'
    for d,w in viol_days:
        alert_html+=f'<div style="background:#FFC7CE;color:#9C0006;border-radius:5px;padding:4px 8px;font-size:12px;font-weight:bold">{d.strftime("%d/%b")}: {w} op</div>'
    alert_html+='</div>'
    st.markdown(alert_html, unsafe_allow_html=True)

    col_a,col_b=st.columns([3,1])
    col_a.markdown(
        f'<div class="prem-ok" style="border-left-color:#C00000;background:#fff5f5">'
        f'🔴 Hay <b>{len(viol_days)}</b> día(s) con menos de <b>{min_oper}</b> personas operando.</div>',
        unsafe_allow_html=True)
    if col_b.button("🔧 Buscar solución", use_container_width=True, type="primary"):
        with st.spinner("Analizando combinaciones..."):
            sols = auto_solve(eq, cur, dc_sets)
        st.session_state[f'sol_{eq}'] = sols or []

    sol_key=f'sol_{eq}'
    if sol_key in st.session_state:
        sols=st.session_state[sol_key]
        if sols:
            st.markdown("#### 💡 Soluciones encontradas")
            BOX={'1 persona':'sug-box','2 personas':'sug-box2','3 personas':'sug-box3'}
            for s in sols:
                tipo=s['tipo']; box=BOX.get(tipo,'sug-box')
                res_txt="✅ resuelve todo" if s['new_viol']==0 else f"reduce a {s['new_viol']} alerta(s)"
                d1=f"{s['fd_orig'].strftime('%d/%b')}→<b>{s['fd_new'].strftime('%d/%b')}</b>"
                txt=f"[{tipo}] 👤<b>{s['nombre']}</b> {d1}"
                if s['idx2'] is not None:
                    d2=f"{s['fd_orig2'].strftime('%d/%b')}→<b>{s['fd_new2'].strftime('%d/%b')}</b>"
                    txt+=f" + 👤<b>{s['nombre2']}</b> {d2}"
                if s.get('idx3') is not None:
                    d3=f"{s['fd_orig3'].strftime('%d/%b')}→<b>{s['fd_new3'].strftime('%d/%b')}</b>"
                    txt+=f" + 👤<b>{s['nombre3']}</b> {d3}"
                txt+=f" | {res_txt}"
                st.markdown(f'<div class="{box}">{txt}</div>', unsafe_allow_html=True)
                bk=f"apl_{s['idx']}_{s.get('idx2','x')}_{s.get('idx3','x')}_{s['fd_new']}"
                if st.button(f"✅ Aplicar",key=bk):
                    st.session_state.ov[(eq,s['idx'])]=s['fd_new']
                    if s['idx2'] is not None: st.session_state.ov[(eq,s['idx2'])]=s['fd_new2']
                    if s.get('idx3') is not None: st.session_state.ov[(eq,s['idx3'])]=s['fd_new3']
                    st.session_state.pop(sol_key,None); st.rerun()
        else:
            st.warning("No se encontró solución moviendo hasta 3 personas. Ajusta manualmente varias fechas.")
else:
    st.success("✅ **Todas las premisas cumplidas** — operando mínimo garantizado en todo el período")

# ── Operando visual ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Personas operando por día")
html='<div style="display:flex;flex-wrap:wrap;gap:3px">'
for d,w in zip(WORK_NOW,oper_vals):
    bg,fg=('#C6EFCE','#276221') if w>=min_oper else ('#FFEB9C','#9C5700') if w>=min_oper-3 else ('#FFC7CE','#9C0006')
    sat='🟡' if d.weekday()==5 else ''
    html+=(f'<div style="background:{bg};color:{fg};border-radius:5px;padding:5px 6px;text-align:center;min-width:46px">'
           f'<div style="opacity:.7;font-size:9px">{d.strftime("%d/%m")}{sat}</div>'
           f'<b style="font-size:15px">{w}</b></div>')
html+='</div>'
st.markdown(html,unsafe_allow_html=True)
st.caption(f"Verde ≥{min_oper} · Amarillo ={min_oper-3}–{min_oper-1} · Rojo <{min_oper-3}")

# ── Tabla personal ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 👥 Personal y descansos")
prev_cyc=None
for i,p in enumerate(cur):
    num,nom,rol,cyc,fd=p
    is_mod=(eq,i) in st.session_state.ov; is_sel=(i==sel)
    if cyc!=prev_cyc:
        bg=DC_BG.get(cyc,'#888'); fg=DC_FG.get(cyc,'white')
        st.markdown(f'<div style="background:{bg};color:{fg};padding:5px 14px;border-radius:6px;font-weight:bold;margin:10px 0 2px;font-size:13px">▸ CICLO {cyc}</div>',unsafe_allow_html=True)
        prev_cyc=cyc
    dcs=gen_dc_list(fd)
    dc_str='&nbsp;'.join([f'<span class="dc-p" style="background:{DC_BG.get(cyc,"#888")};color:{DC_FG.get(cyc,"white")}">{d.strftime("%d/%b")}</span>' for d in dcs])
    rc=ROL_C.get(rol,'#888')
    border='2px solid #375623' if is_sel else ('1px solid #FFD700' if is_mod else '1px solid #eee')
    bg_r='#F0FFF4' if is_sel else ('#FFFDE7' if is_mod else 'white')
    is_pc='POR CONTRATAR' in nom
    ns='color:#999;font-style:italic' if is_pc else 'color:#1a1a1a'
    mi='✏️ ' if is_mod else ''
    st.markdown(
        f'<div style="border:{border};background:{bg_r};border-radius:7px;padding:5px 12px;margin:2px 0;display:flex;align-items:center;gap:10px">'
        f'<span style="font-size:11px;color:#888;min-width:18px">{num}</span>'
        f'<span style="font-size:12px;min-width:210px;{ns}">{mi}{nom}</span>'
        f'<span style="background:{rc};color:white;padding:1px 7px;border-radius:3px;font-size:10px;font-weight:bold">{rol}</span>'
        f'<span style="margin-left:auto">{dc_str}</span>'
        f'</div>', unsafe_allow_html=True)

# ── Calendario ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📆 Calendario de descansos")

months=sorted(set([(cfg()['inicio']+datetime.timedelta(days=i)).month
    for i in range((cfg()['fin']-cfg()['inicio']).days+1)]))
MN={1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
    7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
tab_labels=[f"📅 {MN.get(m,str(m))}" for m in months]+["📋 Premisas"]
all_tabs=st.tabs(tab_labels)

def render_cal(month):
    s=cfg()['inicio']; e=cfg()['fin']
    all_d=[s+datetime.timedelta(days=i) for i in range((e-s).days+1)]
    md=[d for d in all_d if d.month==month]
    mi=[i for i,d in enumerate(all_d) if d.month==month]
    if not md: st.info('Sin datos para este mes'); return

    # Header de fechas
    html='<div style="overflow-x:auto"><table class="cal-table"><thead><tr>'
    html+='<th style="min-width:110px">Persona</th>'
    for d in md:
        if d.weekday()==6:
            html+=f'<th class="cal-sun">{d.day}<br>D</th>'
        elif d.weekday()==5:
            html+=f'<th style="background:#7A6200;color:white;padding:3px 4px;text-align:center">{d.day}<br>S</th>'
        else:
            html+=f'<th>{d.day}<br>{DI[d.weekday()]}</th>'
    html+='</tr></thead><tbody>'

    # Filas de personas
    prev_cyc=None
    for i,p in enumerate(cur):
        num,nom,rol,cyc,fd=p
        dcs_i=dc_sets[i]
        # Separador de ciclo
        if cyc!=prev_cyc:
            bg=DC_BG.get(cyc,'#888'); fg=DC_FG.get(cyc,'white')
            colspan=len(md)+1
            html+=(f'<tr><td colspan="{colspan}" style="background:{bg};color:{fg};'
                   f'font-weight:bold;padding:4px 8px;font-size:11px">▸ {cyc}</td></tr>')
            prev_cyc=cyc
        html+='<tr>'
        # Nombre
        is_pc='POR CONTRATAR' in nom
        nom_style='color:#999;font-style:italic' if is_pc else 'color:#1F3864;font-weight:600'
        html+=f'<td class="cal-nom" style="{nom_style}" title="{nom}">{num}. {nom[:18]}</td>'
        # Días
        for j in mi:
            d=all_d[j]
            if d.weekday()==6:
                html+='<td class="cal-sun">D</td>'
            elif d in dcs_i:
                css_class={'DC1':'cal-dc1','DC2':'cal-dc2','DC3':'cal-dc3'}.get(cyc,'cal-dc1')
                html+=f'<td class="{css_class}">{cyc}</td>'
            else:
                css_class='cal-sat' if d.weekday()==5 else 'cal-empty'
                html+=f'<td class="{css_class}"></td>'
        html+='</tr>'
    html+='</tbody></table></div>'
    st.markdown(html, unsafe_allow_html=True)

for ti,tm in enumerate(months):
    with all_tabs[ti]: render_cal(tm)

with all_tabs[-1]:
    col_p1,col_p2=st.columns(2)
    with col_p1:
        st.markdown("#### ⚙️ Ciclo de descansos")
        ciclo_df=pd.DataFrame([
            ("DC1 → DC2",f"+{cfg()['ciclo'][0]} días"),
            ("DC2 → DC3",f"+{cfg()['ciclo'][1]} días"),
            ("DC3 → DC4",f"+{cfg()['ciclo'][2]} días (ciclo 48h)"),
            ("DC4 → DC5",f"+{cfg()['ciclo'][3]} días"),
            ("DC5 → DC6",f"+{cfg()['ciclo'][4]} días"),
            ("Domingo","→ mueve al lunes siguiente"),
            ("Período",f"{cfg()['inicio'].strftime('%d/%b/%Y')} – {cfg()['fin'].strftime('%d/%b/%Y')}"),
        ],columns=["Paso","Regla"])
        st.dataframe(ciclo_df,hide_index=True,use_container_width=True)

        st.markdown("#### 👥 Mínimos operacionales")
        min_df=pd.DataFrame(
            [(en,str(EQUIPOS[en]['n']),str(ec.get('min_oper','—')))
             for en,ec in cfg()['equipos'].items()],
            columns=["Equipo","Total","Mín operando"])
        st.dataframe(min_df,hide_index=True,use_container_width=True)

    with col_p2:
        st.markdown("#### 🏷️ Roles")
        roles_html=""
        for rol,color in ROL_C.items():
            roles_html+=(f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
                         f'<span style="background:{color};color:white;padding:1px 7px;border-radius:3px;font-size:10px;font-weight:bold;min-width:155px;display:inline-block">{rol}</span>'
                         f'</div>')
        st.markdown(roles_html,unsafe_allow_html=True)

        st.markdown("#### 📌 Reglas especiales")
        reglas=[
            "Líderes SECO y FRÍO no comparten DC",
            "MCs DASA no coinciden con Líder DASA",
            "Mínimo 1 MC operando en DASA",
            "Mínimo 7 auxiliares en DASA",
            "Domingo → lunes automático",
        ]
        for r in reglas:
            st.markdown(f'<div class="prem-ok">📌 {r}</div>',unsafe_allow_html=True)

st.caption("Simulador DC · Jun–Jul 2026 · Ciclo 40-40-48h · Auto-scheduler · Solver 3 personas · Premisas editables")
