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
import os
import argparse
from PIL import Image
import re

PLUGINS_DIR = Path('plugins')

# Carica configurazione
CONFIG_PATH = Path('config.yml')
if not CONFIG_PATH.exists():
    print("Errore: file 'config.yml' non trovato.")
    sys.exit(1)
with CONFIG_PATH.open(encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Plugin attivi elencati nel file di configurazione
PLUGINS = config.get('plugins', [])

# Parametri da config
BASE_URL      = os.getenv('PYBLOG_BASE_URL', config.get('base_url', '/'))
OUTPUT_DIR    = Path(config.get('output_dir', 'site/'))
CONTENT_PAGES = Path(config['content']['pages'])
CONTENT_POSTS = Path(config['content']['posts'])
SITE_TITLE    = config.get('site', {}).get('title', 'Il Mio Blog')
POSTS_PER_PAGE = config.get('posts_per_page', 5)

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

def load_plugins():
    """Carica solo i plugin indicati in config.yml"""
    head, body = [], []
    if not PLUGINS_DIR.exists():
        return {'head': head, 'body': body}
    for name in PLUGINS:
        plugin_dir = PLUGINS_DIR / name
        if not plugin_dir.is_dir():
            continue
        head_file = plugin_dir / 'head.html'
        body_file = plugin_dir / 'body.html'
        if head_file.exists():
            head.append(head_file.read_text(encoding='utf-8'))
        if body_file.exists():
            body.append(body_file.read_text(encoding='utf-8'))
    return {'head': head, 'body': body}

def copy_plugin_static():
    """Copia eventuali cartelle static dei plugin attivi"""
    if not PLUGINS_DIR.exists():
        return
    for name in PLUGINS:
        plugin_dir = PLUGINS_DIR / name
        static_dir = plugin_dir / 'static'
        if static_dir.is_dir():
            dest = OUTPUT_DIR / 'plugins' / plugin_dir.name
            shutil.copytree(static_dir, dest, dirs_exist_ok=True)

def copy_global_static():
    """Copia i file presenti nella cartella 'static' nella cartella di output"""
    static_dir = Path('static')
    if not static_dir.is_dir():
        return
    for item in static_dir.iterdir():
        dest = OUTPUT_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

def optimize_images():
    """Genera versioni ottimizzate delle immagini presenti in static/images."""
    images_src = Path('static/images')
    if not images_src.is_dir():
        return

    dest_dir = OUTPUT_DIR / 'images'
    dest_dir.mkdir(parents=True, exist_ok=True)

    for img_path in images_src.iterdir():
        if not img_path.is_file():
            continue
        dest_original = dest_dir / img_path.name
        shutil.copy2(img_path, dest_original)

        if img_path.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
            continue
        try:
            img = Image.open(img_path)
        except Exception as e:
            print(f"Errore apertura immagine {img_path}: {e}")
            continue

        for label, width in {'mobile': 480, 'desktop': 1280}.items():
            resized = dest_dir / f"{img_path.stem}-{label}{img_path.suffix}"
            im = img.copy()
            im.thumbnail((width, width * 10000))
            im.save(resized, optimize=True, quality=85)

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = str(value)
    value = value.strip().lower()
    value = re.sub(r'[^\w\s-]', '', value) # Remove non-alphanumeric, non-space, non-hyphen
    value = re.sub(r'[-\s]+', '-', value) # Replace spaces and hyphens with a single hyphen
    return value

def load_templates():
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals['now'] = datetime.now()
    env.globals['base_url'] = BASE_URL
    env.globals['site_title'] = SITE_TITLE
    env.globals['config'] = config
    env.filters['slugify'] = slugify # Add slugify as a filter for templates if needed
    plugins = load_plugins()
    env.globals['plugins_head'] = [env.from_string(s).render() for s in plugins['head']]
    env.globals['plugins_body'] = [env.from_string(s).render() for s in plugins['body']]
    return env

def apply_responsive_images(html: str) -> str:
    """Aggiunge attributi srcset per le immagini sotto 'images/'."""
    pattern = re.compile(r'<img([^>]+)src="(?P<src>images/[^">]+)"([^>]*)>')

    def repl(match):
        src = match.group('src')
        stem, ext = os.path.splitext(Path(src).name)
        srcset = (
            f"images/{stem}-mobile{ext} 480w, "
            f"images/{stem}-desktop{ext} 1280w, "
            f"images/{stem}{ext} 1920w"
        )
        replacement = (
            f'<img{match.group(1)}src="images/{stem}-mobile{ext}" '
            f'srcset="{srcset}" sizes="(max-width: 600px) 480px, 1280px"'
            f'{match.group(3)}>'
        )
        return replacement

    return pattern.sub(repl, html)

def render_pages(env):
    """Genera le pagine statiche da CONTENT_PAGES e copia i Markdown"""
    for md_file in CONTENT_PAGES.glob('*.md'):
        text = md_file.read_text(encoding='utf-8')
        html_content = markdown.markdown(text, extensions=['fenced_code'])
        lines = text.splitlines()
        title = lines[0].lstrip('# ').strip() if lines and lines[0].startswith('#') else md_file.stem.title()
        out_file = OUTPUT_DIR / f"{md_file.stem}.html"
        tpl = env.get_template('page.html')
        html = tpl.render(title=title, content=html_content)
        html = apply_responsive_images(html)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding='utf-8')
        # Conserva anche i sorgenti markdown nella cartella di output
        md_out = OUTPUT_DIR / 'pages' / md_file.name
        md_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(md_file, md_out)

def render_posts(env):
    """Genera i post da CONTENT_POSTS, copia i sorgenti Markdown e ritorna metadata"""
    posts = []
    for md_file in CONTENT_POSTS.glob('*.md'):
        full_text = md_file.read_text(encoding='utf-8')
        lines = full_text.splitlines()
        
        post_tags = []
        content_to_render = full_text
        
        if lines and lines[0].lower().startswith('tags:'):
            tag_line = lines[0][len('tags:'):].strip()
            post_tags = [tag.strip().lower() for tag in tag_line.split(',') if tag.strip()]
            content_to_render = "\n".join(lines[1:])

        html_content = markdown.markdown(content_to_render, extensions=['fenced_code'])
        
        # Determina il titolo: prima linea H1 del contenuto da renderizzare o nome file
        content_lines = content_to_render.splitlines()
        title = content_lines[0].lstrip('# ').strip() if content_lines and content_lines[0].startswith('#') else md_file.stem
        
        date_str = md_file.stem[:10] # Assumendo formato YYYY-MM-DD-titolo.md
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            # Se il nome del file non inizia con una data valida, usa la data di oggi o gestisci l'errore
            # Per ora, saltiamo questo post o usiamo una data di default se non è critico
            print(f"Attenzione: formato data non riconosciuto per {md_file.name}. Uso data odierna.")
            date = datetime.now() # o imposta None e gestisci nel template/sorting

        url = f"posts/{md_file.stem}.html"
        
        post_data = {
            'title': title,
            'date': date,
            'url': url,
            'tags': post_tags, # Lista dei tag per questo post
            'content': html_content # Contenuto HTML già renderizzato
        }

        tpl = env.get_template('post.html')
        # Passa i dati del post, inclusi i tag, al template del singolo post
        html_page_content = tpl.render(
            title=post_data['title'],
            date=post_data['date'].strftime('%d %B %Y'),
            content=post_data['content'],
            tags=post_data['tags'] # Assicurati che post.html possa usare questo
        )
        html_page_content = apply_responsive_images(html_page_content)
        
        out_file = OUTPUT_DIR / url
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html_page_content, encoding='utf-8')
        
        # Copia il file markdown originale (senza la riga Tags per coerenza se deciso)
        # o l'originale completo. Per ora, copiamo l'originale completo.
        md_out = OUTPUT_DIR / 'posts' / md_file.name
        md_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(md_file, md_out)
        
        # Aggiungi i metadati completi del post (inclusi i tag grezzi e contenuto) alla lista
        # 'content' qui si riferisce al contenuto HTML per il template del post, non per l'elenco.
        posts.append(post_data) 
        
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

def render_index(env, posts):
    """Genera index.html con lista dei post e paginazione"""
    tpl = env.get_template('index.html')
    total_posts = len(posts)
    total_pages = (total_posts + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    for page_num in range(1, total_pages + 1):
        start_index = (page_num - 1) * POSTS_PER_PAGE
        end_index = start_index + POSTS_PER_PAGE
        current_posts = posts[start_index:end_index]

        posts_meta = [
            {'title': p['title'], 'date': p['date'].strftime('%d %B %Y'), 'url': p['url']}
            for p in current_posts
        ]

        context = {
            'title': "Home" if page_num == 1 else f"Home - Pagina {page_num}",
            'posts': posts_meta,
            'current_page': page_num,
            'total_pages': total_pages
        }

        if page_num == 1:
            out_file = OUTPUT_DIR / 'index.html'
        else:
            page_dir = OUTPUT_DIR / 'page'
            page_dir.mkdir(parents=True, exist_ok=True)
            out_file = page_dir / f'{page_num}.html'
        
        html = tpl.render(context)
        html = apply_responsive_images(html)
        out_file.write_text(html, encoding='utf-8')

def render_index_markdown(posts):
    """Crea un file Markdown con la lista dei post (tutti i post, non paginato)"""
    lines = [f"# {SITE_TITLE}", ""]
    for p in posts:
        line = f"- [{p['title']}]({BASE_URL}{p['url']}) - {p['date'].strftime('%d %B %Y')}"
        lines.append(line)
    md_out = OUTPUT_DIR / 'index.md'
    md_out.write_text("\n".join(lines), encoding='utf-8')

def collect_all_tags_data(posts):
    """Aggrega i dati dei tag da tutti i post."""
    tags_data = {}
    for post in posts:
        # Assicurati che 'date' sia un oggetto datetime per strftime
        post_date_str = post['date'].strftime('%d %B %Y') if isinstance(post['date'], datetime) else post['date']
        
        post_summary = {
            'title': post['title'],
            'url': post['url'],
            'date': post['date'] # Manteniamo l'oggetto datetime per eventuali ordinamenti futuri
        }
        for tag_name in post.get('tags', []):
            slugified_tag = slugify(tag_name)
            if slugified_tag not in tags_data:
                tags_data[slugified_tag] = {'name': tag_name, 'posts': [], 'count': 0}
            tags_data[slugified_tag]['posts'].append(post_summary)
            tags_data[slugified_tag]['count'] += 1
    
    # Ordina i post per ciascun tag per data decrescente
    for tag_info in tags_data.values():
        tag_info['posts'].sort(key=lambda p: p['date'], reverse=True)

    return tags_data

def render_tag_pages(env, all_tags_data):
    """Genera pagine HTML per ogni tag."""
    tpl = env.get_template('tag.html')
    tags_output_dir = OUTPUT_DIR / 'tags'
    tags_output_dir.mkdir(parents=True, exist_ok=True)

    for slugified_tag, tag_info in all_tags_data.items():
        # Per il template tag.html, i post necessitano che la data sia formattata
        # Quindi creiamo una copia dei post con la data formattata per questo contesto specifico
        posts_for_template = []
        for post_meta in tag_info['posts']:
            formatted_post = post_meta.copy() # Evita di modificare l'originale in all_tags_data
            if isinstance(post_meta['date'], datetime):
                 formatted_post['date_str'] = post_meta['date'].strftime('%d %B %Y') # Usato nel template tag.html
            else: # se fosse già stringa per qualche motivo
                 formatted_post['date_str'] = post_meta['date']
            posts_for_template.append(formatted_post)

        html_content = tpl.render(
            tag_name=tag_info['name'],
            posts=posts_for_template, # Usa la lista con date formattate
            # title=f"Posts tagged with '{tag_info['name']}'" # Il titolo è gestito nel template
        )
        html_content = apply_responsive_images(html_content)
        out_file = tags_output_dir / f"{slugified_tag}.html"
        out_file.write_text(html_content, encoding='utf-8')

def render_tags_list_page(env, all_tags_data):
    """Genera la pagina HTML che elenca tutti i tag."""
    tpl = env.get_template('tags_list.html')
    
    # Prepara i dati dei tag per il template: nome, URL, conteggio
    tags_for_list_page = sorted([
        {'name': data['name'], 'url': f"tags/{slugify(data['name'])}.html", 'count': data['count']}
        for slug, data in all_tags_data.items()
    ], key=lambda t: t['name'])


    html_content = tpl.render(
        tags=tags_for_list_page,
        # title="All Tags" # Il titolo è gestito nel template
    )
    html_content = apply_responsive_images(html_content)
    out_file = OUTPUT_DIR / 'tags.html'
    out_file.write_text(html_content, encoding='utf-8')

def main():
    ensure_templates()
    env = load_templates() # env ora ha slugify come filtro globale
    
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    copy_global_static()
    optimize_images()
    copy_plugin_static()
    
    render_pages(env)
    posts = render_posts(env) # posts ora contiene i metadati dei tag per ciascun post
    
    all_tags_data = collect_all_tags_data(posts)
    render_tag_pages(env, all_tags_data)
    render_tags_list_page(env, all_tags_data)
    
    render_index(env, posts) # render_index usa i post originali con oggetti datetime
    render_index_markdown(posts) # Anche questo
    
    print(f"Generazione completata in [{OUTPUT_DIR}]/ con template in [templates]/. Base URL: {BASE_URL}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate the static site")
    parser.add_argument("--base-url", help="Override base_url from config or env")
    args = parser.parse_args()

    if args.base_url:
        BASE_URL = args.base_url
    main()
