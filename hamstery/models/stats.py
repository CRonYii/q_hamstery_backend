from django.db import models
from django.db.models import F

from hamstery.models.singleton import SingletonModel

# XXX: Has racing condition issue
class HamsteryStats(SingletonModel):
    openai_title_parser_calls = models.IntegerField(default=0)
    openai_title_parser_failures = models.IntegerField(default=0)
    openai_title_parser_prompt_tokens_used = models.IntegerField(default=0)
    openai_title_parser_completion_tokens_used = models.IntegerField(default=0)
    openai_title_parser_total_tokens_used = models.IntegerField(default=0)

    def update_title_parser_stats(self, calls=0, fails=0, prompt_tokens=0, completion_tokens=0, total_tokens=0):
        self.openai_title_parser_calls = F('openai_title_parser_calls') + calls
        self.openai_title_parser_failures = F('openai_title_parser_failures') + fails
        self.openai_title_parser_prompt_tokens_used = F('openai_title_parser_prompt_tokens_used') + prompt_tokens
        self.openai_title_parser_completion_tokens_used = F('openai_title_parser_completion_tokens_used') + completion_tokens
        self.openai_title_parser_total_tokens_used = F('openai_title_parser_total_tokens_used') + total_tokens
        self.save()

    def reset_title_parser_stats(self):
        self.openai_title_parser_calls = 0
        self.openai_title_parser_failures = 0
        self.openai_title_parser_prompt_tokens_used = 0
        self.openai_title_parser_completion_tokens_used = 0
        self.openai_title_parser_total_tokens_used = 0
        self.save()

    def __str__(self) -> str:
        return 'Hamstery Stats'
