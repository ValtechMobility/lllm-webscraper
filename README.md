# LLM Webscraper

This tool is designed to look through interactive websites on the hunt for downloadable information.

## Functionality

The scraper recursively follows these general steps:
1. download the current state of a website
2. save all links that directly lead to .pdf files
3. feed the state of the website into a prompted LLM
4. let the LLM rank elements of the page by how interesting they look
5. click on an interesting element and go back to 1. for the new state of the website

It should track which states of the website it has already seen. After reaching a defined depth it stops.

## Set up the environment

Install UV if you havent already

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Source the virtual environment

```bash
uv venv
source .venv/bin/activate
```

Install the required packages

```bash
uv pip install requests beautifulsoup4 playwright
```

Install the browser binary for playwright

```bash
playwright install
```

## Run the scraper

Simply run it with python. make sure to use the correct link you want to try out in the main-py file.

```bash
python main.py
```
