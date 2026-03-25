#!/bin/bash
PASS=0
FAIL=0

TEST_DOMAIN="qa-atom-prompt.example"
WORKFLOW_NAME="搜索并下载文档"

test_prompt_template_render() {
  OUTPUT=$(uv run python3 -c "
import json
from dataclasses import asdict

from cliany_site.explorer.models import ActionStep, ExploreResult
from cliany_site.explorer.prompts import ATOM_EXTRACTION_PROMPT_TEMPLATE

domain = '$TEST_DOMAIN'
workflow_name = '$WORKFLOW_NAME'

actions = [
    ActionStep(
        action_type='navigate',
        page_url=f'https://{domain}/',
        target_url=f'https://{domain}/search',
        description='进入搜索页面',
    ),
    ActionStep(
        action_type='click',
        page_url=f'https://{domain}/search',
        target_ref='@ref=11',
        description='点击搜索输入框',
        target_name='Search',
        target_role='textbox',
        target_attributes={'id': 'search-input', 'name': 'q'},
    ),
    ActionStep(
        action_type='type',
        page_url=f'https://{domain}/search',
        target_ref='@ref=11',
        value='cliany-site',
        description='输入搜索关键词',
        target_name='Search',
        target_role='textbox',
        target_attributes={'id': 'search-input', 'name': 'q'},
    ),
    ActionStep(
        action_type='submit',
        page_url=f'https://{domain}/search',
        description='提交搜索',
    ),
    ActionStep(
        action_type='click',
        page_url=f'https://{domain}/search?q=cliany-site',
        target_ref='@ref=25',
        description='点击结果链接',
        target_name='cliany.site README',
        target_role='link',
        target_attributes={'href': '/repo/cliany-site', 'class': 'result-link'},
    ),
    ActionStep(
        action_type='navigate',
        page_url=f'https://{domain}/search?q=cliany-site',
        target_url=f'https://{domain}/repo/cliany-site',
        description='进入结果详情页',
    ),
    ActionStep(
        action_type='click',
        page_url=f'https://{domain}/repo/cliany-site',
        target_ref='@ref=32',
        description='点击下载按钮',
        target_name='Download',
        target_role='button',
        target_attributes={'id': 'download-btn', 'class': 'btn primary'},
    ),
    ActionStep(
        action_type='click',
        page_url=f'https://{domain}/repo/cliany-site',
        target_ref='@ref=36',
        description='勾选确认下载复选框',
        target_name='我已确认版权',
        target_role='checkbox',
        target_attributes={'id': 'copyright-check'},
    ),
    ActionStep(
        action_type='click',
        page_url=f'https://{domain}/repo/cliany-site',
        target_ref='@ref=38',
        description='确认下载对话框',
        target_name='确认下载',
        target_role='button',
        target_attributes={'id': 'confirm-download'},
    ),
]

explore_result = ExploreResult(actions=actions)
assert len(explore_result.actions) == 9, f'expected 9 actions, got {len(explore_result.actions)}'

actions_json = json.dumps([asdict(a) for a in explore_result.actions], ensure_ascii=False, indent=2)
existing_atoms = json.dumps(
    [
        {
            'atom_id': 'open-search-page',
            'name': '打开搜索页',
            'description': '进入搜索页并聚焦搜索框',
        }
    ],
    ensure_ascii=False,
    indent=2,
)

prompt = ATOM_EXTRACTION_PROMPT_TEMPLATE.format(
    actions_json=actions_json,
    existing_atoms=existing_atoms,
    workflow_name=workflow_name,
    domain=domain,
)

assert '工作流名称: 搜索并下载文档' in prompt
assert f'目标域名: {domain}' in prompt
assert '## ExploreResult.actions（完整 JSON）' in prompt
assert 'open-search-page' in prompt
assert 'actions 中禁止出现 @ref 或 target_ref' in prompt
assert '任何可变输入值必须参数化为 {{param_name}}' in prompt
assert 'action_type' in prompt and 'navigate' in prompt
assert '{actions_json}' not in prompt
assert '{existing_atoms}' not in prompt

print(f'prompt_render_ok length={len(prompt)} actions={len(explore_result.actions)}')
" 2>&1)

  if [ $? -ne 0 ]; then
    echo "[FAIL] Prompt 模板渲染与 fixture 注入: $OUTPUT"
    FAIL=$((FAIL+1))
  else
    echo "[PASS] Prompt 模板渲染与 fixture 注入: $OUTPUT"
    PASS=$((PASS+1))
  fi
}

test_mock_llm_parsing_and_validation() {
  OUTPUT=$(uv run python3 -c "
import json

from cliany_site.explorer.engine import _parse_llm_response

domain = '$TEST_DOMAIN'

mock_payload = {
    'atoms': [
        {
            'atom_id': 'search-repository',
            'name': '搜索仓库',
            'description': '在搜索框输入关键词并提交',
            'parameters': [
                {
                    'name': 'query',
                    'description': '搜索关键词',
                    'default': 'cliany-site',
                    'required': True,
                }
            ],
            'action_indices': [1, 2, 3],
            'actions': [
                {
                    'action_type': 'click',
                    'page_url': f'https://{domain}/search',
                    'target_name': 'Search',
                    'target_role': 'textbox',
                    'target_attributes': {'id': 'search-input'},
                    'description': '激活搜索框',
                },
                {
                    'action_type': 'type',
                    'page_url': f'https://{domain}/search',
                    'target_name': 'Search',
                    'target_role': 'textbox',
                    'target_attributes': {'id': 'search-input'},
                    'value': '{{query}}',
                    'description': '输入关键词',
                },
                {
                    'action_type': 'submit',
                    'page_url': f'https://{domain}/search',
                    'description': '提交搜索',
                },
            ],
        },
        {
            'atom_id': 'open-result-and-download',
            'name': '打开结果并下载',
            'description': '打开结果详情并触发下载',
            'parameters': [
                {
                    'name': 'result_title',
                    'description': '结果标题',
                    'default': 'cliany.site README',
                    'required': False,
                }
            ],
            'action_indices': [4, 6, 8],
            'actions': [
                {
                    'action_type': 'click',
                    'page_url': f'https://{domain}/search?q=cliany-site',
                    'target_name': 'cliany.site README',
                    'target_role': 'link',
                    'target_attributes': {'href': '/repo/cliany-site'},
                    'description': '打开结果详情',
                },
                {
                    'action_type': 'click',
                    'page_url': f'https://{domain}/repo/cliany-site',
                    'target_name': 'Download',
                    'target_role': 'button',
                    'description': '点击下载',
                },
                {
                    'action_type': 'click',
                    'page_url': f'https://{domain}/repo/cliany-site',
                    'target_name': '确认下载',
                    'target_role': 'button',
                    'description': '确认下载',
                },
            ],
        },
    ]
}

mock_json = json.dumps(mock_payload, ensure_ascii=False, indent=2)
json.loads(mock_json)
fence = chr(96) * 3
mock_response = '提取完成。\\n' + fence + 'json\\n' + mock_json + '\\n' + fence

parsed = _parse_llm_response(mock_response)
assert isinstance(parsed, dict), 'parsed response should be dict'

atoms = parsed.get('atoms')
assert isinstance(atoms, list), 'atoms must be list'
assert len(atoms) >= 2, f'expected >=2 atoms, got {len(atoms)}'

parameterized_actions = 0
for i, atom in enumerate(atoms):
    assert atom.get('atom_id'), f'atom[{i}] missing atom_id'
    assert atom.get('name'), f'atom[{i}] missing name'
    assert isinstance(atom.get('parameters'), list), f'atom[{i}] parameters must be list'
    assert isinstance(atom.get('action_indices'), list), f'atom[{i}] action_indices must be list'
    assert isinstance(atom.get('actions'), list), f'atom[{i}] actions must be list'
    assert atom['actions'], f'atom[{i}] actions must not be empty'

    for action in atom['actions']:
        action_text = json.dumps(action, ensure_ascii=False)
        assert '@ref' not in action_text, f'atom[{i}] action contains @ref'
        assert 'target_ref' not in action, f'atom[{i}] action contains target_ref'
        value = action.get('value')
        if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
            parameterized_actions += 1

assert parameterized_actions >= 1, 'expected at least one parameterized action value'

print(f'mock_parse_ok atoms={len(atoms)} parameterized_actions={parameterized_actions}')
" 2>&1)

  if [ $? -ne 0 ]; then
    echo "[FAIL] Mock LLM JSON 解析与结构校验: $OUTPUT"
    FAIL=$((FAIL+1))
  else
    echo "[PASS] Mock LLM JSON 解析与结构校验: $OUTPUT"
    PASS=$((PASS+1))
  fi
}

echo "Running atom extraction prompt tests..."
test_prompt_template_render
test_mock_llm_parsing_and_validation

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
