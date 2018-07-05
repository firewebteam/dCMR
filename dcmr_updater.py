import pgpy
import os


class Updater:
    def __init__(self, up_file_path, config_path):
        self.up_file = up_file_path
        config = open(config_path).read()
        self.priv_key = config.split(";")[1]

    def signing(self, output_path="changes_sign.txt"):
        '''signing changes with private key and exoporting as .txt file'''
        message = pgpy.PGPMessage.new(self.up_file, file=True)
        message |= self.priv_key.sign(message)
        output = open(output_path, "w")
        output.write(str(message))
        return message

    def updating(self):
        '''updating waybill blockchain (wallet) with signed update file - using ChainSign timestamper'''
        try:
            os.system('py -3.4 timestamper.py changes.json')
            return print('jupi! CS works')
        except:
            print('connection with CS failed')


def main():
    up = Updater("changes.json", "config.txt")
    up.signing()
    up.updating()


if __name__ == '__main__':
    main()
