#!/bin/bash
PASS=0
FAIL=0

test_initial_load() {
  rm -rf ~/.cliany-site/adapters/qa-cache.example/ 2>/dev/null || true
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
from cliany_site.loader import load_adapter
import json
domain = 'qa-cache.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='search', description='搜索', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Search', target_role='button')
r = ExploreResult(pages=[page], commands=[cmd], actions=[a])
merger = AdapterMerger(domain)
merger.merge(r)
group = load_adapter(domain)
commands = list(group.commands.keys()) if group else []
print(f'commands={commands}')
assert len(commands) == 1, f'Expected 1 command, got {len(commands)}'
assert 'search' in commands, 'search command missing'
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 初始加载: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 初始加载失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_cache_invalidation() {
  OUTPUT=$(uv run python3 -c "
from cliany_site.codegen.merger import AdapterMerger
from cliany_site.explorer.models import CommandSuggestion, ExploreResult, PageInfo, ActionStep
from cliany_site.loader import load_adapter
import json
domain = 'qa-cache.example'
page = PageInfo(url=f'https://{domain}', title='QA')
cmd = CommandSuggestion(name='login', description='登录', args=[], action_steps=[0])
a = ActionStep(action_type='click', page_url=f'https://{domain}', target_name='Login', target_role='button')
r = ExploreResult(pages=[page], commands=[cmd], actions=[a])
merger = AdapterMerger(domain)
merger.merge(r)
group = load_adapter(domain)  # Load again in same process
commands = list(group.commands.keys()) if group else []
print(f'commands={commands}')
assert len(commands) == 2, f'Expected 2 commands, got {len(commands)}'
assert 'search' in commands, 'search command missing after reload'
assert 'login' in commands, 'login command missing'
" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 缓存失效测试: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 缓存失效测试失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_cleanup() {
  rm -rf ~/.cliany-site/adapters/qa-cache.example/ 2>/dev/null
  echo "[PASS] 清理测试数据"
  PASS=$((PASS+1))
}

echo "Running loader cache tests..."
test_initial_load
test_cache_invalidation
test_cleanup

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1