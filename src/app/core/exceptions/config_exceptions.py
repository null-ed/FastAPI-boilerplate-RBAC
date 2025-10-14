class MissingDatabaseSessionError(Exception):
    def __init__(
        self,
        message: str = (
            "AsyncSession not found or invalid. Ensure the route provides a database dependency, "
            "e.g., `db: AsyncSession = Depends(async_get_db)`, or configure db_param_name correctly."
        ),
    ) -> None:
        self.message = message
        super().__init__(self.message)