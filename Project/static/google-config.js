// Google Calendar credentials — public by design for a client-side app, but
// they MUST stay restricted in Google Cloud Console:
//   - API key: HTTP-referrer locked to the Pages domain, Calendar API v3 only
//   - OAuth client: authorised JavaScript origins only
// Setup steps live in the comment in index.html. Never commit an unrestricted key.
const GOOGLE_CLIENT_ID = '691968245686-5cdnqs5inasr62td91id893m70lg3k09.apps.googleusercontent.com';
const GOOGLE_API_KEY   = 'AIzaSyD3ZFca0_TgjnstevpbHfo1BNtEWtwlAO4';
