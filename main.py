import json
from urllib.parse import urlencode
from requests import get
from bs4 import BeautifulSoup as BS
from json import loads
import instaloader
from celery import Celery
import psycopg2
from celery.__main__ import main


class InstagramScraper:
    def getData(self, instagramUrl):
        global url
        response = get(instagramUrl)
        soup = BS(response.text, 'html.parser')
        scripts = soup.find_all('script')
        data_script = scripts[4]
        content = data_script.contents[0]
        data = content[content.find('{"config"'):-1]
        data_loads = loads(data)
        data_json = data_loads['entry_data']['ProfilePage'][0]['graphql']['user']
        userID = data_json['id']
        posts = data_json['edge_owner_to_timeline_media']['count']
        postsInfo = []
        with open('data.json', 'a+') as outfile:
            for post in range(0, 12):
                likesNComments = {
                'Likes': data_json['edge_owner_to_timeline_media']['edges'][post]['node']['edge_liked_by'],
                'Comments': data_json['edge_owner_to_timeline_media']['edges'][post]['node'][
                    'edge_media_to_comment']}
                postsInfo.append(likesNComments)
        next_page_bool = data_json['edge_owner_to_timeline_media']['page_info']['has_next_page']
        if next_page_bool:
            cursor = data_json['edge_owner_to_timeline_media']['page_info']['end_cursor']
            querykeys = {'id': userID, 'first': 12, 'after': cursor}
            params = {'query_hash': '56a7068fea504063273cc2120ffd54f3', 'variables': json.dumps(querykeys)}
            url = 'https://www.instagram.com/graphql/query/?' + urlencode(params)
        self.morePosts(url, posts, userID, data_json, postsInfo)

    def getPostInfo(self, url, userID, firstCount, data_json, postsInfo):
        response = get(url)
        data = loads(response.text)
        for post in range(0, firstCount):
            likesNComments = {
                "Likes": data['data']['user']['edge_owner_to_timeline_media']['edges'][post]['node'][
                    'edge_media_preview_like'][
                    'count'],
                "Comments": data['data']['user']['edge_owner_to_timeline_media']['edges'][post]['node'][
                    'edge_media_to_comment'][
                    'count']
            }
            postsInfo.append(likesNComments)
        return self.getUrl(data, userID, firstCount, data_json, postsInfo)

    def morePosts(self, url, posts, userID, data_json, postInfo):
        if posts >= 24:
            url = self.getPostInfo(url, userID, 12, data_json, postInfo)
        else:
            url = self.getPostInfo(url, userID, posts - 13, data_json, postInfo)
        for counter in range(23, posts - 1, 12):
            if counter+12 <= posts-1:
                url = self.getPostInfo(url, userID, 12, data_json, postInfo)
            else:
                url = self.getPostInfo(url, userID, (posts - counter) - 1, data_json, postInfo)
        self.toJson(data_json, postInfo)
        # self.followersList(data_json, postInfo)

    def toJson(self, data_json, postInfo):
        print("Printing to file...")
        profileInfo = {
                "Username": data_json['username'],
                "Followers amount": str(data_json['edge_followed_by']),
                "Followed by": str(data_json['edge_follow']),
                "Post amount": data_json['edge_owner_to_timeline_media']['count'],
                "Posts": postInfo,
                # "Followers": followList
                }
        profile = [{
            "Profile Info": profileInfo
        }]
        with open('data.json', 'a+') as outfile:
            json.dump(profile, outfile, indent=4)

    def getUrl(self, data, userID, firstCount, data_json, postInfo):
        next_page_bool = data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        if next_page_bool:
            cursor = data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
            queryKeys = {'id': userID, 'first': firstCount, 'after': cursor}
            params = {'query_hash': '56a7068fea504063273cc2120ffd54f3', 'variables': json.dumps(queryKeys)}
            url = 'https://www.instagram.com/graphql/query/?' + urlencode(params)
            return url



    # def logIn(self):
    #     listOfAccounts = []
    #     logIns = instaloader.Instaloader()
    #     LogInInfo = [("crawy159", "crawy1597"),
    #                 ("vardaspavarde159", "vardaspavarde1597"),
    #                 ("vardenispavardenis159", "vardenispavardenis1597")]
    #
    #     for log in LogInInfo:
    #         username, password = log
    #         logIns.login(username, password)
    #         listOfAccounts.append(logIns)
    #     return listOfAccounts

    # def followersList(self, data_json, postInfo):
    #     global profile
    #     follow_list = []
    #     count = 0
    #     index = 0
    #     listOfAccounts = self.logIn()
    #     for account in listOfAccounts:
    #         profile = instaloader.Profile.from_username(account.context, "norbefilms")
    #     print(profile.get_followees())
    #     for followee in profile.get_followers():
    #         follow_list.append(followee.username)
    #         if count == 12:
    #             print("sleeping...")
    #             time.sleep(3.5)
    #             count = 0
    #             print(index)
    #         count = count + 1
    #         index += 1
    #     self.toJson(data_json, postInfo, follow_list)
    def getInfoFromDb(self):
        POSTGRES_HOST = "localhost:5432"
        POSTGRES_USER = "agenic_backoffice_service"
        POSTGRES_PASSWORD = "postgres"
        POSTGRES_DB = "agenic"
        conn = psycopg2.connect(dbname = POSTGRES_DB, user = POSTGRES_USER, password = POSTGRES_PASSWORD)
        cur = conn.cursor()
        someInfo = cur.execute("select * from account_emailaddress")
        print(someInfo)
        conn.commit()
        cur.close()
        conn.close()


if __name__ == "__main__":
    pass
    url = "https://www.instagram.com/norbefilms/"
    InstagramScraperObject = InstagramScraper
    # InstagramScraperObject.getInfoFromDb(InstagramScraper)
    InstagramScraperObject.getData(InstagramScraper(), url)


