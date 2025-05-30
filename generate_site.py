#!/usr/bin/env python3
"""
Generatore di sito statico da file Markdown, con styling basato su Tailwind CSS.
Crea automaticamente i template di base (se non esistono) e genera pagine e post.
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
└── generate_site.py  # questo script
"""
import shutil
from pathlib import Path
import markdown
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# Percorsi
CONTENT_DIR   = Path('content')
PAGES_DIR     = CONTENT_DIR / 'pages'
POSTS_DIR     = CONTENT_DIR / 'posts'
TEMPLATES_DIR = Path('templates')
OUTPUT_DIR    = Path('site')

# Template di default
_BASE_HTML = """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-900 font-sans">
  <div class="container mx-auto px-4 py-8">
    <header class="mb-8">
      <h1 class="text-4xl font-bold"><a href="/" class="text-blue-600 hover:underline">Il Mio Blog</a></h1>
      <nav class="mt-4">
        <a href="/" class="mr-4 hover:text-blue-600">Home</a>
        <a href="/about.html" class="hover:text-blue-600">About</a>
      </nav>
    </header>
    <main>
      {% block content %}{% endblock %}
    </main>
    <footer class="mt-12 text-center text-sm text-gray-500">
      &copy; {{ now.year }} Il Mio Blog. Tutti i diritti riservati.
    </footer>
  </div>
</body>
</html>"""

_PAGE_HTML = """{% extends 'base.html' %}
{% block content %}
<article class="prose lg:prose-xl bg-white p-8 rounded shadow">
  {{ content | safe }}
</article>
{% endblock %}"""

_POST_HTML = """{% extends 'base.html' %}
{% block content %}
<article class="prose lg:prose-xl bg-white p-8 rounded shadow">
  <h2 class="text-2xl font-bold mb-2">{{ title }}</h2>
  <p class="text-sm text-gray-500 mb-4">{{ date }}</p>
  {{ content | safe }}
</article>
{% endblock %}"""

_INDEX_HTML = """{% extends 'base.html' %}
{% block content %}
<section class="mb-8">
  <h2 class="text-3xl font-bold mb-4">Ultimi Post</h2>
  <ul>
  {% for post in posts %}
    <li class="mb-2">
      <a href="{{ post.url }}" class="text-xl text-blue-600 hover:underline">{{ post.title }}</a>
      <span class="text-sm text-gray-500"> - {{ post.date }}</span>
    </li>
  {% endfor %}
  </ul>
</section>
{% endblock %}"""

def init_templates():
    """Crea i file di template se non esistono"""
    TEMPLATES_DIR.mkdir(exist_ok=True)
    templates = {
        'base.html':   _BASE_HTML,
        'page.html':   _PAGE_HTML,
        'post.html':   _POST_HTML,
        'index.html':  _INDEX_HTML,
    }
    for name, content in templates.items():
        path = TEMPLATES_DIR / name
        if not path.exists():
            path.write_text(content, encoding='utf-8')

def load_templates():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals['now'] = datetime.now()
    return env

def render_pages(env):
    """Genera le pagine statiche da content/pages"""
    for md_file in PAGES_DIR.glob('*.md'):
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
    """Genera i post da content/posts e ritorna metadata"""
    posts = []
    for md_file in POSTS_DIR.glob('*.md'):
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
    # Verifica struttura
    if not CONTENT_DIR.exists():
        print("Errore: crea la cartella 'content' con sottocartelle 'pages' e 'posts' e i tuoi .md.")
        return
    init_templates()
    env = load_templates()
    # Pulisce output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    # Genera pagine e post
    render_pages(env)
    posts = render_posts(env)
    render_index(env, posts)
    print("Generazione completata in [site]/ con template in [templates]/")

if __name__ == '__main__':
    main()
