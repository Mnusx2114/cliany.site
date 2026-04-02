import json
from dataclasses import asdict

from cliany_site.explorer.models import RecordingManifest, StepRecord, TurnSnapshot


class TestTurnSnapshot:
    def test_turn_snapshot_creation(self):
        snapshot = TurnSnapshot(
            turn_index=1,
            actions_before_count=5,
            pages_before_count=3,
            browser_history_index=2,
        )
        assert snapshot.turn_index == 1
        assert snapshot.actions_before_count == 5
        assert snapshot.pages_before_count == 3
        assert snapshot.browser_history_index == 2

    def test_turn_snapshot_to_dict(self):
        snapshot = TurnSnapshot(
            turn_index=1,
            actions_before_count=5,
            pages_before_count=3,
            browser_history_index=2,
        )
        expected = {
            "turn_index": 1,
            "actions_before_count": 5,
            "pages_before_count": 3,
            "browser_history_index": 2,
        }
        assert asdict(snapshot) == expected


class TestStepRecord:
    def test_step_record_defaults(self):
        record = StepRecord(
            step_index=0,
            action_data={"type": "click"},
            llm_response_raw="response",
            timestamp="2023-01-01T00:00:00Z",
        )
        assert record.step_index == 0
        assert record.action_data == {"type": "click"}
        assert record.llm_response_raw == "response"
        assert record.timestamp == "2023-01-01T00:00:00Z"
        assert record.screenshot_path is None
        assert record.axtree_snapshot_path is None
        assert record.rolled_back is False

    def test_step_record_mutable(self):
        record = StepRecord(
            step_index=0,
            action_data={"type": "click"},
            llm_response_raw="response",
            timestamp="2023-01-01T00:00:00Z",
        )
        assert record.rolled_back is False
        record.rolled_back = True
        assert record.rolled_back is True


class TestRecordingManifest:
    def test_recording_manifest_creation(self):
        manifest = RecordingManifest(
            domain="example.com",
            session_id="sess123",
            url="https://example.com",
            workflow="test workflow",
            started_at="2023-01-01T00:00:00Z",
        )
        assert manifest.domain == "example.com"
        assert manifest.session_id == "sess123"
        assert manifest.url == "https://example.com"
        assert manifest.workflow == "test workflow"
        assert manifest.started_at == "2023-01-01T00:00:00Z"
        assert manifest.steps == []
        assert manifest.completed is False

    def test_recording_manifest_to_dict(self):
        manifest = RecordingManifest(
            domain="example.com",
            session_id="sess123",
            url="https://example.com",
            workflow="test workflow",
            started_at="2023-01-01T00:00:00Z",
            steps=[
                StepRecord(
                    step_index=0,
                    action_data={"type": "click"},
                    llm_response_raw="response",
                    timestamp="2023-01-01T00:00:00Z",
                )
            ],
            completed=True,
        )
        result = asdict(manifest)
        assert result["domain"] == "example.com"
        assert result["session_id"] == "sess123"
        assert result["url"] == "https://example.com"
        assert result["workflow"] == "test workflow"
        assert result["started_at"] == "2023-01-01T00:00:00Z"
        assert len(result["steps"]) == 1
        assert result["completed"] is True

    def test_step_record_json_roundtrip(self):
        original = StepRecord(
            step_index=0,
            action_data={"type": "click", "ref": "@1"},
            llm_response_raw="LLM response text",
            timestamp="2023-01-01T00:00:00Z",
            screenshot_path="/path/to/screenshot.png",
            axtree_snapshot_path="/path/to/axtree.json",
            rolled_back=False,
        )
        # Serialize to JSON
        json_str = json.dumps(asdict(original), ensure_ascii=False)
        # Deserialize from JSON
        data = json.loads(json_str)
        # Create new instance
        restored = StepRecord(**data)
        # Check equality
        assert restored.step_index == original.step_index
        assert restored.action_data == original.action_data
        assert restored.llm_response_raw == original.llm_response_raw
        assert restored.timestamp == original.timestamp
        assert restored.screenshot_path == original.screenshot_path
        assert restored.axtree_snapshot_path == original.axtree_snapshot_path
        assert restored.rolled_back == original.rolled_back
