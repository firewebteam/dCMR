from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from datetime import datetime
import json
import hashlib
import sys
import platform
import os


class Timestamper(object):
    """Basic timestamping interface"""

    def verify(self, digest):
        """Checks if digest (hash) is present in selected blockchain and returns
        its timestamp and (unique) transaction hash/id in which it has been
        announced. Returns None if it has not been found."""
        raise NotImplemented

    def publish(self, digest):
        """Publishes digest onto selected blockchain and returns transaction
        hash/id (which should match with one reported by verify call)"""
        raise NotImplemented

    def hash_file(self, fd):
        """Returns sha256 hash of provided open fd."""

        filehash = hashlib.sha256()

        for chunk in iter(lambda: fd.read(8192), b""):
            filehash.update(chunk)

        return filehash.hexdigest()

    def verify_file(self, fd):
        """Verifies file from open fd using sha256."""

        return self.verify(self.hash_file(fd))

    def publish_file(self, fd):
        """Publishes file from open fd using sha256."""

        return self.publish(self.hash_file(fd))


class NamecoinTimestamper(Timestamper):
    """Simple Namecoin proof-of-existence timestamper implementation based on
    poe/ identity prefix.
    """

    IDENTITY = 'poe/{}'

    def __init__(self, url='http://127.0.0.1:8336'):
        self.client = AuthServiceProxy(url)

    def verify(self, digest):
        """Namecoin poe/ verification implementation"""

        try:
            hist = self.client.name_history(self.IDENTITY.format(digest))
        except JSONRPCException as exc:
            # FIXME maybe?
            if str(exc).split(': ')[0] == '-4':
                return None

            raise

        txid = hist[0]['txid']
        tx = self.client.gettransaction(txid)

        return {
            'txid': txid,
            'timestamp': datetime.utcfromtimestamp(tx['time']),
            }

    def publish(self, digest):
        """Namecoin poe/ publishing implementation"""

        name = self.IDENTITY.format(digest)
        reg_txid, nonce = self.client.name_new(name)

        txid = self.client.name_firstupdate(name, nonce, reg_txid, json.dumps({
            'ver': 0,
            }))

        return txid

def parse_bitcoin_conf(fd):
    """Returns dict from bitcoin.conf-like configuration file from open fd"""
    conf = {}
    for l in fd:
        l = l.strip()
        if not l.startswith('#') and '=' in l:
            key, value = l.split('=', 1)
            conf[key] = value

    return conf

def coin_config_path(coin):
    """Returns bitcoin.conf-like configuration path for provided coin"""

    paths = {
        # FIXME use proper AppData path
        'Windows': '~\AppData\Roaming\{0}\{0}.conf',
        'Darwin': '~/Library/Application Support/{0}/{0}.conf',

        # Fallback path (Linux, FreeBSD...)
        None: '~/.{0}/{0}.conf',
        }

    path = paths.get(platform.system(), paths[None])

    return os.path.expanduser(path.format(coin))

def rpcurl_from_config(coin, default=None, config_path=None):
    """Returns RPC URL loaded from bitcoin.conf-like configuration of desired
    currency"""

    config_path = config_path or coin_config_path(coin)
    cookie_path = os.path.join(os.path.dirname(config_path), '.cookie')

    credentials = ''

    try:
        with open(config_path) as fd:
            conf = parse_bitcoin_conf(fd)
            if 'rpcpassword' in conf:
                # Password authentication
                credentials = '{rpcuser}:{rpcpassword}'.format(**conf)
            elif os.path.exists(cookie_path):
                # Cookie authentication
                with open(cookie_path) as cfd:
                    credentials = cfd.read().decode('utf-8').strip() \
                        .replace('/', '%2F')
            else:
                return default

            return 'http://{0}@127.0.0.1:{1}/' \
                .format(credentials, conf.get('rpcport', 8336))
    except:
        return default

def main():
    ts = NamecoinTimestamper(rpcurl_from_config('namecoin', 'http://127.0.0.1:8336/'))
    print(sys.argv)
    for f in ['changes.json']: #sys.argv[1:]:
        with open(f) as fd:
            timestamp = ts.verify(fd)

            if timestamp:
                print('File {} found at: {}'.format(f, timestamp['timestamp']))
            else:
                print('File {} not found'.format(f))


if __name__ == "__main__":
    main()
