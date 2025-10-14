from .custom_fastcrud import FastCRUDNoCommit

from ..models.tier import Tier
from ..schemas.tier import TierCreateInternal, TierDelete, TierRead, TierUpdate, TierUpdateInternal

CRUDTier = FastCRUDNoCommit[Tier, TierCreateInternal, TierUpdate, TierUpdateInternal, TierDelete, TierRead]
crud_tiers = CRUDTier(Tier)
