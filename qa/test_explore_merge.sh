#!/bin/bash
PASS=0
FAIL=0

test_import_works() {
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
print('import OK')
" 2>&1)
  if echo "$OUTPUT" | grep -q "import OK"; then
    echo "[PASS] AdapterMerger 导入成功"
    PASS=$((PASS+1))
  else
    echo "[FAIL] AdapterMerger 导入失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_explore_py_contains_merger() {
  OUTPUT=$(uv run python3 -c "
import pathlib
src = pathlib.Path('src/cliany_site/commands/explore.py').read_text()
assert 'AdapterMerger' in src, 'AdapterMerger not in explore.py'
assert 'adapter_mode' in src, 'adapter_mode not in explore.py'
assert 'commands_added' in src, 'commands_added not in explore.py'
assert 'commands_total' in src, 'commands_total not in explore.py'
assert 'conflicts_resolved' in src, 'conflicts_resolved not in explore.py'
print('source check OK')
" 2>&1)
  if echo "$OUTPUT" | grep -q "source check OK"; then
    echo "[PASS] explore.py 包含 AdapterMerger 和所有 adapter_mode 字段"
    PASS=$((PASS+1))
  else
    echo "[FAIL] explore.py 源码检查失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_first_creation_via_save_adapter() {
  rm -rf ~/.cliany-site/adapters/qa-explore-merge.example/ 2>/dev/null || true
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.generator import AdapterGenerator, save_adapter
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json

domain = 'qa-explore-merge.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='search', description='搜索', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Search', target_role='button')
explore_result = ExploreResult(pages=[page], commands=[cmd], actions=[a])

gen = AdapterGenerator()
code = gen.generate(explore_result, domain)
adapter_path = save_adapter(domain, code, {'source_url': f'https://{domain}', 'workflow': 'test'}, explore_result=explore_result)

from pathlib import Path
meta = json.loads((Path.home() / '.cliany-site' / 'adapters' / domain / 'metadata.json').read_text())
names = [c['name'] for c in meta['commands']]
assert names == ['search'], f'Expected [search], got {names}'
assert isinstance(meta['commands'][0], dict), 'Expected dict format'
print(f'created OK: {names}')
" 2>&1)
  if echo "$OUTPUT" | grep -q "created OK"; then
    echo "[PASS] 首次 save_adapter 创建 adapter: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 首次 save_adapter 失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_merge_path_appends_commands() {
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json

domain = 'qa-explore-merge.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='login', description='登录', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Login', target_role='button')
explore_result = ExploreResult(pages=[page], commands=[cmd], actions=[a])

merger = AdapterMerger(domain)
merge_result = merger.merge(explore_result, json_mode=True)

meta = json.loads(merger.metadata_path.read_text())
names = [c['name'] for c in meta['commands']]
assert 'search' in names, f'search missing from {names}'
assert 'login' in names, f'login missing from {names}'
assert merge_result.added_count == 1, f'Expected added_count=1, got {merge_result.added_count}'
assert merge_result.total_count == 2, f'Expected total_count=2, got {merge_result.total_count}'
print(f'merged OK: {names}, added={merge_result.added_count}, total={merge_result.total_count}')
" 2>&1)
  if echo "$OUTPUT" | grep -q "merged OK"; then
    echo "[PASS] merge 路径追加新命令并保留旧命令: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] merge 路径追加失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_force_overwrite_via_save_adapter() {
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.generator import AdapterGenerator, save_adapter
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json

domain = 'qa-explore-merge.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='new-only', description='仅新命令', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='New', target_role='button')
explore_result = ExploreResult(pages=[page], commands=[cmd], actions=[a])

gen = AdapterGenerator()
code = gen.generate(explore_result, domain)
adapter_path = save_adapter(domain, code, {'source_url': f'https://{domain}', 'workflow': 'force'}, explore_result=explore_result)

from pathlib import Path
meta = json.loads((Path.home() / '.cliany-site' / 'adapters' / domain / 'metadata.json').read_text())
names = [c['name'] for c in meta['commands']]
assert names == ['new-only'], f'Expected only [new-only] after force overwrite, got {names}'
print(f'force overwrite OK: {names}')
" 2>&1)
  if echo "$OUTPUT" | grep -q "force overwrite OK"; then
    echo "[PASS] 强制覆盖仅保留新命令: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 强制覆盖失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_cleanup() {
  rm -rf ~/.cliany-site/adapters/qa-explore-merge.example/ 2>/dev/null
  echo "[PASS] 清理测试数据"
  PASS=$((PASS+1))
}

echo "Running explore merge integration tests..."
test_import_works
test_explore_py_contains_merger
test_first_creation_via_save_adapter
test_merge_path_appends_commands
test_force_overwrite_via_save_adapter
test_cleanup

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
