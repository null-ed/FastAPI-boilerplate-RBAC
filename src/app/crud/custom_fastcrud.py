from typing import TypeVar
from fastcrud import FastCRUD


ModelT = TypeVar("ModelT")
CreateT = TypeVar("CreateT")
UpdateT = TypeVar("UpdateT")
UpdateInternalT = TypeVar("UpdateInternalT")
DeleteT = TypeVar("DeleteT")
ReadT = TypeVar("ReadT")

class FastCRUDNoCommit(FastCRUD[ModelT, CreateT, UpdateT, UpdateInternalT, DeleteT, ReadT]):
    async def create(self, *args, **kwargs):
        kwargs.setdefault("commit", False)
        return await super().create(*args, **kwargs)

    async def update(self, *args, **kwargs):
        kwargs.setdefault("commit", False)
        return await super().update(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        kwargs.setdefault("commit", False)
        return await super().delete(*args, **kwargs)

    async def db_delete(self, *args, **kwargs):
        kwargs.setdefault("commit", False)
        return await super().db_delete(*args, **kwargs)