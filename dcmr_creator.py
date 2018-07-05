import pgpy
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
import json
import smtplib


class Dcmr():
    def __init__(self, file_path, host_address):
        self.parts = []
        data = open(file_path, 'r')
        self.cmr_file = json.load(data)
        self.host = (open(host_address).read().split(";"))[0]

    def get_keys(self):
        '''genarating private keys using PGP and add keys to participants in self.parts list'''
        keys = []
        for i in self.parts:
            key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 512)
            uid = pgpy.PGPUID.new(i[0], comment=i[1], email=i[2])
            key.add_uid(uid, usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
                        hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512, HashAlgorithm.SHA224],
                        ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
                        compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP,
                                     CompressionAlgorithm.Uncompressed])
            keys.append(key)
        self.parts = list(zip(self.parts, keys))

    def export_key(self, path='config.txt'):
        '''exporitng priv_key to config.txt file, we will use it for i.e. signing updates'''
        config = open(path, "a")
        exp = ";\n" + str(self.parts[0][1])
        config.write(exp)

    def keys_out(self):
        '''sending private PGP keys via email; smtp adress is taken from file smtp.txt - few most popular smtps
        will be defined there in the future'''
        for i in self.parts:
            if not i == self.parts[0]:
                content = str(i[1])
                username = self.parts[0][0]
                receiver = i[0]

                mail = smtplib.SMTP(self.host, 587)
                mail.ehlo()
                mail.starttls()
                mail.login(username, input('Email password: '))

                mail.sendmail(username, receiver, content)
                mail.close()

    def signing(self, signer, file_path, output_path="sender_pgp_msg.txt"):
        '''signing waybill with private key and exoporting as .txt file'''
        message = pgpy.PGPMessage.new(file_path, file=True)
        message |= signer.sign(message)
        output = open(output_path, "w")
        output.write(str(message))
        return message

    def load_data(self):
        '''gathering all participants email addresses (Sender, Consignee, Carrier) together'''
        box_no = [1, 2, 16]
        for i in box_no:
            self.parts.append(self.cmr_file[i][2])


def main():
    '''executable function'''
    wbill = Dcmr("ecmr.json", 'smtp.txt')
    wbill.load_data()
    wbill.get_keys()
    wbill.export_key()
    wbill.signing(wbill.parts[0][1], "ecmr.json")
    wbill.keys_out()


if __name__ == '__main__':
    main()
