# Soundcheck
## Description:
Flask web app to analyze your Spotify listening habits

Login with your Spotify account, and wait for the app to process your data, and it will provide your top artists and top tracks from three timelines of 4 weeks, 6 months, and lifetime. It will also provide a list of the most dancable, happiest and energetic tracks you listen to, your top genres, and the average features of your tracks.

#### Instructions to host:

1. Go to https://developer.spotify.com/dashboard and create a new app. Add the redirect uri "https://127.0.0.1:port-used-by-flask/callback" Copy the credentials and run 
```bash 
export SPOT_ID=client_id

export SPOT_SEC=client_secret
 ```

2. Run
```bash
flask run
```

and press the link. You will be presented with the Login button.

## Preview
![Profile](/images/Profile.png)
![Tracks](/images/Tracks.png)
![Artists](/images/Artists.png)
![Ranked](/images/Feature.png)
![Average](/images/FeatureTable.png)
