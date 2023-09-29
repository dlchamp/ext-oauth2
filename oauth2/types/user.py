# thanks disnake

from typing import Literal, Optional, Tuple, TypedDict

from typing_extensions import NotRequired

from oauth2.types import Snowflake

__all__: Tuple[str, ...] = (
    "PartialUser",
    "User",
)


class PartialUser(TypedDict):
    id: Snowflake
    username: str
    discriminator: str  # may be removed in future API versions
    global_name: NotRequired[Optional[str]]
    avatar: Optional[str]


PremiumType = Literal[0, 1, 2]


class User(PartialUser, total=False):
    banner: Optional[str]
    accent_colour: Optional[str]
    bot: bool
    system: bool
    mfa_enabled: bool
    locale: str
    verified: bool
    email: Optional[str]
    flags: int
    premium_type: PremiumType
    public_flags: int
