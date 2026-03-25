#!/bin/bash
# 原子系统端到端集成测试
# 覆盖 4 个场景：首次探索抽取原子 → 二次探索 prompt 注入 → 原子独立执行参数化 → 含 reuse_atom 的工作流
PASS=0
FAIL=0

TEST_DOMAIN="qa-atom-integration.example"
ADAPTER_DIR="$HOME/.cliany-site/adapters/$TEST_DOMAIN"

cleanup() {
  rm -rf "$ADAPTER_DIR" 2>/dev/null || true
}

trap cleanup EXIT

# ─────────────────────────────────────────────────────────────────────────────
# 场景 1：首次探索 → 原子被抽取并持久化
# ─────────────────────────────────────────────────────────────────────────────
echo "=== 场景 1：首次探索 → 原子抽取+落盘 ==="

OUTPUT=$(uv run python3 -c "
import asyncio
import json

from cliany_site.atoms.storage import load_atoms
from cliany_site.explorer.analyzer import AtomExtractor
from cliany_site.explorer.models import ActionStep, ExploreResult


class MockResponse:
    def __init__(self, content):
        self.content = content


class MockLLM:
    async def ainvoke(self, prompt):
        payload = {
            'atoms': [
                {
                    'atom_id': 'fill-search-box',
                    'name': '填写搜索框',
                    'description': '在搜索框输入关键词',
                    'parameters': [
                        {
                            'name': 'query',
                            'description': '搜索关键词',
                            'default': 'cliany-site',
                            'required': True,
                        }
                    ],
                    'action_indices': [0, 1],
                    'actions': [
                        {
                            'action_type': 'click',
                            'page_url': 'https://qa-atom-integration.example/search',
                            'target_name': 'Search',
                            'target_role': 'textbox',
                            'target_attributes': {'id': 'search-input'},
                            'description': '激活搜索框',
                        },
                        {
                            'action_type': 'type',
                            'page_url': 'https://qa-atom-integration.example/search',
                            'target_name': 'Search',
                            'target_role': 'textbox',
                            'target_attributes': {'id': 'search-input'},
                            'value': '{{query}}',
                            'description': '输入关键词',
                        },
                    ],
                },
                {
                    'atom_id': 'submit-search',
                    'name': '提交搜索',
                    'description': '提交搜索表单并等待结果',
                    'parameters': [],
                    'action_indices': [2, 3],
                    'actions': [
                        {
                            'action_type': 'submit',
                            'page_url': 'https://qa-atom-integration.example/search',
                            'description': '提交搜索',
                        },
                        {
                            'action_type': 'navigate',
                            'page_url': 'https://qa-atom-integration.example/search',
                            'target_url': 'https://qa-atom-integration.example/results',
                            'description': '等待结果页面',
                        },
                    ],
                },
            ]
        }
        fence = chr(96) * 3
        content = '提取完成\n' + fence + 'json\n' + json.dumps(payload, ensure_ascii=False) + '\n' + fence
        return MockResponse(content)


async def main():
    domain = 'qa-atom-integration.example'
    actions = [
        ActionStep(action_type='click', page_url=f'https://{domain}/search', description='点击搜索框'),
        ActionStep(action_type='type', page_url=f'https://{domain}/search', value='cliany-site', description='输入关键词'),
        ActionStep(action_type='submit', page_url=f'https://{domain}/search', description='提交搜索'),
        ActionStep(action_type='navigate', page_url=f'https://{domain}/search', target_url=f'https://{domain}/results', description='等待结果页'),
    ]
    result = ExploreResult(actions=actions)

    extractor = AtomExtractor(MockLLM(), domain)
    atoms = await extractor.extract_atoms(result)

    assert len(atoms) == 2, f'expected 2 atoms, got {len(atoms)}'
    atom_ids = {a.atom_id for a in atoms}
    assert atom_ids == {'fill-search-box', 'submit-search'}, f'unexpected ids: {atom_ids}'
    assert all(a.domain == domain for a in atoms), '所有原子 domain 应一致'

    persisted = load_atoms(domain)
    assert len(persisted) == 2, f'expected 2 persisted atoms, got {len(persisted)}'
    persisted_ids = {a.atom_id for a in persisted}
    assert persisted_ids == atom_ids, f'persisted ids mismatch: {persisted_ids}'

    for atom in persisted:
        assert atom.atom_id, 'atom_id 不能为空'
        assert atom.name, 'name 不能为空'
        assert atom.description, 'description 不能为空'
        assert atom.domain == domain, 'domain 不匹配'
        assert isinstance(atom.actions, list) and len(atom.actions) > 0, 'actions 不能为空'
        assert atom.created_at, 'created_at 不能为空'

    # 验证 fill-search-box 有参数
    search_atom = next(a for a in persisted if a.atom_id == 'fill-search-box')
    assert len(search_atom.parameters) == 1, f'expected 1 param, got {len(search_atom.parameters)}'
    assert search_atom.parameters[0].name == 'query', f'expected query, got {search_atom.parameters[0].name}'

    print(f'ok extracted={len(atoms)} persisted={len(persisted)} ids={sorted(atom_ids)}')


asyncio.run(main())
" 2>&1)

if [ $? -ne 0 ]; then
  echo "[FAIL] 场景1: 原子抽取失败: $OUTPUT"
  FAIL=$((FAIL+1))
else
  echo "[PASS] 场景1: 原子抽取成功: $OUTPUT"
  PASS=$((PASS+1))
fi

# 验证原子 JSON 文件实际存在
if [ -f "$ADAPTER_DIR/atoms/fill-search-box.json" ] && [ -f "$ADAPTER_DIR/atoms/submit-search.json" ]; then
  echo "[PASS] 场景1: 原子 JSON 文件存在于 atoms/ 目录"
  PASS=$((PASS+1))
else
  echo "[FAIL] 场景1: 原子 JSON 文件未生成 (dir=$ADAPTER_DIR/atoms/)"
  FAIL=$((FAIL+1))
fi

# 验证原子 JSON 合法
JSON_OK=true
for f in "$ADAPTER_DIR/atoms/fill-search-box.json" "$ADAPTER_DIR/atoms/submit-search.json"; do
  uv run python3 -m json.tool "$f" >/dev/null 2>&1 || JSON_OK=false
done
if [ "$JSON_OK" = true ]; then
  echo "[PASS] 场景1: 原子 JSON 文件格式合法"
  PASS=$((PASS+1))
else
  echo "[FAIL] 场景1: 原子 JSON 文件格式非法"
  FAIL=$((FAIL+1))
fi

# ─────────────────────────────────────────────────────────────────────────────
# 场景 2：二次探索 → prompt 包含原子清单 + reuse_atom 响应解析
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 场景 2：二次探索 → atom inventory 注入 prompt + reuse_atom 解析 ==="

OUTPUT=$(uv run python3 -c "
import asyncio
import json

from cliany_site.explorer.prompts import build_atom_inventory_section
from cliany_site.atoms.storage import load_atoms


async def main():
    domain = 'qa-atom-integration.example'

    # 验证原子已在磁盘（场景1 落盘）
    persisted = load_atoms(domain)
    assert len(persisted) >= 2, f'需要场景1先落盘，当前只有 {len(persisted)} 个原子'

    # 构建 atom inventory section
    section = build_atom_inventory_section(domain)
    assert section, '已有原子时 build_atom_inventory_section 不应返回空字符串'
    assert 'fill-search-box' in section, f'section 应包含 fill-search-box，实际: {section[:200]}'
    assert 'submit-search' in section, f'section 应包含 submit-search，实际: {section[:200]}'
    assert '可复用' in section or '已有原子' in section or '原子操作清单' in section, \
        f'section 应包含"原子操作"相关标题，实际: {section[:200]}'

    print(f'ok section_len={len(section)} atom_count={len(persisted)}')


asyncio.run(main())
" 2>&1)

if [ $? -ne 0 ]; then
  echo "[FAIL] 场景2: atom inventory 注入失败: $OUTPUT"
  FAIL=$((FAIL+1))
else
  echo "[PASS] 场景2: atom inventory 注入 prompt 成功: $OUTPUT"
  PASS=$((PASS+1))
fi

# 验证 reuse_atom 响应被正确解析
OUTPUT=$(uv run python3 -c "
import asyncio
import json

from cliany_site.explorer.analyzer import AtomExtractor
from cliany_site.explorer.models import ActionStep, ExploreResult
from cliany_site.atoms.storage import load_atoms


class MockResponse:
    def __init__(self, content):
        self.content = content


class ReuseAtomLLM:
    '''模拟 LLM 返回 reuse_atom 引用（本次探索不抽取新原子）'''
    async def ainvoke(self, prompt):
        # 验证 prompt 中包含已有原子清单
        assert 'fill-search-box' in prompt, f'prompt 应包含已有原子 fill-search-box'
        # 返回空 atoms（代表当前工作流直接复用，不新增原子）
        payload = {'atoms': []}
        return MockResponse(json.dumps(payload, ensure_ascii=False))


async def main():
    domain = 'qa-atom-integration.example'
    actions = [
        ActionStep(action_type='reuse_atom', page_url=f'https://{domain}/', target_ref='fill-search-box',
                   description='复用填写搜索框原子', target_attributes={'query': 'test'}),
    ]
    result = ExploreResult(actions=actions)

    extractor = AtomExtractor(ReuseAtomLLM(), domain)
    new_atoms = await extractor.extract_atoms(result)

    # 二次探索：prompt 中已有原子，LLM 不新增；仅返回空列表
    assert isinstance(new_atoms, list), '返回值应为列表'
    # 原有两个原子仍在磁盘
    persisted = load_atoms(domain)
    assert len(persisted) >= 2, f'磁盘原子数应 >= 2，实际 {len(persisted)}'

    print(f'ok new_atoms={len(new_atoms)} total_persisted={len(persisted)}')


asyncio.run(main())
" 2>&1)

if [ $? -ne 0 ]; then
  echo "[FAIL] 场景2: reuse_atom prompt 验证失败: $OUTPUT"
  FAIL=$((FAIL+1))
else
  echo "[PASS] 场景2: prompt 包含原子清单，reuse_atom 场景验证通过: $OUTPUT"
  PASS=$((PASS+1))
fi

# ─────────────────────────────────────────────────────────────────────────────
# 场景 3：原子独立执行 → 参数化工作正确
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 场景 3：原子独立执行 → 参数化 ==="

OUTPUT=$(uv run python3 -c "
from cliany_site.action_runtime import substitute_parameters

# 原子 actions 含 {{query}} 占位符
actions = [
    {
        'type': 'type',
        'value': '{{query}}',
        'url': 'https://qa-atom-integration.example/search?q={{query}}',
        'description': '输入 {{query}}',
        'target_name': '{{query}} 输入框',
    }
]
params = {'query': 'integration-test'}

resolved = substitute_parameters(actions, params)
assert resolved[0]['value'] == 'integration-test', f\"value mismatch: {resolved[0]['value']}\"
assert resolved[0]['url'] == 'https://qa-atom-integration.example/search?q=integration-test', \
    f\"url mismatch: {resolved[0]['url']}\"
assert resolved[0]['description'] == '输入 integration-test', f\"desc mismatch: {resolved[0]['description']}\"
assert resolved[0]['target_name'] == 'integration-test 输入框', f\"target_name mismatch: {resolved[0]['target_name']}\"

# 原始 actions 不应被修改（deepcopy 检查）
assert actions[0]['value'] == '{{query}}', '原始 actions 不应被 substitute_parameters 修改'
assert actions[0]['url'] == 'https://qa-atom-integration.example/search?q={{query}}', '原始 url 不应被修改'

print(f'ok resolved_value={resolved[0][\"value\"]}')
" 2>&1)

if [ $? -ne 0 ]; then
  echo "[FAIL] 场景3: substitute_parameters 参数替换失败: $OUTPUT"
  FAIL=$((FAIL+1))
else
  echo "[PASS] 场景3: substitute_parameters 参数替换正确: $OUTPUT"
  PASS=$((PASS+1))
fi

# 验证 generate_atom_command 生成含 @atoms_group.command 和 load_atom 的代码
OUTPUT=$(uv run python3 -c "
from datetime import datetime, timezone
from cliany_site.atoms.models import AtomCommand, AtomParameter
from cliany_site.codegen.generator import AdapterGenerator

domain = 'qa-atom-integration.example'
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
            'page_url': f'https://{domain}/search',
            'target_name': 'Search Input',
            'target_role': 'textbox',
            'value': '{{query}}',
            'description': '输入关键词',
        }
    ],
    created_at=datetime.now(timezone.utc).isoformat(),
    source_workflow='QA 集成测试工作流',
)

gen = AdapterGenerator(domain)
code = gen.generate_atom_command(atom)

assert '@atoms_group.command' in code, f'生成代码应包含 @atoms_group.command，实际: {code[:300]}'
assert 'load_atom(DOMAIN,' in code, f'生成代码应包含 load_atom(DOMAIN,，实际: {code[:300]}'
assert 'substitute_parameters' in code, f'生成代码应包含 substitute_parameters，实际: {code[:300]}'
assert '_normalize_atom_actions' in code, f'生成代码应包含 _normalize_atom_actions，实际: {code[:300]}'
assert '--query' in code, f'生成代码应包含 --query 选项，实际: {code[:300]}'

print(f'ok code_lines={len(code.splitlines())}')
" 2>&1)

if [ $? -ne 0 ]; then
  echo "[FAIL] 场景3: generate_atom_command 生成代码失败: $OUTPUT"
  FAIL=$((FAIL+1))
else
  echo "[PASS] 场景3: generate_atom_command 生成正确 CLI 代码: $OUTPUT"
  PASS=$((PASS+1))
fi

# ─────────────────────────────────────────────────────────────────────────────
# 场景 4：含 reuse_atom 的工作流 → 端到端代码生成 + metadata
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 场景 4：含 reuse_atom 的工作流 → 端到端代码生成 + metadata ==="

OUTPUT=$(uv run python3 -c "
import json
from cliany_site.explorer.models import ActionStep, CommandSuggestion, ExploreResult, PageInfo
from cliany_site.codegen.generator import AdapterGenerator, save_adapter

domain = 'qa-atom-integration.example'

actions = [
    ActionStep(
        action_type='navigate',
        page_url='',
        target_ref='',
        target_url=f'https://{domain}/',
        value='',
        description='导航到首页',
    ),
    ActionStep(
        action_type='reuse_atom',
        page_url=f'https://{domain}/',
        target_ref='fill-search-box',
        target_url='',
        value='',
        description='复用填写搜索框原子',
        target_attributes={'query': 'browser-use'},
    ),
    ActionStep(
        action_type='click',
        page_url=f'https://{domain}/',
        target_ref='99',
        target_url='',
        value='',
        description='点击搜索按钮',
    ),
]

commands = [
    CommandSuggestion(
        name='search',
        description='搜索集成测试',
        args=[{'name': 'query', 'description': '搜索关键词', 'required': True}],
        action_steps=[0, 1, 2],
    )
]

explore_result = ExploreResult(
    pages=[PageInfo(url=f'https://{domain}/', title='QA Integration Test')],
    actions=actions,
    commands=commands,
)

gen = AdapterGenerator(domain)
code = gen.generate(explore_result, domain)
path = save_adapter(domain, code, explore_result=explore_result)
print(path)
" 2>&1)

if [ $? -ne 0 ]; then
  echo "[FAIL] 场景4: 含 reuse_atom 工作流代码生成失败: $OUTPUT"
  FAIL=$((FAIL+1))
else
  echo "[PASS] 场景4: 含 reuse_atom 工作流代码生成成功: $OUTPUT"
  PASS=$((PASS+1))
fi

COMMANDS_FILE="$ADAPTER_DIR/commands.py"
METADATA_FILE="$ADAPTER_DIR/metadata.json"

# 验证 commands.py 包含必要的 import 和 helper
if [ -f "$COMMANDS_FILE" ]; then
  CHECKS_OK=true
  grep -q 'from cliany_site.atoms.storage import load_atom' "$COMMANDS_FILE" || CHECKS_OK=false
  grep -q 'substitute_parameters' "$COMMANDS_FILE" || CHECKS_OK=false
  grep -q '_normalize_atom_actions' "$COMMANDS_FILE" || CHECKS_OK=false

  if [ "$CHECKS_OK" = true ]; then
    echo "[PASS] 场景4: commands.py 包含 load_atom/substitute_parameters/_normalize_atom_actions"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 场景4: commands.py 缺少必要的 import 或 helper"
    FAIL=$((FAIL+1))
  fi
else
  echo "[FAIL] 场景4: commands.py 未生成"
  FAIL=$((FAIL+1))
fi

# 验证 commands.py 同时保留内联 action（json.loads）
if [ -f "$COMMANDS_FILE" ] && grep -q 'json.loads(' "$COMMANDS_FILE"; then
  echo "[PASS] 场景4: commands.py 保留了内联 action 的 json.loads"
  PASS=$((PASS+1))
else
  echo "[FAIL] 场景4: commands.py 缺少内联 action 的 json.loads"
  FAIL=$((FAIL+1))
fi

# 验证 metadata.json 包含 atom_refs
if [ -f "$METADATA_FILE" ]; then
  ATOM_REFS=$(uv run python3 -c "
import json
with open('$METADATA_FILE') as f:
    meta = json.load(f)
cmds = meta.get('commands', [])
for cmd in cmds:
    refs = cmd.get('atom_refs', [])
    if refs:
        print(','.join(refs))
" 2>&1)

  if echo "$ATOM_REFS" | grep -q 'fill-search-box'; then
    echo "[PASS] 场景4: metadata.json commands 包含 atom_refs: $ATOM_REFS"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 场景4: metadata.json commands 缺少 atom_refs (got: $ATOM_REFS)"
    FAIL=$((FAIL+1))
  fi
else
  echo "[FAIL] 场景4: metadata.json 未生成"
  FAIL=$((FAIL+1))
fi

# ─────────────────────────────────────────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
