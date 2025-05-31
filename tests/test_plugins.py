import tempfile
from pathlib import Path
import generate_site


def test_load_plugins(monkeypatch):
    monkeypatch.setattr(generate_site, 'PLUGINS', ['example'])
    plugins = generate_site.load_plugins()
    assert any('Example plugin header' in s for s in plugins['head'])
    assert any('Plugin example active' in s for s in plugins['body'])


def test_copy_plugin_static(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_site, 'PLUGINS', ['example'])
    monkeypatch.setattr(generate_site, 'OUTPUT_DIR', tmp_path)
    generate_site.copy_plugin_static()
    expected_file = tmp_path / 'plugins' / 'example' / 'example.css'
    assert expected_file.exists()
