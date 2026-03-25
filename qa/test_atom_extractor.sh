#!/bin/bash
PASS=0
FAIL=0

cleanup_domain() {
  local domain="$1"
  rm -rf "$HOME/.cliany-site/adapters/$domain" 2>/dev/null || true
}

test_mock_llm_extract_and_save() {
  local domain="qa-atom-extractor-mock.example"
  cleanup_domain "$domain"

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
                    'action_indices': [0, 1, 2],
                    'actions': [
                        {
                            'action_type': 'click',
                            'page_url': 'https://qa-atom-extractor-mock.example/search',
                            'target_name': 'Search',
                            'target_role': 'textbox',
                            'target_attributes': {'id': 'search-input'},
                            'description': '激活搜索框',
                        },
                        {
                            'action_type': 'type',
                            'page_url': 'https://qa-atom-extractor-mock.example/search',
                            'target_name': 'Search',
                            'target_role': 'textbox',
                            'target_attributes': {'id': 'search-input'},
                            'value': '{{query}}',
                            'description': '输入关键词',
                        },
                        {
                            'action_type': 'submit',
                            'page_url': 'https://qa-atom-extractor-mock.example/search',
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
                    'action_indices': [3, 4],
                    'actions': [
                        {
                            'action_type': 'click',
                            'page_url': 'https://qa-atom-extractor-mock.example/search?q=cliany-site',
                            'target_name': 'cliany.site README',
                            'target_role': 'link',
                            'target_attributes': {'href': '/repo/cliany-site'},
                            'description': '打开结果详情',
                        },
                        {
                            'action_type': 'click',
                            'page_url': 'https://qa-atom-extractor-mock.example/repo/cliany-site',
                            'target_name': 'Download',
                            'target_role': 'button',
                            'description': '点击下载',
                        },
                    ],
                },
            ]
        }
        fence = chr(96) * 3
        content = '提取完成\n' + fence + 'json\n' + json.dumps(payload, ensure_ascii=False) + '\n' + fence
        return MockResponse(content)


async def main():
    domain = 'qa-atom-extractor-mock.example'
    actions = [
        ActionStep(action_type='click', page_url=f'https://{domain}/search', description='点击搜索框'),
        ActionStep(action_type='type', page_url=f'https://{domain}/search', value='cliany-site', description='输入关键词'),
        ActionStep(action_type='submit', page_url=f'https://{domain}/search', description='提交搜索'),
    ]
    result = ExploreResult(actions=actions)

    extractor = AtomExtractor(MockLLM(), domain)
    atoms = await extractor.extract_atoms(result)

    assert len(atoms) == 2, f'expected 2 new atoms, got {len(atoms)}'
    assert all(a.domain == domain for a in atoms), 'all extracted atoms should keep current domain'
    atom_ids = {a.atom_id for a in atoms}
    assert atom_ids == {'search-repository', 'open-result-and-download'}, atom_ids

    persisted = load_atoms(domain)
    persisted_ids = {a.atom_id for a in persisted}
    assert persisted_ids == atom_ids, f'persisted mismatch: {persisted_ids}'
    assert all(a.created_at for a in persisted), 'created_at should be filled'

    print(f'mock_ok extracted={len(atoms)} persisted={len(persisted)} ids={sorted(atom_ids)}')


asyncio.run(main())
" 2>&1)

  if [ $? -ne 0 ]; then
    echo "[FAIL] Mock LLM 抽取+落盘: $OUTPUT"
    FAIL=$((FAIL+1))
  else
    echo "[PASS] Mock LLM 抽取+落盘: $OUTPUT"
    PASS=$((PASS+1))
  fi

  cleanup_domain "$domain"
}

test_graceful_fallback_on_llm_error() {
  local domain="qa-atom-extractor-fallback.example"
  cleanup_domain "$domain"

  OUTPUT=$(uv run python3 -c "
import asyncio

from cliany_site.atoms.storage import load_atoms
from cliany_site.explorer.analyzer import AtomExtractor
from cliany_site.explorer.models import ActionStep, ExploreResult


class FailingLLM:
    async def ainvoke(self, prompt):
        raise RuntimeError('invalid api key')


async def main():
    domain = 'qa-atom-extractor-fallback.example'
    result = ExploreResult(actions=[ActionStep(action_type='click', page_url=f'https://{domain}/', description='点击')])
    extractor = AtomExtractor(FailingLLM(), domain)
    atoms = await extractor.extract_atoms(result)
    assert atoms == [], f'expected empty list on failure, got {atoms}'
    assert load_atoms(domain) == [], 'no atom should be saved on failure'
    print('fallback_ok returned_empty_list')


asyncio.run(main())
" 2>&1)

  if [ $? -ne 0 ]; then
    echo "[FAIL] LLM 异常兜底返回空列表: $OUTPUT"
    FAIL=$((FAIL+1))
  else
    echo "[PASS] LLM 异常兜底返回空列表: $OUTPUT"
    PASS=$((PASS+1))
  fi

  cleanup_domain "$domain"
}

test_dedup_existing_atom_id() {
  local domain="qa-atom-extractor-dedup.example"
  cleanup_domain "$domain"

  OUTPUT=$(uv run python3 -c "
import asyncio
import json

from cliany_site.atoms.models import AtomCommand
from cliany_site.atoms.storage import load_atom, load_atoms, save_atom
from cliany_site.explorer.analyzer import AtomExtractor
from cliany_site.explorer.models import ActionStep, ExploreResult


class MockResponse:
    def __init__(self, content):
        self.content = content


class DedupLLM:
    async def ainvoke(self, prompt):
        payload = {
            'atoms': [
                {
                    'atom_id': 'fill-search-box',
                    'name': '应被去重跳过',
                    'description': '重复 atom，不应覆盖',
                    'parameters': [
                        {'name': 'query', 'description': '关键词', 'default': 'new', 'required': True}
                    ],
                    'action_indices': [0],
                    'actions': [
                        {
                            'action_type': 'type',
                            'page_url': 'https://qa-atom-extractor-dedup.example/search',
                            'target_name': 'Search',
                            'target_role': 'textbox',
                            'value': '{{query}}',
                            'description': '重复动作',
                        }
                    ],
                },
                {
                    'atom_id': 'submit-search',
                    'name': '提交搜索',
                    'description': '提交搜索表单',
                    'parameters': [],
                    'action_indices': [1],
                    'actions': [
                        {
                            'action_type': 'submit',
                            'page_url': 'https://qa-atom-extractor-dedup.example/search',
                            'description': '提交',
                        }
                    ],
                },
            ]
        }
        return MockResponse(json.dumps(payload, ensure_ascii=False))


async def main():
    domain = 'qa-atom-extractor-dedup.example'

    existing = AtomCommand(
        atom_id='fill-search-box',
        name='已有填写搜索框',
        description='预置 atom',
        domain=domain,
        parameters=[],
        actions=[
            {
                'action_type': 'type',
                'page_url': f'https://{domain}/search',
                'target_name': 'Search',
                'target_role': 'textbox',
                'value': '{{query}}',
                'description': '已有动作',
            }
        ],
        created_at='2000-01-01T00:00:00+00:00',
        source_workflow='预置工作流',
    )
    save_atom(existing)

    result = ExploreResult(
        actions=[
            ActionStep(action_type='type', page_url=f'https://{domain}/search', value='cliany-site', description='输入'),
            ActionStep(action_type='submit', page_url=f'https://{domain}/search', description='提交'),
        ]
    )
    extractor = AtomExtractor(DedupLLM(), domain)
    new_atoms = await extractor.extract_atoms(result)

    assert len(new_atoms) == 1, f'expected only one new atom, got {len(new_atoms)}'
    assert new_atoms[0].atom_id == 'submit-search', f'unexpected new atom id: {new_atoms[0].atom_id}'

    current_existing = load_atom(domain, 'fill-search-box')
    assert current_existing is not None, 'existing atom missing after dedup'
    assert current_existing.name == '已有填写搜索框', 'existing atom should not be overwritten'
    assert current_existing.source_workflow == '预置工作流', 'existing atom metadata should remain unchanged'

    all_atoms = load_atoms(domain)
    assert {a.atom_id for a in all_atoms} == {'fill-search-box', 'submit-search'}

    print(f'dedup_ok new={new_atoms[0].atom_id} total={len(all_atoms)}')


asyncio.run(main())
" 2>&1)

  if [ $? -ne 0 ]; then
    echo "[FAIL] atom_id 去重跳过已有原子: $OUTPUT"
    FAIL=$((FAIL+1))
  else
    echo "[PASS] atom_id 去重跳过已有原子: $OUTPUT"
    PASS=$((PASS+1))
  fi

  cleanup_domain "$domain"
}

echo "Running atom extractor tests..."
test_mock_llm_extract_and_save
test_graceful_fallback_on_llm_error
test_dedup_existing_atom_id

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
