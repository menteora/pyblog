from pathlib import Path
import generate_site


def test_main_generates_output(monkeypatch, tmp_path):
    output = tmp_path / 'site'
    monkeypatch.setattr(generate_site, 'OUTPUT_DIR', output)
    generate_site.main()
    assert (output / 'index.html').exists()
    assert (output / 'about.html').exists()
    assert (output / 'posts').exists()
    assert (output / 'styles.css').exists()
