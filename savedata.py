import MySQLdb
from datetime import datetime

db = MySQLdb.connect("localhost","root","","anime")
cursor = db.cursor()

# indexes for animes table
ANIME_ID_IDX = 0
ANIME_TITLE_IDX = 1
ANIME_RANK_IDX = 2
ANIME_RATING_IDX = 3
ANIME_EPISODE_NUMBER_IDX = 4
ANIME_IMAGE_URL_IDX = 5
ANIME_GENRES_IDX = 6

# indexes for user table
USER_ID_IDX = 0
USER_NAME_IDX = 1
USER_COMPLETED_IDX = 2
USER_DAYS_SPENT_IDX = 3
USER_MEAN_SCORE_IDX = 4

# indexes for user_history table
HISTORY_USER_ID_IDX = 0
HISTORY_ANIME_ID_IDX = 1
HISTORY_ANIME_RATING_IDX = 2

# indexes for AnimeRating objects
ANIME_ID_IDX = 0
RATING_IDX = 1

# minimum number of common animes betwen 2 users for similarity to be calculated
COMMON_THRESHOLD = 0


# general info from an anime
class Anime:

    def __init__(self,id,title,rank,rating,episodeNumber,imageURL,genres):
        self.id = id
        self.title = title
        self.rank = rank
        self.rating = rating
        self.episodeNumber = episodeNumber
        self.imageURL = imageURL
        self.genres = genres


class User:

    def __init__(self,id,name,completed,daysSpent,meanScore,animeRatings):
        self.id = id
        self.name = name
        self.completed = completed
        self.daysSpent = daysSpent
        self.meanScore = meanScore
        self.animeRatings = animeRatings #list of Anime objects : use ANIME_ID_IDX,RATING_IDX for selection
        self.animeIDs = self.getAnimeIDs()
    
    
    # return all animeIDs of watched ones
    def getAnimeIDs(self):
        lst=[]
        for anime in self.animeRatings:
            lst.append(anime[ANIME_ID_IDX])
        return lst
            
    # return list of common anime ids of current user and otherUsr
    def getCommonAnimes(self,otherUsr):
        return list(set(self.animeIDs)&set(otherUsr.animeIDs))

    # returns similarity coeficient betwen current user and otherUsr
    def getSimilarityBetwenUsers(self,otherUsr):
        common = self.getCommonAnimes(otherUsr)
        meanScore = self.meanScore
        otherMeanScore = otherUsr.meanScore
        
        # go further only if number of common animes is higher than COMMON_THRESHOLD
        if len(common) < COMMON_THRESHOLD:
            return -1
        
        # for all common animes
        #   take all (rating - userMeanScore) product (from both users)
        #   and sum them
        # divide that sum by mean squared error

        # get all common animeRatings
        selfCommon = [[animeId,animeRating] for [animeId,animeRating] in self.animeRatings if animeId in common]
        otherCommon = [[animeId,animeRating] for [animeId,animeRating] in otherUsr.animeRatings if animeId in common]
        selfCommon.sort()
        otherCommon.sort()
        
        sum=0
        selfErr=0
        otherErr=0
        
        for i in range(len(common)):
            selfDif = selfCommon[i][RATING_IDX] - meanScore 
            otherDif = otherCommon[i][RATING_IDX] - otherMeanScore
            sum += selfDif * otherDif
            #print "sum+= " , `sum`
            selfErr += selfDif**2
            #print "selfErr+= " , `selfErr`
            otherErr += otherDif**2
            #print "otherErr +=" , `otherErr`
            
        return float(sum) / ((selfErr**0.5)*(otherErr**0.5))
            
        
def getUserData():

    users = []
    
    fl = 0 ###
    cursor.execute("SELECT * FROM USERS")
    history_cursor = db.cursor()
    for item in cursor:
        fl = fl + 1###
        if fl==5:###
            break;###
        id,name,completed,daysSpent,meanScore =  [int(item[USER_ID_IDX]), item[USER_NAME_IDX],
        int(item[USER_COMPLETED_IDX]), float(item[USER_DAYS_SPENT_IDX]), float(item[USER_MEAN_SCORE_IDX])]
        
        query = "SELECT * FROM USER_HISTORY WHERE USER_ID = %s" %int(id)
        history_cursor.execute(query)
        animes = []
        for animeIt in history_cursor:
            id,anime_id,user_rating = [int(animeIt[HISTORY_USER_ID_IDX]),int(animeIt[HISTORY_ANIME_ID_IDX]),
            int(animeIt[HISTORY_ANIME_RATING_IDX])]
            animes.append([anime_id,user_rating])
        
        # here we have generic data from user + his anime list
        # so we can build the lists / user object
 
        users.append(User(id,name,completed,daysSpent,meanScore,animes))

    return users    
        
def pickleAnimeData():
    pass

def getAnimeRatingStr(animeR):
    str="{"
    for an in animeR:
        str += `an.id` + " " + `an.rating` + "\t"
    str += "}"
    return str
    
def printUserData(user):
    str = `user.id` + " " +  user.name + " " + `user.completed` + " " + `user.daysSpent` + " " + `user.meanScore` + "->"
    str += getAnimeRatingStr(user.animeRatings)
    print str

def main():

    start = datetime.now()
    usrs =  getUserData()
    stop = datetime.now()
    dif = stop-start
    print "getUserData --> ", `dif.seconds`
    #print usrs[0].id
    #for us in usrs:
     #   printUserData(us)
    
    start = datetime.now()
    
    for us in usrs:
        us.id = 0
    
    stop = datetime.now()
    dif = stop-start
    print "passing --> ", `dif.seconds`
    
    r1 = [[1,8],[2,7],[3,7]] 
    r2 = [[1,8],[2,7]]
    r3 = [[1,10],[2,10],[3,7]]
    
    u1 = User(1,"a",1,1,7,r1)
    u2 = User(2,"b",2,2,5,r2)
    u3 = User(3,"c",1,1,7,r3)
    
    
    print "SIM: "
    print u1.getSimilarityBetwenUsers(u2)
    #print len(u1.getCommonAnimes(u2))
    print u1.getSimilarityBetwenUsers(u3)
    #print len(u1.getCommonAnimes(u3))
    
    print "done"

if __name__ == "__main__":
    main()