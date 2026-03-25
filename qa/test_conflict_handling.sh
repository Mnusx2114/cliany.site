#!/bin/bash
PASS=0
FAIL=0

test_json_mode_auto_rename_preserved() {
  rm -rf ~/.cliany-site/adapters/qa-conflict.example/ 2>/dev/null || true
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json
domain = 'qa-conflict.example'
page = PageInfo(url=f'https://{domain}', title='QA')

merger = AdapterMerger(domain)

cmd1 = CommandSuggestion(name='search', description='搜索v1', args=[], action_steps=[0])
a1 = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Search', target_role='button')
r1 = ExploreResult(pages=[page], commands=[cmd1], actions=[a1])
merger.merge(r1, json_mode=True)

cmd2 = CommandSuggestion(name='search', description='搜索v2', args=[], action_steps=[0])
a2 = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Go', target_role='button')
r2 = ExploreResult(pages=[page], commands=[cmd2], actions=[a2])
result = merger.merge(r2, json_mode=True)

meta = json.load(open(merger.metadata_path))
names = [c['name'] for c in meta['commands']]
print(f'commands={names}, conflicts_resolved={result.conflicts_resolved}')
assert 'search' in names, 'Original search missing'
assert 'search-2' in names, 'Renamed search-2 missing'
assert len(result.conflicts_resolved) == 1
assert result.conflicts_resolved[0]['action'] == 'renamed'
assert result.conflicts_resolved[0]['final_name'] == 'search-2'
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] json_mode=True 冲突自动重命名保留不变: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] json_mode=True 冲突自动重命名失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_cascade_rename() {
  rm -rf ~/.cliany-site/adapters/qa-conflict.example/ 2>/dev/null || true
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json
domain = 'qa-conflict.example'
page = PageInfo(url=f'https://{domain}', title='QA')
merger = AdapterMerger(domain)

def make_result(name, desc):
    cmd = CommandSuggestion(name=name, description=desc, args=[], action_steps=[0])
    a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name=name, target_role='button')
    return ExploreResult(pages=[page], commands=[cmd], actions=[a])

merger.merge(make_result('search', 'v1'), json_mode=True)
merger.merge(make_result('search', 'v2'), json_mode=True)
result = merger.merge(make_result('search', 'v3'), json_mode=True)

meta = json.load(open(merger.metadata_path))
names = [c['name'] for c in meta['commands']]
print(f'commands={names}')
assert 'search' in names, 'Original search missing'
assert 'search-2' in names, 'search-2 missing'
assert 'search-3' in names, 'search-3 missing (cascade rename failed)'
assert result.conflicts_resolved[0]['final_name'] == 'search-3'
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 级联重命名 search→search-2→search-3: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 级联重命名失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_conflicts_resolved_action_types() {
  rm -rf ~/.cliany-site/adapters/qa-conflict.example/ 2>/dev/null || true
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json
domain = 'qa-conflict.example'
page = PageInfo(url=f'https://{domain}', title='QA')
merger = AdapterMerger(domain)

cmd1 = CommandSuggestion(name='search', description='搜索v1', args=[], action_steps=[0])
a1 = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Search', target_role='button')
r1 = ExploreResult(pages=[page], commands=[cmd1], actions=[a1])
merger.merge(r1, json_mode=True)

cmd2 = CommandSuggestion(name='search', description='搜索v2', args=[], action_steps=[0])
a2 = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Go', target_role='button')
r2 = ExploreResult(pages=[page], commands=[cmd2], actions=[a2])
result = merger.merge(r2, json_mode=True)

resolved = result.conflicts_resolved
assert len(resolved) == 1, f'Expected 1 resolution, got {len(resolved)}'
r = resolved[0]
assert 'original_name' in r, 'Missing original_name key'
assert 'action' in r, 'Missing action key'
assert 'final_name' in r, 'Missing final_name key'
assert r['action'] in ('renamed', 'overwritten', 'kept_existing'), f'Unknown action: {r[\"action\"]}'
print(f'conflicts_resolved structure valid: {resolved}')
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] conflicts_resolved 包含正确的 action 类型和字段: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] conflicts_resolved 结构验证失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_interactive_mode_code_path_exists() {
  OUTPUT=$(uv run python3 -c "
import inspect
from cliany_site.codegen.merger import AdapterMerger
src = inspect.getsource(AdapterMerger.merge)
assert 'json_mode' in src, 'json_mode parameter missing'
assert 'not json_mode' in src or 'elif' in src, 'No interactive branch found'
assert 'click.prompt' in src, 'click.prompt not found in merge()'
assert 'click.Choice' in src, 'click.Choice not found'
assert 'overwritten' in src, 'overwritten action type missing'
assert 'kept_existing' in src, 'kept_existing action type missing'
print('Interactive mode code path: FOUND')
" 2>&1)
  if echo "$OUTPUT" | grep -q "FOUND"; then
    echo "[PASS] 交互式冲突解决代码路径存在"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 交互式冲突解决代码路径缺失: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_cleanup() {
  rm -rf ~/.cliany-site/adapters/qa-conflict.example/ 2>/dev/null
  echo "[PASS] 清理测试数据"
  PASS=$((PASS+1))
}

echo "Running conflict handling tests..."
test_json_mode_auto_rename_preserved
test_cascade_rename
test_conflicts_resolved_action_types
test_interactive_mode_code_path_exists
test_cleanup

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
