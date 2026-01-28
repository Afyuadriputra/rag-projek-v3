class RequestIdFilter:
    """
    Menambahkan request_id ke record log.
    Jika belum ada, isi dengan '-'.
    """
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True
