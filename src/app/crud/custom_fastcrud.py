from fastcrud import FastCRUD


class FastCRUDNoCommit(FastCRUD):
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