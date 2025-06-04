# PyBlog

Semplice generatore di blog statico scritto in Python. Converte i file Markdown
in HTML utilizzando Jinja2 e Tailwind CSS.

## Utilizzo

```
python3 generate_site.py
```

Il risultato viene scritto nella cartella indicata da `output_dir` in `config.yml` (di default `site/`).

Per visualizzare in locale il sito generato è disponibile lo script `serve_site.py`:

```bash
python3 serve_site.py
```

Il server utilizza la stessa cartella indicata da `output_dir` (per default `site/`) e per default espone la porta `8000`.

### Gestione ambienti

Per sovrascrivere la `base_url` definita in `config.yml` senza modificare il file
si può usare la variabile d'ambiente `PYBLOG_BASE_URL` oppure l'opzione
`--base-url` dello script:

```bash
PYBLOG_BASE_URL=http://localhost:8000/ python3 generate_site.py
# oppure
python3 generate_site.py --base-url http://localhost:8000/
```

## Plugin

È possibile estendere il sito posizionando dei frammenti di codice HTML nella
cartella `plugins/`. Ogni sottocartella rappresenta un plugin e può contenere i
file seguenti:

- `head.html` – inserito nell'elemento `<head>` di ogni pagina.
- `body.html` – inserito prima della chiusura di `<body>`.
- `static/` – cartella opzionale che verrà copiata in `<output_dir>/plugins/<nome>` (dove `<output_dir>` è definito in `config.yml`).

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

## Cartella `static`

Nel repository è presente anche una cartella `static/` destinata a eventuali
asset statici globali del sito. Contiene un semplice README solo per mantenere
la directory sotto version control.

### Ottimizzazione immagini

Le immagini possono essere posizionate in `static/images/`. Durante la
generazione del sito il comando `generate_site.py` copierà tali file nella
cartella `images/` del sito e produrrà automaticamente versioni ridotte per
mobile (`*-mobile`) e per desktop (`*-desktop`). Nei Markdown e nei template
riferisci quindi le immagini con percorso `images/nomefile.ext` per ottenere
una gestione responsive tramite `srcset`.

## Test

Prima di generare il sito è consigliato eseguire i test automatici tramite lo
script `run_tests.py`:

```bash
python run_tests.py
```

Lo script esegue i test del core e quindi quelli dei plugin elencati in
`config.yml`. Ogni plugin può definire i propri test nella cartella
`plugins/<nome>/tests/`.

## Tailwindcss per la produzione
https://tailwindbuild.programmerbee.com/