import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))
import generate_site

pytestmark = pytest.mark.skipif('example' not in generate_site.PLUGINS, reason='example plugin not active')


def test_example_snippets(monkeypatch):
    monkeypatch.setattr(generate_site, 'PLUGINS', ['example'])
    plugins = generate_site.load_plugins()
    assert any('Example plugin header' in s for s in plugins['head'])
    assert any('Plugin example active' in s for s in plugins['body'])


def test_example_static_copy(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_site, 'PLUGINS', ['example'])
    monkeypatch.setattr(generate_site, 'OUTPUT_DIR', tmp_path)
    generate_site.copy_plugin_static()
    expected = tmp_path / 'plugins' / 'example' / 'example.css'
    assert expected.exists()

def test_example_snippet_in_generated_site(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_site, 'PLUGINS', ['example'])
    monkeypatch.setattr(generate_site, 'OUTPUT_DIR', tmp_path)
    generate_site.main()
    html = (tmp_path / 'index.html').read_text(encoding='utf-8')
    assert 'Plugin example active' in html
    assert 'plugins/example/static/example.css' in html
