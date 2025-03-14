from scraper import PDFScraper

def main():
    website_url = website_url = "https://www.deutsche-evergabe.de/dashboards/dashboard_off/52bae542-3b05-4535-9d3f-7cc57847c8e4"

    scraper = PDFScraper()
    pdf_links = scraper.scrape_website(website_url)

    print("\nFound PDF links:")
    for link in pdf_links:
        print(link)

    # Optionally save to file
    with open('pdf_links.txt', 'w') as f:
        for link in pdf_links:
            f.write(f"{link}\n")

if __name__ == "__main__":
    main()
