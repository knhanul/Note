import sys
sys.path.insert(0, '.')
from pathlib import Path
import tempfile
from packages.ollama_plugin.ai_prompt_service import PromptService

temp_dir = Path(tempfile.gettempdir()) / 'note2_test_ai3'
temp_dir.mkdir(parents=True, exist_ok=True)

service = PromptService(temp_dir)
repo = service.repository
conn = repo._connect()
rows = conn.execute('SELECT * FROM ai_actions').fetchall()
print(f'Count: {len(rows)}')
for row in rows:
    d = dict(row)
    print(f"  {d.get('action_id')}: readonly={d.get('readonly')}, source_type={d.get('source_type')}, use_rag={d.get('use_rag')}")
conn.close()
