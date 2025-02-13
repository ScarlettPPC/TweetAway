import json
from twikit import Client

bookmarkedTweets = []
loggedUser = {}


class TwitterClient:
    """Wrapper around the Twikit Client for interacting with Twitter."""

    def __init__(self, cookie_file: str):
        """Initialize the client with cookies loaded from a JSON file."""
        with open(cookie_file, "r") as file:
            cookies = json.load(file)  # Load cookies from the JSON file
        self.client = Client(language='en-US', cookies=cookies)  # Pass cookies to the Client
        

    async def create_tweet(self, content: str, image_paths: list = [], alt_texts: list = [], reply_to: str = None, attachment_url: str = None):
        """Post a tweet using the Twikit Client, optionally quoting another tweet."""
        print(f"Quoting tweet with URL: {attachment_url}")
        try:
            media_id = []

            # If images are provided, upload the images and get the media IDs
            if image_paths:
                image_paths = [x for x in image_paths if x]
                media_id = await self.upload_media(image_paths, alt_texts)

            # Post the tweet with media, reply-to, or quoted tweet
            if attachment_url:
                if media_id:
                    response = await self.client.create_tweet(
                        text=content, media_ids=media_id, attachment_url=attachment_url
                    )
                else:
                    response = await self.client.create_tweet(
                        text=content, attachment_url=attachment_url
                    )
            elif reply_to:
                if media_id:
                    response = await self.client.create_tweet(
                        text=content, media_ids=media_id, reply_to=reply_to
                    )
                else:
                    response = await self.client.create_tweet(
                        text=content, reply_to=reply_to
                    )
            else:
                if media_id:
                    response = await self.client.create_tweet(
                        text=content, media_ids=media_id
                    )
                else:
                    response = await self.client.create_tweet(
                        text=content
                    )

            return response  # Return the response (tweet object or ID)
        except Exception as e:
            raise RuntimeError(f"Error posting tweet: {e}")
        
    async def retweet(self, tweet_id: str):
        try:
            response = await self.client.retweet(
                tweet_id=tweet_id
            )
            return response  # Return the response (tweet object or ID)
        except Exception as e:
            raise RuntimeError(f"Error retweeting: {e}")

    async def upload_media(self, image_paths: list = [], alt_texts: list = []):
        """Upload an image to Twitter and return the media ID."""
        try:
            # Upload the image to Twitter
            media_response = []
            for image_path in image_paths:
                media_response.append(await self.client.upload_media(image_path))

            # If alt text is provided, set it for the image
            if alt_texts:
                for index, image_path in enumerate(image_paths):
                    await self.client.create_media_metadata(
                        media_id=media_response[index],
                        alt_text=alt_texts[index],
                    )
            else:
                await self.client.create_media_metadata(
                    media_id=media_response[0],
                )
            return media_response  # Return the media ID

        except Exception as e:
            raise RuntimeError(f"Error uploading media: {e}")

    async def get_home_feed(self, count: int = 20, seen_tweet_ids: list[str] = None, cursor: str = None):
        """Fetch the home timeline using async get_latest_timeline."""
        try:
            bookmarkedTweets = await self.client.get_bookmarks(count=count)
            # Fetch the timeline using the Twikit method
            timeline_result = await self.client.get_latest_timeline(
                count=count,
                seen_tweet_ids=seen_tweet_ids,
                cursor=cursor,
            )
            tweets = timeline_result  # Extract the list of Tweet objects
            if not timeline_result:
                raise RuntimeError("Twikit returned no tweets. Check your authentication.")

            # Serialize tweets to a JSON-compatible format
            serialised_tweets = []
            for tweet in tweets:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'author': tweet.user.name,
                    'username': tweet.user.screen_name,
                    'created_at': tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at),
                    'is_quote': tweet.is_quote_status,
                    'in_reply_to': tweet.in_reply_to is not None,
                    'is_liked': tweet.favorited,
                }

                # Handle quotes
                if tweet.is_quote_status == True and tweet.quote is not None:
                    try:
                        tweet_data['quoted_tweet'] = {
                            'id': tweet.quote.id,
                            'text': tweet.quote.full_text,
                            'author': tweet.quote.user.name,
                            'username': tweet.quote.user.screen_name,
                            'created_at': tweet.quote.created_at.isoformat() if hasattr(tweet.quote.created_at, 'isoformat') else str(tweet.quote.created_at),
                        }
                    except Exception as e:
                        tweet_data['quoted_tweet_error'] = f"Error fetching quoted tweet: {e}"
                else:
                    tweet_data['quoted_tweet'] = None  # Ensure this key exists even if no quote

                # Handle replies
                if tweet.in_reply_to:
                    try:
                        reply_tweet = await self.client.get_tweet_by_id(tweet.in_reply_to)
                        tweet_data['reply_to'] = {
                            'id': reply_tweet.id,
                            'text': reply_tweet.full_text,
                            'author': reply_tweet.user.name,
                            'username': reply_tweet.user.screen_name,
                            'created_at': reply_tweet.created_at.isoformat() if hasattr(reply_tweet.created_at, 'isoformat') else str(reply_tweet.created_at),
                        }
                    except Exception as e:
                        tweet_data['reply_to_error'] = f"Error fetching reply tweet: {e}"

                if hasattr(tweet, 'media') and tweet.media:
                    media_urls = [media['media_url_https'] for media in tweet.media if 'media_url_https' in media]
                    tweet_data['media_urls'] = media_urls  # Add media URLs to the tweet data
                    
                    
                #Handle if a tweet is bookmarked
                for bookmark in bookmarkedTweets:
                    if tweet.id == bookmark.id:
                        tweet_data['is_bookmarked'] = True 
                        print(tweet.id + " " + bookmark.id) 
                        break
                    else:
                        tweet_data['is_bookmarked'] = False

                serialised_tweets.append(tweet_data)
                
        # Return serialized tweets along with pagination cursor
            return {
                'tweets': serialised_tweets
            }

        except Exception as e:
            raise RuntimeError(f"Error fetching home feed: {e}")
        
    async def get_bookmarks(self, count: int = 20):
        """Fetch the home timeline using async get_latest_timeline."""
        try:
            # Fetch the timeline using the Twikit method
            bookmarks_result = await self.client.get_bookmarks(
                count=count
            )
            tweets = bookmarks_result  # Extract the list of Tweet objects
            if not bookmarks_result:
                raise RuntimeError("Twikit returned no bookmarks. Check your authentication.")

            # Serialize tweets to a JSON-compatible format
            serialised_tweets = []
            for tweet in tweets:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'author': tweet.user.name,
                    'username': tweet.user.screen_name,
                    'created_at': tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at),
                    'quote': tweet.quote,
                    'is_liked': tweet.favorited,
                    'is_bookmarked': True,
                }

                if hasattr(tweet, 'media') and tweet.media:
                    media_urls = [media['media_url_https'] for media in tweet.media if 'media_url_https' in media]
                    tweet_data['media_urls'] = media_urls  # Add media URLs to the tweet data

                serialised_tweets.append(tweet_data)
                
        # Return serialized tweets
            return {
                'tweets': serialised_tweets
            }

        except Exception as e:
            raise RuntimeError(f"Error fetching home feed: {e}")
        
    async def get_notifications(self, count: int = 20):
        """Fetch the home timeline using async get_latest_timeline."""
        try:
            # Fetch the timeline using the Twikit method
            notifications_result = await self.client.get_notifications(
                type='All',
                count=count
            )
            notifications = notifications_result  # Extract the list of Tweet objects
            if not notifications_result:
                raise RuntimeError("Twikit returned no notifications. Check your authentication.")

            # Serialize tweets to a JSON-compatible format
            serialized_notifications = []
            for notification in notifications:
                if notification.from_user:
                    context_id = notification.tweet.id
                    print(context_id)
                    notification_data = {
                        'id': notification.id,
                        'message': notification.message,
                        'from_user': notification.from_user.name,
                        'context_text': notification.tweet.text,
                        'context_id': str(context_id),
                    }
                else:
                    notification_data = {
                        'id': notification.id,
                        'message': notification.message,
                    }
                    
                serialized_notifications.append(notification_data)
                print(serialized_notifications)
        # Return serialized tweets along with pagination cursor
            return {
                'notifications': serialized_notifications
            }

        except Exception as e:
            raise RuntimeError(f"Error fetching notifications: {e}")
            
    async def like_tweet(self, tweet_id: str):
        """Like a tweet using the Twikit Client."""
        try:
            # Send a like to the tweet
            await self.client.favorite_tweet(tweet_id)
        except Exception as e:
            raise RuntimeError(f"Error liking tweet: {e}")
        
    async def bookmark_tweet(self, tweet_id: str):
        """Bookmark a tweet using the Twikit Client."""
        try:
            # Bookmark the tweet
            await self.client.bookmark_tweet(tweet_id)
        except Exception as e:
            raise RuntimeError(f"Error bookmarking tweet: {e}")
        
    async def unbookmark_tweet(self, tweet_id: str):
        """Delete a bookmarked tweet using the Twikit Client."""
        try:
            # Send a like to the tweet
            await self.client.delete_bookmark(tweet_id)
        except Exception as e:
            raise RuntimeError(f"Error deleting bookmark: {e}")
        
    async def unlike_tweet(self, tweet_id: str):
        """Undo like of a tweet using the Twikit Client."""
        try:
            # Send a like to the tweet
            await self.client.unfavorite_tweet(tweet_id)
        except Exception as e:
            raise RuntimeError(f"Error unliking tweet: {e}")
        
    async def follow_user(self, user_id: str):
        """Follow a user."""
        try:
            print(f"following user" + user_id)
            await self.client.follow_user(user_id)
        except Exception as e:
            raise RuntimeError(f"Error following user: {e}")
        
    async def unfollow_user(self, user_id: str):
        """Unfollow a user."""
        try:
            await self.client.unfollow_user(user_id)
        except Exception as e:
            raise RuntimeError(f"Error unfollowing user: {e}")
        
    async def block_user(self, user_id: str):
        """Block a user."""
        try:
            await self.client.block_user(user_id)
        except Exception as e:
            raise RuntimeError(f"Error blocking user: {e}")
        
    async def unblock_user(self, user_id: str):
        """Unblock a user."""
        try:
            await self.client.unblock_user(user_id)
        except Exception as e:
            raise RuntimeError(f"Error unblocking user: {e}")
        
    async def get_user(self):
        try:
           
            profile = await self.client.user()
            
            return {
            'name': profile.name,
            'username': profile.screen_name,
            'profile_image_url': profile.profile_image_url,
            'followers': profile.followers_count,
            'following': profile.following_count,
            'is_followable': False,
            }
            
        except Exception as e:
            raise RuntimeError(f"Error retrieving user: {e}")
        
    async def get_tweet(self, tweet_id):
        try:
           
            tweet = await self.client.get_tweet_by_id(tweet_id)
            
            tweet_data = {
            'id': tweet.id,
            'text': tweet.full_text,
            'author': tweet.user.name,
            'username': tweet.user.screen_name,
            'created_at': tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at),
            'reply_count': tweet.reply_count,
            'view_count': tweet.view_count,
            'quote_count': tweet.quote_count,
            'retweet_count': tweet.retweet_count,
            'likes_count': tweet.favorite_count,
            'is_quote': tweet.is_quote_status,
            'is_liked': tweet.favorited,
            }
            
            #Check if a tweet is quoting another tweet
            if tweet.is_quote_status == True and tweet.quote is not None:
                    try:
                        tweet_data['quoted_tweet'] = {
                            'id': tweet.quote.id,
                            'text': tweet.quote.full_text,
                            'author': tweet.quote.user.name,
                            'username': tweet.quote.user.screen_name,
                            'created_at': tweet.quote.created_at.isoformat() if hasattr(tweet.quote.created_at, 'isoformat') else str(tweet.quote.created_at),
                            'reply_count': tweet.quote.reply_count,
                            'view_count': tweet.quote.view_count,
                            'quote_count': tweet.quote.quote_count,
                            'retweet_count': tweet.quote.retweet_count,
                            'likes_count': tweet.quote.favorite_count,
                        }
                    except Exception as e:
                        tweet_data['quoted_tweet_error'] = f"Error fetching quoted tweet: {e}"
            else:
                    tweet_data['quoted_tweet'] = None  # Ensure this key exists even if no quote
                    
            #Handle if a tweet is bookmarked
            bookmarkedTweets = await self.client.get_bookmarks(count=20)
            for bookmark in bookmarkedTweets:
                if tweet.id == bookmark.id:
                    tweet_data['is_bookmarked'] = True 
                    print(tweet.id + " " + bookmark.id) 
                    break
                else:
                    tweet_data['is_bookmarked'] = False
            if tweet.in_reply_to:
                try:
                    reply_tweet = await self.client.get_tweet_by_id(tweet.in_reply_to)
                    tweet_data['reply_to'] = {
                        'id': reply_tweet.id,
                        'text': reply_tweet.full_text,
                        'author': reply_tweet.user.name,
                        'username': reply_tweet.user.screen_name,
                        'reply_count': reply_tweet.reply_count,
                        'view_count': reply_tweet.view_count,
                        'quote_count': reply_tweet.quote_count,
                        'retweet_count': reply_tweet.retweet_count,
                        'likes_count': reply_tweet.favorite_count,
                        'created_at': reply_tweet.created_at.isoformat() if hasattr(reply_tweet.created_at, 'isoformat') else str(reply_tweet.created_at),
                    }
                except Exception as e:
                        tweet_data['reply_tweet_error'] = f"Error fetching original tweet: {e}"
            else:
                    tweet_data['reply_to'] = None  # Ensure this key exists even if no quote
            
            
            if hasattr(tweet, 'media') and tweet.media:
                    media_urls = [media['media_url_https'] for media in tweet.media if 'media_url_https' in media]
                    tweet_data['media_urls'] = media_urls  # Add media URLs to the tweet data
                    
            return tweet_data
        
        except Exception as e:
            raise RuntimeError(f"Error getting tweet details: {e}")

        
    async def get_tweet_context(self, tweet_id):
        try:
           
            tweet = await self.client.get_tweet_by_id(tweet_id)
            
            tweet_data = {
            'id': tweet.id,
            'text': tweet.full_text,
            'author': tweet.user.name,
            'username': tweet.user.screen_name,
            'created_at': tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at),
            'reply_count': tweet.reply_count,
            'view_count': tweet.view_count,
            'quote_count': tweet.quote_count,
            'retweet_count': tweet.retweet_count,
            'likes_count': tweet.favorite_count,
            'quote': tweet.quote,
            'in_reply_to': tweet.in_reply_to,
            'is_liked': tweet.favorited,
            }
            
            
            
            # Handle quotes
            if tweet.is_quote_status == True and tweet.quote is not None:
                try:
                    tweet_data['quoted_tweet'] = {
                            'id': tweet.quote.id,
                            'text': tweet.quote.full_text,
                            'author': tweet.quote.user.name,
                            'username': tweet.quote.user.screen_name,
                            'created_at': tweet.quote.created_at.isoformat() if hasattr(tweet.quote.created_at, 'isoformat') else str(tweet.quote.created_at),
                        }
                except Exception as e:
                    tweet_data['quoted_tweet_error'] = f"Error fetching quoted tweet: {e}"
            else:
                tweet_data['quoted_tweet'] = None  # Ensure this key exists even if no quote


            # Handle replies
            if tweet.in_reply_to:
                reply_tweet = await self.client.get_tweet_by_id(tweet.in_reply_to)
                tweet_data['reply_to'] = {
                    'id': reply_tweet.id,
                    'text': reply_tweet.full_text,
                    'author': reply_tweet.user.name,
                    'username': reply_tweet.user.screen_name,
                }
                
            #Handle if a tweet is bookmarked
            for bookmark in bookmarkedTweets:
                if tweet.id == bookmark.id:
                    tweet_data['is_bookmarked'] = True 
                    print(tweet.id + " " + bookmark.id) 
                    break
                else:
                    tweet_data['is_bookmarked'] = False
                    
            return tweet_data
        
        except Exception as e:
            raise RuntimeError(f"Error getting tweet details: {e}")
        
    async def get_replies(self, tweet_id: str, count: int = 20):
        """Fetch replies to a tweet using the get_tweet_by_id method."""
        try:
            # Fetch the tweet by ID to get replies
            tweet = await self.client.get_tweet_by_id(tweet_id)
            
            # Extract replies from the tweet object
            replies = tweet.replies  # Assuming tweet.replies contains a list of reply Tweet objects
            if not replies:
                raise RuntimeError("No replies found for the tweet.")

            # Serialize replies to a JSON-compatible format
            serialized_replies = []
            for reply in replies:
                reply_data = {
                    'id': reply.id,
                    'text': reply.text,
                    'author': reply.user.name,
                    'username': reply.user.screen_name,
                    'created_at': reply.created_at.isoformat() if hasattr(reply.created_at, 'isoformat') else str(reply.created_at),
                    'reply_count': reply.reply_count,
                    'view_count': reply.view_count,
                    'quote_count': reply.quote_count,
                    'retweet_count': reply.retweet_count,
                    'likes_count': reply.favorite_count,
                    'is_liked': reply.favorited,
                }

                if hasattr(reply, 'media') and reply.media:
                    media_urls = [media['media_url_https'] for media in reply.media if 'media_url_https' in media]
                    reply_data['media_urls'] = media_urls  # Add media URLs to the reply data

                serialized_replies.append(reply_data)

            return {
                'replies': serialized_replies
            }
        except Exception as e:
            raise RuntimeError(f"Error fetching replies: {e}")
        
    async def get_user_profile(self, username, count: int = 20):
        try:
            profile = await self.client.get_user_by_screen_name(username, )
            user_tweets = await profile.get_tweets('Tweets', count=count)
            if not user_tweets:
                raise RuntimeError("Twikit returned no tweets. Check your authentication.")

            print(f"i am in the user replies: {user_tweets}")
            # Serialize tweets to a JSON-compatible format
            serialised_tweets = []
            for tweet in user_tweets:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'author': tweet.user.name,
                    'created_at': tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at),
                    'is_liked': tweet.favorited,
                }
                
                if tweet.is_quote_status == True and tweet.quote is not None:
                    try:
                        tweet_data['quoted_tweet'] = {
                            'id': tweet.quote.id,
                            'text': tweet.quote.full_text,
                            'author': tweet.quote.user.name,
                            'username': tweet.quote.user.screen_name,
                            'created_at': tweet.quote.created_at.isoformat() if hasattr(tweet.quote.created_at, 'isoformat') else str(tweet.quote.created_at),
                        }
                    except Exception as e:
                        tweet_data['quoted_tweet_error'] = f"Error fetching quoted tweet: {e}"
                else:
                    tweet_data['quoted_tweet'] = None  # Ensure this key exists even if no quote
                    
                if tweet.in_reply_to:
                    reply_tweet = await self.client.get_tweet_by_id(tweet.in_reply_to)
                    tweet_data['reply_to'] = {
                        'id': reply_tweet.id,
                        'text': reply_tweet.full_text,
                        'author': reply_tweet.user.name,
                        'username': reply_tweet.user.screen_name,
                    }
                
                #Handle if a tweet is bookmarked
                for bookmark in bookmarkedTweets:
                    if tweet.id == bookmark.id:
                        tweet_data['is_bookmarked'] = True 
                        print(tweet.id + " " + bookmark.id) 
                        break
                    else:
                        tweet_data['is_bookmarked'] = False

                if hasattr(tweet, 'media') and tweet.media:
                    media_urls = [media['media_url_https'] for media in tweet.media if 'media_url_https' in media]
                    tweet_data['media_urls'] = media_urls  # Add media URLs to the tweet data

                serialised_tweets.append(tweet_data)
            
            
            
            
            
            print(f"i am in the user getter: {profile}")
            profile_data = {
            'middleId': profile.id,
            'middleName': profile.name,
            'middleUsername': profile.screen_name,
            'middleFollowers': profile.followers_count,
            'middleFollowing': profile.following_count,
            'bio': profile.description,
            'middleProfileImage': profile.profile_image_url,
            'bannerUrl': profile.profile_banner_url,
            'tweets': serialised_tweets
            }
            
            loggedUser = await self.client.user()
            
            if profile.screen_name == loggedUser.screen_name:
                profile_data['is_followable'] = False
            else:
                profile_data['is_followable'] = True
            
            #Handle if you follow the user or not
            profile_followers = await loggedUser.get_following(count=500)
            for user in profile_followers:
                if user.screen_name == profile.screen_name:
                    print(user.screen_name + " = " + profile.screen_name + " MATCH")
                    profile_data['is_followed'] = True 
                    break
                else:
                    print(user.screen_name + " = " + profile.screen_name + " NO MATCH")
                    profile_data['is_followed'] = False
            
            
            return profile_data
        
        except Exception as e:
            print(f"there is an error with the users {e}")
            raise RuntimeError(f"Error fetching user profile: {e}")

    async def get_chat_history(self, user_id):
        """Fetch the chat history with a specific user."""
        try:
            messages = await self.client.get_dm_history(user_id=user_id)
            print(f"i am in the user DMs: {user_id}")
            return [{'sender': msg.id, 'text': msg.text} for msg in messages]
        except Exception as e:
            raise RuntimeError(f"Error fetching chat history: {e}")

    async def send_message(self, user_id, text):
        """Send a message to a specific user."""
        try:
            await self.client.send_dm(user_id=user_id, text=text)
        except Exception as e:
            raise RuntimeError(f"Error sending message: {e}")
        
    async def get_user_id(self, username):
        """Fetch the user_id for a given username."""
        try:
            user = await self.client.get_user_by_screen_name(username)
            print(f"i am in the user DMs: {user.id}")
            return user.id
        except Exception as e:
            raise RuntimeError(f"Error fetching user ID: {e}")
        
    async def search_twitter(self, query):
        try:
            bookmarkedTweets = await self.client.get_bookmarks(count=20)
            
            user_list = await self.client.search_user(query, count=3)
            search_result = await self.client.search_tweet(query=query, count=10,product='Top')
            


            print(f"i am in the search tweets results: {search_result}")
            # Serialize tweets to a JSON-compatible format
            serialised_tweets = []
            for tweet in search_result:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'author': tweet.user.name,
                    'created_at': tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at),
                    'is_liked': tweet.favorited,
                }
                
                if tweet.is_quote_status == True and tweet.quote is not None:
                    try:
                        tweet_data['quoted_tweet'] = {
                            'id': tweet.quote.id,
                            'text': tweet.quote.full_text,
                            'author': tweet.quote.user.name,
                            'username': tweet.quote.user.screen_name,
                            'created_at': tweet.quote.created_at.isoformat() if hasattr(tweet.quote.created_at, 'isoformat') else str(tweet.quote.created_at),
                        }
                    except Exception as e:
                        tweet_data['quoted_tweet_error'] = f"Error fetching quoted tweet: {e}"
                else:
                    tweet_data['quoted_tweet'] = None  # Ensure this key exists even if no quote
                    
                if tweet.in_reply_to:
                    reply_tweet = await self.client.get_tweet_by_id(tweet.in_reply_to)
                    tweet_data['reply_to'] = {
                        'id': reply_tweet.id,
                        'text': reply_tweet.full_text,
                        'author': reply_tweet.user.name,
                        'username': reply_tweet.user.screen_name,
                    }

                if hasattr(tweet, 'media') and tweet.media:
                    media_urls = [media['media_url_https'] for media in tweet.media if 'media_url_https' in media]
                    tweet_data['media_urls'] = media_urls  # Add media URLs to the tweet data
                    
                #Handle if a tweet is bookmarked
                for bookmark in bookmarkedTweets:
                    if tweet.id == bookmark.id:
                        print(f"TWEET IS BOOKMARKED in search results")
                        tweet_data['is_bookmarked'] = True 
                        print(tweet.id + " " + bookmark.id) 
                        break
                    else:
                        tweet_data['is_bookmarked'] = False

                serialised_tweets.append(tweet_data)
            
            
            
            
            
            print(f"i am in the user results: {user_list}")
            serialised_users = []
            for profile in user_list:
                profile_data = {
                'searchResultId': profile.id,
                'searchResultName': profile.name,
                'searchResultUsername': profile.screen_name,
                'searchResultProfileImage': profile.profile_image_url,
                }
                
                loggedUser = await self.client.user()
                
                if profile.screen_name == loggedUser.screen_name:
                    profile_data['is_followable'] = False
                else:
                    profile_data['is_followable'] = True
                
                #Handle if you follow the user or not
                profile_followers = await loggedUser.get_following(count=500)
                for user in profile_followers:
                    if user.screen_name == profile.screen_name:
                        print(user.screen_name + " = " + profile.screen_name + " MATCH")
                        profile_data['is_followed'] = True 
                        break
                    else:
                        print(user.screen_name + " = " + profile.screen_name + " NO MATCH")
                        profile_data['is_followed'] = False
                serialised_users.append(profile_data)
            
            print(f"searching twitter with query: " + query)
            
            return {
                'user_results': serialised_users,
                'tweet_results': serialised_tweets
            }
        
        except Exception as e:
            print(f"there is an error with the users {e}")
            raise RuntimeError(f"Error fetching user profile: {e}")