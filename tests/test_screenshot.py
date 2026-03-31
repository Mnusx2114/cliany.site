import base64

import pytest


class TestScreenshotToBase64:
    def test_empty_data_returns_empty_string(self):
        from cliany_site.browser.screenshot import screenshot_to_base64

        assert screenshot_to_base64(b"") == ""

    def test_valid_data_returns_data_url(self):
        from cliany_site.browser.screenshot import screenshot_to_base64

        data = b"\x89PNG\r\n\x1a\nfakedata"
        result = screenshot_to_base64(data, format="png")
        assert result.startswith("data:image/png;base64,")
        b64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)
        assert decoded == data

    def test_jpeg_format(self):
        from cliany_site.browser.screenshot import screenshot_to_base64

        result = screenshot_to_base64(b"fake", format="jpeg")
        assert "image/jpeg" in result


class TestScreenshotToRawBase64:
    def test_empty_data(self):
        from cliany_site.browser.screenshot import screenshot_to_raw_base64

        assert screenshot_to_raw_base64(b"") == ""

    def test_valid_data(self):
        from cliany_site.browser.screenshot import screenshot_to_raw_base64

        data = b"hello world"
        result = screenshot_to_raw_base64(data)
        assert base64.b64decode(result) == data


class TestAnnotateScreenshotWithSom:
    @pytest.fixture
    def sample_png(self):
        try:
            from io import BytesIO

            from PIL import Image
        except ImportError:
            pytest.skip("Pillow not installed")

        img = Image.new("RGB", (100, 100), (200, 200, 200))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_empty_screenshot_returns_empty(self):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som

        data, mapping = annotate_screenshot_with_som(b"", {})
        assert data == b""
        assert mapping == {}

    def test_no_bounds_returns_original(self, sample_png):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som

        selector_map = {"1": {"role": "button", "name": "Click"}}
        data, mapping = annotate_screenshot_with_som(sample_png, selector_map)
        assert len(data) > 0
        assert mapping == {}

    def test_with_bounds_annotates(self, sample_png):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som

        selector_map = {
            "1": {
                "role": "button",
                "name": "Click",
                "_bounds": {"x": 10, "y": 10, "width": 30, "height": 20},
            }
        }
        data, mapping = annotate_screenshot_with_som(sample_png, selector_map)
        assert len(data) > 0
        assert "1" in mapping
        assert mapping["1"] == "0"

    def test_max_labels_limit(self, sample_png):
        from cliany_site.browser.screenshot import annotate_screenshot_with_som

        selector_map = {
            str(i): {
                "role": "button",
                "name": f"Btn {i}",
                "_bounds": {"x": i * 2, "y": 10, "width": 10, "height": 10},
            }
            for i in range(100)
        }
        data, mapping = annotate_screenshot_with_som(
            sample_png,
            selector_map,
            max_labels=5,
        )
        assert len(mapping) == 5
