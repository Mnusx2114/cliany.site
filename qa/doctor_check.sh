#!/bin/bash
# 验证 cliany-site 安装和基础环境
PASS=0; FAIL=0

check_installed() {
  if command -v cliany-site &>/dev/null; then
    echo "[PASS] cliany-site 已安装"
    PASS=$((PASS+1))
  else
    echo "[FAIL] cliany-site 未安装"
    FAIL=$((FAIL+1))
  fi
}

check_version() {
  OUTPUT=$(cliany-site --version 2>&1)
  if echo "$OUTPUT" | grep -q "0\."; then
    echo "[PASS] cliany-site --version 输出: $OUTPUT"
    PASS=$((PASS+1))
  else
    echo "[FAIL] cliany-site --version 失败: $OUTPUT"
    FAIL=$((FAIL+1))
  fi
}

check_doctor_json() {
  OUTPUT=$(cliany-site doctor --json 2>&1)
  if echo "$OUTPUT" | python3 -m json.tool &>/dev/null; then
    echo "[PASS] doctor --json 输出有效 JSON"
    PASS=$((PASS+1))
  else
    echo "[FAIL] doctor --json 未返回有效 JSON"
    FAIL=$((FAIL+1))
  fi
  # 验证返回 JSON 格式（有 success 字段）
  if echo "$OUTPUT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); assert 'success' in d" 2>/dev/null; then
    echo "[PASS] doctor 返回包含 'success' 字段"
    PASS=$((PASS+1))
  else
    echo "[FAIL] doctor 返回缺少 'success' 字段"
    FAIL=$((FAIL+1))
  fi
}

check_dirs() {
  if [ -d ~/.cliany-site/adapters ] && [ -d ~/.cliany-site/sessions ]; then
    echo "[PASS] ~/.cliany-site/ 目录结构正确"
    PASS=$((PASS+1))
  else
    echo "[FAIL] ~/.cliany-site/ 目录不完整"
    FAIL=$((FAIL+1))
  fi
}

check_installed
check_version
check_doctor_json
check_dirs

echo ""
echo "=== 结果 ==="
echo "PASS: $PASS, FAIL: $FAIL"
[ $FAIL -eq 0 ] && exit 0 || exit 1
