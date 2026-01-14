import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


@dataclass
class Listing:
    company: str
    role: str
    location: str
    apply_link: str
    date_posted: str

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "role": self.role,
            "location": self.location,
            "apply_link": self.apply_link,
            "date_posted": self.date_posted,
        }

    @staticmethod
    def from_dict(data: dict) -> "Listing":
        return Listing(
            company=data["company"],
            role=data["role"],
            location=data["location"],
            apply_link=data["apply_link"],
            date_posted=data["date_posted"],
        )

    def __eq__(self, other):
        if not isinstance(other, Listing):
            return False
        return (
            self.company == other.company
            and self.role == other.role
            and self.location == other.location
        )


def scrape_canadian_internships(url: str) -> list[Listing]:
    """Scrape the Canadian Tech Internships repo."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table inside markdown-accessiblity-table
    table = soup.find("markdown-accessiblity-table")
    if not table:
        raise ValueError("Could not find internship table")

    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("Could not find table body")

    listings = []
    rows = tbody.find_all("tr")[:20]

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        company = cells[0].get_text(strip=True)
        role = cells[1].get_text(strip=True)
        location = cells[2].get_text(strip=True)

        # Apply link is in the 4th cell
        apply_cell = cells[3]
        apply_link_tag = apply_cell.find("a")
        apply_link = apply_link_tag["href"] if apply_link_tag else ""

        date_posted = cells[4].get_text(strip=True)

        listings.append(
            Listing(
                company=company,
                role=role,
                location=location,
                apply_link=apply_link,
                date_posted=date_posted,
            )
        )

    return listings


def scrape_us_internships(url: str) -> list[Listing]:
    """Scrape the SimplifyJobs US Internships repo."""
    response = requests.get(url, headers=HEADERS, timeout=300)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table inside markdown-accessiblity-table
    table = soup.find("markdown-accessiblity-table")
    if not table:
        raise ValueError("Could not find internship table")

    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("Could not find table body")

    listings = []
    rows = tbody.find_all("tr")[:20]

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        company = cells[0].get_text(strip=True)
        role = cells[1].get_text(strip=True)
        location = cells[2].get_text(strip=True)

        # Apply link is in the 4th cell, inside a div
        apply_cell = cells[3]
        apply_link_tag = apply_cell.find("a")
        apply_link = apply_link_tag["href"] if apply_link_tag else ""

        date_posted = cells[4].get_text(strip=True)

        listings.append(
            Listing(
                company=company,
                role=role,
                location=location,
                apply_link=apply_link,
                date_posted=date_posted,
            )
        )

    return listings
