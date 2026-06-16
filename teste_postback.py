"""
Script para testar o PostBack da Sonhar Digital localmente.
Execute: python teste_postback.py
"""
import requests
import json

BASE_URL = 'http://localhost:5000'
POSTBACK_KEY = 'aeb82267e3b25c1d2debe5b4eaf64337'

# ── TESTE 1: Novo pedido chegando da Sonhar Digital ──
print('\n🧪 TESTE 1 — Novo pedido via PostBack')
payload_novo = {
    "id": "SD-001234",
    "status": "aprovado",
    "nome": "Maria Fernanda Silva",
    "cpf": "123.456.789-00",
    "telefone": "(34) 9.9234-5678",
    "email": "maria@email.com",
    "produto": "Kit Sonhar 3 Meses",
    "valor": 297.00,
    "codigo_rastreio": "",
    "status_rastreio": ""
}
r = requests.post(
    f'{BASE_URL}/postback/sonhar',
    json=payload_novo,
    headers={'X-Postback-Key': POSTBACK_KEY}
)
print(f'Status: {r.status_code}')
print(f'Resposta: {r.json()}')

# ── TESTE 2: Atualização de status ──
print('\n🧪 TESTE 2 — Atualização de status (enviado + rastreio)')
payload_update = {
    "id": "SD-001234",
    "status": "enviado",
    "codigo_rastreio": "BR123456789BR",
    "status_rastreio": "objeto postado"
}
r2 = requests.post(
    f'{BASE_URL}/postback/sonhar',
    json=payload_update,
    headers={'X-Postback-Key': POSTBACK_KEY}
)
print(f'Status: {r2.status_code}')
print(f'Resposta: {r2.json()}')

# ── TESTE 3: Chave inválida ──
print('\n🧪 TESTE 3 — Chave inválida (deve retornar 401)')
r3 = requests.post(
    f'{BASE_URL}/postback/sonhar',
    json=payload_novo,
    headers={'X-Postback-Key': 'chave_errada'}
)
print(f'Status: {r3.status_code}')
print(f'Resposta: {r3.json()}')

# ── TESTE 4: Listar pedidos ──
print('\n🧪 TESTE 4 — Listar pedidos')
r4 = requests.get(f'{BASE_URL}/api/pedidos')
print(f'Status: {r4.status_code}')
print(f'Pedidos: {json.dumps(r4.json(), indent=2, ensure_ascii=False)}')

# ── TESTE 5: Resumo ──
print('\n🧪 TESTE 5 — Resumo do dashboard')
r5 = requests.get(f'{BASE_URL}/api/resumo')
print(f'Status: {r5.status_code}')
print(f'Resumo: {json.dumps(r5.json(), indent=2, ensure_ascii=False)}')

print('\n✅ Testes concluídos!')
