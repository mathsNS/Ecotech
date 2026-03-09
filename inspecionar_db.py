# realizar debugs/inspecoes no banco por aqui

import sqlite3

conn = sqlite3.connect('ecotech.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# lista todas as tabelas
print("TABELAS NO BANCO:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    nome_tabela = table['name']
    print(f"\ntabela {nome_tabela}")
    
    # conta quantos registros tem
    cursor.execute(f"SELECT COUNT(*) as total FROM {nome_tabela}")
    count = cursor.fetchone()
    print(f"   Registros: {count['total']}")
    
    # mostra estrutura da tabela
    cursor.execute(f"PRAGMA table_info({nome_tabela})")
    colunas = cursor.fetchall()
    print(f"   Colunas: {', '.join([c['name'] for c in colunas])}")

# mostra alguns dados de exemplo
print("\n" + "=" * 50)
print("DADOS DE EXEMPLO:")
print("=" * 50)

# usuarios
print("\nUSUÁRIOS:")
cursor.execute("SELECT id, nome, email, tipo FROM usuario LIMIT 3")
for row in cursor.fetchall():
    print(f"   {row['id'][:8]}... | {row['nome']} | {row['tipo']}")

# dispositivos
print("\nDISPOSITIVOS:")
cursor.execute("SELECT id, nome, marca, modelo, peso_kg FROM dispositivo LIMIT 5")
for row in cursor.fetchall():
    print(f"   {row['id'][:8]}... | {row['nome']} | {row['marca']} {row['modelo']} | {row['peso_kg']}kg")

# solicitacoes
print("\nSOLICITAÇÕES:")
cursor.execute("SELECT id, id_usuario, estado FROM solicitacao_descarte LIMIT 5")
for row in cursor.fetchall():
    user_id = row['id_usuario'] if row['id_usuario'] else 'N/A'
    user_str = user_id[:8] + '...' if len(str(user_id)) > 8 else user_id
    print(f"   {row['id'][:8]}... | Usuario: {user_str} | Estado: {row['estado']}")

# pontos de coleta
print("\nPONTOS DE COLETA:")
cursor.execute("SELECT id, nome, endereco FROM ponto_coleta")
for row in cursor.fetchall():
    print(f"   {row['id'][:8]}... | {row['nome']}")

conn.close()
print("\n" + "=" * 50)
