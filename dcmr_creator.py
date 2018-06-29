import pgpy
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
import json
import smtplib
from email.mime.text import MIMEText
import os


class Dcmr():
    def __init__(self, file_path, host_address):
        self.parts = []
        data = open(file_path, 'r')
        self.cmr_file = json.load(data)
        self.host = open(host_address).read()

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

    def keys_out(self):
        '''sending private PGP keys via email; smtp adress is taken from file smtp.txt - few most popular smtps
        will be defined there in the future'''
        for i in self.parts:
            print(i)
            if not i == self.parts[0]:
                mail = MIMEText(str(i[1]))
                mail['Subject'] = 'Your private key to CMR waybill no. %s' % self.cmr_file[0]
                mail['From'] = self.parts[0][0]
                mail['To'] = i[0]
                server = smtplib.SMTP(self.host)
                server.starttls()
                server.login(self.parts[0][0], input('email password: '))
                server.send_message(mail)
                server.quit()

    def signing(self, signer, file_path, output_path="sender_pgp_msg.txt"):
        '''signing waybill with private key and exoporting as .txt file'''
        message = pgpy.PGPMessage.new(file_path, file=True)
        message |= signer.sign(message)
        output = open(output_path, "w")
        output.write(str(message))
        return message

    def update_block(self, up_file):
        '''updating waybill blockchain (wallet) with any box_no:value pair - using ChainSign'''
        signer = self.parts[0][1]
        self.signing(signer, up_file, output_path=up_file)
        try:
            os.system('py -3.4 timestamper.py changes.json')
            return print('jupi! CS works')
        except:
            print('connection with CS failed')

    def let_send(self):
        '''executable function'''
        self.load_data()
        self.get_keys()
        self.signing(self.parts[0][1], "ecmr.json")
        self.update_block('changes.json')
        self.keys_out()

    def load_data(self):
        '''gathering all participants email addresses (Sender, Consignee, Carrier) together'''
        box_no = [1, 2, 16]
        for i in box_no:
            self.parts.append(self.cmr_file[i][2])


c = Dcmr("ecmr.json", 'smtp.txt')
c.let_send()
