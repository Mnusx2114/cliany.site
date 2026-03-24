#!/bin/bash
# 验证错误处理
PASS=0; FAIL=0

test_unknown_command() {
  OUTPUT=$(cliany-site nonexistent-xyz --json 2>&1)
  EXIT_CODE=$?
  if [ $EXIT_CODE -ne 0 ]; then
    echo "[PASS] 未知命令 exit 非 0"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 未知命令应 exit 非 0"
    FAIL=$((FAIL+1))
  fi
  if echo "$OUTPUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert 'error' in d and d['success']==False" 2>/dev/null; then
    echo "[PASS] 未知命令返回 JSON 错误"
    PASS=$((PASS+1))
  else
    echo "[FAIL] 未知命令应返回 JSON 错误"
    FAIL=$((FAIL+1))
  fi
}

test_doctor_fail_exit_code() {
  SAVE_KEY="$ANTHROPIC_API_KEY"
  SAVE_OPENAI="$OPENAI_API_KEY"
  unset ANTHROPIC_API_KEY OPENAI_API_KEY
  OUTPUT=$(cliany-site doctor --json 2>&1)
  EXIT_CODE=$?
  if [ $EXIT_CODE -ne 0 ]; then
    echo "[PASS] doctor 失败时 exit 非 0"
    PASS=$((PASS+1))
  else
    echo "[FAIL] doctor 失败时应 exit 非 0（实际 exit $EXIT_CODE）"
    FAIL=$((FAIL+1))
  fi
  [ -n "$SAVE_KEY" ] && export ANTHROPIC_API_KEY="$SAVE_KEY"
  [ -n "$SAVE_OPENAI" ] && export OPENAI_API_KEY="$SAVE_OPENAI"
}

test_json_structure() {
  OUTPUT=$(cliany-site doctor --json 2>&1)
  if echo "$OUTPUT" | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
assert 'success' in d, 'missing success'
assert 'data' in d, 'missing data'
assert 'error' in d, 'missing error'
if not d['success']:
    assert d['error'] is not None, 'error should not be null on failure'
    assert 'code' in d['error'], 'missing error.code'
    assert 'message' in d['error'], 'missing error.message'
" 2>/dev/null; then
    echo "[PASS] doctor 错误响应结构正确"
    PASS=$((PASS+1))
  else
    echo "[FAIL] doctor 错误响应结构不正确"
    FAIL=$((FAIL+1))
  fi
}

test_login_no_cdp() {
  OUTPUT=$(cliany-site login "https://example.com" --json 2>&1)
  EXIT_CODE=$?
  if echo "$OUTPUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert d['success']==False and d['error']['code']=='CDP_UNAVAILABLE'" 2>/dev/null; then
    echo "[PASS] login 无 CDP 时返回 CDP_UNAVAILABLE"
    PASS=$((PASS+1))
  else
    echo "[FAIL] login 无 CDP 时应返回 CDP_UNAVAILABLE"
    FAIL=$((FAIL+1))
  fi
}

test_unknown_command
test_doctor_fail_exit_code
test_json_structure
test_login_no_cdp

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
