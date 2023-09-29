from __future__ import annotations

import asyncio
import collections
import logging
import secrets
from typing import Optional, Tuple

import aiohttp

from oauth2._http import HTTPClient
from oauth2.appinfo import AppInfo
from oauth2.scopes import OAuthScopes
from oauth2.session import OAuth2Session
from oauth2.utils import PromptTypes, ResponseTypes, get_oauth2_url

__all__: Tuple[str, ...] = ("Client",)
_log = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        client_id: int,
        *,
        scopes: OAuthScopes,
        client_secret: str,
        redirect_uri: str,
        bot_token: Optional[str] = None,
        connector: Optional[aiohttp.BaseConnector] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        max_states_cache: int = 1000,
    ) -> None:
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.__states: collections.deque[str] = collections.deque(
            maxlen=max_states_cache
        )

        # should raise a deprecation warning
        self.loop = loop or asyncio.get_event_loop()
        self.http = HTTPClient(
            connector,
            self.loop,
            client_id=client_id,
            client_secret=client_secret,
            bot_token=bot_token,
        )

    @property
    def states(self) -> Tuple[str, ...]:
        return tuple(self.__states)

    async def generate_state_link(
        self,
        permissions: Optional[int] = None,
        guild_id: Optional[int] = None,
        disable_guild_select: bool = False,
        response_type: ResponseTypes = "code",
        prompt: PromptTypes = "consent",
    ) -> str:
        # implementation of state for security reasons
        # https://discord.com/developers/docs/topics/oauth2#state-and-security
        state_future = self.loop.run_in_executor(None, secrets.token_urlsafe, 32)
        await state_future

        state = state_future.result()
        self.__states.append(state)

        return get_oauth2_url(
            client_id=self.client_id,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            response_type=response_type,
            state=state,
            prompt=prompt,
            permissions=permissions,
            guild_id=guild_id,
            disable_guild_select=disable_guild_select,
        )

    async def exchange_code(self, code: str, state: Optional[str]) -> OAuth2Session:
        data = await self.http._exchange_token(
            code=code, redirect_uri=self.redirect_uri
        )

        # validate the state
        if state:
            # this state wasn't generated by us!
            if state not in self.__states:
                raise

        return OAuth2Session.from_data(data, state, self)

    async def fetch_client_credentials_token(self) -> OAuth2Session:
        data = await self.http._get_client_credentials_token(self.scopes)
        return OAuth2Session.from_data(data, None, self)

    async def fetch_application_info(self) -> AppInfo:
        data = await self.http._get_app_info()
        return AppInfo.from_payload(data, self.http)
