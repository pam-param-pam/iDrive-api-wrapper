class User:
    def __init__(self, data):
        self.name = data['user']['name']
        self.root_id = data['user']['root']
        self.max_discord_message_size = data['user']['maxDiscordMessageSize']
        self.perms = data['perms']
        self.settings = data['settings']

    def __str__(self):
        return f"User({self.name})"

    def __repr__(self):
        return self.name
