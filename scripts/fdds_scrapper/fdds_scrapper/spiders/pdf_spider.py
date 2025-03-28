import scrapy
from typing import Any


class RegionMainSpider(scrapy.Spider):
    """
    Spider to scrape educational courses and check for PDF links.

    This spider starts by scraping a set of predefined category pages,
    extracts all course links, and checks if they contain PDF links.
    If a PDF is found, the URL is saved in the 'pdfs.txt' file.
    If a non-PDF link is encountered, the spider performs
    double-check to ensure all relevant PDF links are captured.
    """

    name = "get_pdf_links"
    start_urls = [
        "https://edukacja.fdds.pl/course/index.php?categoryid=29",
        "https://edukacja.fdds.pl/course/index.php?categoryid=30",
        "https://edukacja.fdds.pl/course/index.php?categoryid=32",
    ]

    def start_requests(self):
        """
        Initial request handler for the start URLs.

        This method starts scraping from the list of start
        URLs defined in `start_urls`. It prints each URL being scraped
        and yields a request to scrape the page.
        The response is passed to the `parse` method.
        """
        for url in self.start_urls:
            yield scrapy.Request(url, meta={"playwright": True}, callback=self.parse)

    def parse(self, response, **kwargs: Any):
        """
        Parse the main category page and extract course links.

        This method extracts all the links from the category page and follows
        each of them to check if they contain PDF links.
        Each URL is followed and the response is passed to `check_for_pdfs`.

        Args:
            response (scrapy.http.Response):
                The response object containing the HTML content of the page.
        """
        urls = response.css("#region-main a::attr(href)").getall()

        for url in urls:
            absolute_url = response.urljoin(url)
            print(absolute_url)
            yield scrapy.Request(
                absolute_url,
                meta={"playwright": True},
                callback=self.check_for_pdfs,
                dont_filter=True,
            )

    def check_for_pdfs(self, response):
        """
        Check the page for PDF links under the course content section.

        This method checks if any links on the course page are pointing to PDFs.
        It does so by looking for links under the `#coursecontentcollapse0`.
        If PDF links are found, they are passed to `check_if_pdf` for
        further validation.

        Args:
            response (scrapy.http.Response):
                The response object containing the HTML content of the page.
        """
        links = response.css("#coursecontentcollapse0 a::attr(href)").getall()

        for link in links:
            absolute_url = response.urljoin(link)
            yield scrapy.Request(absolute_url, callback=self.check_if_pdf)

    def check_if_pdf(self, response):
        """
        Check if the content type of the response is PDF.

        This method checks the `Content-Type` of the response to
        determine if it's a PDF. If the content type is `application/pdf`,
        it saves the URL in a file called `pdfs.txt`.
        If the content type is not a PDF, it performs double-check by
        following additional links on the page.

        Args:
            response (scrapy.http.Response):
                The response object containing the content of the PDF or another page.
        """
        content_type = response.headers.get("Content-Type")
        if content_type and b"application/pdf" in content_type:
            with open("pdfs.txt", "a+") as f:
                f.write(response.url + "\n")
        else:
            print(f"Performing double check for: {response.url}")
            yield scrapy.Request(
                response.url,
                dont_filter=True,
                callback=self.double_check_for_pdfs,
            )

    def double_check_for_pdfs(self, response):
        """
        Perform a second-level check for PDF links if the first check fails.

        This method will check for PDF links on a different part of the page
        (the `#region-main` section) in case the initial check for
        PDF links didn't work. It will follow all relevant links on
        the page and pass the responses to `last_check_if_pdf`.

        Args:
            response (scrapy.http.Response):
                The response object containing the HTML content of the page.
        """
        links = response.css("#region-main a::attr(href)").getall()
        for link in links:
            absolute_url = response.urljoin(link)
            yield scrapy.Request(absolute_url, callback=self.last_check_if_pdf)

    def last_check_if_pdf(self, response):
        """
        Perform a final check to determine if the page content is a PDF.

        This is the last step in the double-check process.
        If a page is found to be a PDF after additional checks,
        the URL will be saved to `pdfs.txt`

        Args:
            response (scrapy.http.Response):
                The response object containing the content of the page.
        """
        content_type = response.headers.get("Content-Type")
        if content_type and b"application/pdf" in content_type:
            with open("pdfs.txt", "a+") as f:
                f.write(response.url + "\n")
