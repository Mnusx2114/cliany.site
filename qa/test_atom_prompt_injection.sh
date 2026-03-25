#!/bin/bash
PASS=0
FAIL=0

TEST_DOMAIN="qa-prompt.example"
ADAPTER_DIR="$HOME/.cliany-site/adapters/$TEST_DOMAIN"

cleanup_test_data() {
  rm -rf "$ADAPTER_DIR" 2>/dev/null || true
}

# Test 1: 3 atoms -> section contains all 3 atom_ids and descriptions
test_three_atoms_all_appear() {
  cleanup_test_data

  OUTPUT=$(uv run python3 -c "
from datetime import datetime, timezone
from cliany_site.atoms import AtomCommand, save_atom
from cliany_site.explorer.prompts import build_atom_inventory_section

domain = 'qa-prompt.example'
atom_ids = ['fill-search-box', 'click-download', 'submit-login-form']
names = ['填写搜索框', '点击下载', '提交登录表单']
descs = ['在搜索框输入关键词', '点击下载按钮并确认', '输入账号密码并提交登录']

for aid, name, desc in zip(atom_ids, names, descs):
    atom = AtomCommand(
        atom_id=aid,
        name=name,
        description=desc,
        domain=domain,
        parameters=[],
        actions=[],
        created_at=datetime.now(timezone.utc).isoformat(),
        source_workflow='测试工作流',
    )
    save_atom(atom)

section = build_atom_inventory_section(domain)

assert section != '', 'section should not be empty when atoms exist'
for aid, desc in zip(atom_ids, descs):
    assert aid in section, f'atom_id {aid!r} not found in section'
    assert desc in section, f'description {desc!r} not found in section'

print('OK: all 3 atom_ids and descriptions present')
" 2>&1)

  if [ $? -eq 0 ]; then
    echo "[PASS] 3 个原子全部出现在 section 中: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 3 个原子 section 测试失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

# Test 2: 50 atoms -> section contains at most 30 atom_id occurrences
test_fifty_atoms_truncated_to_thirty() {
  cleanup_test_data

  OUTPUT=$(uv run python3 -c "
import time
from datetime import datetime, timezone, timedelta
from cliany_site.atoms import AtomCommand, save_atom
from cliany_site.explorer.prompts import build_atom_inventory_section

domain = 'qa-prompt.example'

base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
for i in range(50):
    atom = AtomCommand(
        atom_id=f'test-atom-{i:03d}',
        name=f'测试原子 {i}',
        description=f'测试原子描述 {i}',
        domain=domain,
        parameters=[],
        actions=[],
        created_at=(base_time + timedelta(seconds=i)).isoformat(),
        source_workflow='压测工作流',
    )
    save_atom(atom)

section = build_atom_inventory_section(domain)

count = section.count('atom_id:')
assert count == 30, f'expected 30 atom_id entries, got {count}'

# verify the 30 most recent (test-atom-020 through test-atom-049) are present
for i in range(20, 50):
    aid = f'test-atom-{i:03d}'
    assert aid in section, f'{aid} should be in section (it is one of the 30 most recent)'

# verify the 20 oldest (test-atom-000 through test-atom-019) are absent
for i in range(0, 20):
    aid = f'test-atom-{i:03d}'
    assert aid not in section, f'{aid} should NOT be in section (it was truncated)'

print(f'OK: atom_id count = {count}')
" 2>&1)

  if [ $? -eq 0 ]; then
    echo "[PASS] 50 个原子截断为 30: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 截断测试失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

# Test 3: nonexistent domain -> returns empty string
test_nonexistent_domain_returns_empty() {
  OUTPUT=$(uv run python3 -c "
from cliany_site.explorer.prompts import build_atom_inventory_section

section = build_atom_inventory_section('nonexistent-domain.example')
assert section == '', f'expected empty string, got: {section!r}'
print('OK: empty string returned')
" 2>&1)

  if [ $? -eq 0 ]; then
    echo "[PASS] 不存在的域名返回空字符串: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 不存在域名测试失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

test_cleanup() {
  cleanup_test_data
  echo "[PASS] 清理测试数据"
  PASS=$((PASS+1))
}

echo "Running atom prompt injection tests..."
test_three_atoms_all_appear
test_fifty_atoms_truncated_to_thirty
test_nonexistent_domain_returns_empty
test_cleanup

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
