#!/bin/bash
# 验证 explore 命令的错误处理
PASS=0; FAIL=0

test_explore_no_cdp() {
  OUTPUT=$(cliany-site explore "https://example.com" "test workflow" --json 2>/dev/null)
  EXIT_CODE=$?
  if [ $EXIT_CODE -ne 0 ]; then
    echo "[PASS] explore 无 CDP 时 exit 非 0"
    PASS=$((PASS+1))
  else
    echo "[FAIL] explore 无 CDP 时应 exit 非 0"
    FAIL=$((FAIL+1))
  fi
  if echo "$OUTPUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert d['success']==False" 2>/dev/null; then
    echo "[PASS] explore 无 CDP 时返回 success:false"
    PASS=$((PASS+1))
  else
    echo "[FAIL] explore 无 CDP 时应返回 success:false"
    FAIL=$((FAIL+1))
  fi
  if echo "$OUTPUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert d['error']['code']=='CDP_UNAVAILABLE'" 2>/dev/null; then
    echo "[PASS] explore 返回 CDP_UNAVAILABLE 错误码"
    PASS=$((PASS+1))
  else
    echo "[FAIL] explore 应返回 CDP_UNAVAILABLE 错误码"
    FAIL=$((FAIL+1))
  fi
}

test_explore_no_llm() {
  SAVE_KEY="$ANTHROPIC_API_KEY"
  SAVE_OPENAI="$OPENAI_API_KEY"
  unset ANTHROPIC_API_KEY OPENAI_API_KEY
  OUTPUT=$(cliany-site explore "https://example.com" "test" --json 2>/dev/null)
  EXIT_CODE=$?
  if [ $EXIT_CODE -ne 0 ]; then
    echo "[PASS] explore 无环境配置时 exit 非 0"
    PASS=$((PASS+1))
  else
    echo "[FAIL] explore 无环境配置时应 exit 非 0"
    FAIL=$((FAIL+1))
  fi
  [ -n "$SAVE_KEY" ] && export ANTHROPIC_API_KEY="$SAVE_KEY"
  [ -n "$SAVE_OPENAI" ] && export OPENAI_API_KEY="$SAVE_OPENAI"
}

test_explore_help() {
  OUTPUT=$(cliany-site explore --help 2>&1)
  if echo "$OUTPUT" | grep -q "Usage:"; then
    echo "[PASS] explore --help 正确显示"
    PASS=$((PASS+1))
  else
    echo "[FAIL] explore --help 未显示 Usage"
    FAIL=$((FAIL+1))
  fi
}

test_explore_no_cdp
test_explore_no_llm
test_explore_help

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
