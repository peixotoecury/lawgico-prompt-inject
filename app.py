"""
LAWgico Prompt Inject — Detecção de Prompt Injection + Análise de Risco
Peixoto & Cury Advogados · Controladoria Time B
"""
import os
import datetime
import streamlit as st

from modules.extractor   import extrair_texto
from modules.static_scan import scan_estatico
from modules.ai_analyzer import analisar_com_ia, risco_combinado
from modules.report_gen  import gerar_excel

# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LAWgico Prompt Inject",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

_key = os.environ.get("ANTHROPIC_API_KEY", "")

RISCO_ORDEM = {'CRÍTICO': 4, 'ALTO': 3, 'MÉDIO': 2, 'LIMPO': 1, '—': 0}

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;}

section[data-testid="stSidebar"]{
  background:linear-gradient(160deg,#001e36 0%,#003B5C 100%)!important;
  border-right:none;}
section[data-testid="stSidebar"] *{color:#fff!important;}
section[data-testid="stSidebar"] label{
  color:rgba(255,255,255,.7)!important;font-size:10px!important;
  font-weight:700!important;text-transform:uppercase!important;letter-spacing:.7px!important;}
section[data-testid="stSidebar"] .stSelectbox>div>div,
section[data-testid="stSidebar"] input{
  background:rgba(255,255,255,.1)!important;
  border:1px solid rgba(0,169,224,.4)!important;color:#fff!important;border-radius:6px!important;}
/* Botão de upload visível na sidebar */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button *,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small{
  color:#001e36!important;background:#00A9E0!important;border-radius:6px!important;}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{
  background:rgba(255,255,255,.08)!important;border:1px dashed rgba(0,169,224,.5)!important;
  border-radius:8px!important;}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span{
  color:rgba(255,255,255,.6)!important;}

.hdr{background:linear-gradient(135deg,#001e36 0%,#003B5C 100%);
  box-shadow:0 2px 8px rgba(0,0,0,.3);padding:10px 24px;
  display:flex;align-items:center;gap:14px;
  margin:0 -5rem 20px -5rem;padding-left:5.5rem;padding-right:2rem;}
.hdr-div{width:1px;height:40px;background:rgba(255,255,255,.15);}
.hdr-info h1{font-size:15px;font-weight:700;color:#fff;margin:0;}
.hdr-info .sub{font-size:10px;color:#90c8e0;margin-top:2px;}
.hdr-right{margin-left:auto;display:flex;align-items:center;gap:8px;}
.badge{font-size:10px;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:.3px;}
.badge-ia{background:rgba(0,169,224,.2);border:1px solid #00A9E0;color:#00A9E0;}
.badge-pc{background:rgba(255,255,255,.1);color:#fff;}

/* KPIs */
.kpi{background:#fff;border:1px solid rgba(0,59,92,.1);border-radius:10px;
  padding:14px 16px;border-left:4px solid #00A9E0;box-shadow:0 1px 4px rgba(0,59,92,.06);}
.kpi .lbl{font-size:9px;text-transform:uppercase;letter-spacing:.6px;font-weight:700;color:#6B7F93;}
.kpi .val{font-size:22px;font-weight:800;color:#003B5C;margin-top:4px;}
.kpi.critico{border-left-color:#DC2626;} .kpi.critico .val{color:#991B1B;}
.kpi.alto{border-left-color:#F59E0B;} .kpi.alto .val{color:#92400E;}
.kpi.revisar{border-left-color:#F97316;} .kpi.revisar .val{color:#7C2D12;}
.kpi.risco{border-left-color:#EF4444;} .kpi.risco .val{color:#7F1D1D;}

/* Badges */
.rb{display:inline-block;font-size:10px;font-weight:700;padding:2px 10px;border-radius:8px;letter-spacing:.3px;}
.rb-critico{background:#7F1D1D;color:#fff;}
.rb-alto{background:#FEE2E2;color:#991B1B;}
.rb-medio{background:#FEF9C3;color:#713F12;}
.rb-limpo{background:#D1FAE5;color:#065F46;}
.rb-1{background:#D1FAE5;color:#065F46;}
.rb-2{background:#A7F3D0;color:#065F46;}
.rb-3{background:#FEF9C3;color:#713F12;}
.rb-4{background:#FEE2E2;color:#991B1B;}
.rb-5{background:#FCA5A5;color:#7F1D1D;}

/* Tabela */
.tbl{width:100%;border-collapse:collapse;font-size:12px;}
.tbl thead tr{background:linear-gradient(135deg,#001e36,#003B5C);color:#fff;}
.tbl thead th{padding:9px 12px;text-align:left;font-size:10px;
  text-transform:uppercase;letter-spacing:.5px;white-space:nowrap;}
.tbl tbody td{padding:8px 12px;border-bottom:1px solid rgba(0,59,92,.07);
  color:#17324D;vertical-align:middle;}
.tbl tbody tr:hover td{background:rgba(0,169,224,.04);}
.tbl td.mono{font-family:monospace;font-size:11px;color:#991B1B;word-break:break-all;}

/* Card de achado */
.achado-card{background:#fff;border:1px solid rgba(0,59,92,.1);border-radius:8px;
  padding:12px 16px;margin-bottom:10px;}
.achado-card.critico{border-left:4px solid #DC2626;}
.achado-card.alto{border-left:4px solid #F59E0B;}
.achado-card.medio{border-left:4px solid #FCD34D;}
.achado-card .trecho{background:#FFF5F5;border:1px solid #FECACA;border-radius:6px;
  padding:8px 10px;font-family:monospace;font-size:11px;color:#991B1B;
  margin-top:8px;word-break:break-all;}
.conf-alta{color:#065F46;font-weight:700;}
.conf-media{color:#713F12;font-weight:700;}
.conf-baixa{color:#6B7F93;font-weight:600;}

/* Aviso */
.aviso-revisao{background:#FEF3C7;border:1px solid #FCD34D;border-radius:8px;
  padding:10px 16px;font-size:12px;color:#713F12;margin-bottom:12px;}

/* Remove padding topo Streamlit — seletores abrangentes */
[data-testid*="Block"]{padding-top:0!important;}
[class*="block-container"]{padding-top:0!important;}
[class*="BlockContainer"]{padding-top:0!important;}
section[data-testid="stMain"]{padding-top:0!important;}
section[data-testid="stMain"] > div{padding-top:0!important;}
section[data-testid="stMain"] > div > div{padding-top:0!important;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.components.v1.html("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
      html,body{margin:0;padding:0;background:#001e36;}
      .logo-wrap{font-family:'Inter',Arial,sans-serif;padding:14px 16px 12px;border-bottom:1px solid rgba(0,169,224,.2);}
      .logo-rel{position:relative;display:inline-block;line-height:1;}
      .logo-main{font-size:40px;font-weight:900;color:#fff;letter-spacing:-2px;line-height:1;display:block;}
      .logo-tag{position:absolute;top:-13px;right:0;font-size:9px;font-weight:700;color:#fff;letter-spacing:2px;white-space:nowrap;}
      .logo-sub{font-size:8px;font-weight:700;color:#fff;letter-spacing:3px;text-transform:lowercase;margin-top:5px;}
      .logo-firm{font-size:8px;color:rgba(255,255,255,.4);margin-top:3px;}
    </style>
    <div class="logo-wrap">
      <div class="logo-rel">
        <span class="logo-tag">prompt inject</span>
        <span class="logo-main">LAWgico</span>
      </div>
      <div class="logo-sub">lawyers at work</div>
      <div class="logo-firm">Peixoto &amp; Cury Advogados</div>
    </div>
    """, height=110, scrolling=False)
    if _key:
        st.markdown('<div style="font-size:11px;color:#10b981;margin-top:6px;">✅ IA configurada</div>',
                    unsafe_allow_html=True)
    else:
        api_key_in = st.text_input("Chave Anthropic", type="password")
        if api_key_in:
            os.environ["ANTHROPIC_API_KEY"] = api_key_in
            _key = api_key_in

    st.markdown("---")
    st.markdown("**ANÁLISE**")

    cliente = st.text_input("Cliente (opcional)", placeholder="ex: Telefônica, Bridgestone...")

    modo = st.selectbox("Modo de análise", ["completo", "injection", "risco"],
        format_func=lambda x: {
            "completo":  "🔍 Completo (Injection + Risco)",
            "injection": "🛡️ Só Prompt Injection",
            "risco":     "⚖️ Só Análise de Risco",
        }[x])

    st.markdown("---")
    st.markdown("**UPLOAD**")
    pdfs = st.file_uploader(
        "PDFs (qualquer peça processual)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Petições iniciais, sentenças, laudos, contestações...",
    )

    st.markdown("---")

    analisar = st.button("🔍 Analisar documentos", type="primary",
                         disabled=(not pdfs or not _key),
                         use_container_width=True)

    if not _key:
        st.markdown('<div style="font-size:10px;color:#F87171;">Configure a chave Anthropic acima.</div>',
                    unsafe_allow_html=True)
    if not pdfs:
        st.markdown('<div style="font-size:10px;color:rgba(255,255,255,.4);">Faça upload de PDFs para começar.</div>',
                    unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:10px;color:rgba(255,255,255,.3);text-align:center;margin-top:8px;">'
        'v1.0 · Jun/2026<br>Claude Opus · Scan Estático + IA</div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
hoje_str = datetime.date.today().strftime("%A, %d de %B de %Y")
st.markdown(f"""
<div class="hdr">
  <img src="https://www.peixotoecury.com.br/assets/images/ui/logo-light.png"
       style="height:38px;flex-shrink:0;"/>
  <div class="hdr-div"></div>
  <div class="hdr-info">
    <h1>Prompt Inject — Análise de Documentos</h1>
    <div class="sub">{hoje_str} &nbsp;·&nbsp; Peixoto &amp; Cury Advogados</div>
  </div>
  <div class="hdr-right">
    <span class="badge badge-ia">IA Claude Opus</span>
    <span class="badge badge-pc">P&amp;C</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ESTADO
# ─────────────────────────────────────────────
if "resultados" not in st.session_state:
    st.session_state.resultados = []

resultados = st.session_state.resultados


# ─────────────────────────────────────────────
# ANÁLISE
# ─────────────────────────────────────────────
if analisar and pdfs and _key:
    st.session_state.resultados = []
    resultados = []

    prog_bar = st.progress(0, text="Iniciando análise...")
    status_box = st.empty()
    n = len(pdfs)

    for idx, pdf_file in enumerate(pdfs):
        fname = pdf_file.name
        status_box.info(f"📄 [{idx+1}/{n}] **{fname}** — extraindo texto...")

        file_bytes = pdf_file.read()

        # 1 — Extração
        ext = extrair_texto(file_bytes, fname)

        if ext["ilegivel"]:
            resultados.append({
                "filename": fname,
                "static": {"achados": [], "risco_injection": "LIMPO", "n_achados": 0},
                "ia": {"injection": {"detectada": False, "risco": "LIMPO",
                                     "confianca": "Baixa", "achados": []},
                       "agressividade": {"nivel": 0, "confianca": "Baixa",
                                         "justificativa": "PDF ilegível ou sem texto",
                                         "valor_estimado": 0, "verbas_pedidas": [],
                                         "teses_juridicas": [], "pontos_atencao": [],
                                         "resumo": "PDF não contém texto extraível (pode ser escaneado)."},
                       "observacoes": ext.get("aviso", "PDF ilegível")},
                "risco_final": {"risco": "LIMPO", "confianca": "Baixa",
                                "requer_revisao": False, "concordam": True},
            })
            prog_bar.progress((idx+1)/n, text=f"[{idx+1}/{n}] {fname} — ilegível, pulado")
            continue

        # 2 — Scan estático
        status_box.info(f"🔎 [{idx+1}/{n}] **{fname}** — scan estático...")
        stat = scan_estatico(ext["texto"], fname)

        # 3 — Análise IA
        status_box.info(f"🤖 [{idx+1}/{n}] **{fname}** — analisando com IA (pode demorar ~30s)...")
        try:
            ia_result = analisar_com_ia(
                texto=ext["texto"],
                filename=fname,
                static_result=stat,
                api_key=_key,
                modo=modo,
            )
        except Exception as e:
            ia_result = {
                "filename": fname,
                "erro": str(e),
                "injection": {"detectada": False, "risco": "LIMPO", "confianca": "Baixa", "achados": []},
                "agressividade": {"nivel": 0, "confianca": "Baixa",
                                  "justificativa": f"Erro IA: {e}",
                                  "valor_estimado": 0, "verbas_pedidas": [],
                                  "teses_juridicas": [], "pontos_atencao": [],
                                  "resumo": f"Erro ao analisar: {e}"},
                "observacoes": f"Erro: {e}",
            }

        # 4 — Risco combinado
        stat_risco = stat.get("risco_injection", "LIMPO")
        ia_risco   = ia_result.get("injection", {}).get("risco", "LIMPO")
        ia_conf    = ia_result.get("injection", {}).get("confianca", "Baixa")
        rc = risco_combinado(stat_risco, ia_risco, ia_conf)

        resultados.append({
            "filename": fname,
            "static": stat,
            "ia": ia_result,
            "risco_final": rc,
        })

        prog_bar.progress((idx+1)/n, text=f"[{idx+1}/{n}] {fname} — {rc['risco']}")

    st.session_state.resultados = resultados
    status_box.success(f"✅ {n} documento(s) analisado(s).")
    prog_bar.progress(1.0, text="Concluído!")


# ─────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────
if not resultados:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#6B7F93;">
      <div style="font-size:48px;margin-bottom:16px;">🔍</div>
      <div style="font-size:16px;font-weight:600;color:#003B5C;margin-bottom:8px;">
        LAWgico Prompt Inject</div>
      <div style="font-size:13px;margin-bottom:6px;">
        Faça upload de PDFs de petições iniciais na barra lateral e clique em <strong>Analisar documentos</strong>.</div>
      <div style="font-size:12px;color:#9DB3C0;">
        O sistema faz scan estático + análise com Claude Opus.<br>
        Cada documento recebe score de injection e nível de agressividade com citação obrigatória de trecho.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── KPIs ──
total    = len(resultados)
critico  = sum(1 for r in resultados if r.get("risco_final", {}).get("risco") == "CRÍTICO")
alto     = sum(1 for r in resultados if r.get("risco_final", {}).get("risco") == "ALTO")
revisar  = sum(1 for r in resultados if r.get("risco_final", {}).get("requer_revisao"))
n4_5     = sum(1 for r in resultados if r.get("ia", {}).get("agressividade", {}).get("nivel", 0) >= 4)
n_inject = sum(1 for r in resultados if r.get("risco_final", {}).get("risco") not in ("LIMPO", None))

c1, c2, c3, c4, c5 = st.columns(5)
for col, val, lbl, cls in [
    (c1, total,    "Documentos",         ""),
    (c2, critico,  "Injection CRÍTICO",  "critico"),
    (c3, alto,     "Injection ALTO",     "alto"),
    (c4, revisar,  "Fila de Revisão",    "revisar"),
    (c5, n4_5,     "Agressividade N4-5", "risco"),
]:
    col.markdown(f'<div class="kpi {cls}"><div class="lbl">{lbl}</div>'
                 f'<div class="val">{val}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


def risco_badge(r):
    cls = {'CRÍTICO': 'critico', 'ALTO': 'alto', 'MÉDIO': 'medio', 'LIMPO': 'limpo'}.get(r, 'limpo')
    return f'<span class="rb rb-{cls}">{r}</span>'

def nivel_badge(n):
    return f'<span class="rb rb-{n}">N{n}</span>' if n else '<span style="color:#9DB3C0;">—</span>'

def conf_cls(c):
    return {'Alta': 'conf-alta', 'Média': 'conf-media', 'Baixa': 'conf-baixa'}.get(c, 'conf-baixa')


# ── Tabs ──
tab_visao, tab_proc, tab_inject, tab_rev, tab_rel = st.tabs([
    "📊 Visão Geral",
    "📋 Processos",
    f"🔴 Injeções ({n_inject})",
    f"🟡 Revisar ({revisar})",
    "📄 Relatório",
])


# ── TAB 1: VISÃO GERAL ──
with tab_visao:
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("**Distribuição por Risco de Injection**")
        contagem = {}
        for r in resultados:
            risco = r.get("risco_final", {}).get("risco", "LIMPO")
            contagem[risco] = contagem.get(risco, 0) + 1

        ordem = ["CRÍTICO", "ALTO", "MÉDIO", "LIMPO"]
        cores  = {"CRÍTICO": "#DC2626", "ALTO": "#F59E0B", "MÉDIO": "#FCD34D", "LIMPO": "#34D399"}
        for nivel in ordem:
            cnt = contagem.get(nivel, 0)
            pct = int(cnt / total * 100) if total else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
                f'{risco_badge(nivel)}'
                f'<div style="flex:1;background:#F1F7FA;border-radius:4px;height:18px;">'
                f'<div style="background:{cores[nivel]};height:18px;border-radius:4px;width:{pct}%;'
                f'display:flex;align-items:center;padding-left:8px;">'
                f'<span style="font-size:10px;color:#fff;font-weight:700;">{cnt}</span></div></div>'
                f'<span style="font-size:11px;color:#6B7F93;width:30px;text-align:right;">{pct}%</span>'
                f'</div>', unsafe_allow_html=True)

    with col_r:
        st.markdown("**Distribuição por Nível de Agressividade**")
        niv_cnt = {}
        for r in resultados:
            n = r.get("ia", {}).get("agressividade", {}).get("nivel", 0)
            if n: niv_cnt[n] = niv_cnt.get(n, 0) + 1

        niv_cores = {1:"#34D399",2:"#6EE7B7",3:"#FCD34D",4:"#F87171",5:"#DC2626"}
        niv_labs  = {1:"Branda",2:"Leve",3:"Moderada",4:"Alta",5:"Extrema"}
        for n in range(5, 0, -1):
            cnt = niv_cnt.get(n, 0)
            pct = int(cnt / total * 100) if total else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
                f'{nivel_badge(n)}'
                f'<span style="font-size:10px;color:#6B7F93;width:60px;">{niv_labs[n]}</span>'
                f'<div style="flex:1;background:#F1F7FA;border-radius:4px;height:18px;">'
                f'<div style="background:{niv_cores[n]};height:18px;border-radius:4px;width:{pct}%;'
                f'display:flex;align-items:center;padding-left:8px;">'
                f'<span style="font-size:10px;color:#fff;font-weight:700;">{cnt}</span></div></div>'
                f'<span style="font-size:11px;color:#6B7F93;width:30px;text-align:right;">{pct}%</span>'
                f'</div>', unsafe_allow_html=True)


# ── TAB 2: PROCESSOS ──
with tab_proc:
    f_risco = st.selectbox("Filtrar por injection",
                           ["Todos", "CRÍTICO", "ALTO", "MÉDIO", "LIMPO"], key="f_risco")
    f_nivel = st.selectbox("Filtrar por nível",
                           ["Todos", "5", "4", "3", "2", "1"], key="f_nivel")

    filtrados = resultados
    if f_risco != "Todos":
        filtrados = [r for r in filtrados if r.get("risco_final", {}).get("risco") == f_risco]
    if f_nivel != "Todos":
        filtrados = [r for r in filtrados
                     if str(r.get("ia", {}).get("agressividade", {}).get("nivel", "")) == f_nivel]

    filtrados_sorted = sorted(filtrados,
        key=lambda r: (RISCO_ORDEM.get(r.get("risco_final",{}).get("risco",""), 0),
                       r.get("ia",{}).get("agressividade",{}).get("nivel", 0)),
        reverse=True)

    rows_html = ""
    for r in filtrados_sorted:
        rf   = r.get("risco_final", {})
        ia   = r.get("ia", {})
        agr  = ia.get("agressividade", {})
        risco = rf.get("risco", "—")
        niv   = agr.get("nivel", 0)
        val   = agr.get("valor_estimado", 0)
        val_s = f'R$ {val:,.2f}'.replace(',','X').replace('.',',').replace('X','.') if val else '—'
        rev   = "⚠️ Revisar" if rf.get("requer_revisao") else ""
        resumo = (agr.get("resumo") or ia.get("observacoes", "—") or "—")[:120]

        rows_html += f"""<tr>
          <td style="max-width:220px;word-break:break-word;">{r.get('filename','')}</td>
          <td>{risco_badge(risco)}</td>
          <td><span class="{conf_cls(rf.get('confianca',''))}">{rf.get('confianca','—')}</span></td>
          <td>{nivel_badge(niv)}</td>
          <td style="text-align:right;font-variant-numeric:tabular-nums;">{val_s}</td>
          <td style="color:#F59E0B;font-size:10px;">{rev}</td>
          <td style="color:#5B7A8E;font-style:italic;font-size:11px;">{resumo}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="tbl">
      <thead><tr>
        <th>Arquivo</th><th>Injection</th><th>Confiança</th>
        <th>Nível</th><th style="text-align:right">Valor Est.</th>
        <th></th><th>Resumo</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>
    """, unsafe_allow_html=True)


# ── TAB 3: INJEÇÕES ──
with tab_inject:
    inject_list = [r for r in resultados
                   if r.get("risco_final", {}).get("risco") not in ("LIMPO", None)]
    inject_list.sort(key=lambda r: RISCO_ORDEM.get(r.get("risco_final",{}).get("risco",""), 0),
                     reverse=True)

    if not inject_list:
        st.success("✅ Nenhuma injeção detectada nos documentos analisados.")
    else:
        for r in inject_list:
            rf  = r.get("risco_final", {})
            ia  = r.get("ia", {})
            agr = ia.get("agressividade", {})
            inj = ia.get("injection", {})
            risco = rf.get("risco", "—")
            css_cls = {'CRÍTICO':'critico','ALTO':'alto','MÉDIO':'medio'}.get(risco,'medio')

            # Agrega achados estático + IA (sem duplicar)
            achados_stat = r.get("static", {}).get("achados", [])
            achados_ia   = inj.get("achados", [])

            with st.expander(
                f"{'🔴' if risco=='CRÍTICO' else '🟠' if risco=='ALTO' else '🟡'} "
                f"**{r.get('filename','')}** — {risco_badge(risco)} "
                f'<span class="{conf_cls(rf.get("confianca",""))}"> · Confiança {rf.get("confianca","—")}</span>',
                expanded=(risco == "CRÍTICO")
            ):
                if rf.get("requer_revisao"):
                    st.markdown(
                        '<div class="aviso-revisao">⚠️ <strong>Requer revisão manual</strong> antes de usar este documento em análise IA.</div>',
                        unsafe_allow_html=True)

                if not rf.get("concordam", True):
                    st.warning("Scan estático e IA divergiram neste documento — revise manualmente.")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Injection**")
                    st.markdown(f"- Risco final: {risco_badge(risco)}", unsafe_allow_html=True)
                    st.markdown(f"- Confiança: **{rf.get('confianca','—')}**")
                    st.markdown(f"- Scan estático: {risco_badge(rf.get('static_risco','LIMPO'))}", unsafe_allow_html=True)
                    st.markdown(f"- Análise IA: {risco_badge(rf.get('ia_risco','LIMPO'))}", unsafe_allow_html=True)
                with col_b:
                    niv = agr.get("nivel", 0)
                    st.markdown(f"**Agressividade**")
                    st.markdown(f"- Nível: {nivel_badge(niv)}", unsafe_allow_html=True)
                    val = agr.get("valor_estimado", 0)
                    if val:
                        st.markdown(f'- Valor estimado: **R$ {val:,.2f}**'.replace(',','X').replace('.',',').replace('X','.'))

                st.markdown("**Achados detalhados:**")
                for achado in (achados_stat + achados_ia):
                    a_css = {'CRÍTICO':'critico','ALTO':'alto','MÉDIO':'medio'}.get(
                        achado.get('risco',''), 'medio')
                    trecho = str(achado.get("trecho","—"))
                    st.markdown(f"""
                    <div class="achado-card {a_css}">
                      <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;">
                        {risco_badge(achado.get('risco','—'))}
                        <strong style="font-size:12px;">{achado.get('tipo','—').replace('_',' ').title()}</strong>
                        <span class="{conf_cls(achado.get('confianca',''))}">
                          · Confiança {achado.get('confianca','—')}</span>
                      </div>
                      <div style="font-size:12px;color:#5B7A8E;">{achado.get('descricao','—')}</div>
                      {"<div class='trecho'>" + trecho[:400] + "</div>" if trecho != '—' else ""}
                    </div>
                    """, unsafe_allow_html=True)


# ── TAB 4: REVISAR ──
with tab_rev:
    revisar_list = [r for r in resultados if r.get("risco_final", {}).get("requer_revisao")]

    if not revisar_list:
        st.success("✅ Nenhum documento na fila de revisão.")
    else:
        st.markdown(f"**{len(revisar_list)} documento(s) aguardam revisão manual.**")
        st.markdown("Estes documentos tiveram resultado inconclusivo ou discordância entre scan estático e IA.")

        for r in revisar_list:
            rf   = r.get("risco_final", {})
            ia   = r.get("ia", {})
            agr  = ia.get("agressividade", {})
            risco = rf.get("risco","—")

            motivo = "Discordância entre scan estático e IA" if not rf.get("concordam", True) \
                else f"Risco {risco} requer confirmação humana"

            with st.expander(f"📋 **{r.get('filename','')}** — {motivo}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"- Risco injection: {risco_badge(risco)}", unsafe_allow_html=True)
                    st.markdown(f"- Confiança IA: **{rf.get('confianca','—')}**")
                    st.markdown(f"- Scan estático: {risco_badge(rf.get('static_risco','LIMPO'))}", unsafe_allow_html=True)
                    st.markdown(f"- IA: {risco_badge(rf.get('ia_risco','LIMPO'))}", unsafe_allow_html=True)
                with col_b:
                    niv = agr.get("nivel", 0)
                    st.markdown(f"- Nível agressividade: {nivel_badge(niv)}", unsafe_allow_html=True)
                    obs = ia.get("observacoes","")
                    if obs:
                        st.markdown(f"- Observação: _{obs}_")

                achados = r.get("static", {}).get("achados", []) + \
                          ia.get("injection", {}).get("achados", [])
                for ach in achados[:3]:
                    st.markdown(
                        f'<div class="achado-card medio">'
                        f'<strong>{ach.get("tipo","—").replace("_"," ").title()}</strong>'
                        f'<div class="trecho">{str(ach.get("trecho","—"))[:300]}</div>'
                        f'</div>', unsafe_allow_html=True)


# ── TAB 5: RELATÓRIO ──
with tab_rel:
    st.markdown("**Exportar relatório completo**")
    st.markdown("O Excel contém 3 abas: Resumo geral · Injeções detalhadas · Análise de risco jurídico")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📊 Gerar Excel", type="primary", use_container_width=True):
            with st.spinner("Gerando Excel..."):
                xls = gerar_excel(resultados, cliente=cliente)
            nome = f"LAWgico_PromptInject_{cliente or 'Geral'}_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
            st.download_button("⬇️ Baixar Excel", data=xls, file_name=nome,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

    with col_b:
        # Resumo rápido para copiar no Teams
        resumo_lines = [f"📌 **LAWgico Prompt Inject — {cliente or 'Análise'}**\n"]
        resumo_lines.append(f"📄 {total} documentos analisados · {datetime.date.today().strftime('%d/%m/%Y')}\n")
        if critico:  resumo_lines.append(f"🔴 {critico} injection CRÍTICO")
        if alto:     resumo_lines.append(f"🟠 {alto} injection ALTO")
        if n4_5:     resumo_lines.append(f"⚖️ {n4_5} processos nível 4-5")
        if revisar:  resumo_lines.append(f"⚠️ {revisar} para revisão manual")
        if not critico and not alto: resumo_lines.append("✅ Nenhum injection de alto risco detectado")

        resumo_text = "\n".join(resumo_lines)
        st.text_area("Resumo para Teams / e-mail", value=resumo_text, height=160)

