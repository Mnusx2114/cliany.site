#!/bin/bash
PASS=0
FAIL=0

test_first_merge() {
  rm -rf ~/.cliany-site/adapters/qa-merge.example/ 2>/dev/null || true
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json
domain = 'qa-merge.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='search', description='搜索', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Search', target_role='button')
r = ExploreResult(pages=[page], commands=[cmd], actions=[a])
merger = AdapterMerger(domain)
result = merger.merge(r)
meta = json.load(open(merger.metadata_path))
print(f'commands={len(meta[\"commands\"])}, added={result.added_count}')
assert len(meta['commands']) == 1, f'Expected 1 command, got {len(meta[\"commands\"])}'
assert isinstance(meta['commands'][0], dict), 'Commands should be dicts (extended format)'
assert meta['commands'][0]['name'] == 'search'
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 首次合并创建适配器: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 首次合并失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_append_merge() {
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json
domain = 'qa-merge.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='login', description='登录', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Login', target_role='button')
r = ExploreResult(pages=[page], commands=[cmd], actions=[a])
merger = AdapterMerger(domain)
result = merger.merge(r)
meta = json.load(open(merger.metadata_path))
names = [c['name'] for c in meta['commands']]
print(f'commands={names}, added={result.added_count}')
assert 'search' in names, 'Original search command missing'
assert 'login' in names, 'New login command missing'
assert len(names) == 2
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 追加合并保留旧命令: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 追加合并失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_conflict_auto_rename() {
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
import json
domain = 'qa-merge.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='search', description='搜索v2', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Go', target_role='button')
r = ExploreResult(pages=[page], commands=[cmd], actions=[a])
merger = AdapterMerger(domain)
result = merger.merge(r, json_mode=True)
meta = json.load(open(merger.metadata_path))
names = [c['name'] for c in meta['commands']]
print(f'commands={names}, conflicts_resolved={result.conflicts_resolved}')
assert 'search' in names, 'Original search missing'
assert 'search-2' in names, 'Renamed search-2 missing'
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 冲突自动重命名: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 冲突自动重命名失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_commands_py_loadable() {
  OUTPUT=$(uv run python3 -c "
import importlib.util, os
adapter_dir = os.path.expanduser('~/.cliany-site/adapters/qa-merge.example')
spec = importlib.util.spec_from_file_location('commands', os.path.join(adapter_dir, 'commands.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('commands.py loadable: OK')
" 2>&1)
  if echo "$OUTPUT" | grep -q "OK"; then
    echo "[PASS] commands.py 可正常加载"
    PASS=$((PASS+1))
  else
    echo "[FAIL] commands.py 加载失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_atomic_write() {
  OUTPUT=$(uv run python3 -c "
import inspect
from cliany_site.codegen.merger import AdapterMerger
src = inspect.getsource(AdapterMerger)
assert 'os.replace' in src or 'shutil.move' in src or 'rename' in src, 'No atomic write pattern'
print('Atomic write pattern: FOUND')
" 2>&1)
  if echo "$OUTPUT" | grep -q "FOUND"; then
    echo "[PASS] 原子写入模式存在"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 原子写入模式缺失: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_cleanup() {
  rm -rf ~/.cliany-site/adapters/qa-merge.example/ 2>/dev/null
  echo "[PASS] 清理测试数据"
  PASS=$((PASS+1))
}

echo "Running adapter merge tests..."
test_first_merge
test_append_merge
test_conflict_auto_rename
test_commands_py_loadable
test_atomic_write
test_cleanup

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
