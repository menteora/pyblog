import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))
import generate_site

pytestmark = pytest.mark.skipif('cookieconsent' not in generate_site.PLUGINS, reason='cookieconsent plugin not active')


def test_ga_id_rendered(monkeypatch):
    monkeypatch.setattr(generate_site, 'PLUGINS', ['cookieconsent'])
    env = generate_site.load_templates()
    ga_id = generate_site.config['COOKIECONSENT_GA_ID']
    assert any(ga_id in snippet for snippet in env.globals['plugins_body'])
