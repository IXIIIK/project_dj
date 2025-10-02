# cards/utils/host.py
import idna

def canonical_host(request_or_host: str):
    """
    Принимает request или строку-хост. Возвращает ascii (punycode), lower.
    """
    if hasattr(request_or_host, "get_host"):
        host = request_or_host.get_host().split(":")[0]
    else:
        host = str(request_or_host).split(":")[0]

    try:
        return idna.encode(host, uts46=True).decode("ascii").lower()
    except Exception:
        return host.lower()
