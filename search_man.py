from mastodon import Mastodon, StreamListener
import re
import signal
import sys
import wikipedia

wikipedia.set_lang('ja')


class SearchMan(StreamListener):
    @staticmethod
    def take_page(word):
        try:
            titles = wikipedia.search(word)
            page = wikipedia.page(titles[0])
        except:
            page = None
        return page

    @staticmethod
    def make_text_with_page(page):
        spoiler_text = "なになに？「{title}」とは、".format(title=page.title)
        status = page.content[:400] + '.....\n' + page.url
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
                # in_reply_to_id=in_reply_to_id,  # LTLに現れないので除外
                visibility='public',
            )
        except:
            # 文字数が多かったりするとエラーを吐くらしい
            pass

    def got_word(self, word, acct, status_id):
        page = self.take_page(word)
        if page is None:
            status, spoiler_text = self.make_text_with_none(word)
        else:
            status, spoiler_text = self.make_text_with_page(page)
            spoiler_text = spoiler_text + ' @{acct}'.format(acct=acct)
        self.post(self.mastodon, status, spoiler_text, status_id)

    def on_update(self, status):
        content = self.re_remove_html_tag.sub('', status['content'])
        m = self.re_search.search(content)
        if m is None:
            return

        word = m.group(1)
        acct = status["account"]["acct"]
        status_id = str(status['id'])
        self.got_word(word, acct, status_id)

    def __init__(self):
        self.mastodon = Mastodon(
            client_id='hiho_bot_app.secret',
            access_token='hihobot1.secret',
            api_base_url='https://friends.nico'
        )

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
