import requests
from bs4 import BeautifulSoup
import json
import re

# TODO: Implement full scraping logic

def parse_listing_html(soup):
    # Title
    title = soup.find('h1', class_='bfsTitle')
    title = title.get_text(strip=True) if title else None

    # Location
    location = soup.find('span', class_='f-l cs-800 flex-center g8 opacity-70')
    location = location.get_text(strip=True) if location else None

    # Financials
    def extract_financial(label):
        p = soup.find('span', string=label)
        if p:
            val_span = p.find_next_sibling('span')
            if not val_span:
                # Sometimes the value is in the parent <p>
                val_span = p.parent.find('span', class_='normal')
            if val_span:
                val = val_span.get_text(strip=True)
                if 'Not Disclosed' in val:
                    return None
                # Remove $ and ,
                num = re.sub(r'[^\d.]', '', val)
                try:
                    return int(float(num))
                except Exception:
                    return val
        return None

    asking_price = extract_financial('Asking Price:')
    gross_revenue = extract_financial('Gross Revenue:')
    cash_flow = extract_financial('Cash Flow (SDE):')
    ebitda = extract_financial('EBITDA:')
    established = extract_financial('Established:')

    # Seller Financing
    seller_financing = False
    seller_financing_span = soup.find('span', string=re.compile(r'Seller Financing Available', re.I))
    if seller_financing_span:
        seller_financing = True

    # Business Description
    desc_div = soup.find('div', class_='businessDescription')
    business_description = desc_div.get_text("\n", strip=True) if desc_div else None

    # Detailed Information (dl/dt/dd pairs)
    details = {}
    dl = soup.find('dl', class_='listingProfile_details')
    if dl:
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        for dt, dd in zip(dts, dds):
            label = dt.get_text(strip=True).replace(':', '')
            value = dd.get_text("\n", strip=True)
            details[label] = value

    # Map details
    inventory = details.get('Inventory')
    ffe = details.get('Furniture, Fixtures, & Equipment (FF&E)')
    employees = details.get('Employees')
    real_estate = details.get('Real Estate')
    facilities = details.get('Facilities')
    competition = details.get('Competition')
    growth_expansion = details.get('Growth & Expansion')
    financing = details.get('Financing')
    support_training = details.get('Support & Training')
    reason_for_selling = details.get('Reason for Selling')

    # Broker info from JSON-LD
    broker = None
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if 'offers' in data and 'offeredBy' in data['offers']:
                offered_by = data['offers']['offeredBy']
                broker_name = offered_by.get('name')
                company = offered_by.get('worksFor', {}).get('name')
                phone = None  # Not always available
                broker = ', '.join(filter(None, [broker_name, company, phone]))
                break
        except Exception:
            continue

    # Calculated fields
    def safe_div(a, b):
        try:
            return round(a / b, 2)
        except Exception:
            return None

    price_rev_multiple = safe_div(asking_price, gross_revenue) if asking_price and gross_revenue else None
    price_cf_multiple = safe_div(asking_price, cash_flow) if asking_price and cash_flow else None
    price_ebitda_multiple = safe_div(asking_price, ebitda) if asking_price and ebitda else None
    profit_margin = safe_div(cash_flow, gross_revenue) * 100 if cash_flow and gross_revenue else None

    return {
        "Title": title,
        "Location": location,
        "AskingPrice": asking_price,
        "GrossRevenue": gross_revenue,
        "CashFlow": cash_flow,
        "EBITDA": ebitda,
        "Established": established,
        "SellerFinancing": 'Yes' if seller_financing else 'No',
        "Inventory": inventory,
        "FF&E": ffe,
        "Employees": employees,
        "RealEstate": real_estate,
        "Facilities": facilities,
        "Competition": competition,
        "GrowthExpansion": growth_expansion,
        "Financing": financing,
        "SupportTraining": support_training,
        "ReasonForSelling": reason_for_selling,
        "Broker": broker,
        "Price/Revenue Multiple": price_rev_multiple,
        "Price/CashFlow Multiple": price_cf_multiple,
        "Price/EBITDA Multiple": price_ebitda_multiple,
        "Profit Margin %": round(profit_margin, 2) if profit_margin is not None else None,
        "BusinessDescription": business_description
    }


def scrape_listing(url):
    """
    Fetches a BizBuySell listing and returns a dict of extracted fields.
    """
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0"})
    soup = BeautifulSoup(response.text, 'html.parser')
    return parse_listing_html(soup)

# For local HTML testing (optional):
if __name__ == "__main__":
    with open("sample_listing.html", encoding="utf-8") as f:
        soup = BeautifulSoup(f, 'html.parser')
        data = parse_listing_html(soup)
        import pprint; pprint.pprint(data) 