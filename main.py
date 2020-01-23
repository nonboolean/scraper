"""
Data to grab on each page of a thread:
    * author of each post
    * timestamp of each post
    * who liked each post (store in the likes matrix) {
        Three cases to check for:
            - no likes: 
            - <= 3 likes
            - > 3 likes
    }
    * what posters are co-occurring (store in the author_overlap matrix)
Want to store:
    * Co-occurring likes
    * Co-occurring posts
    * how many threads were made over time
    * how many posts were made over time
    * has thread length jas changed over time
"""

import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup as bs4
import random
import time
from datetime import datetime
import pickle

BASE_URL = "https://forums.civfanatics.com/"
OT_URL =  urljoin(BASE_URL, "forums/off-topic.18/")
HEADERS = {
    'user-agent': '',
    'referer': '',
}

user2id = {}
user2likes = {}
day2posts = {}
coposts = {}

get_likes = lambda likers: [l.text.strip() for l in likers]

def checkpoint():
    with open('likes.pickle', 'wb') as f:
        pickle.dump(user2likes, f, protocol=pickle.HIGHEST_PROTOCOL)

    with open('days.pickle', 'wb') as f:
        pickle.dump(day2posts, f, protocol=pickle.HIGHEST_PROTOCOL)  

def get_page_parser(url):
    print("Visiting {}...".format(url))
    delay = random.uniform(0, 3)
    time.sleep(delay)
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    html = res.content
    parser = bs4(html, 'html.parser')
    return parser

def parse_likes_page(post_id):
    url = urljoin(BASE_URL, "/posts/" + str(post_id) + "/likes")
    parser = get_page_parser(url)
    likers = parser.findAll('a', {'class': 'username StatusTooltip'})
    likers = get_likes(likers)
    return likers

def parse_post(post):
    author = post['data-author']
    post_id = post["id"].split('-')[1]

    date_tag = post.find('a', {'class': 'datePermalink'})
    datestr = date_tag.text.split("at")[0].strip()
    timestamp = datetime.strptime(datestr, '%b %d, %Y')
    if (timestamp not in day2posts.keys()):
        day2posts[timestamp] = 1
    else:
        day2posts[timestamp] += 1
    likes = post.find('span', {'class': 'LikeText'})
    if (likes is not None):
        likers = likes.findAll('a')
        if (len(likers) <= 3):
            likers = get_likes(likers)
        else:
            likers = parse_likes_page(post_id)
        for l in likers:
            if not l in user2likes:
                user2likes[l] = {}
            if not author in user2likes[l]:
                user2likes[l][author] = 1
            else:
                user2likes[l][author] += 1

def parse_page(parser):
    posts = parser.findAll("li", {"class": "message"})
    for post in posts:
        parse_post(post)

def parse_thread(thread_url):
    parser = get_page_parser(thread_url)
    parse_page(parser)
    nav = parser.find('div', {'class': 'PageNav'})
    if (nav is not None):
        num_pages = int(nav['data-last'])
        for i in range(2, num_pages + 1):
            page_url = urljoin(thread_url, 'page-' + str(i))
            parser = get_page_parser(page_url)
            parse_page(parser)

    checkpoint()

def parse_board_page():
    start = time.time()
    parser = get_page_parser(OT_URL)
    threads = parser.findAll("a", {"class": "PreviewTooltip"})
    for t in threads:
        url = urljoin(BASE_URL, t['href'])
        parse_thread(url)
    end = time.time()
    print("Time: {} seconds".format(end - start))

def main():
    '''Set up to just check the first page of OT;
    not coded to crawl the entire board.
    '''
    parse_board_page()
    checkpoint()      

if __name__ == '__main__':
    main()
