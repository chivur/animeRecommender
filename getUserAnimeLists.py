import urllib
import re
import xmltodict
from bs4 import BeautifulSoup
import sys
from datetime import datetime
import MySQLdb

INF = 50000

# db connection
db = MySQLdb.connect("192.168.0.104","razvan","constantin","anime")

# filenames
users_file = "_usrs_2.txt"


# gets the animeList of user
# return type: dict
def getUserAnimeList(username):
    
    url = "http://myanimelist.net/malappinfo.php?u=" + username + "&status=all&type=anime"
    data = urllib.urlopen(url).read()
    return xmltodict.parse(data)
    
    
    
# gets the mean score and days watched
# for the user
# return type: (float,float)
def getUserMeanScoreAndDays(username):
    url = "https://myanimelist.net/profile/" + username
    data = urllib.urlopen(url).read()
    soup = BeautifulSoup(data,"html.parser")
    html_tags = soup.find_all("div", class_="stat-score di-t w100 pt8")
    return (float(html_tags[0].get_text().split("\n")[2][12::].replace(',','')),float(html_tags[0].get_text().split("\n")[1][6::].replace(',','')))
    
    
    
#   ########################################
#     Parse myanimelist entries from dict
#   ########################################
    
# returns "My Info" from a dict entry
def getMyInfo(entry):
    return entry['myanimelist']['myinfo']

# returns user_name
def getUsername(entry):
    return entry['myanimelist']['myinfo']['user_name']

# returns user_id
def getUserId(entry):
    return entry['myanimelist']['myinfo']['user_id']

# returns user_completed
def getUserCompleted(entry):
    return entry['myanimelist']['myinfo']['user_completed']

# returns user_plantowatch
def getUserPlantowatch(entry):
    return entry['myanimelist']['myinfo']['user_plantowatch']

# returns user_days_spent_watching
def getUserDaysSpentWatching(entry):
    return entry['myanimelist']['myinfo']['user_days_spent_watching']

# returns animes info
def getUserAnimes(entry):
    return entry['myanimelist']['anime']

# returns anime info for anime idx
def getUserAnime(entry,idx):
    return entry['myanimelist']['anime'][idx]

# returns anime id for anime idx
def getUserAnimeId(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_animedb_id']

def getUserAnimeTitle(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_title']

# returns a list of synonims for the title
def getUserAnimeSynonims(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_synonyms'].split("; ")

def getUserAnimeImageURL(entry,idx):
    return entry['myanimelist']['anime'][idx]['series_image']

def getUserAnimeWatchedEpisodes(entry,idx):
    return entry['myanimelist']['anime'][idx]['my_watched_episodes']

def getUserAnimeScore(entry,idx):
    return entry['myanimelist']['anime'][idx]['my_score']

def getUserAnimeTags(entry,idx):
    return entry['myanimelist']['anime'][idx]['my_tags']

    
def main():

    file = open(users_file)
    users = file.read().split("\n")
    file.close()
    
    cursor = db.cursor()
    query = ""
    
    
    u_idx=0
    for user in users:
        print u_idx
        u_idx+=1
        [mean_score,days_spent] = getUserMeanScoreAndDays(user)
        animeList = getUserAnimeList(user)
        user_id = getUserId(animeList)
        completed = getUserCompleted(animeList)
        if(days_spent>0 and int(completed) > 1):
            animes = getUserAnimes(animeList)
            qry = "insert into users values(%s,\'%s\',%s,%s,%s)" %(int(user_id),user,int(completed),float(days_spent),float(mean_score))
            #print qry
            try:
                cursor.execute(qry)
                db.commit()
            except:
                db.rollback()
            for i in range(len(animes)):
                anime_id = getUserAnimeId(animeList,i)
                rating = getUserAnimeScore(animeList,i)
                query = "insert into user_history values(%s,%s,%s)" %(int(user_id),int(anime_id),int(rating))
                #print query
                try:
                    cursor.execute(query)
                    db.commit()
                except:
                    db.rollback()
            
    #print "done"
    
    
main()


    