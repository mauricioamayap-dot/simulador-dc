# SIMULADOR DC — Streamlit

## OPCIÓN A: Desplegar en Streamlit Cloud (GRATIS, sin instalar nada)

1. Crea cuenta gratuita en https://streamlit.io
2. Ve a "New app" → "From existing repo" 
3. Sube `simulador_dc.py` y `requirements.txt` a GitHub
4. Conecta el repo → Deploy
5. ¡Listo! Tienes una URL pública que cualquiera puede usar

---

## OPCIÓN B: Ejecutar en tu computador

### Requisitos
- Python 3.9+

### Pasos
```bash
# 1. Instalar dependencias
pip install streamlit pandas

# 2. Ejecutar
streamlit run simulador_dc.py
```
Se abre automáticamente en http://localhost:8501

---

## CÓMO FUNCIONA

1. Selecciona el equipo en el panel izquierdo (L1 SECO, L2 SECO, DASA, etc.)
2. Escoge la persona a simular
3. Cambia la fecha del 1er DC con el calendario
4. Clic en ✅ Aplicar
5. El calendario y el semáforo OPERANDO se actualizan al instante

## PREMISAS ACTIVAS
- Ciclo: +8d / +8d / +15d / +8d / +8d
- Domingo → se mueve al lunes automáticamente
- Mínimo operando por equipo:
  - Lotes SECO: 27 personas
  - DASA Frío: 28 personas  
  - Facturación/Inventarios: 6 personas
  - Devolutivos: 9 personas
- Alertas en rojo si se viola alguna premisa
