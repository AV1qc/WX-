# /web-scraper/web-scraper/src/main.py

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class ImageParser:
    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def get_image_urls(self):
        images = self.soup.find_all('img')
        img_urls = [img.get('data-src') or img.get('src') for img in images if img.get('data-src') or img.get('src')]
        return img_urls

def download_image(img_url, folder_path, index):
    response = requests.get(img_url, stream=True)
    if response.status_code == 200:
        img_path = os.path.join(folder_path, f'图片{index}.jpg')
        with open(img_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f'Downloaded {img_url} to {img_path}')
    else:
        print(f'Failed to download {img_url}')

def download_images(url, folder_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        parser = ImageParser(response.text)
        img_urls = parser.get_image_urls()
        for index, img_url in enumerate(img_urls, start=1):
            img_url = urljoin(url, img_url)
            download_image(img_url, folder_path, index)
    else:
        print(f'Failed to retrieve the webpage: {url}')

def main():
    url = input("请输入要爬取的网页URL: ")
    save_folder = 'C:\\Users\\联想\\Desktop\\原图'

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    download_images(url, save_folder)

if __name__ == "__main__":
    main()