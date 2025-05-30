#!/usr/bin/env python3
"""
Generatore di sito statico da file Markdown, con styling basato su Tailwind CSS.
Legge la configurazione da config.yml per base_url, cartelle di contenuto e directory di output.
Crea automaticamente i template di base (se non esistono), genera sample content se mancante, e genera pagine e post.
Struttura consigliata:
.
├── content
│   ├── pages      # .md per pagine statiche (es. about.md)
│   └── posts      # .md per i post (nomi: YYYY-MM-DD-titolo.md)
├── templates      # generato automaticamente la prima volta
│   ├── base.html
│   ├── page.html
│   ├── post.html
│   └── index.html
├── config.yml     # configurazione di base_url, directory etc.
└── generate_site.py  # questo script
"""
import sys
import shutil
from pathlib import Path
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Carica configurazione
CONFIG_PATH = Path('config.yml')
if not CONFIG_PATH.exists():
    print("Errore: file 'config.yml' non trovato.")
    sys.exit(1)
with CONFIG_PATH.open(encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Parametri da config
BASE_URL      = config.get('base_url', '/')
OUTPUT_DIR    = Path(config.get('output_dir', 'site/'))
CONTENT_PAGES = Path(config['content']['pages'])
CONTENT_POSTS = Path(config['content']['posts'])
SITE_TITLE    = config.get('site', {}).get('title', 'Il Mio Blog')

# Se cartelle mancanti o vuote, crea sample content
for dir_path, sample_file, sample_content in [
    (CONTENT_PAGES, 'about.md', '# About\n\nBenvenuto sul mio blog! Scrivi qui le informazioni sulla tua pagina About.'),
    (CONTENT_POSTS, f"{datetime.now():%Y-%m-%d}-hello-world.md", '# Hello World\n\nQuesto è il tuo primo post! Scrivilo in Markdown.'),
]:
    dir_path.mkdir(parents=True, exist_ok=True)
    if not any(dir_path.iterdir()):
        sample_path = dir_path / sample_file
        sample_path.write_text(sample_content, encoding='utf-8')
        print(f"Creato sample: {sample_path}")

TEMPLATE_DIR = Path('templates')

def ensure_templates():
    """Verifica la presenza dei template richiesti"""
    required = ['base.html', 'page.html', 'post.html', 'index.html']
    if not TEMPLATE_DIR.exists():
        print("Errore: cartella 'templates' non trovata.")
        sys.exit(1)
    missing = [f for f in required if not (TEMPLATE_DIR / f).exists()]
    if missing:
        print(f"Errore: mancano i seguenti template: {', '.join(missing)}")
        sys.exit(1)

def load_templates():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals['now'] = datetime.now()
    env.globals['base_url'] = BASE_URL
    env.globals['site_title'] = SITE_TITLE
    return env

def render_pages(env):
    """Genera le pagine statiche da CONTENT_PAGES"""
    for md_file in CONTENT_PAGES.glob('*.md'):
        text = md_file.read_text(encoding='utf-8')
        html_content = markdown.markdown(text, extensions=['fenced_code'])
        lines = text.splitlines()
        title = lines[0].lstrip('# ').strip() if lines and lines[0].startswith('#') else md_file.stem.title()
        out_file = OUTPUT_DIR / f"{md_file.stem}.html"
        tpl = env.get_template('page.html')
        html = tpl.render(title=title, content=html_content)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding='utf-8')

def render_posts(env):
    """Genera i post da CONTENT_POSTS e ritorna metadata"""
    posts = []
    for md_file in CONTENT_POSTS.glob('*.md'):
        text = md_file.read_text(encoding='utf-8')
        html_content = markdown.markdown(text, extensions=['fenced_code'])
        lines = text.splitlines()
        title = lines[0].lstrip('# ').strip() if lines and lines[0].startswith('#') else md_file.stem
        date_str = md_file.stem[:10]
        date = datetime.strptime(date_str, '%Y-%m-%d')
        url = f"posts/{md_file.stem}.html"
        tpl = env.get_template('post.html')
        html = tpl.render(title=title, date=date.strftime('%d %B %Y'), content=html_content)
        out_file = OUTPUT_DIR / url
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding='utf-8')
        posts.append({'title': title, 'date': date, 'url': url})
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

def render_index(env, posts):
    """Genera index.html con lista dei post"""
    tpl = env.get_template('index.html')
    posts_meta = [
        {'title': p['title'], 'date': p['date'].strftime('%d %B %Y'), 'url': p['url']}
        for p in posts
    ]
    html = tpl.render(title="Home", posts=posts_meta)
    out_file = OUTPUT_DIR / 'index.html'
    out_file.write_text(html, encoding='utf-8')

def main():
    ensure_templates()
    env = load_templates()
    # Pulisce output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    # Genera pagine e post
    render_pages(env)
    posts = render_posts(env)
    render_index(env, posts)
    print(f"Generazione completata in [{OUTPUT_DIR}]/ con template in [templates]/. Base URL: {BASE_URL}")

if __name__ == '__main__':
    main()
