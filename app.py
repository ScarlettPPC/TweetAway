from quart import Quart, request, jsonify, render_template
import os
from twitter_client import TwitterClient
from flask import send_from_directory

app = Quart(__name__)

# Initialize TwitterClient with the path to your cookies file
twitter_client = TwitterClient(cookie_file="cookie.json")

@app.route('/')
async def home():
    """Render the home page."""
    return await render_template('index.html')

@app.route('/tweet_form.html')
async def tweet_form():
    """Render the tweet form page."""
    return await render_template('tweet_form.html')

@app.route('/search', methods=['GET'])
async def search_tweets():
    """Search for tweets based on a query."""
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    try:
        tweets = await twitter_client.search_tweets(query)  # Use async search method
        return jsonify({'tweets': tweets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tweet', methods=['POST'])
async def create_tweet():
    """Post a tweet."""
    data = await request.json  # Use await for request.json in Quart
    content = data.get('content')
    image_path1 = data.get('image_path1')
    image_path2 = data.get('image_path2')
    image_path3 = data.get('image_path3')
    image_path4 = data.get('image_path4')
    alt_text1 = data.get('alt_text1')
    alt_text2 = data.get('alt_text2')
    alt_text3 = data.get('alt_text3')
    alt_text4 = data.get('alt_text4')
    reply_to = data.get('reply_to')
    attachment_url = data.get('attachment_url')

    if not content:
        return jsonify({'error': 'Content is required to create a tweet'}), 400

    try:
        image_paths = [image_path1, image_path2, image_path3, image_path4]
        alt_texts = [alt_text1, alt_text2, alt_text3, alt_text4]
        response = await twitter_client.create_tweet(content, image_paths, alt_texts, reply_to, attachment_url)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/quote', methods=['POST'])
async def quote_tweet():
    """Quote a tweet."""
    data = await request.json  # Use await for request.json in Quart
    content = data.get('content')
    image_path1 = data.get('image_path1')
    image_path2 = data.get('image_path2')
    image_path3 = data.get('image_path3')
    image_path4 = data.get('image_path4')
    alt_text1 = data.get('alt_text1')
    alt_text2 = data.get('alt_text2')
    alt_text3 = data.get('alt_text3')
    alt_text4 = data.get('alt_text4')
    attachment_url = data.get('attachment_url')

    if not content:
        return jsonify({'error': 'Content is required to create a tweet'}), 400

    try:
        image_paths = [image_path1, image_path2, image_path3, image_path4]
        alt_texts = [alt_text1, alt_text2, alt_text3, alt_text4]
        response = await twitter_client.quote_tweet(content, image_paths, alt_texts, attachment_url)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/home_feed', methods=['GET'])
async def home_feed():
    """Fetch the user's home feed."""
    count = request.args.get('count', 20, type=int)
    seen_tweet_ids = request.args.getlist('seen_tweet_ids')
    cursor = request.args.get('cursor', None)

    try:
        feed = await twitter_client.get_home_feed(count=count, seen_tweet_ids=seen_tweet_ids, cursor=cursor)
        return jsonify(feed)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/bookmarks_feed', methods=['GET'])
async def bookmarks_feed():
    """Fetch the user's bookmarks."""
    count = request.args.get('count', 20, type=int)

    try:
        feed = await twitter_client.get_bookmarks(count=count)
        return jsonify(feed)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/notifications_list', methods=['GET'])
async def notifications_list():
    """Fetch the user's notifications."""
    count = request.args.get('count', 20, type=int)

    try:
        feed = await twitter_client.get_notifications(count=count)
        return jsonify(feed)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/current_user', methods=['GET'])
async def current_user():
    """Fetch the logged-in user's profile details."""
    try:
        current_user = await twitter_client.get_user()  # Get the profile info
        return jsonify(current_user)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/tweet/<tweet_id>', methods=['GET'])
async def get_tweet(tweet_id):
    """fetch a tweet with details by id"""
    try:
        tweet = await twitter_client.get_tweet(tweet_id)
        return jsonify(tweet)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/like/<tweet_id>', methods=['POST'])
async def like_tweet(tweet_id):
    """Like a tweet."""
    try:
        await twitter_client.like_tweet(tweet_id)
        return jsonify({'response': 'Tweet liked successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/bookmark/<tweet_id>', methods=['POST'])
async def bookmark_tweet(tweet_id):
    """Bookmark a tweet."""
    try:
        await twitter_client.bookmark_tweet(tweet_id)
        return jsonify({'response': 'Tweet bookmarked successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/unbookmark/<tweet_id>', methods=['POST'])
async def unbookmark_tweet(tweet_id):
    """Delete a bookmark."""
    try:
        await twitter_client.unbookmark_tweet(tweet_id)
        return jsonify({'response': 'Removed bookmark successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/unlike/<tweet_id>', methods=['POST'])
async def unlike_tweet(tweet_id):
    """Unlike a tweet."""
    try:
        await twitter_client.unlike_tweet(tweet_id)
        return jsonify({'response': 'Tweet unliked successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/follow/<user_id>', methods=['POST'])
async def follow_user(user_id):
    """Follow a user."""
    try:
        await twitter_client.follow_user(user_id)
        return jsonify({'response': 'User followed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/unfollow/<user_id>', methods=['POST'])
async def unfollow_user(user_id):
    """Unfollow a user."""
    try:
        await twitter_client.unfollow_user(user_id)
        return jsonify({'response': 'User unfollowed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/block/<user_id>', methods=['POST'])
async def block_user(user_id):
    """Block a user."""
    try:
        await twitter_client.block_user(user_id)
        return jsonify({'response': 'User blocked successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/unblock/<user_id>', methods=['POST'])
async def unblock_user(user_id):
    """Unblock a user."""
    try:
        await twitter_client.unblock_user(user_id)
        return jsonify({'response': 'User unblocked successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/retweet/<tweet_id>', methods=['POST'])
async def retweet(tweet_id):
    """Retweet."""
    try:
        # Use the TwitterClient to reweet
        response = await twitter_client.retweet(tweet_id)
        return jsonify({'response': 'Retweeted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/tweet/<tweet_id>/replies')
async def get_replies(tweet_id):
    try:
        replies = await twitter_client.get_replies(tweet_id)
        return jsonify(replies)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/tweet/<tweet_id>/context')
async def get_tweet_context(tweet_id):
    """fetch a tweet with details by id"""
    try:
        tweet = await twitter_client.get_tweet_context(tweet_id)
        return jsonify(tweet)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/user_profile/<username>', methods=['GET'])
async def user_profile(username):
    """Fetch the user's profile and their tweets."""
    try:
        # Fetch user data
        user_data = await twitter_client.get_user_profile(username, count=10)


        # Prepare the response
        return jsonify(user_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/direct_messages/<user_id>', methods=['GET'])
async def chat_history(user_id):
    """Fetch chat history with a specific user."""
    try:
        messages = await twitter_client.get_chat_history(user_id)
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_message/<user_id>', methods=['POST'])
async def send_message(user_id):
    """Send a direct message to a user."""
    data = await request.json
    text = data.get('text')
    if not text:
        return jsonify({'error': 'Message text is required'}), 400
    try:
        await twitter_client.send_message(user_id, text)
        return jsonify({'response': 'Message sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_user_id/<username>', methods=['GET'])
async def get_user_id(username):
    """Fetch the user_id for a given username."""
    try:
        user_id = await twitter_client.get_user_id(username)
        return jsonify({'user_id': user_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/search/<query>', methods=['GET'])
async def search(query):
    """Search tweets and users using key words."""
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    
    try:
        search_results = await twitter_client.search_twitter(query=query)
        
        return jsonify(search_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
