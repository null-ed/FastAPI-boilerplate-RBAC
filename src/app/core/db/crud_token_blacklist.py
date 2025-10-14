from ...crud.custom_fastcrud import FastCRUDNoCommit

from ..db.token_blacklist import TokenBlacklist
from ..schemas import TokenBlacklistCreate, TokenBlacklistRead, TokenBlacklistUpdate

CRUDTokenBlacklist = FastCRUDNoCommit[
    TokenBlacklist,
    TokenBlacklistCreate,
    TokenBlacklistUpdate,
    TokenBlacklistUpdate,
    TokenBlacklistUpdate,
    TokenBlacklistRead,
]
crud_token_blacklist = CRUDTokenBlacklist(TokenBlacklist)
