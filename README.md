# PyBlog

Semplice generatore di blog statico scritto in Python. Converte i file Markdown
in HTML utilizzando Jinja2 e Tailwind CSS.

## Utilizzo

```
python3 generate_site.py
```

Il risultato viene scritto nella cartella `site/`.

## Plugin

È possibile estendere il sito posizionando dei frammenti di codice HTML nella
cartella `plugins/`. Ogni sottocartella rappresenta un plugin e può contenere i
file seguenti:

- `head.html` – inserito nell'elemento `<head>` di ogni pagina.
- `body.html` – inserito prima della chiusura di `<body>`.
- `static/` – cartella opzionale che verrà copiata in `site/plugins/<nome>`.

Esempio di struttura:

```
plugins/
└── esempio/
    ├── head.html
    ├── body.html
    └── static/
        └── example.css
```

I frammenti possono usare le variabili dei template Jinja2, ad esempio
`{{ base_url }}`.

Per attivare i plugin è sufficiente indicarne il nome nella chiave `plugins` di `config.yml`. Ogni voce deve corrispondere al nome di una cartella presente sotto `plugins/`.

Esempio:

```yaml
plugins:
  - example
  - cookieconsent
```

Il plugin `cookieconsent` integra la libreria [cookieconsent](https://github.com/orestbida/cookieconsent) e carica Google Analytics solo dopo il consenso. L'ID di tracciamento va specificato nella variabile `COOKIECONSENT_GA_ID` sempre nel file di configurazione.
