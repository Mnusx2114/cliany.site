#!/bin/bash
PASS=0
FAIL=0

TEST_DOMAIN="qa-atom.example"
ADAPTER_DIR="$HOME/.cliany-site/adapters/$TEST_DOMAIN"
ATOMS_DIR="$ADAPTER_DIR/atoms"

cleanup_test_data() {
  rm -rf "$ADAPTER_DIR" 2>/dev/null || true
}

test_save_and_load_atom() {
  cleanup_test_data

  OUTPUT=$(uv run python3 -c "
from datetime import datetime, timezone
from pathlib import Path

from cliany_site.atoms import AtomCommand, AtomParameter, load_atom, save_atom

domain = 'qa-atom.example'
atom = AtomCommand(
    atom_id='fill-search-box',
    name='填写搜索框',
    description='在搜索框输入关键词',
    domain=domain,
    parameters=[
        AtomParameter(
            name='query',
            description='搜索关键词',
            default='cliany-site',
            required=True,
        )
    ],
    actions=[
        {
            'action_type': 'type',
            'page_url': 'https://qa-atom.example/search',
            'target_ref': '@ref=12',
            'target_name': 'Search',
            'target_role': 'textbox',
            'target_attributes': {
                'id': 'search-input',
                'placeholder': '搜索',
                'name': 'q',
            },
            'value': '{{query}}',
            'description': '向搜索框输入内容',
        }
    ],
    created_at=datetime.now(timezone.utc).isoformat(),
    source_workflow='搜索仓库流程',
)

path = save_atom(atom)
assert Path(path).exists(), f'atom file not found: {path}'

loaded = load_atom(domain, 'fill-search-box')
assert loaded is not None, 'load_atom returned None'
assert loaded.atom_id == atom.atom_id
assert loaded.name == atom.name
assert loaded.description == atom.description
assert loaded.domain == atom.domain
assert loaded.source_workflow == atom.source_workflow
assert len(loaded.parameters) == 1
assert loaded.parameters[0].name == 'query'
assert loaded.parameters[0].default == 'cliany-site'
assert loaded.parameters[0].required is True
assert len(loaded.actions) == 1
assert loaded.actions[0]['action_type'] == 'type'
assert loaded.actions[0]['target_name'] == 'Search'
assert loaded.actions[0]['target_role'] == 'textbox'
assert loaded.actions[0]['target_attributes']['id'] == 'search-input'
assert loaded.actions[0]['value'] == '{{query}}'
assert 'target_ref' not in loaded.actions[0], 'target_ref should not be persisted'

print(path)
" 2>&1)

  if [ $? -ne 0 ]; then
    echo "[FAIL] 保存并加载 atom（数据回环）: $OUTPUT"
    FAIL=$((FAIL+1))
    return
  fi

  JSON_CHECK=$(uv run python3 -m json.tool "$ATOMS_DIR/fill-search-box.json" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 保存并加载 atom（含 JSON 合法性）: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] atom JSON 不是有效 JSON: $JSON_CHECK"
    FAIL=$((FAIL+1))
  fi
}

test_list_atoms_lightweight() {
  OUTPUT=$(uv run python3 -c "
from datetime import datetime, timezone

from cliany_site.atoms import AtomCommand, list_atoms, load_atoms, save_atom

domain = 'qa-atom.example'

atom = AtomCommand(
    atom_id='submit-search',
    name='提交搜索',
    description='提交搜索表单',
    domain=domain,
    parameters=[],
    actions=[
        {
            'action_type': 'submit',
            'page_url': 'https://qa-atom.example/search',
            'description': '回车提交',
        }
    ],
    created_at=datetime.now(timezone.utc).isoformat(),
    source_workflow='搜索仓库流程',
)
save_atom(atom)

loaded_atoms = load_atoms(domain)
assert len(loaded_atoms) >= 2, f'expected >= 2 loaded atoms, got {len(loaded_atoms)}'
assert any(a.atom_id == 'fill-search-box' for a in loaded_atoms), 'fill-search-box missing'
assert any(a.atom_id == 'submit-search' for a in loaded_atoms), 'submit-search missing'

items = list_atoms(domain)
assert len(items) >= 2, f'expected >= 2 atoms, got {len(items)}'

required_keys = {'atom_id', 'name', 'description', 'domain', 'source_workflow', 'created_at'}
for item in items:
    assert required_keys.issubset(item.keys()), f'missing keys: {item}'
    assert 'actions' not in item, 'list_atoms should not include actions'
    assert 'parameters' not in item, 'list_atoms should not include parameters'

print([i['atom_id'] for i in items])
" 2>&1)

  if [ $? -ne 0 ]; then
    echo "[FAIL] 列出 atom 失败: $OUTPUT"
    FAIL=$((FAIL+1))
    return
  fi

  JSON_CHECK=$(uv run python3 -m json.tool "$ATOMS_DIR/submit-search.json" 2>&1)
  if [ $? -eq 0 ]; then
    echo "[PASS] 列出 atom 轻量信息: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] submit-search JSON 不是有效 JSON: $JSON_CHECK"
    FAIL=$((FAIL+1))
  fi
}

test_no_ref_field_in_saved_json() {
  if grep -R '@ref' "$ATOMS_DIR"/*.json >/dev/null 2>&1 || grep -R '"target_ref"' "$ATOMS_DIR"/*.json >/dev/null 2>&1; then
    echo "[FAIL] 保存的 atom JSON 包含 @ref/target_ref，不符合要求"
    FAIL=$((FAIL+1))
  else
    echo "[PASS] 保存的 atom JSON 不包含 @ref/target_ref"
    PASS=$((PASS+1))
  fi
}

test_cleanup() {
  cleanup_test_data
  echo "[PASS] 清理测试数据"
  PASS=$((PASS+1))
}

echo "Running atom storage tests..."
test_save_and_load_atom
test_list_atoms_lightweight
test_no_ref_field_in_saved_json
test_cleanup

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
