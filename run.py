import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def get_rendered_html(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(5000)
            page.evaluate("""() => { document.querySelectorAll('script').forEach(n => n.remove()); }""")
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"⚠️ Playwright gagal: {e}, fallback ke requests")
        try:
            return requests.get(url, timeout=30).text
        except:
            return ""


def fix_relative_paths(html, base_url):
    patterns = ["css", "js", "images", "assets"]
    for folder in patterns:
        html = re.sub(rf'href=["\']{folder}/', f'href="{base_url}/{folder}/', html)
        html = re.sub(rf'src=["\']{folder}/', f'src="{base_url}/{folder}/', html)
    return html

def remove_navbar(html):
    return re.sub(r'<!-- Navbar -->.*?<!-- /Navbar -->', '', html, flags=re.DOTALL)

def replace_images(html):
    replacements = {
        "https://photoku.io/images/2025/08/13/Fjf6rkzW.png":
            "https://i.postimg.cc/HWSJVRvt/image.png",

        "https://olx29.ramalan.info/images/icon-apk.webp":
            "https://i.postimg.cc/CKXg3Cck/image-removebg-preview-1.png",

        "https://photoku.io/images/2025/08/13/bg-olx-baruu1.webp":
            "https://aix-asset.s3.ap-southeast-1.amazonaws.com/global/seamless/1626/IDR/background/331017492.png"
    }
    for old, new in replacements.items():
        html = html.replace(old, new)
    return html

def remove_olxtoto_block(html):
    return re.sub(
        r'<h1><strong>OLXTOTO.*?dengan sangat mudah di Olxtoto slot gacor\.<\/p>\s*<\/div>',
        '',
        html,
        flags=re.DOTALL
    )


def clean_with_bs(html):
    soup = BeautifulSoup(html, "html.parser")

    for mobile_div in soup.select("div.d-lg-none.d-sm-block"): mobile_div.decompose()
    for footer in soup.select("footer.text-center.text-light.py-3"): footer.decompose()
    for pagination in soup.select("div.swiper-pagination.swiper-pagination-progressbar.swiper-pagination-horizontal"): pagination.decompose()
    for slide in soup.select("div.swiper-slide"): slide.decompose()
    for slider in soup.select("div.swiper.slider-blog.swiper-initialized.swiper-horizontal.swiper-backface-hidden"): slider.decompose()
    for banner_div in soup.select("div.col-lg-5.d-none.d-lg-block"): banner_div.decompose()
    for winner in soup.select("div.winner-wrapper"): winner.decompose()
    for top_nav in soup.select("div.top-nav"): top_nav.decompose()
    for wa_link in soup.select('a[href="https://api.whatsapp.com/send?phone=6282160303218"]'): wa_link.decompose()

    for btn in soup.select("a.btn.btn-sm.btn-warning, a.btn.btn-sm.btn-danger"):
        if any(text in btn.text for text in ["RTP Slot", "Promo", "Login"]):
            btn.decompose()

    for div in soup.select("div.col-md.col-6.d-grid"):
        button = div.find("button", class_="btntabb")
        if button and not ("Result Togel" in button.text or "Prediksi Togel" in button.text):
            div.decompose()

    for span in soup.select("span.position-absolute.notify.translate-middle.badge.rounded-pill.bg-primary"):
        parent_button = span.find_parent("div", class_="col-md col-6 d-grid")
        if parent_button and parent_button.find("button"):
            btn_text = parent_button.find("button").text
            if not ("Result Togel" in btn_text or "Prediksi Togel" in btn_text):
                span.decompose()

    for tag in soup.find_all(string=True):
        if "SELAMAT DATANG DI OLXTOTO BANDAR TOGEL" in tag:
            tag.replace_with(tag.replace("SELAMAT DATANG DI OLXTOTO BANDAR TOGEL", "SELAMAT DATANG DI RESULT TOGEL HARI INI"))
        if "OLXTOTO – Situs Bandar Prediksi Togel Terjitu" in tag:
            tag.replace_with(tag.replace("OLXTOTO – Situs Bandar Prediksi Togel Terjitu", "RESULT TOGEL – Situs Bandar Prediksi Togel Terjitu"))
        if "OLXTOTO situs bandar togel dengan prediksi terbaik" in tag:
            tag.replace_with(tag.replace("OLXTOTO situs bandar togel dengan prediksi terbaik", "RESULT TOGEL situs bandar togel dengan prediksi terbaik"))

    html_str = str(soup).replace(
        'https://imgstore.io/images/2025/02/15/icon.png',
        'https://i.postimg.cc/CKXg3Cck/image-removebg-preview-1.png'
    )

    html_str = html_str.replace(
        '<button class="btn btntabb btn-warning" onclick="changeTab(\'prediksi\')"><i class="fas fa-bowling-ball"></i> Prediksi Togel</button>',
        '<a href="https://prediksi.gbg-coc.org/?page=prediksi-togel&no=1"><button class="btn btntabb btn-warning"><i class="fas fa-bowling-ball"></i> Prediksi Togel</button></a>'
    )

    return html_str


if __name__ == "__main__":
    target_url = "https://olx29.ramalan.info/"
    base_url   = "https://olx29.ramalan.info"

    html_raw = get_rendered_html(target_url)
    html_fixed = fix_relative_paths(html_raw, base_url)
    html_clean = remove_navbar(html_fixed)
    html_replaced = replace_images(html_clean)
    html_final = remove_olxtoto_block(html_replaced)

    final_html = clean_with_bs(html_final)

    url = "https://hasil.gbg-coc.org/upload.php"
    files = {"file": ("index.php", final_html.encode("utf-8"))}
    response = requests.post(url, files=files)

    print("🌍 Server response:", response.text)
