import json
import requests
import time
from utils import log
from utils.utils import parse_date
from network import twitch_api


class TwitchChannel:
    def __init__(self, USERID):
        self.USERID = USERID
        self.follows = []

        self.verified_follows = {}
        self.probable_bots = {}
        self.confirmed_bots = {}

    def detect_bot(self):
        """
        Perform a full verification of the twitch account followers
        :return:
        """

        # Massive data Fetch

        log.notice("Collecting All follows [Initial Fetch]")
        self.follows = twitch_api.fetch_follows(self.USERID, limit=20000)

        # Adding all flags
        log.notice("Adding flags entry..")
        for user_id in self.follows:
            self.add_flag_entry(user_id)

        log.notice("Converting dates to Unix Timestamp..")
        for user_id in self.follows:
            self.convert_dates(user_id)

        log.notice("Looking for follow blob..")
        for user_id in self.follows:
            self.follow_blob(user_id)

        log.notice("Looking for suspicious follow - account creation interval")
        for user_id in self.follows:
            self.creation_to_follow_interval(user_id)

        """
        log.notice("Expanding Database : Adding User Data [Step 2/2 Initial Data Fetch]")
        self.expand_user()

        log.warning("Warning : This next step may take a long time.")
        log.notice("Expanding Database : Adding Stream and Account Data [Step 3/3 Initial Data Fetch]")
        self.expand_stream()
        """
        log.notice("End of checking.")

    def follow_blob(self, user_id, threshold=100, spacing=5):
        """

        :param user_id:
        :param threshold:
        :param spacing:
        :return:
        """

        amount = 0
        follow_date = self.follows[user_id]["created_at"]

        # Looking for > amount follow blob
        for follow in self.follows:
            if user_id != follow:
                if abs(follow_date - self.follows[follow]["created_at"]) < spacing:
                    amount += 1

        # Registering flag
        self.follows[user_id]['flags']['in_follow_blob'] = amount >= threshold

        # Logging
        if self.follows[user_id]['flags']['in_follow_blob']:
            log.warning(f"{self.follows[user_id]['user']['name']} : In follow blob ({amount} follows in a {spacing}s radius)")





    def convert_dates(self, user_id):
        self.follows[user_id]['user']['created_at'] = parse_date(str(self.follows[user_id]['user']['created_at'][0:18]+"Z"))
        self.follows[user_id]['user']['updated_at'] = parse_date(str(self.follows[user_id]['user']['updated_at'][0:18]+"Z"))
        self.follows[user_id]['created_at'] = parse_date(self.follows[user_id]['created_at'][0:18]+"Z")


    def add_flag_entry(self, user_id):
        self.follows[user_id]['flags'] = {}


    def creation_to_follow_interval(self, user_id, threshold=30):
        """
        Checks the difference beetween account creation and follow
        :param threshold:
        :return: Bool
        """
        creation = self.follows[user_id]['user']['created_at']
        follow = self.follows[user_id]['created_at']
        self.follows[user_id]['flags']['suspect_c_to_f_interval'] = follow - creation < threshold
        # Logging Suspicious
        if self.follows[user_id]['flags']['suspect_c_to_f_interval']:
            log.warning(f"Suspicious creation/follow interval for {self.follows[user_id]['user']['display_name']}")

    def expand_user(self):
        """
        Add user data to unverified follow list
        :return:
        """
        for user in twitch_api.fetch_users(list(self.follows)):
            try:
                self.follows[user['id']]['user_data'] = user
            except Exception as err:
                log.warning(f"Error getting user info for {user} : {err}")



    def expand_stream(self):
        """
        Add Stream data to unverified follow list
        :return:
        """
        # This step takes a long time. Logging Progress
        i = 0
        for follow in self.follows:
            # Sleep to avoid burning V5 API Poll rate (much higher than V6)
            time.sleep(0.1)
            log.log(f"Getting Stream Data for {follow} - [{round(i / len(self.follows) * 100, 2)}%]")
            query = twitch_api.streams(follow)
            self.follows[follow]['stream_data'] = query
            i += 1


    def expand_social(self):
        """
        Add Followed/Followers to unverified follow list
        :return:
        """

        progress = 0
        total = len(self.follows)

        for follow in self.follows:
            try:
                progress += 1
                log.log(f"Fetching Social connection from {follow} [{round(progress / total * 100, 2)}%]")

                self.follows[follow]['social'] = {}
                self.follows[follow]['social']['followed_by'] = twitch_api.fetch_follows(follow)
                self.follows[follow]['social']['is_following'] = twitch_api.fetch_following(follow)

            except Exception as err:
                log.warning(f"Error fetching follows {follow} : {err}")
