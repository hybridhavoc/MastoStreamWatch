# MastoStreamWatch
Script which watches the streaming API endpoint and checks messages against a known list of regular expressions. It takes a configuration file which includes:

- **access-token** : Mastodon access token with read:statuses, write:reports, admin:read:accounts, admin:write:accounts, admin:read:reports, and admin:write:reports permissions
- **server** : Mastodon server domain, i.e. mastodon.social
- **regex-file** : Filepath for a text file with one regular expression per line.
- **log-directory** : Path to a directory for logs.
- **logging-level** : Specify the log level, either error, info, or debug.

Sample config file and regex file provided.

> py watchstream.py -c config.json

The script does require the use of [Requests](https://pypi.org/project/requests/).