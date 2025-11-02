import logging

try:
    from app.internal.pkg.middlewares.correlation import request_id_ctx, idempotency_key_ctx
except Exception as exc:
    request_id_ctx = None  # type: ignore
    idempotency_key_ctx = None  # type: ignore
    logging.error("Error when import", exc_info=exc)


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        req_id = "-"
        idem = "-"
        if request_id_ctx is not None:
            try:
                req_id = request_id_ctx.get()
            except LookupError:
                pass
        if idempotency_key_ctx is not None:
            try:
                idem = idempotency_key_ctx.get()
            except LookupError:
                pass
        setattr(record, "request_id", req_id)
        setattr(record, "idempotency_key", idem)
        return True
