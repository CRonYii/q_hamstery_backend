import json
import logging
import traceback
from functools import lru_cache

from django.conf import settings
from openai import OpenAI
from openai.types import Model

from hamstery.hamstery_settings import SettingsHandler, settings_manager
from hamstery.models.settings import HamsterySettings
from hamstery.models.stats import HamsteryStats

logger = logging.getLogger(__name__)

def is_supported_model(model: Model):
    return ('gpt-4-1106-preview' in model.id) or ('gpt-3.5-turbo-1106' in model.id)

class OpenAIManager:

    enable_handle_title = False

    def __init__(self):
        if settings.BUILDING is True:
            return
        instance = settings_manager.settings
        self.load_client(instance)
        settings_manager.register_settings_handler(SettingsHandler([
            'openai_api_key', 'openai_title_parser_mode', 'openai_title_parser_model',
        ], self.on_openai_config_update))

    def load_client(self, instance: HamsterySettings):
        self.client = OpenAI(api_key=instance.openai_api_key)
        self.enable_openai = instance.openai_api_key != ''
        self.enable_handle_title = self.enable_openai and (instance.openai_title_parser_mode != HamsterySettings.TitleParserMode.DISABLED) and (instance.openai_title_parser_model != '')

    def on_openai_config_update(self, instance: HamsterySettings):
        logger.info(
            'Detected OpenAI configuration changes, loading new OpenAI client...')
        self.load_client(instance)
    
    def list_models(self):
        if not self.enable_openai:
            return []
        models = (filter(is_supported_model,  self.client.models.list()))
        return [{ 'id': model.id, 'created': model.created, 'owned_by': model.owned_by } for model in models]

    @lru_cache(maxsize=128)
    def get_episode_number_from_title(self, title: str) -> int:
        if self.enable_handle_title is False:
            return None
        settings = settings_manager.settings
        stats = HamsteryStats.singleton()
        try:
            logger.info("Querying OpenAI ChatCompletion API Model '%s' to extract episode number from '%s'" % (settings.openai_title_parser_model, title))
            stats.update_title_parser_stats(calls=1)
            response = self.client.chat.completions.create(
                model=settings.openai_title_parser_model,
                messages=[
                    {
                        "role": "system", 
                        "content":
    '''I need you to act as a single API that reads user input in JSON format as a request, processes the request, and responds in JSON format.
    - User input will a JSON object containing a title of a video file. For example: { "title": "([POPGO][Ghost_in_the_Shell][S.A.C._2nd_GIG][08][AVC_FLACx2+AC3][BDrip][1080p][072D2CD7]).mkv" }
    - The string represents a video name of an episode of a show, the task is to guess the episode number out of the video name
    - You should expect any naming convention of the video file. It does not always come in a well-formatted name like EP01. You should expect any natural human language that may indicate the episode number of the file.
    - The file name can be languages, includes but not limit to English, Chinese, Japanese etc.
    - You should respond in a JSON response format containing the episode number the video name. In this example, You should respond with: { "episode": 8 }.
    - If the input format is incorrect, you respond with : { "error": "<an error message>", "episode": null }. 
    Note: You must respond with only the JSON response, you must not respond with any extra text.'''},
                    {
                        "role": "user", 
                        "content": '{ "title": "%s" }' % (title)
                    },
                ],
                response_format={ "type": "json_object" },
            )
        except Exception:
            stats.update_title_parser_stats(fails=1)
            logger.error(traceback.format_exc())
            return None
        if response.usage:
            stats.update_title_parser_stats(prompt_tokens=response.usage.prompt_tokens, 
                                            completion_tokens=response.usage.completion_tokens, 
                                            total_tokens=response.usage.total_tokens)
        choice = response.choices[0]
        # We are not handling finish_reason=length since it's not very likely to happen for a single episode name parsing
        if choice.finish_reason != "stop":
            stats.update_title_parser_stats(fails=1)
            logger.error("OpenAI API failed with: %s" % (choice['finish_reason']))
            return None
        try:
            content = json.loads(choice.message.content)
        except:
            stats.update_title_parser_stats(fails=1)
            logger.error("Faile to decode ChatGPT JSON response: %s" % (choice.message.content))
            return None
        if 'error' in content:
            stats.update_title_parser_stats(fails=1)
            logger.error("OpenAI ChatGPT failed to extract episode number: %s" % (content['error']))
            return None
        episode_number = content['episode']
        logger.info("OpenAI ChatCompletion extracted '%s' from '%s'" % (episode_number, title))
        return episode_number


openai_manager = OpenAIManager()
