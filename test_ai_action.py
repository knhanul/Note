import sys
sys.path.insert(0, '.')
from pathlib import Path
from packages.ollama_plugin.ai_prompt_repository import PromptRepository, DEFAULT_ACTION_IDS
from packages.ollama_plugin.ai_prompt_service import PromptService

import tempfile
temp_dir = Path(tempfile.gettempdir()) / 'note2_test_ai'
temp_dir.mkdir(parents=True, exist_ok=True)

service = PromptService(temp_dir)

actions = service.list_actions()
print(f'Actions count: {len(actions)}')

for action in actions:
    if action['action_id'] in DEFAULT_ACTION_IDS:
        print(f"  {action['action_id']}: readonly={action['readonly']}, use_rag={action['use_rag']}, source_type={action['source_type']}")

new_action = service.create_action({
    'name': 'Test Action',
    'description': 'Test description',
    'category': 'test'
})
print(f'Created action: {new_action["action_id"]}')

retrieved = service.get_action(new_action['action_id'])
print(f'Retrieved: {retrieved["name"]}')

updated = service.update_action(new_action['action_id'], {'name': 'Updated Test'})
print(f'Updated: {updated["name"]}')

service.move_action_down('summarize_note')
print('Move action down OK')

service.set_binding(new_action['action_id'], 'summarize_note')
print(f'Binding set: {service.get_action(new_action["action_id"])["binding_prompt_doc_id"]}')

print('All tests passed!')
