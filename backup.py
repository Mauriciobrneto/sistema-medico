import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'sistema')

BACKUP_DIR = 'backups'
os.makedirs(BACKUP_DIR, exist_ok=True)

data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
arquivo_backup = os.path.join(BACKUP_DIR, f'backup_{DB_NAME}_{data_hora}.sql')

comando = [
    r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe',
    '-h', DB_HOST,
    '-u', DB_USER,
    f'-p{DB_PASSWORD}',
    DB_NAME
]

try:
    with open(arquivo_backup, 'w', encoding='utf-8') as arquivo:
        subprocess.run(comando, stdout=arquivo, check=True)

    print(f'Backup criado com sucesso: {arquivo_backup}')

except Exception as e:
    print(f'Erro ao criar backup: {e}')