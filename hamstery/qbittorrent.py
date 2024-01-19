import logging

import qbittorrentapi
from qbittorrentapi import exceptions as qbt_exceptions
from django.conf import settings
from packaging import version

from hamstery.hamstery_settings import SettingsHandler, settings_manager
from hamstery.models.settings import HamsterySettings

logger = logging.getLogger(__name__)

# require Web API >= 2.8.3 to run properly
MINIMUM_WEB_API_VERSION = version.parse('2.8.3')


class Qbittorrent:

    client = None
    known_status = False
    auto_test = False

    def __init__(self):
        if settings.BUILDING is True:
            return
        instance = settings_manager.settings
        self.load_client(instance)
        settings_manager.register_settings_handler(SettingsHandler([
            'qbittorrent_host',
            'qbittorrent_port',
            'qbittorrent_username',
            'qbittorrent_password',
        ], self.on_qbt_config_update))

    def load_client(self, instance: HamsterySettings):
        self.client = qbittorrentapi.Client(
            host=instance.qbittorrent_host,
            port=instance.qbittorrent_port,
            username=instance.qbittorrent_username,
            password=instance.qbittorrent_password,
        )
        if self.auto_test:
            self.test_connection()

    def on_qbt_config_update(self, instance: HamsterySettings):
        logger.info(
            'Detected qbittorrent configuration changes, loading new qbittorrent client...')
        self.load_client(instance)

    def test_connection(self):
        [self.known_status, msg] = self.__test_connection()
        logger.info('Testing qBittorrent connection...')
        if self.known_status:
            logger.info(msg)
        else:
            logger.error(msg)
        return [self.known_status, msg]

    def __test_connection(self):
        try:
            qbt.client.auth_log_in()
            qbt_version = version.parse(qbt.client.app.web_api_version)
            # check if version requirement is satisfied
            if qbt_version < MINIMUM_WEB_API_VERSION:
                return [False,
                        f'''Please update your qBittorrent client
The minimum supported qBittorrent Web API Version is: {MINIMUM_WEB_API_VERSION}
Your qBittorrent Web API Version is: {qbt.client.app.web_api_version}''']
            # Sucessfully connected to a compatible qBittorrent client, display qBittorrent info
            return [True,
                    f'''Connected to qBittorrent@{qbt.client.host}:{qbt.client.port} successfully
qBittorrent Version: {qbt.client.app.version}
qBittorrent Web API Version: {qbt.client.app.web_api_version}''']
        except qbt_exceptions.APIError as e:
            # An error occured with the connection attempt
            return [False,
                    f'''Connection to qBittorrent@{qbt.client.host}:{qbt.client.port} failed with error:
{e}''']


qbt = Qbittorrent()
