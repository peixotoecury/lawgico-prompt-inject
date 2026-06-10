"""
Scan estático de prompt injection — sem IA, rápido.
Detecta padrões conhecidos antes de enviar para Claude.
"""
from __future__ import annotations
import re
import unicodedata

# Caracteres Unicode invisíveis/suspeitos
UNICODE_SUSPEITOS = [
    ('​', 'Zero Width Space'),
    ('‌', 'Zero Width Non-Joiner'),
    ('‍', 'Zero Width Joiner'),
    ('﻿', 'BOM / Zero Width No-Break Space'),
    ('­', 'Soft Hyphen'),
    ('⁠', 'Word Joiner'),
    ('᠎', 'Mongolian Vowel Separator'),
    ('‪', 'Left-to-Right Embedding'),
    ('‫', 'Right-to-Left Embedding'),
    ('‬', 'Pop Directional Formatting'),
    ('‭', 'Left-to-Right Override'),
    ('‮', 'Right-to-Left Override'),
    (' ', 'Line Separator'),
    (' ', 'Paragraph Separator'),
]

# Padrões de injection (regex, tipo, risco)
PADROES_INJECTION = [
    # Resets de instrução em PT-BR
    (r'ignore\s+(as\s+)?(instru[çc][õo]es|tudo|o\s+anterior|previous)', 'reset_instrucoes', 'ALTO'),
    (r'esqueça\s+(tudo|as\s+instru[çc][õo]es|o\s+anterior)', 'reset_instrucoes', 'ALTO'),
    (r'desconsider[ea]\s+(tudo|as\s+instru[çc][õo]es)', 'reset_instrucoes', 'ALTO'),
    (r'novo\s+sistema\s*[:\-\n]', 'reset_sistema', 'ALTO'),
    (r'voc[êe]\s+(agora\s+)?(é|e|será|sera)\s+(um|uma|o|a)\s+\w', 'reset_identidade', 'ALTO'),
    (r'atue\s+como\s+', 'reset_identidade', 'ALTO'),
    (r'finja\s+(que\s+)?(voc[êe]\s+[eé]|ser)\s+', 'reset_identidade', 'ALTO'),
    (r'(roleplay|jailbreak|DAN\s+mode)', 'reset_identidade', 'CRÍTICO'),
    # Marcadores de sistema
    (r'\[SYSTEM\]|\[INSTRUÇÃO\]|\[PROMPT\]|\[ADMIN\]|\[ROOT\]', 'marcador_sistema', 'CRÍTICO'),
    (r'---\s*(NOVA INSTRUÇÃO|SYSTEM|OVERRIDE|RESET)\s*---', 'marcador_sistema', 'CRÍTICO'),
    # Fake JSON / LLM constructs
    (r'\{["\']role["\']\s*:\s*["\']system["\']', 'json_falso', 'CRÍTICO'),
    (r'"instructions"\s*:\s*["\[]', 'json_falso', 'ALTO'),
    (r'"system_prompt"\s*:', 'json_falso', 'ALTO'),
    # Inglês fora de contexto (pode ser injection em processos BR)
    (r'you are now|ignore previous|disregard all|do not follow', 'inject_ingles', 'ALTO'),
    (r'as an AI|as a language model|pretend you are', 'inject_ingles', 'MÉDIO'),
    # Conteúdo completamente fora de contexto
    (r'código de barras[\s\S]{0,100}vencimento\s+\d{2}/\d{2}/\d{4}', 'conteudo_fora_contexto', 'MÉDIO'),
    (r'prezado\s+cliente[\s\S]{0,200}conta\s+deste\s+m[eê]s', 'conteudo_fora_contexto', 'MÉDIO'),
    (r'(nota\s+fiscal|danfe|chave\s+de\s+acesso)\s*\d{44}', 'conteudo_fora_contexto', 'MÉDIO'),
]

# Whitelist PJe — padrões legítimos que NÃO são injection
# Assinaturas digitais, hashes, QR codes e marcadores do sistema PJe
WHITELIST_PJE = [
    re.compile(r'assinado\s+(eletronicamente|digitalmente)', re.IGNORECASE),
    re.compile(r'(sha-?256|sha-?512|md5)\s*:\s*[a-f0-9]{16,}', re.IGNORECASE),
    re.compile(r'código\s+de\s+verificação', re.IGNORECASE),
    re.compile(r'certificado\s+(digital|icp-brasil)', re.IGNORECASE),
    re.compile(r'pje\s*[-–]\s*processo\s+judicial\s+eletr', re.IGNORECASE),
    re.compile(r'chave\s+de\s+assinatura', re.IGNORECASE),
]

def _texto_tem_whitelist_pje(texto: str) -> bool:
    """Retorna True se o documento tem marcadores legítimos de assinatura PJe."""
    return any(p.search(texto) for p in WHITELIST_PJE)

# Sequências de lixo (muitos chars não-alfanuméricos consecutivos)
RE_LIXO = re.compile(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]{8,}')

NIVEL_ORDEM = {'CRÍTICO': 4, 'ALTO': 3, 'MÉDIO': 2, 'BAIXO': 1, 'LIMPO': 0}


def _trecho(texto: str, match: re.Match, janela: int = 120) -> str:
    """Retorna trecho ao redor de um match."""
    s = max(0, match.start() - 40)
    e = min(len(texto), match.end() + janela)
    return repr(texto[s:e])


def scan_estatico(texto: str, filename: str) -> dict:
    """
    Executa varredura estática no texto extraído.
    Retorna dict com achados, risco máximo e resumo.
    """
    achados = []
    risco_max = 'LIMPO'

    # 1 — Unicode invisível
    unicode_encontrados = []
    for char, nome in UNICODE_SUSPEITOS:
        count = texto.count(char)
        if count > 0:
            pos = texto.index(char)
            ctx = repr(texto[max(0, pos-20):pos+20])
            unicode_encontrados.append({'char': repr(char), 'nome': nome, 'count': count, 'contexto': ctx})

    if unicode_encontrados:
        total = sum(u['count'] for u in unicode_encontrados)
        risco = 'CRÍTICO' if total > 10 else 'ALTO' if total > 3 else 'MÉDIO'
        achados.append({
            'tipo': 'unicode_invisivel',
            'risco': risco,
            'confianca': 'Alta',
            'descricao': f'{total} caractere(s) Unicode invisível/suspeito encontrado(s): '
                         + ', '.join(f"{u['nome']} (×{u['count']})" for u in unicode_encontrados),
            'trecho': unicode_encontrados[0]['contexto'],
            'detalhes': unicode_encontrados,
        })
        if NIVEL_ORDEM.get(risco, 0) > NIVEL_ORDEM.get(risco_max, 0):
            risco_max = risco

    # 1.5 — Verifica se documento tem assinaturas PJe legítimas (reduz falsos positivos)
    tem_pje = _texto_tem_whitelist_pje(texto)

    # 2 — Padrões de injeção
    for pattern, tipo, risco in PADROES_INJECTION:
        m = re.search(pattern, texto, re.IGNORECASE | re.MULTILINE)
        if m:
            achados.append({
                'tipo': tipo,
                'risco': risco,
                'confianca': 'Alta',
                'descricao': f'Padrão de injection detectado: {tipo.replace("_", " ")}',
                'trecho': _trecho(texto, m),
            })
            if NIVEL_ORDEM.get(risco, 0) > NIVEL_ORDEM.get(risco_max, 0):
                risco_max = risco

    # 3 — Sequências de lixo
    lixos = RE_LIXO.findall(texto)
    if lixos:
        # Se documento tem PJe, lixo sozinho é mais provável OCR → confiança Baixa
        conf_lixo = 'Baixa' if tem_pje else 'Média'
        risco = 'MÉDIO' if len(lixos) > 2 else 'BAIXO'
        achados.append({
            'tipo': 'sequencia_lixo',
            'risco': risco,
            'confianca': conf_lixo,
            'descricao': f'{len(lixos)} sequência(s) de caracteres suspeita(s) — '
                         + ('provável artefato de OCR/PJe' if tem_pje else 'verificar manualmente'),
            'trecho': repr(lixos[0][:80]),
        })
        if NIVEL_ORDEM.get(risco, 0) > NIVEL_ORDEM.get(risco_max, 0):
            risco_max = risco

    return {
        'filename': filename,
        'achados': achados,
        'risco_injection': risco_max,
        'n_achados': len(achados),
        'requer_revisao_manual': risco_max in ('CRÍTICO', 'ALTO'),
    }
