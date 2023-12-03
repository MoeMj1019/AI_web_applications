from bs4 import BeautifulSoup
import requests
from datetime import datetime

class InfoParser:
    def __init__(self) -> None:
        pass
    
    def get_info_from_response(self,url:str, resopnse: requests.models.Response):
        """
        extract the info from the html content
        get words and their counts
            args:
                url: str
                html_content: BeautifulSoup
            returns:
                dict of the info
        """
        raw_html_content = resopnse.text

        return self.get_info_from_html(url, raw_html_content)
    
        soup_html_content = BeautifulSoup(raw_html_content, "html.parser")

        text_content = soup_html_content.get_text(separator=' ', strip=True)
        # text_content = soup_html_content.text

        title_tag = soup_html_content.find('title')
        title = title_tag.text if title_tag else None
        
        description_tag = soup_html_content.find('meta', attrs={"name": "description"}) or \
                        soup_html_content.find('meta', attrs={"property": "og:description"})
        description = str(description_tag.get('content', None)) if description_tag else None
        time_stamp = datetime.now().replace(microsecond=0)

        info = {"url":url, "title":title, "description": description, "time_stamp":time_stamp, "content":text_content}
        return info 
    
    def get_info_from_html(self, url:str, html_content:str):
        """
        extract the info from the html content
        get words and their counts
            args:
                url: str
                html_content: str
            returns:
                dict of the info
        """
        soup_html_content = BeautifulSoup(html_content, "html.parser")
        text_content = soup_html_content.get_text(separator=' ', strip=True)
        # text_content = soup_html_content.text

        title_tag = soup_html_content.find('title')
        title = title_tag.text if title_tag else None
        
        description_tag = soup_html_content.find('meta', attrs={"name": "description"}) or \
                        soup_html_content.find('meta', attrs={"property": "og:description"})
        description = str(description_tag.get('content', None)) if description_tag else None
        time_stamp = datetime.now().replace(microsecond=0)

        info = {"url":url, "title":title, "description": description, "time_stamp":time_stamp, "content":text_content}
        return info

