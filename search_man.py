import datetime
from mastodon import Mastodon, StreamListener
import re
import signal
import sys
import wikipedia

wikipedia.set_lang('ja')


class SearchMan(StreamListener):
    @staticmethod
    def should_respect_ltl(old_status, new_status, min_seconds=10):
        old_time = datetime.datetime.strptime(old_status['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        new_time = datetime.datetime.strptime(new_status['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return (new_time - old_time).seconds <= min_seconds

    @staticmethod
    def take_page(word):
        try:
            titles = wikipedia.search(word)
            page = wikipedia.page(titles[0])
        except:
            page = None
        return page

    @staticmethod
    def make_text_with_respect(acct):
        status = '@{acct} '.format(acct=acct) + "やー、ちょっと疲れたんでパスで・・・"
        spoiler_text = None
        return status, spoiler_text

    @staticmethod
    def make_text_with_page(page, acct):
        spoiler_text = "なになに？「{title}」とは、".format(title=page.title)
        status = '@{acct} '.format(acct=acct) + page.content[:450 - len(page.url)] + '.....\n' + page.url
        return status, spoiler_text

    @staticmethod
    def make_text_with_none(word):
        status = "え、{word}ってなんすか".format(word=word)
        spoiler_text = None
        return status, spoiler_text

    @staticmethod
    def post(mastodon, status, spoiler_text=None, in_reply_to_id=None):
        try:
            mastodon.status_post(
                status=status,
                spoiler_text=spoiler_text,
                in_reply_to_id=in_reply_to_id,  # LTLに現れないので除外
                visibility='private',
            )
        except:
            # 文字数が多かったりするとエラーを吐くらしい
            pass

    def got_word(self, word, acct, status_id):
        page = self.take_page(word)
        if page is None:
            status, spoiler_text = self.make_text_with_none(word)
        else:
            status, spoiler_text = self.make_text_with_page(page, acct)
        self.post(self.mastodon, status, spoiler_text, status_id)

    def on_update(self, status):
        content = self.re_remove_html_tag.sub('', status['content'])
        m = self.re_search.search(content)
        if m is None:
            return

        word = m.group(1)
        acct = status["account"]["acct"]
        status_id = str(status['id'])

        # status history
        if len(self.status_history) >= 1 and self.should_respect_ltl(self.status_history[0], status):
            status, spoiler_text = self.make_text_with_respect(acct)
            self.post(self.mastodon, status, spoiler_text, status_id)
            return
        self.status_history.append(status)
        self.status_history = self.status_history[1:]

        self.got_word(word, acct, status_id)

    def __init__(self):
        self.mastodon = Mastodon(
            client_id='hiho_bot_app.secret',
            access_token='hihobot1.secret',
            api_base_url='https://friends.nico'
        )

        self.status_history = []
        self.re_remove_html_tag = re.compile(r'<[^>]+>')
        self.re_search = re.compile('\s?(.+)って(何|なに|ナニ|何ですか|なんですか)？$')

    def start(self):
        self.post(self.mastodon, '生き返りました')
        self.mastodon.local_stream(self, async=False)

    def finish(self):
        self.post(self.mastodon, '死にました')


def shutdown(*args):
    instance.finish()
    sys.exit(0)


if True:
    for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(sig, shutdown)

    instance = SearchMan()
    instance.start()
