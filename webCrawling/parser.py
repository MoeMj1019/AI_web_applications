from bs4 import BeautifulSoup
import requests
from datetime import datetime

class InfoParser:
    def __init__(self) -> None:
        pass
    
    def get_info(self,url:str, resopnse: requests.models.Response):
        """
        extract the info from the html content
        get words and their counts
            args:
                url: str
                html_content: BeautifulSoup
            returns:
                dict of the info
        """
        # global IGNORED_WORDS

        raw_html_content = resopnse.text
        soup_html_content = BeautifulSoup(raw_html_content, "html.parser")

        text_content = soup_html_content.get_text(separator=' ', strip=True)
        # text_content = soup_html_content.text

        title_tag = soup_html_content.find('title')
        title = title_tag.text if title_tag else None
        
        description_tag = soup_html_content.find('meta', attrs={"name": "description"}) or \
                        soup_html_content.find('meta', attrs={"property": "og:description"})
        description = str(description_tag['content']) if description_tag else None
        time_stamp = datetime.now().replace(microsecond=0)

        info = {"url":url, "title":title, "description": description, "time_stamp":time_stamp, "content":text_content}
        # tokens = [stemmer.stem(word) for word in word_tokenize(text.lower())
        #                         if word.isalpha() and word not in self.stop_words]
        # tokens = re.findall(r'\b\w+\b', text.lower())
        # tokens = [word for word in tokens if word not in IGNORED_WORDS]
        # words_counts = Counter(tokens)

        return info 
