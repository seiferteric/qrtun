import qrtools
import pyqrcode
from pytun import TunTapDevice, IFF_TAP, IFF_TUN, IFF_NO_PI
import base64
import sys
import select
import signal
import os
import cv2
import scipy.misc
import StringIO
import pygame
SIZE = 1024

class QRTun(object):
    def __init__(self, side):
        self.side = int(side)
        if self.side not in [1,2]:
            print("Side must be 1 or 2")
            raise Exception("Invalid Side")
        self.tun = TunTapDevice(flags=IFF_TUN|IFF_NO_PI, name='qrtun%d'%self.side)
        self.tun.addr = '10.0.8.%d'%(self.side)
        if self.side == 1:
            self.other_side = 2
        else:
            self.other_side = 1
        self.tun.netmask = '255.255.255.0'
        #MTU must be set low enough to fit in a single qrcode
        self.tun.mtu = 500
        self.epoll = select.epoll()
        self.epoll.register(self.tun.fileno(), select.EPOLLIN)
        self.tun.up()
        #self.outfile = 'resources/toscreen%d.png'%(self.side)
        self.outfile = None
        self.infile = 'resources/toscreen%d.png'%(self.other_side)
        self.indata = None
        self.olddata = ""
        self.outdata = ""
        self.running = False
        self.qr = qrtools.QR()
        self.vc = cv2.VideoCapture(0)
        self.vc.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 720)
        self.vc.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
        pygame.init()
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([pygame.KEYDOWN, pygame.QUIT])
        self.screen = pygame.display.set_mode((SIZE, SIZE))
        self.scale = 12
        pygame.display.set_caption("qrtun - QR Code scale %d"%(self.scale))
    def read_tun(self):
        events = self.epoll.poll(0)
        if events:
            self.outdata = self.tun.read(self.tun.mtu)
            return True
        return False
    def write_qrcode(self):

        #Could not get binary mode working with qrtool library... so instead opt to
        # use base32 for now, obviously binary would be better.
        #Base32 encode since alphanumeic qr code only allows A-Z, 0-9 and some
        # symbols, but base64 uses lowercase as well....
        #Also alphanumeric mode does not support '=', so replace with '/' and
        # switch back on the other side...
        #body = base64.b32encode(self.outdata).replace('=', '/')
        #qr = qrtools.QR()
        #qrb = qrtools.QR()
        #qrb.data = "  "
        #qr.data = body
        code = pyqrcode.create(self.outdata, mode='binary', encoding='string_escape')

        #Had an issue where decoded data did not match encoded data...
        #So I just add plus symbols as padding until they match, then strip
        # on the other side....
        #while self.outdata != qrb.data:
        #    #qr.pixel_size = 12
        #    #qr.encode(self.outfile)
        self.outfile = StringIO.StringIO()
        code.png(self.outfile, scale=self.scale)
        self.outfile.seek(0)

        #    qrb.decode(self.outfile)
        #    if qrb.data != qr.data:
        #        print("EncodingFailure", qr.data)
        #        qr.data += '+'
        if self.outfile and not self.outfile.closed:
            #self.outfile = StringIO.StringIO(self.outfile.getvalue())
            pimg = pygame.image.load(self.outfile)
            if pimg.get_width() > self.screen.get_width() or pimg.get_height() > self.screen.get_height():
                pygame.display.set_mode((pimg.get_width(), pimg.get_height()))
            self.screen.fill((0,0,0))
            self.screen.blit(pimg, (0,0))
            pygame.display.flip()


        self.msg_read = False
    def write_tun(self):
        try:
            if len(self.indata.get('body')) > 0:
                data = self.indata.get('body')
                if data != self.olddata:
                    self.tun.write(data)
                    #This is a hacky way to avoid dup packets...
                    #surely a better way to do this...
                    self.olddata = data
        except:
            print("Failed to write to tun!")
    def read_qrcode(self):
        qr = qrtools.QR()
        try:
            if not qr.decode(self.infile):
                return False
            #Hack to convert unicde to python string
            body = qr.data.encode('latin-1')
            self.indata = {'body': body}
            self.write_tun()
        except:
            pass


    def run(self):
        self.running = True
        while self.running:
            if self.read_tun():
                self.write_qrcode()

            rval, frame = self.vc.read()
            if not rval:
                running = False
                break
            scipy.misc.toimage(frame).save(self.infile)
            self.read_qrcode()

               

            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False 
                    pygame.quit()
                elif event.key == pygame.K_UP:
                    self.scale += 1
                    pygame.display.set_caption("qrtun - QR Code scale %d"%(self.scale))
                    self.write_qrcode()
                elif event.key == pygame.K_DOWN:
                    self.scale -= 1
                    pygame.display.set_caption("qrtun - QR Code scale %d"%(self.scale))
                    self.write_qrcode()
 
        try:
            #os.unlink(self.outfile)
            os.unlink(self.infile)
        except:
            pass

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ['1', '2']:
        print("Must specify side 1 or 2 of tunnel")
        sys.exit(0)
    tun = QRTun(sys.argv[1])
    def signal_handler(signal, frame):
            print('Shutting down')
            tun.running = False
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)




    try:
        os.mkdir("resources")
    except:
        pass
    
    tun.run()
    sys.exit(0)


if __name__ == "__main__":
    main()
